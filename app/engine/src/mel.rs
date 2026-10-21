//! Espectrograma "log-mel" exatamente como o Whisper original calcula (o mesmo do
//! faster-whisper): o áudio é completado com silêncio até 30 s, o volume é ajustado
//! pelo trecho inteiro e o silêncio de preenchimento entra como áudio de verdade.
//! Qualquer diferença aqui faz o modelo "ouvir" um som diferente do que foi treinado.

use realfft::RealFftPlanner;

pub const SAMPLE_RATE: usize = 16_000;
pub const N_FFT: usize = 400;
pub const HOP: usize = 160;
pub const CHUNK_S: usize = 30;
pub const N_SAMPLES: usize = SAMPLE_RATE * CHUNK_S; // 480 000
pub const N_FRAMES: usize = N_SAMPLES / HOP; // 3 000

/// Banco de filtros mel no estilo "Slaney" (o mesmo do librosa usado pelo Whisper).
pub fn mel_filters(n_mels: usize) -> Vec<Vec<f32>> {
    let n_freqs = N_FFT / 2 + 1;
    let fft_freqs: Vec<f64> = (0..n_freqs)
        .map(|i| i as f64 * SAMPLE_RATE as f64 / N_FFT as f64)
        .collect();
    let hz_to_mel = |f: f64| -> f64 {
        let (f_sp, min_log_hz) = (200.0 / 3.0, 1000.0);
        let min_log_mel = min_log_hz / f_sp;
        let logstep = (6.4f64).ln() / 27.0;
        if f >= min_log_hz { min_log_mel + (f / min_log_hz).ln() / logstep } else { f / f_sp }
    };
    let mel_to_hz = |m: f64| -> f64 {
        let (f_sp, min_log_hz) = (200.0 / 3.0, 1000.0);
        let min_log_mel = min_log_hz / f_sp;
        let logstep = (6.4f64).ln() / 27.0;
        if m >= min_log_mel { min_log_hz * (logstep * (m - min_log_mel)).exp() } else { f_sp * m }
    };
    let (mmin, mmax) = (hz_to_mel(0.0), hz_to_mel(SAMPLE_RATE as f64 / 2.0));
    let mel_pts: Vec<f64> = (0..n_mels + 2)
        .map(|i| mel_to_hz(mmin + (mmax - mmin) * i as f64 / (n_mels + 1) as f64))
        .collect();
    let mut w = vec![vec![0f32; n_freqs]; n_mels];
    for m in 0..n_mels {
        let (lo, ce, hi) = (mel_pts[m], mel_pts[m + 1], mel_pts[m + 2]);
        let enorm = 2.0 / (hi - lo); // normalização "slaney": área constante
        for (k, &f) in fft_freqs.iter().enumerate() {
            let lower = (f - lo) / (ce - lo);
            let upper = (hi - f) / (hi - ce);
            let v = lower.min(upper).max(0.0);
            w[m][k] = (v * enorm) as f32;
        }
    }
    w
}

/// Log-mel de um trecho de até 30 s → vetor achatado [n_mels × N_FRAMES], igual ao
/// faster-whisper: acrescenta 160 amostras de silêncio, STFT centrado com reflexão,
/// descarta o último quadro, ajusta o volume pelos quadros reais e completa até 3 000
/// quadros com zeros (já no domínio log-mel).
pub fn log_mel(audio: &[f32], filters: &[Vec<f32>]) -> Vec<f32> {
    let n_mels = filters.len();
    let n = audio.len().min(N_SAMPLES);
    let mut x: Vec<f32> = audio[..n].to_vec();
    x.extend(std::iter::repeat(0.0).take(HOP));
    let len = x.len();
    let pad = N_FFT / 2;
    let mut padded = Vec::with_capacity(len + 2 * pad);
    for i in (1..=pad).rev() {
        padded.push(x[i.min(len - 1)]);
    }
    padded.extend_from_slice(&x);
    for i in 0..pad {
        padded.push(x[len.saturating_sub(2 + i)]);
    }
    let window: Vec<f32> = (0..N_FFT)
        .map(|i| 0.5 - 0.5 * (2.0 * std::f32::consts::PI * i as f32 / N_FFT as f32).cos())
        .collect();
    let mut planner = RealFftPlanner::<f32>::new();
    let fft = planner.plan_fft_forward(N_FFT);
    let mut input = fft.make_input_vec();
    let mut spectrum = fft.make_output_vec();
    let n_freqs = N_FFT / 2 + 1;
    let frames = (1 + len / HOP).saturating_sub(1).min(N_FRAMES); // descarta o último quadro
    let mut mel = vec![0f32; n_mels * frames];
    let mut power = vec![0f32; n_freqs];
    for t in 0..frames {
        let start = t * HOP;
        for i in 0..N_FFT {
            input[i] = padded[start + i] * window[i];
        }
        fft.process(&mut input, &mut spectrum).expect("fft");
        for k in 0..n_freqs {
            power[k] = spectrum[k].norm_sqr();
        }
        for m in 0..n_mels {
            let s: f32 = filters[m].iter().zip(&power).map(|(a, b)| a * b).sum();
            mel[m * frames + t] = s.max(1e-10).log10();
        }
    }
    let max = mel.iter().cloned().fold(f32::MIN, f32::max);
    let mut out = vec![0f32; n_mels * N_FRAMES];
    for m in 0..n_mels {
        for t in 0..frames {
            out[m * N_FRAMES + t] = (mel[m * frames + t].max(max - 8.0) + 4.0) / 4.0;
        }
    }
    out
}
