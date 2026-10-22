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
