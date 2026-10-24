//! Linha de comando do motor (testes e medições).
//!
//!   praxis-cli asr <modelo> <áudio.wav> <idioma>
//!   praxis-cli asr-corpus <modelo> <pasta com manifest.json> <idioma> <saída.json> [--gpu]
use std::path::PathBuf;
use std::time::Instant;

use anyhow::{bail, Result};
use praxis_engine::{asr::Asr, audio, devices, mt, pipeline, tts, vad};
use std::sync::Arc;

/// Alto-falante de teste: espera a duração do áudio (como um de verdade) e não toca nada.
struct FakeSpeaker;
impl pipeline::Speaker for FakeSpeaker {
    fn play(&self, samples: &[f32], sr: u32) {
        std::thread::sleep(std::time::Duration::from_secs_f32(samples.len() as f32 / sr as f32));
    }
}

fn pct(v: &mut Vec<f32>, p: f32) -> f32 {
    if v.is_empty() {
        return f32::NAN;
    }
    v.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let i = ((v.len() - 1) as f32 * p).round() as usize;
    v[i]
}

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let gpu = args.iter().any(|a| a == "--gpu");
    let pos: Vec<&String> = args.iter().filter(|a| !a.starts_with("--")).collect();
    let threads = std::env::var("PRAXIS_THREADS").ok().and_then(|v| v.parse().ok()).unwrap_or(0);
    match pos.first().map(|s| s.as_str()) {
        Some("asr") if pos.len() == 4 => {
            let asr = Asr::load(pos[1].as_ref(), gpu, threads)?;
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
        // asr-corpus-ao-vivo <modelo> <pasta> <idioma> <saída.json> <silero.onnx> [--max-seg=6]
        Some("asr-corpus-ao-vivo") if pos.len() == 6 => {
            let asr = Asr::load(pos[1].as_ref(), gpu, threads)?;
            let dir = PathBuf::from(pos[2]);
            let lang = pos[3].as_str();
            let max_seg: f32 = args.iter().find_map(|a| a.strip_prefix("--max-seg=")).and_then(|v| v.parse().ok()).unwrap_or(6.0);
            let threshold: f32 = args.iter().find_map(|a| a.strip_prefix("--limiar=")).and_then(|v| v.parse().ok()).unwrap_or(vad::THRESHOLD);
            let adiantado = args.iter().any(|a| a == "--adiantado");
            let mut reuse_count = (0usize, 0usize);
            let manifest: Vec<serde_json::Value> =
                serde_json::from_str(&std::fs::read_to_string(dir.join("manifest.json"))?)?;
            let (mut samples, mut asr_s, mut audio_s, mut nseg) = (vec![], 0f64, 0f64, 0usize);
            for it in &manifest {
                let file = it["file"].as_str().unwrap_or_default();
                let mut a = audio::read_wav_16k_mono(&dir.join(file))?;
                audio_s += a.len() as f64 / 16_000.0;
                a.extend(std::iter::repeat(0.0).take(16_000 * 6 / 10)); // 0,6 s de silêncio no fim
                let cfg = vad::SegmenterConfig { max_seg_s: max_seg, threshold, ..Default::default() };
                let chunks: Vec<&[f32]> = a.chunks(vad::CHUNK).filter(|c| c.len() == vad::CHUNK).collect();
                let mut parts = vec![];
                if pos[5].contains("v5") {
                    let mut seg = vad::Segmenter::new(vad::SileroProbe::load(pos[5], threshold)?, cfg);
                    for c in &chunks { parts.extend(seg.push(c)); }
                    parts.extend(seg.flush());
                } else {
                    let mut seg = vad::Segmenter::new(vad::SileroV6::load(pos[5], threshold)?, cfg);
                    // --adiantado: usa o áudio adiantado quando o produto o reaproveitaria
                    let mut tent: Option<Vec<f32>> = None;
                    let (mut reused, mut total) = (0usize, 0usize);
                    for c in &chunks {
                        for f in seg.push(c) {
                            total += 1;
                            match tent.take() {
                                Some(t) if adiantado && vad::reuse_ok(&t, &f) => { reused += 1; parts.push(vad::with_tail_silence(&t)) }
                                _ => parts.push(f),
                            }
                        }
                        if let Some(t) = seg.tentative() { tent = Some(t); }
                    }
                    parts.extend(seg.flush());
                    if adiantado { reuse_count.0 += reused; reuse_count.1 += total; }
                }
                nseg += parts.len();
                let t = Instant::now();
                let mut texts = vec![];
                for p in &parts {
                    let r = asr.transcribe(p, lang)?;
                    if !r.text.is_empty() {
                        texts.push(r.text);
                    }
                }
                asr_s += t.elapsed().as_secs_f64();
                let hyp = texts.join(" ");
                eprintln!("  {file}  {} trechos  {hyp}", parts.len());
                samples.push(serde_json::json!({"file": file, "speaker": it["speaker"], "ref": it["text"],
                    "hyp": "", "hyp_live": hyp, "dur_s": 0}));
            }
            let out = serde_json::json!({"kind": "asr", "engine": "praxis-rs", "results": [{
                "model": "rust", "lang": lang, "n": samples.len(), "backend": asr.device(),
                "live_segments": nseg, "rtf_live": asr_s / audio_s.max(1e-9), "samples": samples}]});
            std::fs::write(pos[4], serde_json::to_string_pretty(&out)?)?;
            eprintln!("trechos por frase: {:.2}", nseg as f64 / manifest.len().max(1) as f64);
            if adiantado {
                eprintln!("trechos com trabalho adiantado reaproveitado: {} de {}", reuse_count.0, reuse_count.1);
            }
        }
        // tts <pasta da voz> <frases.txt> <pasta de saída>  — um WAV por linha
        // robo <reconhecedor> <silero> <voz> [modelo do ollama]: a "outra pessoa" numa chamada, feita
        // de IA local, para testar o bilateral. Ouve o "Praxis Mic" (a minha tradução), responde
        // com o Ollama e fala no "Praxis Speaker" (o Praxis traduz a resposta de volta para mim).
        Some("robo") if pos.len() >= 4 => {
            use praxis_engine::pipeline::Speaker;
            let modelo = pos.get(4).map(|s| s.to_string()).unwrap_or_else(|| "llama3.2:3b".into());
            let lingua = std::env::var("PRAXIS_ROBO_IDIOMA").unwrap_or_else(|_| "en".into());
            let asr = Asr::load(pos[1].as_ref(), false, 4)?;
            let voz = tts::Voice::load_voz(pos[3].as_ref(), &lingua, 2, false, false)?;
            let saida = devices::Speakers(vec![devices::OutputDevice::open(Some("Praxis Speaker".into()))?],
                                          Arc::new(std::sync::atomic::AtomicBool::new(false)));
            let (tx, rx) = std::sync::mpsc::channel::<Vec<f32>>();
            let _cap = devices::spawn_capture(Some("Praxis Mic".into()), tx, Arc::new(std::sync::atomic::AtomicBool::new(false)))?;
            let mut seg = vad::Segmenter::new(vad::SileroV6::load(pos[2], vad::THRESHOLD)?, vad::SegmenterConfig { max_seg_s: 15.0, ..Default::default() });
            let mut conversa = vec![serde_json::json!({"role": "system", "content": format!(
                "You are Alex, a friendly colleague talking with Diego on a video call. Reply in language '{lingua}' only, \
                 in one or two short natural sentences, and sometimes ask a question back. No emojis, no lists.")})];
            eprintln!("robô pronto: ouvindo o \"Praxis Mic\", falando no \"Praxis Speaker\" ({modelo}, {lingua})");
            let mut pedaco: Vec<f32> = vec![];
            let mut ultimo = Instant::now();
            // transcrição do pedaço atual (refeita só quando chega fala nova)
            let mut lido: Option<String> = None;
            loop {
                match rx.recv_timeout(std::time::Duration::from_millis(100)) {
                    Ok(c) => { for t in seg.push(&c) { pedaco.extend(t); ultimo = Instant::now(); lido = None; } }
                    Err(std::sync::mpsc::RecvTimeoutError::Timeout) => {}
                    Err(_) => break,
                }
                // a tradução chega em pedaços, com pausas entre eles: só responde com a frase
                // terminada (. ? !) e 1,2 s de silêncio, ou depois de 4 s de silêncio de qualquer jeito
                let calado = ultimo.elapsed().as_secs_f32();
                if pedaco.is_empty() || calado < 1.2 { continue; }
                if lido.is_none() { lido = Some(asr.transcribe(&pedaco, &lingua)?.text); }
                let ouvido = lido.clone().unwrap_or_default();
                let terminou = ouvido.trim_end().ends_with(['.', '?', '!']);
                if !terminou && calado < 4.0 { continue; }
                pedaco.clear();
                lido = None;
                if ouvido.split_whitespace().count() < 2 { continue; }
                eprintln!("\n🗣  ouvi: {ouvido}");
                conversa.push(serde_json::json!({"role": "user", "content": ouvido}));
                let t = Instant::now();
                let corpo = serde_json::json!({"model": modelo, "stream": false, "keep_alive": "30m",
                                               "options": {"num_predict": 60, "temperature": 0.7}, "messages": conversa});
                let r: serde_json::Value = serde_json::from_str(&ureq::post("http://localhost:11434/api/chat")
                    .header("Content-Type", "application/json")
                    .send(corpo.to_string())?
                    .body_mut().read_to_string()?)?;
                let resposta = r["message"]["content"].as_str().unwrap_or("").trim().to_string();
                eprintln!("🤖 respondo ({:.1} s): {resposta}", t.elapsed().as_secs_f32());
                conversa.push(serde_json::json!({"role": "assistant", "content": resposta}));
                for frase in praxis_engine::text::speech_chunks(&resposta) {
                    let a = voz.synthesize(&frase, 1.0)?;
                    saida.play(&a, voz.sample_rate);
                }
                // o que entrou enquanto eu falava não é resposta para mim
                while rx.try_recv().is_ok() {}
            }
        }
        // omni-falar <pasta omnivoice> <reconhecedor> <gravação.wav> <idioma da gravação> <idioma alvo> <frases.txt> <saída>
        Some("omni-falar") if pos.len() == 8 => {
            let d = PathBuf::from(pos[1]);
            let t0 = Instant::now();
            let o = praxis_engine::omni::OmniVoice::carregar(&d.join("omnivoice-base-Q8_0.gguf"), &d.join("omnivoice-tokenizer-F32.gguf"),
                &praxis_engine::omni::dispositivo_preferido(), std::env::var("PRAXIS_PASSOS").ok().and_then(|v| v.parse().ok()).unwrap_or(8))?;
            eprintln!("carga {:.1} s em {}", t0.elapsed().as_secs_f32(), o.dispositivo);
            let x = audio::read_wav_16k_mono(pos[3].as_ref())?;
            let (a, b) = praxis_engine::omni::trecho_de_referencia(&x);
            let asr = Asr::load(pos[2].as_ref(), false, 4)?;
            let texto = asr.transcribe(&x[a..b], pos[4])?.text;
            eprintln!("referência {:.1}–{:.1} s: {texto}", a as f32 / 16000.0, b as f32 / 16000.0);
            let t1 = Instant::now();
            o.definir_referencia(&x[a..b], &texto)?;
            eprintln!("referência codificada em {:.2} s", t1.elapsed().as_secs_f32());
            let out = PathBuf::from(pos[7]);
            std::fs::create_dir_all(&out)?;
            let pausa: f32 = std::env::var("PRAXIS_PAUSA_S").ok().and_then(|v| v.parse().ok()).unwrap_or(0.0);
            for (i, l) in std::fs::read_to_string(pos[6])?.lines().filter(|l| !l.trim().is_empty()).enumerate() {
                if pausa > 0.0 { std::thread::sleep(std::time::Duration::from_secs_f32(pausa)); }
                let t = Instant::now();
                let a = o.falar(l, pos[5])?;
                let dt = t.elapsed().as_secs_f32();
                let dur = a.len() as f32 / 24_000.0;
                eprintln!("{i}: {dt:.2} s para {dur:.1} s de fala ({:.2} s por s) — {l}", dt / dur);
                audio::write_wav16(&out.join(format!("{i:02}.wav")), &a, 24_000)?;
            }
        }
        // omni-passo <pacote> <processador|coreml> <llm_fp32.onnx|llm_fp16.onnx> [vezes]
        Some("omni-passo") if pos.len() >= 4 => {
            let placa = if pos[2].as_str() == "coreml" { praxis_engine::omni::Placa::CoreMlPlaca } else { praxis_engine::omni::Placa::Processador };
            let vezes = pos.get(4).and_then(|v| v.parse().ok()).unwrap_or(3);
            let (t, dif, carga) = praxis_engine::omni::medir_passo(pos[1].as_ref(), pos[3], placa, 4, vezes)?;
            println!("{} {}: carga {carga:.1} s, passo {t:.3} s, diferença máx. {dif:.4}", pos[2], pos[3]);
        }
        // clonar <gravação.wav> <pacote supertonic> <medidor de voz.onnx> <saída voice.bin> [rodadas]
        Some("clonar") if pos.len() >= 5 => {
            let rodadas = pos.get(5).and_then(|v| v.parse().ok()).unwrap_or(praxis_engine::clone::RODADAS);
            let x = audio::read_wav_16k_mono(pos[1].as_ref())?;
            let parar = std::sync::atomic::AtomicBool::new(false);
            let c = praxis_engine::clone::clonar(&x, pos[2].as_ref(), pos[3].as_ref(), pos[4].as_ref(), rodadas, 4,
                &|f, t| eprintln!("{:3.0}% {t}", f * 100.0), &parar)?;
            println!("{}", serde_json::to_string(&c)?);
        }
        Some("tts") if pos.len() == 4 => {
            // teste da voz: PRAXIS_TTS_IDIOMA, PRAXIS_TTS_MASCULINA=1, PRAXIS_TTS_ESCALA (velocidade)
            let lang = std::env::var("PRAXIS_TTS_IDIOMA").unwrap_or_else(|_| "en".into());
            let masc = std::env::var("PRAXIS_TTS_MASCULINA").map(|v| v == "1").unwrap_or(false);
            let escala: f32 = std::env::var("PRAXIS_TTS_ESCALA").ok().and_then(|v| v.parse().ok()).unwrap_or(1.0);
            let v = tts::Voice::load_voz(pos[1].as_ref(), &lang, 4, false, masc)?;
            let out = PathBuf::from(pos[3]);
            std::fs::create_dir_all(&out)?;
            let lines: Vec<String> = std::fs::read_to_string(pos[2])?.lines().map(String::from).collect();
            v.synthesize("aquecimento", 1.0)?;
            let (mut synth_s, mut audio_s) = (0f64, 0f64);
            for (i, l) in lines.iter().enumerate() {
                let t = Instant::now();
                let a = v.synthesize(l, escala)?;
                synth_s += t.elapsed().as_secs_f64();
                audio_s += a.len() as f64 / v.sample_rate as f64;
                let spec = hound::WavSpec { channels: 1, sample_rate: v.sample_rate, bits_per_sample: 16, sample_format: hound::SampleFormat::Int };
                let mut w = hound::WavWriter::create(out.join(format!("{i:03}.wav")), spec)?;
                for x in a {
                    w.write_sample((x.clamp(-1.0, 1.0) * 32767.0) as i16)?;
                }
                w.finalize()?;
            }
            eprintln!("{} frases: {:.2} s de síntese para {:.1} s de fala ({:.3} s por s de fala)",
                      lines.len(), synth_s, audio_s, synth_s / audio_s.max(1e-9));
        }
        // stream <whisper> <silero> <gravação.wav> <origem> <destino> <nllb|argos> <tradutor> <voz> <saída.json>
        Some("stream") if pos.len() == 10 => {
            let max_seg: f32 = args.iter().find_map(|a| a.strip_prefix("--max-seg=")).and_then(|v| v.parse().ok()).unwrap_or(6.0);
            let (src, tgt) = (pos[4].to_string(), pos[5].to_string());
            let asr = Arc::new(Asr::load(pos[1].as_ref(), gpu, threads)?);
            let translator: Arc<dyn pipeline::Translate> = match pos[6].as_str() {
                "nllb" => Arc::new(mt::Nllb::load(pos[7].as_ref(), gpu)?),
                _ => {
                    let dir = PathBuf::from(pos[7]);
                    let route = if src != "en" && tgt != "en" {
                        vec![mt::ArgosPair::load(&mt::argos_package(&dir, &src, "en")?, gpu)?,
                             mt::ArgosPair::load(&mt::argos_package(&dir, "en", &tgt)?, gpu)?]
                    } else {
                        vec![mt::ArgosPair::load(&mt::argos_package(&dir, &src, &tgt)?, gpu)?]
                    };
                    Arc::new(pipeline::ArgosRoute(route))
                }
            };
            // a voz fala o idioma de destino; o Kokoro precisa de 4 núcleos.
            // PRAXIS_OMNI_DIR (modelos GGUF) + PRAXIS_OMNI_GRAVACAO (a voz, no idioma de origem): OmniVoice
            let vdir = PathBuf::from(pos[8]);
            let vthreads = if vdir.join("voices.bin").exists() { 4 } else { 2 };
            let voice = Arc::new(match (std::env::var("PRAXIS_OMNI_DIR"), std::env::var("PRAXIS_OMNI_GRAVACAO")) {
                (Ok(d), Ok(g)) => {
                    let d = PathBuf::from(d);
                    let passos = std::env::var("PRAXIS_PASSOS").ok().and_then(|v| v.parse().ok()).unwrap_or(8);
                    let o = praxis_engine::omni::OmniVoice::carregar(&d.join("omnivoice-base-Q8_0.gguf"), &d.join("omnivoice-tokenizer-F32.gguf"),
                                                                     &praxis_engine::omni::dispositivo_preferido(), passos)?;
                    let x = audio::read_wav_16k_mono(g.as_ref())?;
                    let (a, b) = praxis_engine::omni::trecho_de_referencia(&x);
                    let texto = asr.transcribe(&x[a..b], &std::env::var("PRAXIS_OMNI_IDIOMA").unwrap_or_else(|_| "pt".into()))?.text;
                    o.definir_referencia(&x[a..b], &texto)?;
                    let r = o.medir()?;
                    eprintln!("placa: {r:.2} s por s de fala; pedaço mínimo {} palavras", o.pedaco_minimo());
                    tts::Voice::omni(Arc::new(o), &tgt)
                }
                _ => tts::Voice::load_on(&vdir, &tgt, vthreads, gpu)?,
            });
            eprintln!("voz na placa de vídeo: {}", gpu && vdir.join("voices.bin").exists() && tts::cuda_provider_available());
            // aquecimento (como o teste do Python)
            asr.transcribe(&vec![0.0; 16_000], &src)?;
            translator.translate("warm up.", &src, &tgt)?;
            voice.synthesize("warm up.", 1.0)?;
            let wav = PathBuf::from(pos[3]);
            let reference = std::fs::read_to_string(wav.with_extension("json")).ok()
                .and_then(|s| serde_json::from_str::<serde_json::Value>(&s).ok())
                .and_then(|m| m["text"].as_str().map(String::from)).unwrap_or_default();
            let mut a = audio::read_wav_16k_mono(&wav)?;
            let speech_s = a.len() as f32 / 16_000.0;
            a.extend(std::iter::repeat(0.0).take(16_000 * 3)); // o falante para
            let (atx, arx) = std::sync::mpsc::channel();
            let (etx, erx) = std::sync::mpsc::channel();
            let shared = pipeline::Shared::new();
            let dir = pipeline::Direction { name: "out".into(), src: src.clone(), tgt: tgt.clone(), to_speaker: false, echo_gate: false, leaks: false, leak_when: None, simultaneous: !args.iter().any(|a| a == "--por-frase") };
            let cfg = vad::SegmenterConfig { max_seg_s: max_seg, ..Default::default() };
            let handles = pipeline::spawn_direction(arx, asr, translator, Some(voice), Arc::new(FakeSpeaker), dir, cfg,
                                                     pos[2].to_string(), shared.clone(), etx)?;
            let t0 = Instant::now();
            for (k, c) in a.chunks(vad::CHUNK).enumerate() {
                let target = std::time::Duration::from_secs_f32(k as f32 * vad::CHUNK as f32 / 16_000.0);
                if let Some(d) = target.checked_sub(t0.elapsed()) { std::thread::sleep(d); }
                if c.len() == vad::CHUNK { atx.send(c.to_vec())?; }
            }
            // espera a fila esvaziar: nada novo por 3 s e nada tocando (máx. 120 s)
            let mut evs = vec![];
            let mut last = Instant::now();
            let mut play_until = 0f32;
            while last.elapsed().as_secs_f32() < 3.0 || shared.now_s() < play_until {
                if let Ok(e) = erx.recv_timeout(std::time::Duration::from_millis(100)) {
                    if let pipeline::Event::Play { start_s, dur_s, .. } = &e { play_until = play_until.max(start_s + dur_s); }
                    evs.push(e);
                    last = Instant::now();
                }
                if t0.elapsed().as_secs_f32() > speech_s + 120.0 { break; }
            }
            shared.stop.store(true, std::sync::atomic::Ordering::Relaxed);
            drop(atx);
            for h in handles { let _ = h.join(); }
            let mut ends = std::collections::HashMap::new();
            let mut first_play = std::collections::HashMap::new();
            let (mut transcript, mut translation) = (vec![], vec![]);
            for e in &evs {
                match e {
                    pipeline::Event::Segment { id, speech_end_s, .. } => { ends.insert(*id, *speech_end_s); }
                    pipeline::Event::Play { id, start_s, .. } => { first_play.entry(*id).or_insert(*start_s); }
                    pipeline::Event::Transcript { text, .. } => transcript.push(text.clone()),
                    pipeline::Event::Translation { text, .. } => translation.push(text.clone()),
                    pipeline::Event::Error { msg } => eprintln!("erro: {msg}"),
                    pipeline::Event::Stage { .. } => {}
                }
            }
            // onde vai o tempo, trecho a trecho: espera do silêncio → reconhecer → traduzir → voz → fila
            let mut at: std::collections::HashMap<(usize, String), f32> = std::collections::HashMap::new();
            let mut emitted = std::collections::HashMap::new();
            for e in &evs {
                match e {
                    pipeline::Event::Stage { id, stage, at_s, .. } => { at.insert((*id, stage.clone()), *at_s); }
                    pipeline::Event::Segment { id, emitted_s, .. } => { emitted.insert(*id, *emitted_s); }
                    _ => {}
                }
            }
            let mut ids: Vec<usize> = first_play.keys().cloned().collect();
            ids.sort();
            let mut cols: Vec<Vec<f32>> = vec![vec![]; 5];
            for id in &ids {
                let g = |k: &str| at.get(&(*id, k.to_string())).cloned();
                if let (Some(end), Some(em), Some(a), Some(b), Some(c), Some(p)) =
                    (ends.get(id), emitted.get(id), g("transcrito"), g("traduzido"), g("voz"), first_play.get(id)) {
                    let row = [em - end, a - em, b - a, c - b, p - c].map(|x| x * 1000.0);
                    eprintln!("  trecho {id:2}: silêncio {:4.0} | reconhecer {:4.0} | traduzir {:4.0} | voz {:4.0} | fila {:5.0} ms",
                              row[0], row[1], row[2], row[3], row[4]);
                    for (c, v) in cols.iter_mut().zip(row) { c.push(v); }
                }
            }
            if !cols[0].is_empty() {
                let m: Vec<f32> = cols.iter_mut().map(|c| pct(c, 0.5)).collect();
                eprintln!("  mediana: silêncio {:.0} | reconhecer {:.0} | traduzir {:.0} | voz {:.0} | fila {:.0} ms", m[0], m[1], m[2], m[3], m[4]);
            }
            // tradução simultânea: início da fala do trecho → 1º som, e fim da fala → último som
            {
                let mut last_play = std::collections::HashMap::new();
                let mut starts = std::collections::HashMap::new();
                for e in &evs {
                    if let pipeline::Event::Play { id, start_s, .. } = e { last_play.insert(*id, *start_s); }
                    if let pipeline::Event::Segment { id, speech_end_s, .. } = e { starts.entry(*id).or_insert(*speech_end_s); }
                }
                let mut antes: Vec<f32> = vec![];
                let mut fim: Vec<f32> = vec![];
                for (id, end) in &ends {
                    if let (Some(f), Some(l)) = (first_play.get(id), last_play.get(id)) {
                        antes.push(end - f);   // > 0: a tradução começou a tocar antes da fala acabar
                        fim.push(l - end);
                    }
                }
                if !antes.is_empty() {
                    let fala_antes = antes.iter().filter(|x| **x > 0.0).count();
                    eprintln!("simultânea: em {fala_antes} de {} trechos a tradução começou ANTES da pessoa terminar (mediana {:.1} s antes); \
                              último pedaço depois do fim da fala: mediana {:.2} s, máx. {:.2} s",
                              antes.len(), pct(&mut antes.clone(), 0.5), pct(&mut fim.clone(), 0.5), fim.iter().cloned().fold(0.0, f32::max));
                }
            }
            let mut lats: Vec<(f32, f32)> = first_play.iter().filter_map(|(id, p)| ends.get(id).map(|e| (*e, (p - e) * 1000.0))).collect();
            lats.sort_by(|a, b| a.0.partial_cmp(&b.0).unwrap());
            let mut l: Vec<f32> = lats.iter().map(|x| x.1).collect();
            let half = speech_s / 2.0;
            let mut l1: Vec<f32> = lats.iter().filter(|x| x.0 <= half).map(|x| x.1).collect();
            let mut l2: Vec<f32> = lats.iter().filter(|x| x.0 > half).map(|x| x.1).collect();
            let trend = pct(&mut l2, 0.5) - pct(&mut l1, 0.5);
            let drain = (play_until - speech_s).max(0.0);
            let (p50, p95, max) = (pct(&mut l, 0.5), pct(&mut l, 0.95), l.iter().cloned().fold(0.0, f32::max));
            let keeps_up = p50 <= 4000.0 && trend <= 1500.0 && drain <= 8.0;
            eprintln!("{src}->{tgt}: atraso típico {:.0} ms, pior caso comum {:.0} ms, máx. {:.0} ms | crescimento {:+.0} ms | pendente {:.1} s | {}",
                      p50, p95, max, trend, drain, if keeps_up { "ACOMPANHA" } else { "FICA PARA TRÁS" });
            let out = serde_json::json!({"pair": format!("{src}->{tgt}"), "engine": "praxis-rs", "speech_s": speech_s,
                "reference": reference, "transcript": transcript.join(" "), "translation": translation.join(" "),
                "latency_audio_ms": {"p50": p50, "p95": p95, "max": max}, "lag_trend_ms": trend,
                "drain_s": drain, "keeps_up": keeps_up, "segments": ends.len()});
            std::fs::write(pos[9], serde_json::to_string_pretty(&out)?)?;
        }
        // tom médio de uma gravação 16 kHz (a mesma conta que escolhe a voz grave ou aguda)
        Some("tom") if pos.len() == 2 => {
            let x = audio::read_wav_16k_mono(pos[1].as_ref())?;
            let tom = audio::tom_medio(&x, 16_000);
            println!("{}", serde_json::json!({"tom_hz": tom, "masculina": tom.map(|t| t < 165.0), "segundos": x.len() as f32 / 16_000.0}));
        }
        // apps tocando som agora (bilateral: de qual app vem a outra pessoa)
        Some("apps") => {
            println!("{}", serde_json::to_string_pretty(&praxis_engine::app_audio::list())?);
        }
        // teste no Windows: grava o som de um app num arquivo / muda o volume de um app
        #[cfg(windows)]
        Some("gravar-app") if pos.len() == 4 => {
            let (tx, rx) = std::sync::mpsc::channel::<Vec<f32>>();
            let stop = Arc::new(std::sync::atomic::AtomicBool::new(false));
            let h = praxis_engine::app_audio::spawn_capture(pos[1].to_string(), tx, stop.clone())?;
            let fim = Instant::now() + std::time::Duration::from_secs_f32(pos[2].parse()?);
            let mut todo = vec![];
            while Instant::now() < fim {
                if let Ok(c) = rx.recv_timeout(std::time::Duration::from_millis(100)) { todo.extend(c); }
            }
            stop.store(true, std::sync::atomic::Ordering::Relaxed);
            let _ = h.join();
            let rms = (todo.iter().map(|x| x * x).sum::<f32>() / todo.len().max(1) as f32).sqrt();
            audio::write_wav16(pos[3].as_ref(), &todo, vad::SR as u32)?;
            println!("{{\"segundos\": {:.1}, \"nivel\": {rms:.4}}}", todo.len() as f32 / vad::SR as f32);
        }
        #[cfg(windows)]
        Some("volume-app") if pos.len() == 3 => {
            println!("{} sessões", praxis_engine::app_audio::set_app_volume(pos[1], pos[2].parse()?));
        }
        Some("dispositivos") => {
            println!("{}", serde_json::to_string_pretty(&serde_json::json!({
                "entradas": devices::list_inputs(), "saidas": devices::list_outputs()}))?);
        }
        // run --src pt --tgt en --whisper D --silero F --tradutor nllb|argos --modelo-tradutor D --voz D
        //     [--voz-in D (bilateral)] [--mic NOME] [--saida NOME] [--ouvir] [--fones] [--max-seg=S] [--segundos=N]
        Some("run") => {
            let opt = |k: &str| args.iter().position(|a| a == k).and_then(|i| args.get(i + 1)).cloned();
            let need = |k: &str| opt(k).ok_or_else(|| anyhow::anyhow!("falta {k}"));
            let (src, tgt) = (need("--src")?, need("--tgt")?);
            let fones = args.iter().any(|a| a == "--fones");
            let ouvir = args.iter().any(|a| a == "--ouvir");
            let bilateral = opt("--voz-in").is_some();
            let max_seg: f32 = args.iter().find_map(|a| a.strip_prefix("--max-seg=")).and_then(|v| v.parse().ok())
                .unwrap_or(if gpu { 15.0 } else { 6.0 });
            let secs: Option<f32> = args.iter().find_map(|a| a.strip_prefix("--segundos=")).and_then(|v| v.parse().ok());
            let emit = |v: serde_json::Value| println!("{v}");
            emit(serde_json::json!({"e": "progress", "pct": 10, "msg": "Preparando o microfone virtual…"}));
            let vm = devices::VirtualMic::setup(bilateral, opt("--app"))?;
            emit(serde_json::json!({"e": "virtual_mic", "mic": vm.mic_label, "peer": vm.peer_label}));
            emit(serde_json::json!({"e": "progress", "pct": 30, "msg": "Carregando o reconhecimento de fala…"}));
            let asr = Arc::new(Asr::load(need("--whisper")?.as_ref(), gpu, threads)?);
            emit(serde_json::json!({"e": "progress", "pct": 60, "msg": "Carregando a tradução…"}));
            let load_tr = |a: &str, b: &str| -> Result<Arc<dyn pipeline::Translate>> {
                let path = need("--modelo-tradutor")?;
                Ok(match opt("--tradutor").as_deref() {
                    Some("nllb") => Arc::new(mt::Nllb::load(path.as_ref(), gpu)?),
                    _ => {
                        let dir = PathBuf::from(&path);
                        let route = if a != "en" && b != "en" {
                            vec![mt::ArgosPair::load(&mt::argos_package(&dir, a, "en")?, gpu)?,
                                 mt::ArgosPair::load(&mt::argos_package(&dir, "en", b)?, gpu)?]
                        } else {
                            vec![mt::ArgosPair::load(&mt::argos_package(&dir, a, b)?, gpu)?]
                        };
                        Arc::new(pipeline::ArgosRoute(route))
                    }
                })
            };
            emit(serde_json::json!({"e": "progress", "pct": 80, "msg": "Carregando a voz…"}));
            let voice_out = Arc::new(tts::PiperVoice::load(need("--voz")?.as_ref(), 2)?);
            let shared = pipeline::Shared::new();
            let (etx, erx) = std::sync::mpsc::channel();
            let mut handles = vec![];
            let cfg = vad::SegmenterConfig { max_seg_s: max_seg, ..Default::default() };
            let silero = need("--silero")?;
            // ida: meu microfone → tradução → microfone virtual (+ meu fone, se pedi para ouvir)
            let mut outs = vec![devices::OutputDevice::open(vm.target.clone())?];
            if ouvir {
                outs.push(devices::OutputDevice::open(opt("--saida"))?);
            }
            let (mtx, mrx) = std::sync::mpsc::channel();
            handles.push(devices::spawn_capture(opt("--mic"), mtx, Arc::new(std::sync::atomic::AtomicBool::new(false)))?);
            let dir_out = pipeline::Direction { name: "out".into(), src: src.clone(), tgt: tgt.clone(),
                to_speaker: ouvir, echo_gate: !fones && (ouvir || opt("--voz-in").is_some()), leaks: ouvir && !fones, leak_when: None, simultaneous: !args.iter().any(|a| a == "--por-frase") };
            handles.extend(pipeline::spawn_direction(mrx, asr.clone(), load_tr(&src, &tgt)?, Some(voice_out),
                Arc::new(devices::Speakers(outs, Arc::new(std::sync::atomic::AtomicBool::new(false)))), dir_out, cfg, silero.clone(), shared.clone(), etx.clone())?);
            // volta (bilateral): a outra pessoa → tradução → meu fone/caixa de som
            if let Some(vin) = opt("--voz-in") {
                let voice_in = Arc::new(tts::PiperVoice::load(vin.as_ref(), 2)?);
                let (ptx, prx) = std::sync::mpsc::channel();
                handles.push(devices::spawn_peer_capture(&vm, ptx, Arc::new(std::sync::atomic::AtomicBool::new(false)))?);
                let dir_in = pipeline::Direction { name: "in".into(), src: tgt.clone(), tgt: src.clone(),
                    to_speaker: true, echo_gate: false, leaks: !fones, leak_when: None, simultaneous: !args.iter().any(|a| a == "--por-frase") };
                // a trava de eco da ida também precisa saber quando a volta toca no alto-falante
                handles.extend(pipeline::spawn_direction(prx, asr.clone(), load_tr(&tgt, &src)?, Some(voice_in),
                    Arc::new(devices::Speakers(vec![devices::OutputDevice::open(opt("--saida"))?], Arc::new(std::sync::atomic::AtomicBool::new(false)))), dir_in, cfg,
                    silero.clone(), shared.clone(), etx.clone())?);
            }
            drop(etx);
            emit(serde_json::json!({"e": "progress", "pct": 100, "msg": "Traduzindo"}));
            emit(serde_json::json!({"e": "ready"}));
            let t0 = Instant::now();
            loop {
                if let Some(s) = secs { if t0.elapsed().as_secs_f32() > s { break; } }
                match erx.recv_timeout(std::time::Duration::from_millis(200)) {
                    Ok(e) => println!("{}", serde_json::to_string(&e)?),
                    Err(std::sync::mpsc::RecvTimeoutError::Timeout) => {}
                    Err(_) => break,
                }
            }
            shared.stop.store(true, std::sync::atomic::Ordering::Relaxed);
            drop(vm); // remove os dispositivos virtuais (Linux)
            emit(serde_json::json!({"e": "stopped"}));
            std::process::exit(0);
        }
        Some("asr-corpus") if pos.len() == 5 => {
            let asr = Asr::load(pos[1].as_ref(), gpu, threads)?;
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
                "model": model, "lang": lang, "n": samples.len(), "backend": asr.device(),
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
