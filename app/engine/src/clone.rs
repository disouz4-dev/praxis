//! Clonagem da voz do usuário, dentro do Praxis e sem placa de vídeo.
//!
//! A partir da gravação (passo "Sua voz"), procura a combinação das 10 vozes do Supertonic 3
//! cuja impressão de voz (medidor wespeaker, pelo sherpa-onnx) mais se aproxima da do usuário,
//! e guarda o resultado como um `voice.bin` do Supertonic: a tradução passa a sair nessa voz.
//! Busca sem gradiente (estratégia evolutiva com passo adaptativo): a cada rodada, uma família
//! de candidatos vai num único voice.bin e cada um fala três frases curtas (pt, en, es).

use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering};

use anyhow::{anyhow, bail, Context, Result};
use sherpa_onnx::{
    GenerationConfig, OfflineTts, OfflineTtsConfig, OfflineTtsModelConfig, OfflineTtsSupertonicModelConfig,
    SpeakerEmbeddingExtractor, SpeakerEmbeddingExtractorConfig,
};

use crate::tts::file_with;

/// Medidor de impressão de voz (wespeaker ResNet34, VoxCeleb; 26 MB, CC BY 4.0)
pub const EMB_FILE: &str = "wespeaker_en_voxceleb_resnet34_LM.onnx";
pub const EMB_URL: &str =
    "https://github.com/k2-fsa/sherpa-onnx/releases/download/speaker-recongition-models/wespeaker_en_voxceleb_resnet34_LM.onnx";
pub const EMB_SHA256: &str = "e9848563da86f263117134dfd7ad63c92355b37de492b55e325400c9d9c39012";

const TTL: usize = 50 * 256;
const DP: usize = 8 * 16;
/// Candidatos por rodada e quantos dos melhores formam a próxima média
const LAMBDA: usize = 12;
const MU: usize = 4;
/// Rodadas: medido (23/10/2026, gravação do usuário no app) ~30 s cada com 4 núcleos
pub const RODADAS: usize = 24;
const FRASES: [(&str, &str); 3] = [
    ("pt", "Eu gosto de conversar com calma e explicar as ideias."),
    ("en", "Thank you for joining the call, it is good to hear you."),
    ("es", "Mañana vamos a revisar el proyecto con todo el equipo."),
];

/// As vozes de um voice.bin do Supertonic: (timbre 50×256, duração 8×16) de cada uma.
pub struct Estilos {
    pub ttl: Vec<Vec<f32>>,
    pub dp: Vec<Vec<f32>>,
}

impl Estilos {
    pub fn ler(path: &Path) -> Result<Self> {
        let b = std::fs::read(path).with_context(|| format!("lendo {}", path.display()))?;
        let h: Vec<i64> = b.chunks(8).take(6).map(|c| i64::from_le_bytes(c.try_into().unwrap())).collect();
        if h.len() < 6 || h[1] != 50 || h[2] != 256 || h[4] != 8 || h[5] != 16 || h[0] != h[3] {
            bail!("voice.bin com formato inesperado: {h:?}");
        }
        let n = h[0] as usize;
        let f: Vec<f32> = b[48..].chunks(4).map(|c| f32::from_le_bytes(c.try_into().unwrap())).collect();
        if f.len() != n * (TTL + DP) {
            bail!("voice.bin com tamanho inesperado");
        }
        Ok(Self {
            ttl: (0..n).map(|i| f[i * TTL..(i + 1) * TTL].to_vec()).collect(),
            dp: (0..n).map(|i| f[n * TTL + i * DP..n * TTL + (i + 1) * DP].to_vec()).collect(),
        })
    }

    pub fn gravar(&self, path: &Path) -> Result<()> {
        let n = self.ttl.len() as i64;
        let mut b: Vec<u8> = [n, 50, 256, n, 8, 16].iter().flat_map(|v| v.to_le_bytes()).collect();
        for v in self.ttl.iter().chain(&self.dp) {
            b.extend(v.iter().flat_map(|x| x.to_le_bytes()));
        }
        std::fs::write(path, b).with_context(|| format!("gravando {}", path.display()))
    }

    /// Combinação das vozes: `pesos` tem 2n números (n para o timbre, n para a duração).
    fn misturar(&self, pesos: &[f64]) -> (Vec<f32>, Vec<f32>) {
        let n = self.ttl.len();
        let comb = |vs: &[Vec<f32>], w: &[f64]| {
            let mut out = vec![0f32; vs[0].len()];
            for (v, &k) in vs.iter().zip(w) {
                out.iter_mut().zip(v).for_each(|(o, x)| *o += k as f32 * x);
            }
            out
        };
        (comb(&self.ttl, &pesos[..n]), comb(&self.dp, &pesos[n..]))
    }
}

/// Gerador de números (xorshift) com sorteio normal — sem dependência nova.
struct Sorteio(u64);
impl Sorteio {
    fn uniforme(&mut self) -> f64 {
        self.0 ^= self.0 << 13;
        self.0 ^= self.0 >> 7;
        self.0 ^= self.0 << 17;
        (self.0 >> 11) as f64 / (1u64 << 53) as f64
    }
    fn normal(&mut self) -> f64 {
        let (u, v) = (self.uniforme().max(1e-12), self.uniforme());
        (-2.0 * u.ln()).sqrt() * (2.0 * std::f64::consts::PI * v).cos()
    }
}

struct Medidor(SpeakerEmbeddingExtractor);
impl Medidor {
    fn novo(modelo: &Path, threads: i32) -> Result<Self> {
        let cfg = SpeakerEmbeddingExtractorConfig { model: Some(modelo.to_string_lossy().into()), num_threads: threads, ..Default::default() };
        Ok(Self(SpeakerEmbeddingExtractor::create(&cfg).ok_or_else(|| anyhow!("não foi possível carregar o medidor de voz"))?))
    }
    /// Impressão de voz normalizada (comprimento 1)
    fn impressao(&self, x: &[f32], sr: i32) -> Result<Vec<f32>> {
        let s = self.0.create_stream().ok_or_else(|| anyhow!("medidor de voz"))?;
        s.accept_waveform(sr, x);
        s.input_finished();
        let e = self.0.compute(&s).ok_or_else(|| anyhow!("áudio curto demais para medir a voz"))?;
        let n = e.iter().map(|v| v * v).sum::<f32>().sqrt().max(1e-9);
        Ok(e.into_iter().map(|v| v / n).collect())
    }
}

fn cos(a: &[f32], b: &[f32]) -> f64 {
    a.iter().zip(b).map(|(x, y)| (x * y) as f64).sum()
}

fn tts_com(pacote: &Path, voice_bin: &Path, threads: i32) -> Result<OfflineTts> {
    let s = |p: PathBuf| Some(p.to_string_lossy().to_string());
    let model = OfflineTtsModelConfig {
        num_threads: threads,
        supertonic: OfflineTtsSupertonicModelConfig {
            duration_predictor: Some(file_with(pacote, "duration_predictor", ".onnx")?),
            text_encoder: Some(file_with(pacote, "text_encoder", ".onnx")?),
            vector_estimator: Some(file_with(pacote, "vector_estimator", ".onnx")?),
            vocoder: Some(file_with(pacote, "vocoder", ".onnx")?),
            tts_json: s(pacote.join("tts.json")),
            unicode_indexer: s(pacote.join("unicode_indexer.bin")),
            voice_style: s(voice_bin.to_path_buf()),
        },
        ..Default::default()
    };
    OfflineTts::create(&OfflineTtsConfig { model, max_num_sentences: 1, ..Default::default() })
        .ok_or_else(|| anyhow!("não foi possível carregar a voz Supertonic"))
}

/// Resultado da clonagem
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Clone {
    /// semelhança com a gravação (0 a 1, no medidor usado na busca)
    pub semelhanca: f64,
    /// a voz pronta mais parecida, antes da busca
    pub semelhanca_pronta: f64,
    pub segundos: u64,
    /// impressão digital da gravação usada (refazer quando ela mudar)
    pub gravacao_sha256: String,
}

/// Clona a voz da `gravacao` (16 kHz) e grava `saida` (um voice.bin com a voz em todas as 10
/// posições, para qualquer número de voz servir). `progresso(fração, texto)`; `parar` cancela.
pub fn clonar(
    gravacao: &[f32],
    pacote_supertonic: &Path,
    medidor_voz: &Path,
    saida: &Path,
    rodadas: usize,
    threads: i32,
    progresso: &dyn Fn(f32, &str),
    parar: &AtomicBool,
) -> Result<Clone> {
    let t0 = std::time::Instant::now();
    let prontas = Estilos::ler(&pacote_supertonic.join("voice.bin"))?;
    let n = prontas.ttl.len();
    let med = Medidor::novo(medidor_voz, threads)?;
    // impressão da gravação: média de pedaços de 4 s (mais estável que o arquivo inteiro)
    let sr = 16_000usize;
    let mut soma = vec![0f32; 0];
    let mut i = 0;
    while i + 2 * sr <= gravacao.len() {
        let e = med.impressao(&gravacao[i..(i + 4 * sr).min(gravacao.len())], sr as i32)?;
        if soma.is_empty() { soma = vec![0.0; e.len()]; }
        soma.iter_mut().zip(&e).for_each(|(s, v)| *s += v);
        i += 3 * sr;
    }
    if soma.is_empty() {
        bail!("gravação curta demais para clonar a voz");
    }
    let nrm = soma.iter().map(|v| v * v).sum::<f32>().sqrt();
    let alvo: Vec<f32> = soma.iter().map(|v| v / nrm).collect();

    let tmp = saida.with_extension("candidatos.bin");
    // nota de cada candidato: semelhança média das três frases com a gravação
    let pontuar = |cands: &[Vec<f64>]| -> Result<Vec<f64>> {
        let (ttl, dp): (Vec<_>, Vec<_>) = cands.iter().map(|p| prontas.misturar(p)).unzip();
        Estilos { ttl, dp }.gravar(&tmp)?;
        let tts = tts_com(pacote_supertonic, &tmp, threads)?;
        let mut notas = vec![];
        for k in 0..cands.len() {
            let mut s = 0.0;
            for (lang, frase) in FRASES {
                let cfg = GenerationConfig {
                    sid: k as i32,
                    num_steps: crate::tts::SUPERTONIC_STEPS,
                    extra: Some(std::collections::HashMap::from([("lang".to_string(), serde_json::json!(lang))])),
                    ..Default::default()
                };
                let a = tts.generate_with_config::<fn(&[f32], f32) -> bool>(frase, &cfg, None)
                    .ok_or_else(|| anyhow!("a síntese de voz falhou"))?;
                s += cos(&med.impressao(a.samples(), a.sample_rate())?, &alvo);
            }
            notas.push(s / FRASES.len() as f64);
        }
        Ok(notas)
    };

    // 1. a voz pronta mais parecida
    progresso(0.02, "Comparando com as vozes prontas…");
    let base: Vec<Vec<f64>> = (0..n).map(|k| (0..2 * n).map(|j| if j % n == k { 1.0 } else { 0.0 }).collect()).collect();
    let notas0 = pontuar(&base)?;
    let k0 = (0..n).max_by(|a, b| notas0[*a].total_cmp(&notas0[*b])).unwrap();
    let mut media = base[k0].clone();
    let mut melhor = (notas0[k0], media.clone());
    let pronta = notas0[k0];

    // 2. busca: a média anda na direção dos melhores; o passo cresce quando acha melhora
    let mut rng = Sorteio(0x9E37_79B9_7F4A_7C15);
    let mut passo = 0.15;
    for r in 0..rodadas {
        if parar.load(Ordering::Relaxed) {
            bail!("clonagem cancelada");
        }
        progresso(0.05 + 0.93 * r as f32 / rodadas as f32, &format!("Aprendendo a sua voz… ({}/{rodadas})", r + 1));
        let cands: Vec<Vec<f64>> = (0..LAMBDA).map(|_| media.iter().map(|m| m + passo * rng.normal()).collect()).collect();
        let notas = pontuar(&cands)?;
        let mut ordem: Vec<usize> = (0..LAMBDA).collect();
        ordem.sort_by(|a, b| notas[*b].total_cmp(&notas[*a]));
        let achou = notas[ordem[0]] > melhor.0;
        if achou {
            melhor = (notas[ordem[0]], cands[ordem[0]].clone());
        }
        media = (0..2 * n).map(|j| ordem[..MU].iter().map(|&c| cands[c][j]).sum::<f64>() / MU as f64).collect();
        passo *= if achou { 1.15 } else { 0.85 };
    }
    let _ = std::fs::remove_file(&tmp);

    // 3. grava a voz clonada nas 10 posições
    let (ttl, dp) = prontas.misturar(&melhor.1);
    Estilos { ttl: vec![ttl; n], dp: vec![dp; n] }.gravar(saida)?;
    progresso(1.0, "Voz clonada");
    Ok(Clone { semelhanca: melhor.0, semelhanca_pronta: pronta, segundos: t0.elapsed().as_secs(), gravacao_sha256: String::new() })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn voice_bin_ida_e_volta() {
        let e = Estilos { ttl: vec![vec![0.5; TTL], vec![-1.0; TTL]], dp: vec![vec![2.0; DP], vec![3.0; DP]] };
        let p = std::env::temp_dir().join("praxis-teste-voice.bin");
        e.gravar(&p).unwrap();
        let l = Estilos::ler(&p).unwrap();
        assert_eq!(l.ttl.len(), 2);
        assert_eq!(l.ttl[1][0], -1.0);
        assert_eq!(l.dp[0][DP - 1], 2.0);
        // mistura: 0,5·a + 0,5·b
        let (t, d) = l.misturar(&[0.5, 0.5, 1.0, 0.0]);
        assert!((t[0] - (-0.25)).abs() < 1e-6);
        assert_eq!(d[0], 2.0);
        let _ = std::fs::remove_file(p);
    }

    #[test]
    fn sorteio_normal_tem_media_zero() {
        let mut r = Sorteio(42);
        let m: f64 = (0..20_000).map(|_| r.normal()).sum::<f64>() / 20_000.0;
        assert!(m.abs() < 0.05);
    }
}
