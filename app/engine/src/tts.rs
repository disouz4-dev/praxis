//! Voz: Piper (VITS) pelo sherpa-onnx — os mesmos modelos de voz do Praxis em Python,
//! empacotados pelo sherpa-onnx com o vocabulário de sons (tokens.txt) e o espeak-ng-data.

use std::path::Path;

use anyhow::{anyhow, Result};
use sherpa_onnx::{GenerationConfig, OfflineTts, OfflineTtsConfig, OfflineTtsModelConfig, OfflineTtsVitsModelConfig};

pub struct PiperVoice {
    tts: OfflineTts,
    pub sample_rate: u32,
}

impl PiperVoice {
    /// `dir`: pasta de um pacote "vits-piper-…" do sherpa-onnx (*.onnx, tokens.txt, espeak-ng-data).
    pub fn load(dir: &Path, threads: i32) -> Result<Self> {
        let model = std::fs::read_dir(dir)?
            .filter_map(|e| e.ok().map(|e| e.path()))
            .find(|p| p.extension().map(|x| x == "onnx").unwrap_or(false))
            .ok_or_else(|| anyhow!("nenhum modelo .onnx em {}", dir.display()))?;
        let s = |p: &Path| Some(p.to_string_lossy().to_string());
        let config = OfflineTtsConfig {
            model: OfflineTtsModelConfig {
                vits: OfflineTtsVitsModelConfig {
                    model: s(&model),
                    tokens: s(&dir.join("tokens.txt")),
                    data_dir: s(&dir.join("espeak-ng-data")),
                    // valores padrão do Piper (os mesmos do Praxis em Python)
                    noise_scale: 0.667,
                    noise_scale_w: 0.8,
                    length_scale: 1.0,
                    ..Default::default()
                },
                num_threads: threads,
                ..Default::default()
            },
            max_num_sentences: 1,
            ..Default::default()
        };
        let tts = OfflineTts::create(&config).ok_or_else(|| anyhow!("não foi possível carregar a voz {}", dir.display()))?;
        let sample_rate = tts.sample_rate() as u32;
        Ok(Self { tts, sample_rate })
    }

    /// Sintetiza `text`; `length_scale` < 1 fala mais rápido (velocidade adaptativa do Praxis).
    pub fn synthesize(&self, text: &str, length_scale: f32) -> Result<Vec<f32>> {
        let cfg = GenerationConfig { speed: 1.0 / length_scale.max(0.1), ..Default::default() };
        let audio = self
            .tts
            .generate_with_config::<fn(&[f32], f32) -> bool>(text, &cfg, None)
            .ok_or_else(|| anyhow!("a síntese de voz falhou"))?;
        Ok(audio.samples().to_vec())
    }
}
