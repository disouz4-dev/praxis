//! Detector de fala e corte em trechos — a mesma lógica do vad_worker do Praxis em
//! Python (medida com fala real), sobre o Silero do sherpa-onnx:
//!   * pré-gravação: o detector dispara um pouco depois do início da fala; os últimos
//!     PREROLL_S de áudio entram antes, para a primeira sílaba não se perder;
//!   * trecho longo é cortado no ponto mais silencioso do final (corte inteligente),
//!     sem reiniciar o detector;
//!   * sobra menor que MIN_SEG_S vai junto com o próximo trecho, ou sai sozinha
//!     depois de CARRY_MAX_WAIT_S de silêncio ("Sim." não fica preso).

use std::collections::VecDeque;

use anyhow::{anyhow, Result};
use sherpa_onnx::{SileroVadModelConfig, VadModelConfig, VoiceActivityDetector};

pub const SR: usize = 16_000;
pub const CHUNK: usize = 512; // 32 ms
pub const CHUNK_S: f32 = CHUNK as f32 / SR as f32;
pub const SILENCE_S: f32 = 0.2;
pub const PREROLL_S: f32 = 0.25;
pub const MIN_SEG_S: f32 = 0.8;
pub const CARRY_MAX_WAIT_S: f32 = 1.0;
pub const SMART_CUT_WINDOW_S: f32 = 1.5;
/// Sensibilidade 0,25: corta menos frases no meio (inglês 4,0% → 2,8% de erro real).
pub const THRESHOLD: f32 = 0.25;

#[derive(Debug, Clone, Copy)]
pub struct SegmenterConfig {
    pub threshold: f32,
    pub max_seg_s: f32,
    pub preroll_s: f32,
    pub smart_cut: bool,
}

impl Default for SegmenterConfig {
    fn default() -> Self {
        Self { threshold: THRESHOLD, max_seg_s: 6.0, preroll_s: PREROLL_S, smart_cut: true }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Event {
    None,
    Start,
    End,
}

/// O que diz quando a fala começa e termina (permite testar o corte sem o modelo).
pub trait SpeechProbe {
    fn feed(&mut self, chunk: &[f32]) -> Event;
    fn reset(&mut self);
}

/// Silero v6 — o mesmo arquivo e a mesma regra do Praxis em Python (OnnxSileroVAD, que
/// imita o VADIterator do Silero): começa quando a probabilidade passa do limiar; termina
/// quando fica abaixo de limiar − 0,15 por SILENCE_S. Roda no onnxruntime que o sherpa-onnx
/// instala ao lado do executável (carregado na hora de rodar).
pub struct SileroV6 {
    session: ort::session::Session,
    h: Vec<f32>,
    c: Vec<f32>,
    ctx: Vec<f32>,
    threshold: f32,
    triggered: bool,
    temp_end: usize,
    current: usize,
}

const CONTEXT: usize = 64;

fn onnxruntime_path() -> std::path::PathBuf {
    if let Ok(p) = std::env::var("PRAXIS_ONNXRUNTIME") {
        return p.into();
    }
    let dir = std::env::current_exe().ok().and_then(|p| p.parent().map(|d| d.to_path_buf())).unwrap_or_default();
    let name = if cfg!(target_os = "windows") {
        "onnxruntime.dll"
    } else if cfg!(target_os = "macos") {
        "libonnxruntime.dylib"
    } else {
        "libonnxruntime.so"
    };
    dir.join(name)
}

static ORT_ENV: std::sync::OnceLock<std::result::Result<ort::environment::Environment, String>> = std::sync::OnceLock::new();

impl SileroV6 {
    pub fn load(model: &str, threshold: f32) -> Result<Self> {
        let env = ORT_ENV
            .get_or_init(|| {
                ort::init_from(onnxruntime_path())
                    .map_err(|e| e.to_string())?
                    .build()
                    .map_err(|e| e.to_string())
            })
            .as_ref()
            .map_err(|e| anyhow!("onnxruntime: {e}"))?;
        let e = |x: &dyn std::fmt::Display| anyhow!("Silero v6: {x}");
        let session = ort::session::Session::builder(env)
            .map_err(|x| e(&x))?
            .with_intra_threads(1)
            .map_err(|x| e(&x))?
            .with_inter_threads(1)
            .map_err(|x| e(&x))?
            .commit_from_file(model)
            .map_err(|x| e(&x))?;
        let mut v = Self { session, h: vec![], c: vec![], ctx: vec![], threshold, triggered: false, temp_end: 0, current: 0 };
        v.reset();
        Ok(v)
    }

    fn prob(&mut self, chunk: &[f32]) -> Result<f32> {
        let mut x = self.ctx.clone();
        x.extend_from_slice(chunk);
        let n = x.len();
        let m = |x: ort::Error| anyhow!("Silero v6: {x}");
        let input = ort::value::Tensor::from_array(([1usize, n], x)).map_err(m)?;
        let h = ort::value::Tensor::from_array(([1usize, 1, 128], self.h.clone())).map_err(m)?;
        let c = ort::value::Tensor::from_array(([1usize, 1, 128], self.c.clone())).map_err(m)?;
        let out = self.session.run(ort::inputs!["input" => input, "h" => h, "c" => c]).map_err(m)?;
        let p = out[0].try_extract_tensor::<f32>().map_err(m)?.1[0];
        self.h = out[1].try_extract_tensor::<f32>().map_err(m)?.1.to_vec();
        self.c = out[2].try_extract_tensor::<f32>().map_err(m)?.1.to_vec();
        self.ctx = chunk[chunk.len().saturating_sub(CONTEXT)..].to_vec();
        Ok(p)
    }
}

impl SpeechProbe for SileroV6 {
    fn feed(&mut self, chunk: &[f32]) -> Event {
        self.current += chunk.len();
        let p = match self.prob(chunk) {
            Ok(p) => p,
            Err(_) => return Event::None,
        };
        let min_silence = (SR as f32 * SILENCE_S) as usize;
        if p >= self.threshold && self.temp_end != 0 {
            self.temp_end = 0;
        }
        if p >= self.threshold && !self.triggered {
            self.triggered = true;
            return Event::Start;
        }
        if p < self.threshold - 0.15 && self.triggered {
            if self.temp_end == 0 {
                self.temp_end = self.current;
            }
            if self.current - self.temp_end < min_silence {
                return Event::None;
            }
            self.temp_end = 0;
            self.triggered = false;
            return Event::End;
        }
        Event::None
    }

    fn reset(&mut self) {
        self.h = vec![0.0; 128];
        self.c = vec![0.0; 128];
        self.ctx = vec![0.0; CONTEXT];
        self.triggered = false;
        self.temp_end = 0;
        self.current = 0;
    }
}

/// Silero do próprio sherpa-onnx (versão 5) — medido pior que o v6 (inglês ao vivo
/// 8,7% × 7,0%); mantido só para comparação.
pub struct SileroProbe {
    vad: VoiceActivityDetector,
    was: bool,
}

impl SileroProbe {
    pub fn load(model: &str, threshold: f32) -> Result<Self> {
        let config = VadModelConfig {
            silero_vad: SileroVadModelConfig {
                model: Some(model.to_string()),
                threshold,
                min_silence_duration: SILENCE_S,
                min_speech_duration: CHUNK_S,
                window_size: CHUNK as i32,
                max_speech_duration: 3600.0, // o corte por tamanho é feito aqui, não no Silero
            },
            sample_rate: SR as i32,
            num_threads: 1,
            ..Default::default()
        };
        let vad = VoiceActivityDetector::create(&config, 30.0)
            .ok_or_else(|| anyhow!("não foi possível carregar o detector de fala {model}"))?;
        Ok(Self { vad, was: false })
    }
}

impl SpeechProbe for SileroProbe {
    fn feed(&mut self, chunk: &[f32]) -> Event {
        self.vad.accept_waveform(chunk);
        while !self.vad.is_empty() {
            self.vad.pop(); // os trechos do próprio Silero não são usados
        }
        let now = self.vad.detected();
        let ev = match (self.was, now) {
            (false, true) => Event::Start,
            (true, false) => Event::End,
            _ => Event::None,
        };
        self.was = now;
        ev
    }

    fn reset(&mut self) {
        self.vad.reset();
        self.was = false;
    }
}

pub struct Segmenter<P: SpeechProbe> {
    probe: P,
    cfg: SegmenterConfig,
    speaking: bool,
    buf: Vec<Vec<f32>>,
    preroll: VecDeque<Vec<f32>>,
    preroll_len: usize,
    carry: Vec<Vec<f32>>,
    carry_age: usize,
    /// amostras entregues até agora (relógio do áudio)
    pos: usize,
    /// posição (em amostras) do fim de cada trecho entregue, na mesma ordem
    pub ends: Vec<usize>,
}

impl<P: SpeechProbe> Segmenter<P> {
    pub fn new(probe: P, cfg: SegmenterConfig) -> Self {
        let preroll_len = (cfg.preroll_s / CHUNK_S).round() as usize;
        Self {
            probe,
            cfg,
            speaking: false,
            buf: vec![],
            preroll: VecDeque::new(),
            preroll_len,
            carry: vec![],
            carry_age: 0,
            pos: 0,
            ends: vec![],
        }
    }

    fn emit(&mut self, chunks: Vec<Vec<f32>>, force: bool, out: &mut Vec<Vec<f32>>) {
        let mut all = std::mem::take(&mut self.carry);
        all.extend(chunks);
        self.carry_age = 0;
        if all.is_empty() {
            return;
        }
        if !force && (all.len() as f32) * CHUNK_S < MIN_SEG_S {
            self.carry = all; // curto demais para o Whisper sozinho: vai com o próximo
            return;
        }
        self.ends.push(self.pos.saturating_sub(self.buf.len() * CHUNK)); // o que ficou no buffer vem depois
        out.push(all.concat());
    }

    fn cut_long(&mut self, out: &mut Vec<Vec<f32>>) {
        let k = (self.buf.len().saturating_sub(1)).min((SMART_CUT_WINDOW_S / CHUNK_S) as usize);
        let (seg, rest) = if self.cfg.smart_cut && k > 0 {
            let start = self.buf.len() - k;
            let energy: Vec<f32> = self.buf[start..]
                .iter()
                .map(|c| c.iter().map(|x| x * x).sum::<f32>() / c.len() as f32)
                .collect();
            let j = start
                + energy
                    .iter()
                    .enumerate()
                    .min_by(|a, b| a.1.partial_cmp(b.1).unwrap_or(std::cmp::Ordering::Equal))
                    .map(|(i, _)| i)
                    .unwrap_or(0);
            let rest = self.buf.split_off(j + 1);
            (std::mem::take(&mut self.buf), rest)
        } else {
            (std::mem::take(&mut self.buf), vec![])
        };
        self.buf = rest; // antes de entregar: o fim do trecho é antes deste resto
        self.emit(seg, false, out);
    }

    /// Entrega um bloco de 32 ms; devolve os trechos de fala que ficaram prontos.
    pub fn push(&mut self, chunk: &[f32]) -> Vec<Vec<f32>> {
        let mut out = vec![];
        self.pos += chunk.len();
        let ev = self.probe.feed(chunk);
        let (start, end) = (ev == Event::Start, ev == Event::End);
        if start && !self.speaking {
            self.speaking = true;
            self.buf = self.preroll.drain(..).collect(); // início da fala, de antes do disparo
        }
        if self.speaking {
            self.buf.push(chunk.to_vec());
        } else {
            self.preroll.push_back(chunk.to_vec());
            while self.preroll.len() > self.preroll_len {
                self.preroll.pop_front();
            }
            if !self.carry.is_empty() {
                self.carry_age += 1;
                if (self.carry_age as f32) * CHUNK_S >= CARRY_MAX_WAIT_S {
                    self.emit(vec![], true, &mut out); // fala curta seguida de silêncio
                }
            }
        }
        if end && self.speaking {
            let b = std::mem::take(&mut self.buf);
            self.emit(b, false, &mut out);
            self.speaking = false;
            self.probe.reset();
        } else if self.speaking && (self.buf.len() as f32) * CHUNK_S >= self.cfg.max_seg_s {
            self.cut_long(&mut out);
        }
        out
    }

    /// Fim do áudio: entrega o que sobrou.
    pub fn flush(&mut self) -> Vec<Vec<f32>> {
        let mut out = vec![];
        let b = std::mem::take(&mut self.buf);
        if !b.is_empty() || !self.carry.is_empty() {
            self.emit(b, true, &mut out);
        }
        self.speaking = false;
        out
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Diz "começou"/"terminou" quando o volume do bloco muda.
    struct Loudness(bool);
    impl SpeechProbe for Loudness {
        fn feed(&mut self, c: &[f32]) -> Event {
            let now = c.iter().map(|x| x.abs()).sum::<f32>() / c.len() as f32 > 0.01;
            let ev = match (self.0, now) {
                (false, true) => Event::Start,
                (true, false) => Event::End,
                _ => Event::None,
            };
            self.0 = now;
            ev
        }
        fn reset(&mut self) {
            self.0 = false;
        }
    }

    fn blocks(speech_s: f32, silence_s: f32) -> Vec<Vec<f32>> {
        let n = (speech_s / CHUNK_S) as usize;
        let m = (silence_s / CHUNK_S) as usize;
        (0..n).map(|_| vec![0.1; CHUNK]).chain((0..m).map(|_| vec![0.0; CHUNK])).collect()
    }

    fn run(s: &mut Segmenter<Loudness>, bl: Vec<Vec<f32>>) -> Vec<Vec<f32>> {
        bl.iter().flat_map(|b| s.push(b)).collect()
    }

    #[test]
    fn fala_inteira_vira_um_trecho_com_pre_gravacao() {
        let mut s = Segmenter::new(Loudness(false), SegmenterConfig::default());
        let mut bl = blocks(0.0, 0.5);
        bl.extend(blocks(2.0, 0.5));
        let out = run(&mut s, bl);
        assert_eq!(out.len(), 1);
        let dur = out[0].len() as f32 / SR as f32;
        assert!(dur > 2.0 + PREROLL_S - 0.05, "inclui a pré-gravação: {dur}");
    }

    #[test]
    fn fala_longa_e_cortada_no_limite() {
        let mut s = Segmenter::new(Loudness(false), SegmenterConfig { max_seg_s: 6.0, ..Default::default() });
        let out = run(&mut s, blocks(14.0, 0.5));
        assert!(out.len() >= 2 && out.iter().all(|o| o.len() as f32 / SR as f32 <= 6.0 + 0.1));
    }

    #[test]
    fn sobra_curta_vai_com_o_proximo_ou_sai_sozinha() {
        let mut s = Segmenter::new(Loudness(false), SegmenterConfig::default());
        let mut bl = blocks(0.3, 0.3); // "Sim." curto
        bl.extend(blocks(0.0, 1.2)); // silêncio longo: sai sozinho
        let out = run(&mut s, bl);
        assert_eq!(out.len(), 1);
    }
}
