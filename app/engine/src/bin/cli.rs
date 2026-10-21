//! Linha de comando do motor (testes e medições).
//!
//!   praxis-cli asr <modelo> <áudio.wav> <idioma>
//!   praxis-cli asr-corpus <modelo> <pasta com manifest.json> <idioma> <saída.json> [--gpu]
use std::path::PathBuf;
use std::time::Instant;

use anyhow::{bail, Result};
use praxis_engine::{asr::WhisperAsr, audio, mt};

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let gpu = args.iter().any(|a| a == "--gpu");
    let pos: Vec<&String> = args.iter().filter(|a| !a.starts_with("--")).collect();
    let threads = std::env::var("PRAXIS_THREADS").ok().and_then(|v| v.parse().ok()).unwrap_or(0);
    match pos.first().map(|s| s.as_str()) {
        Some("asr") if pos.len() == 4 => {
            let asr = WhisperAsr::load(pos[1].as_ref(), gpu, threads)?;
            let a = audio::read_wav_16k_mono(pos[2].as_ref())?;
            let reps: usize = std::env::var("PRAXIS_REPETIR").ok().and_then(|v| v.parse().ok()).unwrap_or(1);
            let mut r = None;
            for i in 0..reps {
                let t = Instant::now();
                r = Some(asr.transcribe(&a, pos[3])?);
                eprintln!("rodada {}: {:.2} s", i + 1, t.elapsed().as_secs_f32());
            }
            println!("{}", serde_json::to_string_pretty(&r)?);
        }
        Some("asr-corpus") if pos.len() == 5 => {
            let asr = WhisperAsr::load(pos[1].as_ref(), gpu, threads)?;
            let dir = PathBuf::from(pos[2]);
            let lang = pos[3].as_str();
            let manifest: Vec<serde_json::Value> =
                serde_json::from_str(&std::fs::read_to_string(dir.join("manifest.json"))?)?;
            let (mut samples, mut asr_s, mut audio_s) = (vec![], 0f64, 0f64);
            for it in &manifest {
                let file = it["file"].as_str().unwrap_or_default();
                let a = audio::read_wav_16k_mono(&dir.join(file))?;
                let t = Instant::now();
                let r = asr.transcribe(&a, lang)?;
                let dt = t.elapsed().as_secs_f64();
                asr_s += dt;
                audio_s += a.len() as f64 / 16_000.0;
                eprintln!("  {file}  {dt:.2} s  {}", r.text);
                samples.push(serde_json::json!({
                    "file": file, "speaker": it["speaker"], "ref": it["text"], "hyp": r.text,
                    "dur_s": a.len() as f64 / 16_000.0, "asr_s": dt,
                    "no_speech": r.no_speech, "avg_logprob": r.avg_logprob,
                }));
            }
            let model = PathBuf::from(pos[1]).file_name().map(|s| s.to_string_lossy().to_string()).unwrap_or_default();
            let out = serde_json::json!({"kind": "asr", "engine": "praxis-rs", "results": [{
                "model": model, "lang": lang, "n": samples.len(), "backend": asr.device,
                "rtf": asr_s / audio_s.max(1e-9), "samples": samples}]});
            std::fs::write(pos[4], serde_json::to_string_pretty(&out)?)?;
            eprintln!("tempo de transcrição por segundo de fala: {:.3}", asr_s / audio_s.max(1e-9));
        }
        // mt <nllb|argos> <modelo ou pasta de pacotes> <origem> <destino> <entrada.txt> <saída.txt>
        Some("mt") if pos.len() == 7 => {
            let (src, tgt) = (pos[3].to_string(), pos[4].to_string());
            let lines: Vec<String> = std::fs::read_to_string(pos[5])?.lines().map(String::from).collect();
            // carrega e aquece antes de cronometrar (igual à medição do Python)
            let f: Box<dyn Fn(&str) -> Result<String>> = match pos[1].as_str() {
                "nllb" => {
                    let m = mt::Nllb::load(pos[2].as_ref(), gpu)?;
                    let (s2, t2) = (src.clone(), tgt.clone());
                    Box::new(move |l| m.translate(l, &s2, &t2))
                }
                "argos" => {
                    let dir = PathBuf::from(pos[2]);
                    if src != "en" && tgt != "en" {
                        // sem par direto: passa pelo inglês, como o Praxis em Python
                        let a = mt::ArgosPair::load(&mt::argos_package(&dir, &src, "en")?, gpu)?;
                        let b = mt::ArgosPair::load(&mt::argos_package(&dir, "en", &tgt)?, gpu)?;
                        Box::new(move |l| b.translate(&a.translate(l)?))
                    } else {
                        let m = mt::ArgosPair::load(&mt::argos_package(&dir, &src, &tgt)?, gpu)?;
                        Box::new(move |l| m.translate(l))
                    }
                }
                k => bail!("tradutor desconhecido: {k}"),
            };
            if let Some(first) = lines.first() {
                f(first)?;
            }
            let t0 = Instant::now();
            let mut out = Vec::new();
            let mut slowest = 0f32;
            for l in &lines {
                let t = Instant::now();
                out.push(f(l)?);
                slowest = slowest.max(t.elapsed().as_secs_f32());
            }
            std::fs::write(pos[6], out.join("\n") + "\n")?;
            let total = t0.elapsed().as_secs_f32();
            eprintln!("{} frases em {:.2} s (média {:.2} s, mais lenta {:.2} s)", lines.len(), total,
                      total / lines.len().max(1) as f32, slowest);
        }
        _ => bail!("uso: praxis-cli asr <modelo> <áudio.wav> <idioma> | asr-corpus <modelo> <pasta> <idioma> <saída.json> [--gpu]"),
    }
    Ok(())
}
