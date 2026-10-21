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
