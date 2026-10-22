//! Motor em tempo real: uma "direção" (quem fala → quem ouve) com quatro tarefas em
//! paralelo, como no Praxis em Python:
//!
//!   áudio (blocos de 32 ms) → detector de fala → reconhecimento + tradução + voz → reprodução
//!
//! A reprodução roda numa tarefa própria: enquanto uma frase toca, a próxima já está sendo
//! transcrita (no desenho serial antigo o processador ficava cada vez mais atrasado).
//! A voz fala mais rápido quando a tradução acumula (velocidade adaptativa) e, se a
//! tradução toca num alto-falante, o microfone fica surdo enquanto ela toca (trava de eco).

use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::mpsc::{channel, Receiver, RecvTimeoutError, Sender};
use std::sync::{Arc, Mutex};
use std::thread::JoinHandle;
use std::time::{Duration, Instant};

use anyhow::Result;

use crate::asr::Asr;
use crate::mt;
use crate::text::speech_chunks;
use crate::tts::PiperVoice;
use crate::vad::{Segmenter, SegmenterConfig, SileroV6, SR};

/// (atraso de reprodução ≤ s, length_scale): a voz acelera quando a tradução se acumula.
pub const RATE_STEPS: [(f32, f32); 4] = [(1.5, 1.0), (4.0, 0.87), (8.0, 0.77), (f32::INFINITY, 0.7)];
/// Folga da trava de eco depois que o alto-falante para.
pub const ECHO_TAIL_S: f32 = 0.35;

pub fn speech_length_scale(backlog_s: f32) -> f32 {
    RATE_STEPS.iter().find(|(lim, _)| backlog_s <= *lim).map(|(_, s)| *s).unwrap_or(0.7)
}

pub trait Translate: Send + Sync {
    fn translate(&self, text: &str, src: &str, tgt: &str) -> Result<String>;
}

impl Translate for mt::Nllb {
    fn translate(&self, text: &str, src: &str, tgt: &str) -> Result<String> {
        mt::Nllb::translate(self, text, src, tgt)
    }
}

/// Argos: par direto, ou passando pelo inglês quando nenhum lado é inglês.
pub struct ArgosRoute(pub Vec<mt::ArgosPair>);

impl Translate for ArgosRoute {
    fn translate(&self, text: &str, _src: &str, _tgt: &str) -> Result<String> {
        let mut t = text.to_string();
        for p in &self.0 {
            t = p.translate(&t)?;
        }
        Ok(t)
    }
}

/// Toca áudio e só volta quando terminar (como um alto-falante de verdade).
pub trait Speaker: Send + Sync {
    fn play(&self, samples: &[f32], sample_rate: u32);
}

#[derive(Debug, Clone, serde::Serialize)]
#[serde(tag = "e", rename_all = "snake_case")]
pub enum Event {
    Transcript { dir: String, text: String },
    Translation { dir: String, text: String },
    Error { msg: String },
    /// um trecho de fala ficou pronto (fim da fala no relógio do áudio, em segundos)
    Segment { dir: String, id: usize, speech_end_s: f32, emitted_s: f32 },
    /// começou a tocar a tradução de um trecho
    Play { dir: String, id: usize, start_s: f32, dur_s: f32 },
    /// uma etapa terminou para um trecho ("transcrito", "traduzido", "voz"), no relógio do áudio
    Stage { dir: String, id: usize, stage: String, at_s: f32 },
}

pub struct Shared {
    pub stop: AtomicBool,
    /// até quando (ms desde t0) o alto-falante está tocando — trava de eco
    pub speaker_busy_until_ms: AtomicU64,
    pub t0: Instant,
}

impl Shared {
    pub fn new() -> Arc<Self> {
        Arc::new(Self { stop: AtomicBool::new(false), speaker_busy_until_ms: AtomicU64::new(0), t0: Instant::now() })
    }
    pub fn now_s(&self) -> f32 {
        self.t0.elapsed().as_secs_f32()
    }
}

pub struct Direction {
    pub name: String, // "out" (usuário) | "in" (interlocutor)
    pub src: String,
    pub tgt: String,
    /// a tradução toca num alto-falante (eco possível)
    pub to_speaker: bool,
    pub echo_gate: bool,
}

/// Fim da fala dentro do trecho: último bloco com volume (as bordas são silêncio).
fn voiced_end(audio: &[f32]) -> usize {
    let chunk = crate::vad::CHUNK;
    let env: Vec<f32> = audio.chunks(chunk).map(|c| (c.iter().map(|x| x * x).sum::<f32>() / c.len() as f32).sqrt()).collect();
    let max = env.iter().cloned().fold(0.0f32, f32::max);
    let thr = (0.1 * max).max(0.01);
    env.iter().rposition(|&e| e > thr).map(|i| (i + 1) * chunk).unwrap_or(audio.len()).min(audio.len())
}

/// Trabalho para o reconhecedor: um trecho adiantado (a fala parece ter acabado) ou o
/// trecho final (o fim se confirmou).
enum Job {
    Tentative(Vec<f32>),
    Final(usize, Vec<f32>),
}

/// Resultado de um trecho: texto, tradução e a voz do 1º pedaço já pronta.
struct Done {
    text: String,
    translation: String,
    first: Option<Vec<f32>>,
    rest: Vec<String>,
}

#[allow(clippy::too_many_arguments)]
pub fn spawn_direction(
    audio_rx: Receiver<Vec<f32>>,
    asr: Arc<Asr>,
    translator: Arc<dyn Translate>,
    voice: Arc<PiperVoice>,
    speaker: Arc<dyn Speaker>,
    dir: Direction,
    seg_cfg: SegmenterConfig,
    silero_model: String,
    shared: Arc<Shared>,
    events: Sender<Event>,
) -> Result<Vec<JoinHandle<()>>> {
    let dir = Arc::new(dir);
    let (seg_tx, seg_rx) = channel::<Job>();
    let (play_tx, play_rx) = channel::<(usize, Vec<f32>, u32)>();
    let backlog = Arc::new(Mutex::new(0f32)); // segundos de tradução ainda não tocados
    let probe = SileroV6::load(&silero_model, seg_cfg.threshold)?;
    let mut handles = vec![];

    // 1. detector de fala
    {
        let (shared, events, dir) = (shared.clone(), events.clone(), dir.clone());
        handles.push(std::thread::spawn(move || {
            let mut seg = Segmenter::new(probe, seg_cfg);
            let mut id = 0usize;
            while !shared.stop.load(Ordering::Relaxed) {
                let mut chunk = match audio_rx.recv_timeout(Duration::from_millis(200)) {
                    Ok(c) => c,
                    Err(RecvTimeoutError::Timeout) => continue,
                    Err(RecvTimeoutError::Disconnected) => break,
                };
                let now_ms = (shared.now_s() * 1000.0) as u64;
                if dir.echo_gate && now_ms < shared.speaker_busy_until_ms.load(Ordering::Relaxed) {
                    chunk.iter_mut().for_each(|x| *x = 0.0); // alto-falante vazando: vira silêncio
                }
                for audio in seg.push(&chunk) {
                    let end = *seg.ends.last().unwrap_or(&0);
                    // fim da fala no relógio do aplicativo (o mesmo da reprodução): o áudio chega
                    // em tempo real, então a amostra `fim` tocou há (posição − fim) amostras. O
                    // relógio do áudio começa quando o microfone abre, depois de carregar os
                    // modelos, e a diferença aparecia como atraso falso de 2 a 5 s.
                    let fim = end - (audio.len() - voiced_end(&audio));
                    let speech_end = shared.now_s() - seg.position().saturating_sub(fim) as f32 / SR as f32;
                    let _ = events.send(Event::Segment { dir: dir.name.clone(), id, speech_end_s: speech_end, emitted_s: shared.now_s() });
                    let _ = seg_tx.send(Job::Final(id, audio));
                    id += 1;
                }
                // a fala parece ter acabado: adianta o trabalho enquanto o fim é confirmado
                if let Some(audio) = seg.tentative() {
                    let _ = seg_tx.send(Job::Tentative(audio));
                }
            }
            for audio in seg.flush() {
                let _ = seg_tx.send(Job::Final(id, audio));
                id += 1;
            }
        }));
    }

    // 2. reconhecimento + tradução + voz
    {
        let (shared, events, dir, backlog) = (shared.clone(), events.clone(), dir.clone(), backlog.clone());
        handles.push(std::thread::spawn(move || {
            // reconhecer + traduzir + sintetizar o 1º pedaço da voz
            let work = |audio: &[f32]| -> Result<Option<Done>> {
                let t = asr.transcribe(audio, &dir.src)?;
                if t.text.is_empty() {
                    return Ok(None);
                }
                let tr = translator.translate(&t.text, &dir.src, &dir.tgt)?;
                let mut chunks = speech_chunks(&tr);
                let first = if chunks.is_empty() {
                    None
                } else {
                    let c = chunks.remove(0);
                    let scale = speech_length_scale(*backlog.lock().unwrap());
                    Some(voice.synthesize(&c, scale)?)
                };
                Ok(Some(Done { text: t.text, translation: tr, first, rest: chunks }))
            };
            // trabalho adiantado do trecho em curso: (áudio, resultado)
            let mut spec: Option<(Vec<f32>, Result<Option<Done>>)> = None;
            while !shared.stop.load(Ordering::Relaxed) {
                let (id, audio) = match seg_rx.recv_timeout(Duration::from_millis(200)) {
                    Ok(Job::Tentative(audio)) => {
                        let r = work(&crate::vad::with_tail_silence(&audio));
                        spec = Some((audio, r));
                        continue;
                    }
                    Ok(Job::Final(id, audio)) => (id, audio),
                    Err(RecvTimeoutError::Timeout) => continue,
                    Err(RecvTimeoutError::Disconnected) => break,
                };
                // o fim se confirmou: reaproveita o adiantado se o trecho é o mesmo
                let r = match spec.take() {
                    Some((t, r)) if crate::vad::reuse_ok(&t, &audio) => r,
                    _ => work(&audio),
                };
                let done = match r {
                    Ok(Some(d)) => d,
                    Ok(None) => continue,
                    Err(e) => {
                        let _ = events.send(Event::Error { msg: format!("{e:#}") });
                        continue; // um trecho com problema não pode derrubar a direção
                    }
                };
                for name in ["transcrito", "traduzido"] {
                    let _ = events.send(Event::Stage { dir: dir.name.clone(), id, stage: name.into(), at_s: shared.now_s() });
                }
                let _ = events.send(Event::Transcript { dir: dir.name.clone(), text: done.text.clone() });
                let _ = events.send(Event::Translation { dir: dir.name.clone(), text: done.translation.clone() });
                let send = |pcm: Vec<f32>| {
                    *backlog.lock().unwrap() += pcm.len() as f32 / voice.sample_rate as f32;
                    let _ = play_tx.send((id, pcm, voice.sample_rate));
                };
                if let Some(pcm) = done.first.filter(|p| !p.is_empty()) {
                    let _ = events.send(Event::Stage { dir: dir.name.clone(), id, stage: "voz".into(), at_s: shared.now_s() });
                    send(pcm);
                }
                // o resto, pedaço a pedaço: o primeiro já toca enquanto o próximo é sintetizado
                for sent in done.rest {
                    // a trava do atraso é solta antes de sintetizar: `send` a pega de novo
                    let scale = speech_length_scale(*backlog.lock().unwrap());
                    match voice.synthesize(&sent, scale) {
                        Ok(pcm) if !pcm.is_empty() => send(pcm),
                        Ok(_) => {}
                        Err(e) => {
                            let _ = events.send(Event::Error { msg: format!("síntese de voz: {e:#}") });
                        }
                    }
                }
            }
        }));
    }

    // 3. reprodução (em ordem, sem sobreposição)
    {
        let (shared, events, dir) = (shared.clone(), events.clone(), dir.clone());
        handles.push(std::thread::spawn(move || {
            while !shared.stop.load(Ordering::Relaxed) {
                let (id, pcm, sr) = match play_rx.recv_timeout(Duration::from_millis(200)) {
                    Ok(x) => x,
                    Err(RecvTimeoutError::Timeout) => continue,
                    Err(RecvTimeoutError::Disconnected) => break,
                };
                let dur = pcm.len() as f32 / sr as f32;
                let start = shared.now_s();
                if dir.to_speaker && dir.echo_gate {
                    let until = ((start + dur + ECHO_TAIL_S) * 1000.0) as u64;
                    shared.speaker_busy_until_ms.fetch_max(until, Ordering::Relaxed);
                }
                let _ = events.send(Event::Play { dir: dir.name.clone(), id, start_s: start, dur_s: dur });
                speaker.play(&pcm, sr);
                let mut b = backlog.lock().unwrap();
                *b = (*b - dur).max(0.0);
            }
        }));
    }
    Ok(handles)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn velocidade_adaptativa_como_no_python() {
        assert_eq!(speech_length_scale(0.5), 1.0);
        assert_eq!(speech_length_scale(3.0), 0.87);
        assert_eq!(speech_length_scale(6.0), 0.77);
        assert_eq!(speech_length_scale(30.0), 0.7);
    }
}
