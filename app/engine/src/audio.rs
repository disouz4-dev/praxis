//! Leitura de áudio WAV (16 kHz mono) para os testes e a linha de comando.
use anyhow::{bail, Result};
use std::path::Path;

pub fn read_wav_16k_mono(path: &Path) -> Result<Vec<f32>> {
    let mut r = hound::WavReader::open(path)?;
    let spec = r.spec();
    if spec.sample_rate != 16_000 {
        bail!("{}: taxa de amostragem {} (esperado 16 000)", path.display(), spec.sample_rate);
    }
    let ch = spec.channels.max(1) as usize;
    let samples: Vec<f32> = match spec.sample_format {
        hound::SampleFormat::Int => {
            let scale = (1i64 << (spec.bits_per_sample - 1)) as f32;
            r.samples::<i32>().map(|s| s.map(|v| v as f32 / scale)).collect::<Result<_, _>>()?
        }
        hound::SampleFormat::Float => r.samples::<f32>().collect::<Result<_, _>>()?,
    };
    Ok(samples.chunks(ch).map(|c| c.iter().sum::<f32>() / ch as f32).collect())
}

/// Grava mono, 16 bits.
pub fn write_wav16(path: &Path, samples: &[f32], sample_rate: u32) -> Result<()> {
    let spec = hound::WavSpec { channels: 1, sample_rate, bits_per_sample: 16, sample_format: hound::SampleFormat::Int };
    let mut w = hound::WavWriter::create(path, spec)?;
    for s in samples {
        w.write_sample((s.clamp(-1.0, 1.0) * 32767.0) as i16)?;
    }
    w.finalize()?;
    Ok(())
}

/// Tom médio da voz (Hz), pela autocorrelação de janelas de 40 ms que têm fala. Serve para
/// escolher a voz pronta do mesmo tipo (grave/aguda) da voz do usuário.
pub fn tom_medio(x: &[f32], sample_rate: u32) -> Option<f32> {
    let sr = sample_rate as usize;
    let w = sr * 40 / 1000;
    let (lo, hi) = (sr / 400, sr / 70);
    let mut tons = vec![];
    for janela in x.chunks_exact(w) {
        let media = janela.iter().sum::<f32>() / w as f32;
        let s: Vec<f32> = janela.iter().map(|v| v - media).collect();
        let energia = (s.iter().map(|v| v * v).sum::<f32>() / w as f32).sqrt();
        if energia < 0.02 {
            continue;
        }
        let mut melhor = (0usize, f32::MIN);
        for k in lo..hi.min(w - 1) {
            let a: f32 = s[..w - k].iter().zip(&s[k..]).map(|(p, q)| p * q).sum();
            if a > melhor.1 {
                melhor = (k, a);
            }
        }
        if melhor.0 > 0 {
            tons.push(sample_rate as f32 / melhor.0 as f32);
        }
    }
    if tons.len() < 10 {
        return None;
    }
    tons.sort_by(|a, b| a.partial_cmp(b).unwrap());
    Some(tons[tons.len() / 2])
}

#[cfg(test)]
mod testes_tom {
    #[test]
    fn tom_de_um_seno() {
        let sr = 16_000u32;
        let x: Vec<f32> = (0..sr).map(|i| 0.3 * (2.0 * std::f32::consts::PI * 120.0 * i as f32 / sr as f32).sin()).collect();
        let t = super::tom_medio(&x, sr).unwrap();
        assert!((t - 120.0).abs() < 4.0, "{t}");
    }
}
