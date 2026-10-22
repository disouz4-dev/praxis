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

/// Tom médio da voz (Hz), pelo método YIN (de Cheveigné e Kawahara, 2002) em janelas de 50 ms
/// com fala. O método simples de autocorrelação confundia o tom com o dobro dele (homens
/// medidos a 270–300 Hz); o YIN normaliza a diferença e pega o primeiro vale abaixo do limiar.
/// Serve para escolher a voz pronta do mesmo tipo (grave/aguda) da voz do usuário.
pub fn tom_medio(x: &[f32], sample_rate: u32) -> Option<f32> {
    let sr = sample_rate as usize;
    let quadro = sr / 20;            // 50 ms
    let passo = sr / 40;             // 25 ms
    let (lo, hi) = (sr / 400, sr / 65); // de 65 a 400 Hz
    let largura = quadro.saturating_sub(hi);
    if largura < 32 || x.len() < quadro {
        return None;
    }
    let mut tons = vec![];
    let mut d = vec![0f32; hi + 1];
    let mut i = 0;
    while i + quadro <= x.len() {
        let q = &x[i..i + quadro];
        i += passo;
        let energia = (q.iter().map(|v| v * v).sum::<f32>() / quadro as f32).sqrt();
        if energia < 0.01 {
            continue;
        }
        for tau in 1..=hi {
            d[tau] = (0..largura).map(|j| { let e = q[j] - q[j + tau]; e * e }).sum();
        }
        // diferença normalizada pela média acumulada
        let mut acumulado = 0f32;
        let mut cmnd = vec![1f32; hi + 1];
        for tau in 1..=hi {
            acumulado += d[tau];
            cmnd[tau] = if acumulado > 0.0 { d[tau] * tau as f32 / acumulado } else { 1.0 };
        }
        let limiar: f32 = std::env::var("PRAXIS_TOM_LIMIAR").ok().and_then(|v| v.parse().ok()).unwrap_or(0.25);
        let mut achado = None;
        let mut tau = lo;
        while tau < hi {
            if cmnd[tau] < limiar {
                while tau + 1 < hi && cmnd[tau + 1] < cmnd[tau] {
                    tau += 1;
                }
                achado = Some(tau);
                break;
            }
            tau += 1;
        }
        // vale no dobro do período bem mais fundo: o primeiro vale era o 2º harmônico (o tom
        // real é uma oitava abaixo — o erro típico em vozes graves)
        let fator: f32 = std::env::var("PRAXIS_TOM_FATOR").ok().and_then(|v| v.parse().ok()).unwrap_or(0.5);
        if let Some(t) = achado {
            if 2 * t + 1 < hi {
                let t2 = (2 * t - 2..=2 * t + 2).min_by(|a, b| cmnd[*a].partial_cmp(&cmnd[*b]).unwrap()).unwrap();
                if cmnd[t2] < cmnd[t] * fator {
                    achado = Some(t2);
                }
            }
        }
        if let Some(t) = achado {
            // interpolação parabólica em volta do vale
            let (a, b, c) = (cmnd[t - 1], cmnd[t], cmnd[t + 1]);
            let den = a - 2.0 * b + c;
            let ajuste = if den.abs() > 1e-9 { 0.5 * (a - c) / den } else { 0.0 };
            tons.push(sample_rate as f32 / (t as f32 + ajuste));
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
