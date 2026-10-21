//! Voz pelo sherpa-onnx. Três famílias, escolhidas pela pasta do pacote:
//!   * Kokoro 82M (voices.bin): a voz mais clara medida em pt, en, es, fr, it e zh;
//!   * Supertonic 3 (tts.json): 31 idiomas, ganha do Piper em todos os outros do Praxis;
//!   * Piper (VITS): só para idioma que nenhuma das duas fale.
//! Medido com o Whisper como ouvinte (benchmarks/vozes_inteligibilidade.py).

use std::collections::HashMap;
use std::path::Path;

use anyhow::{anyhow, Result};
use sherpa_onnx::{
    GenerationConfig, OfflineTts, OfflineTtsConfig, OfflineTtsKokoroModelConfig, OfflineTtsModelConfig,
    OfflineTtsSupertonicModelConfig, OfflineTtsVitsModelConfig,
};

/// Voz do Kokoro v1.0 para cada idioma: (número da voz no voices.bin, idioma da pronúncia)
pub const KOKORO_VOICES: &[(&str, i32, &str)] = &[
    ("pt", 42, "pt-br"), // pf_dora
    ("en", 3, "en-us"),  // af_heart
    ("es", 28, "es"),    // ef_dora
    ("fr", 30, "fr"),    // ff_siwis
    ("it", 35, "it"),    // if_sara
    ("zh", 47, "zh"),    // zf_xiaoxiao
];

/// Idiomas do Supertonic 3 entre os do Praxis (não fala chinês)
pub const SUPERTONIC_LANGS: &[&str] =
    &["pt", "en", "es", "fr", "de", "it", "ru", "nl", "pl", "uk", "tr", "ar", "hi", "ja", "ko"];

/// Passos de geração do Supertonic: 5 em vez de 8 deixa 35% mais rápido com a mesma clareza
/// (alemão 5,0% → 5,2%, russo 6,1% → 5,6%, italiano 1,8% → 2,2%).
pub const SUPERTONIC_STEPS: i32 = 5;

enum Kind {
    Piper,
    Kokoro { sid: i32 },
    Supertonic { lang: String },
}

pub struct Voice {
    tts: OfflineTts,
    kind: Kind,
    pub sample_rate: u32,
}

/// Nome antigo: o Praxis começou só com o Piper.
pub type PiperVoice = Voice;

fn file_with(dir: &Path, prefix: &str, ext: &str) -> Result<String> {
    let mut v: Vec<_> = std::fs::read_dir(dir)?
        .filter_map(|e| e.ok().map(|e| e.path()))
        .filter(|p| {
            let n = p.file_name().unwrap_or_default().to_string_lossy();
            n.starts_with(prefix) && n.ends_with(ext)
        })
        .collect();
    v.sort();
    v.into_iter()
        .next()
        .map(|p| p.to_string_lossy().to_string())
        .ok_or_else(|| anyhow!("falta {prefix}*{ext} em {}", dir.display()))
}

impl Voice {
    /// `dir`: pasta de um pacote de voz do sherpa-onnx; `lang`: idioma que a voz vai falar
    /// (Kokoro e Supertonic falam vários). Vazio = PRAXIS_VOZ_IDIOMA ou "en".
    pub fn load(dir: &Path, threads: i32) -> Result<Self> {
        let lang = std::env::var("PRAXIS_VOZ_IDIOMA").unwrap_or_else(|_| "en".into());
        Self::load_for(dir, &lang, threads)
    }

    pub fn load_for(dir: &Path, lang: &str, threads: i32) -> Result<Self> {
        let s = |p: &Path| Some(p.to_string_lossy().to_string());
        let mut model = OfflineTtsModelConfig { num_threads: threads, ..Default::default() };
        let mut config = OfflineTtsConfig { max_num_sentences: 1, ..Default::default() };
        let kind = if dir.join("voices.bin").exists() {
            let (_, sid, code) = KOKORO_VOICES.iter().find(|(l, _, _)| *l == lang)
                .ok_or_else(|| anyhow!("o Kokoro não fala {lang}"))?;
            let d = dir.display();
            model.kokoro = OfflineTtsKokoroModelConfig {
                model: Some(file_with(dir, "model", ".onnx")?),
                voices: s(&dir.join("voices.bin")),
                tokens: s(&dir.join("tokens.txt")),
                data_dir: s(&dir.join("espeak-ng-data")),
                lexicon: match lang {
                    "en" => Some(format!("{d}/lexicon-us-en.txt")),
                    "zh" => Some(format!("{d}/lexicon-us-en.txt,{d}/lexicon-zh.txt")),
                    _ => None,
                },
                dict_dir: if lang == "zh" { s(&dir.join("dict")) } else { None },
                lang: Some(code.to_string()),
                length_scale: 1.0,
                ..Default::default()
            };
            if lang == "zh" {
                config.rule_fsts = Some(format!("{d}/phone-zh.fst,{d}/date-zh.fst,{d}/number-zh.fst"));
            }
            Kind::Kokoro { sid: *sid }
        } else if dir.join("tts.json").exists() {
            model.supertonic = OfflineTtsSupertonicModelConfig {
                duration_predictor: Some(file_with(dir, "duration_predictor", ".onnx")?),
                text_encoder: Some(file_with(dir, "text_encoder", ".onnx")?),
                vector_estimator: Some(file_with(dir, "vector_estimator", ".onnx")?),
                vocoder: Some(file_with(dir, "vocoder", ".onnx")?),
                tts_json: s(&dir.join("tts.json")),
                unicode_indexer: s(&dir.join("unicode_indexer.bin")),
                voice_style: s(&dir.join("voice.bin")),
            };
            Kind::Supertonic { lang: lang.to_string() }
        } else {
            model.vits = OfflineTtsVitsModelConfig {
                model: Some(file_with(dir, "", ".onnx")?),
                tokens: s(&dir.join("tokens.txt")),
                data_dir: s(&dir.join("espeak-ng-data")),
                // valores padrão do Piper (os mesmos do Praxis em Python)
                noise_scale: 0.667,
                noise_scale_w: 0.8,
                length_scale: 1.0,
                ..Default::default()
            };
            Kind::Piper
        };
        config.model = model;
        let tts = OfflineTts::create(&config).ok_or_else(|| anyhow!("não foi possível carregar a voz {}", dir.display()))?;
        let sample_rate = tts.sample_rate() as u32;
        Ok(Self { tts, kind, sample_rate })
    }

    /// Sintetiza `text`; `length_scale` < 1 fala mais rápido (velocidade adaptativa do Praxis).
    pub fn synthesize(&self, text: &str, length_scale: f32) -> Result<Vec<f32>> {
        let mut cfg = GenerationConfig { speed: 1.0 / length_scale.max(0.1), ..Default::default() };
        match &self.kind {
            Kind::Piper => {}
            Kind::Kokoro { sid } => cfg.sid = *sid,
            Kind::Supertonic { lang } => {
                cfg.num_steps = SUPERTONIC_STEPS;
                cfg.extra = Some(HashMap::from([("lang".to_string(), serde_json::json!(lang))]));
            }
        }
        let audio = self
            .tts
            .generate_with_config::<fn(&[f32], f32) -> bool>(text, &cfg, None)
            .ok_or_else(|| anyhow!("a síntese de voz falhou"))?;
        Ok(audio.samples().to_vec())
    }
}
