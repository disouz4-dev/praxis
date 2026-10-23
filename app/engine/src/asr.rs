//! Reconhecimento de fala com o Whisper (CTranslate2, os mesmos modelos do
//! faster-whisper). Reproduz as regras medidas no Praxis em Python:
//!   * decodificação gulosa, sem marcas de tempo, sem texto anterior como dica
//!     (a busca em 5 caminhos e o contexto foram medidos e não ajudaram);
//!   * descarta o trecho quando o modelo acha que não é fala E está inseguro do
//!     texto (no_speech > 0,5 e confiança média < −1,0), a regra do faster-whisper.

use std::path::Path;

use anyhow::{anyhow, Result};
use ct2rs::sys::{StorageView, Whisper, WhisperOptions};
use ct2rs::tokenizers::hf;
use ct2rs::{ComputeType, Config, Device, Tokenizer};

use crate::mel;

pub const NO_SPEECH_DROP: f32 = 0.5;
pub const LOGPROB_DROP: f32 = -1.0;

#[derive(Debug, Clone, serde::Serialize)]
pub struct Transcript {
    pub text: String,
    /// probabilidade de o trecho não ter fala (0–1)
    pub no_speech: f32,
    /// confiança média do texto (logaritmo; perto de 0 = confiante)
    pub avg_logprob: f32,
    /// o trecho foi descartado como "não é fala"
    pub dropped: bool,
}

pub struct WhisperAsr {
    model: Whisper,
    tokenizer: hf::Tokenizer,
    filters: Vec<Vec<f32>>,
    pub device: &'static str,
}

impl WhisperAsr {
    /// `gpu`: usa a placa de vídeo NVIDIA (CUDA) se o motor tiver sido compilado com ela.
    pub fn load(model_dir: &Path, gpu: bool, threads: usize) -> Result<Self> {
        let config = Config {
            device: if gpu { Device::CUDA } else { Device::CPU },
            // processador: pesos em 8 bits, como o faster-whisper (compute_type="int8")
            compute_type: match std::env::var("PRAXIS_COMPUTE").as_deref() {
                Ok("float32") => ComputeType::FLOAT32,
                Ok("int8_float32") => ComputeType::INT8_FLOAT32,
                _ if gpu => ComputeType::INT8_FLOAT16,
                _ => ComputeType::INT8,
            },
            num_threads_per_replica: threads,
            ..Default::default()
        };
        let model = Whisper::new(model_dir, config)?;
        let tokenizer = hf::Tokenizer::new(model_dir)?;
        let filters = mel::mel_filters(model.n_mels());
        Ok(Self { model, tokenizer, filters, device: if gpu { "cuda" } else { "cpu" } })
    }

    /// Transcreve um trecho (16 kHz, até 30 s) no idioma `lang` (código "pt", "en"…).
    pub fn transcribe(&self, audio: &[f32], lang: &str) -> Result<Transcript> {
        let n_mels = self.filters.len();
        let mut feats = mel::log_mel(audio, &self.filters);
        let view = StorageView::new(&[1, n_mels, mel::N_FRAMES], &mut feats, Default::default())?;
        let lang_tok = format!("<|{lang}|>");
        let prompt = vec![vec![
            "<|startoftranscript|>".to_string(),
            lang_tok,
            "<|transcribe|>".to_string(),
            "<|notimestamps|>".to_string(),
        ]];
        let options = WhisperOptions {
            beam_size: 1,
            return_scores: true,
            return_no_speech_prob: true,
            ..Default::default()
        };
        let res = self
            .model
            .generate(&view, &prompt, &options)?
            .into_iter()
            .next()
            .ok_or_else(|| anyhow!("o Whisper não devolveu resultado"))?;
        let tokens = res.sequences.into_iter().next().unwrap_or_default();
        let n = tokens.len();
        // mesma conta do faster-whisper: soma das probabilidades / (tokens + 1)
        let score = res.scores.first().copied().unwrap_or(0.0);
        let avg_logprob = score * n as f32 / (n as f32 + 1.0);
        let text = self
            .tokenizer
            .decode(tokens.into_iter().filter(|t| !(t.starts_with("<|") && t.ends_with("|>"))).collect())?
            .trim()
            .to_string();
        let dropped = res.no_speech_prob > NO_SPEECH_DROP && avg_logprob < LOGPROB_DROP;
        Ok(Transcript {
            text: if dropped { String::new() } else { crate::text::clean_transcript(&text) },
            no_speech: res.no_speech_prob,
            avg_logprob,
            dropped,
        })
    }
}

/// Parakeet TDT (NVIDIA, licença CC BY 4.0) pelo sherpa-onnx: no processador erra menos
/// que o Whisper small nos idiomas europeus e é rápido o bastante para trechos de 15 s.
/// O idioma é reconhecido sozinho; pontuação e maiúsculas vêm prontas.
pub struct ParakeetAsr {
    rec: sherpa_onnx::OfflineRecognizer,
    pub device: &'static str,
}

impl ParakeetAsr {
    // Medido no FLEURS: o Parakeet perde o fim da frase quando a gravação é baixa
    // (pico 0,003) e devolve vazio quando o trecho começa no meio da fala (corte
    // forçado). Volume ajustado + silêncio em volta resolvem os dois.
    pub const PEAK: f32 = 0.5;
    pub const MAX_GAIN: f32 = 200.0;
    pub const PAD_BEFORE_S: f32 = 0.5;
    pub const PAD_AFTER_S: f32 = 1.0;

    /// `dir`: pasta de um pacote "sherpa-onnx-nemo-parakeet-…" (encoder/decoder/joiner .onnx, tokens.txt).
    pub fn load(dir: &Path, gpu: bool, threads: usize) -> Result<Self> {
        let pick = |prefix: &str| -> Result<Option<String>> {
            let mut v: Vec<_> = std::fs::read_dir(dir)?
                .filter_map(|e| e.ok().map(|e| e.path()))
                .filter(|p| {
                    let n = p.file_name().unwrap_or_default().to_string_lossy();
                    n.starts_with(prefix) && n.ends_with(".onnx")
                })
                .collect();
            v.sort();
            v.into_iter()
                .next()
                .map(|p| Some(p.to_string_lossy().to_string()))
                .ok_or_else(|| anyhow!("falta {prefix}*.onnx em {}", dir.display()))
        };
        let mut config = sherpa_onnx::OfflineRecognizerConfig::default();
        if pick("encoder").is_ok() {
            config.model_config.transducer = sherpa_onnx::OfflineTransducerModelConfig {
                encoder: pick("encoder")?,
                decoder: pick("decoder")?,
                joiner: pick("joiner")?,
            };
            config.model_config.model_type = Some("nemo_transducer".into());
            // compara 4 caminhos antes de decidir cada palavra: −0,2 a −0,4 ponto de erro
            // (pt 3,1% → 2,9%, de 3,0% → 2,7%) por +0,04 s por trecho
            config.decoding_method = Some("modified_beam_search".into());
            config.max_active_paths = 4;
        } else {
            // pacote CTC (Parakeet japonês): um único model*.onnx
            config.model_config.nemo_ctc = sherpa_onnx::OfflineNemoEncDecCtcModelConfig { model: pick("model")? };
            config.decoding_method = Some("greedy_search".into());
        }
        config.model_config.tokens = Some(dir.join("tokens.txt").to_string_lossy().to_string());
        config.model_config.num_threads = threads as i32;
        config.model_config.provider = Some(if gpu { crate::tts::cuda_provider() } else { "cpu".into() });
        if let Ok(p) = std::env::var("PRAXIS_PROVEDOR") {
            config.model_config.provider = Some(p);
        }
        let rec = sherpa_onnx::OfflineRecognizer::create(&config)
            .ok_or_else(|| anyhow!("não foi possível carregar o Parakeet de {}", dir.display()))?;
        Ok(Self { rec, device: if gpu { "cuda" } else { "cpu" } })
    }

    /// Volume ajustado (pico em PEAK, no máximo MAX_GAIN vezes) e silêncio antes e depois.
    pub fn prepare(audio: &[f32]) -> Vec<f32> {
        let peak = audio.iter().fold(0f32, |m, x| m.max(x.abs()));
        let gain = if peak > 0.0 { (Self::PEAK / peak).min(Self::MAX_GAIN) } else { 1.0 };
        let before = (Self::PAD_BEFORE_S * 16000.0) as usize;
        let after = (Self::PAD_AFTER_S * 16000.0) as usize;
        let mut out = vec![0f32; before];
        out.extend(audio.iter().map(|x| x * gain));
        out.resize(out.len() + after, 0.0);
        out
    }

    pub fn transcribe(&self, audio: &[f32]) -> Result<Transcript> {
        let st = self.rec.create_stream();
        st.accept_waveform(16000, &Self::prepare(audio));
        self.rec.decode(&st);
        let text = st.get_result().map(|r| r.text).unwrap_or_default();
        Ok(Transcript { text: crate::text::clean_transcript(text.trim()), no_speech: 0.0, avg_logprob: 0.0, dropped: false })
    }
}

/// Metade dos núcleos (como o Praxis em Python): o resto fica para tradução e voz.
fn default_threads() -> usize {
    (std::thread::available_parallelism().map(|n| n.get()).unwrap_or(4) / 2).max(1)
}

/// O reconhecedor de fala em uso: Whisper ou Parakeet, escolhido pela pasta do modelo.
pub enum Asr {
    Whisper(WhisperAsr),
    Parakeet(ParakeetAsr),
}

impl Asr {
    /// Pasta com tokens.txt e encoder*.onnx → Parakeet; senão, Whisper (CTranslate2).
    pub fn load(model_dir: &Path, gpu: bool, threads: usize) -> Result<Self> {
        if Self::is_parakeet(model_dir) {
            // na placa de vídeo quando a biblioteca de placa de vídeo do onnxruntime acompanha o
            // Praxis (a placa é sempre o motor principal); senão no processador
            let on_gpu = gpu && crate::tts::cuda_provider_available();
            Ok(Self::Parakeet(ParakeetAsr::load(model_dir, on_gpu, if threads == 0 { default_threads() } else { threads })?))
        } else {
            Ok(Self::Whisper(WhisperAsr::load(model_dir, gpu, threads)?))
        }
    }

    pub fn is_parakeet(model_dir: &Path) -> bool {
        model_dir.join("tokens.txt").exists()
            && std::fs::read_dir(model_dir)
                .map(|d| d.filter_map(|e| e.ok()).any(|e| e.file_name().to_string_lossy().ends_with(".onnx")))
                .unwrap_or(false)
    }

    pub fn device(&self) -> &'static str {
        match self {
            Self::Whisper(w) => w.device,
            Self::Parakeet(p) => p.device,
        }
    }

    pub fn transcribe(&self, audio: &[f32], lang: &str) -> Result<Transcript> {
        match self {
            Self::Whisper(w) => w.transcribe(audio, lang),
            Self::Parakeet(p) => p.transcribe(audio),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::ParakeetAsr;

    #[test]
    fn parakeet_ajusta_volume_e_poe_silencio_em_volta() {
        let audio = vec![0.001f32, -0.003, 0.002];
        let out = ParakeetAsr::prepare(&audio);
        assert_eq!(out.len(), 8000 + 3 + 16000);
        assert!(out[..8000].iter().all(|&x| x == 0.0));
        assert!((out[8001] + 0.5).abs() < 1e-6, "pico vai a 0,5");
        // nunca amplifica mais que MAX_GAIN (silêncio quase total não vira ruído alto)
        let quase_nada = ParakeetAsr::prepare(&[1e-6]);
        assert!((quase_nada[8000] - 1e-6 * ParakeetAsr::MAX_GAIN).abs() < 1e-9);
    }
}
