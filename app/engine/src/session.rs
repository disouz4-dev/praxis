//! Sessão do Praxis: escolhe modelo e tradutor pelo computador (as regras medidas do
//! Praxis em Python), aplica o limite de qualidade por idioma, baixa o que faltar e liga o
//! motor. A janela (Tauri) e a linha de comando usam a mesma sessão.

use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::mpsc::Sender;
use std::sync::Arc;
use std::thread::JoinHandle;

use anyhow::{anyhow, bail, Result};
use serde::{Deserialize, Serialize};

use crate::asr::Asr;
use crate::devices::{self, OutputDevice, Speakers, VirtualMic};
use crate::models::ModelStore;
use crate::mt;
use crate::pipeline::{self, ArgosRoute, Direction, Shared, Translate};
use crate::tts::Voice;
use crate::vad::SegmenterConfig;

/// Meta do produto: 1% de erro; teto de 3%. Idioma acima disso neste hardware não é oferecido.
pub const QUALITY_LIMIT: f32 = 0.03;

/// Erro REAL da transcrição no modo ao vivo, medido com 40 frases de vários falantes por
/// idioma (Google FLEURS) e auditado (inglês com 100 frases) — mesma tabela do Python.
pub const MEASURED_ERROR_GPU: &[(&str, f32)] = &[
    ("pt", 0.024), ("en", 0.020), ("es", 0.017), ("fr", 0.043), ("de", 0.019), ("it", 0.024),
    ("ru", 0.036), ("zh", 0.093), ("nl", 0.036), ("pl", 0.047), ("uk", 0.032), ("tr", 0.041),
    ("ar", 0.076), ("hi", 0.197), ("ja", 0.045), ("ko", 0.138),
];
/// Processador: Parakeet (ultra, v2 no inglês, v3 em ru/uk, japonês) com trecho de até 15 s
/// e busca por vários caminhos; Whisper small nos outros.
pub const MEASURED_ERROR_CPU: &[(&str, f32)] = &[
    ("pt", 0.029), ("en", 0.020), ("es", 0.020), ("fr", 0.043), ("de", 0.027), ("it", 0.018),
    ("ru", 0.050), ("zh", 0.173), ("nl", 0.049), ("pl", 0.064), ("uk", 0.058), ("tr", 0.166),
    ("ar", 0.293), ("hi", 0.745), ("ja", 0.047), ("ko", 0.252),
];
/// No processador, o NLLB só entra nos idiomas em que o Argos é fraco (+6 a +10 pontos);
/// com placa de vídeo, em tudo (é mais rápido e melhor em 149 de 210 sentidos).
pub const NLLB_WEAK_LANGS: &[&str] = &["ar", "tr", "ko", "ja", "uk", "hi"];
/// Pacotes do Argos com divisão "BPE + Moses", ainda não lidos pelo motor em Rust
pub const ARGOS_BPE_PAIRS: &[(&str, &str)] = &[("es", "en"), ("en", "pl"), ("uk", "en")];

pub fn has_nvidia_gpu() -> bool {
    if cfg!(target_os = "macos") {
        return false;
    }
    if std::env::var("PRAXIS_DEVICE").map(|v| v == "cpu").unwrap_or(false) {
        return false;
    }
    std::process::Command::new("nvidia-smi").arg("-L").output()
        .map(|o| o.status.success() && String::from_utf8_lossy(&o.stdout).contains("GPU"))
        .unwrap_or(false)
}

pub fn measured_error(lang: &str, gpu: bool) -> Option<f32> {
    let t = if gpu { MEASURED_ERROR_GPU } else { MEASURED_ERROR_CPU };
    t.iter().find(|(l, _)| *l == lang).map(|(_, e)| *e)
}

/// Liberado neste hardware? (explicação em linguagem simples quando não)
pub fn language_allowed(lang: &str, gpu: bool) -> (bool, String) {
    match measured_error(lang, gpu) {
        Some(e) if e > QUALITY_LIMIT => {
            let mut msg = format!(
                "O reconhecimento deste idioma erra cerca de {:.0}% das palavras {} — acima do limite de qualidade do Praxis ({:.0}%).",
                e * 100.0, if gpu { "mesmo com placa de vídeo" } else { "neste computador sem placa de vídeo" }, QUALITY_LIMIT * 100.0);
            if !gpu {
                if let Some(g) = measured_error(lang, true).filter(|g| *g <= QUALITY_LIMIT) {
                    msg.push_str(&format!(" Com uma placa de vídeo o erro cai para cerca de {:.0}%.", g * 100.0));
                }
            }
            (false, msg)
        }
        _ => (true, String::new()),
    }
}

/// Melhor reconhecedor medido por idioma (erro real ao vivo, FLEURS, 21/10/2026) — a mesma
/// tabela do Python (ASR_CHOICE). Com placa de vídeo o Parakeet roda no processador ao lado.
pub const ASR_CHOICE_CPU: &[(&str, &str)] = &[
    ("en", "parakeet-tdt-0.6b-v2-int8"), ("pt", "parakeet-ultra-int8"), ("de", "parakeet-ultra-int8"),
    ("es", "parakeet-ultra-int8"), ("it", "parakeet-ultra-int8"), ("fr", "parakeet-ultra-int8"),
    ("nl", "parakeet-ultra-int8"), ("pl", "parakeet-ultra-int8"), ("ru", "parakeet-tdt-0.6b-v3-int8"),
    ("uk", "parakeet-tdt-0.6b-v3-int8"), ("ja", "parakeet-tdt_ctc-0.6b-ja-35000-int8"),
];
pub const ASR_CHOICE_GPU: &[(&str, &str)] = &[
    ("en", "parakeet-tdt-0.6b-v2-int8"), ("fr", "parakeet-ultra-int8"), ("pt", "large-v3-turbo"),
    ("es", "large-v3-turbo"), ("de", "large-v3-turbo"), ("it", "large-v3-turbo"),
];

/// Reconhecimento de fala para quem fala `lang`: o melhor medido; fora da tabela, Whisper
/// large-v3 com placa de vídeo e Whisper small no processador.
pub fn asr_model_for(lang: &str, gpu: bool, choice: &str) -> String {
    if choice != "auto" {
        return choice.to_string();
    }
    let (table, other) = if gpu { (ASR_CHOICE_GPU, "large-v3") } else { (ASR_CHOICE_CPU, "small") };
    table.iter().find(|(l, _)| *l == lang).map(|(_, m)| *m).unwrap_or(other).to_string()
}

/// Trecho máximo de fala: 15 s com placa de vídeo ou Parakeet (o corte no meio da fala era a
/// maior fonte de erro); 6 s com o Whisper no processador (trecho longo atrasa demais).
pub fn max_segment_s(model: &str, gpu: bool) -> f32 {
    if gpu || model.starts_with("parakeet") { 15.0 } else { 6.0 }
}

pub fn translator_for(src: &str, tgt: &str, gpu: bool, choice: &str) -> &'static str {
    match choice {
        "argos" if !ARGOS_BPE_PAIRS.contains(&(src, tgt)) => "argos",
        "nllb" => "nllb",
        _ if gpu => "nllb",
        _ if NLLB_WEAK_LANGS.contains(&src) || NLLB_WEAK_LANGS.contains(&tgt) => "nllb",
        // o par passa pelo inglês: se qualquer metade for BPE, vai pelo NLLB
        _ => {
            let route: Vec<(&str, &str)> = if src != "en" && tgt != "en" { vec![(src, "en"), ("en", tgt)] } else { vec![(src, tgt)] };
            if route.iter().any(|p| ARGOS_BPE_PAIRS.contains(p)) { "nllb" } else { "argos" }
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionConfig {
    pub src: String,
    pub tgt: String,
    /// "auto" (turbo com placa de vídeo, small sem) ou o nome do modelo
    #[serde(default = "auto")]
    pub model: String,
    /// "auto" | "argos" | "nllb"
    #[serde(default = "auto")]
    pub translator: String,
    #[serde(default)]
    pub mic: Option<String>,
    /// saída para ouvir (fone/caixa)
    #[serde(default)]
    pub output: Option<String>,
    /// também tocar a minha tradução na saída acima
    #[serde(default)]
    pub monitor: bool,
    /// modo bilateral (a outra pessoa também é traduzida)
    #[serde(default)]
    pub bilateral: bool,
    /// tradução simultânea (fala enquanto a pessoa ainda fala) — a premissa do Praxis; falso =
    /// espera o fim de cada trecho
    #[serde(default = "sim")]
    pub simultaneous: bool,
    /// estou de fone: sem trava de eco
    #[serde(default)]
    pub headphones: bool,
    /// vozes (pacotes sherpa-onnx); vazio = a padrão de cada idioma
    #[serde(default)]
    pub voice_out: Option<String>,
    #[serde(default)]
    pub voice_in: Option<String>,
    /// bilateral: o app de chamada de onde vem a outra pessoa (o Praxis pega o som dele
    /// sozinho); vazio = o usuário manda a saída do app para o "Praxis Speaker"
    #[serde(default)]
    pub peer_app: Option<String>,
    /// gravação da voz do usuário (obrigatória; amostra da voz clonada). Enquanto a clonagem
    /// não entra, serve para escolher a voz pronta do mesmo tipo (grave ou aguda).
    #[serde(default)]
    pub minha_voz: Option<String>,
    /// bilateral: a outra pessoa ganha voz traduzida (falso = só legenda: ouço a voz original
    /// e leio a tradução, por exemplo para treinar o idioma)
    #[serde(default = "sim")]
    pub peer_voice: bool,
    /// bilateral: volume da voz original da outra pessoa por baixo da tradução (0 = não ouvir)
    #[serde(default)]
    pub original_volume: f32,
    /// ignora o limite de qualidade (só para testes)
    #[serde(default)]
    pub allow_weak_language: bool,
}

fn auto() -> String {
    "auto".into()
}

fn sim() -> bool {
    true
}

#[derive(Debug, Clone, Serialize)]
#[serde(tag = "e", rename_all = "snake_case")]
pub enum SessionEvent {
    Progress { pct: u32, msg: String },
    Download { what: String, got: u64, total: u64 },
    Hardware { gpu: bool, model: String, translator: String, max_seg_s: f32 },
    VirtualMic { mic: String, peer: String },
    Ready,
    Engine { ev: pipeline::Event },
    Stopped,
    Error { msg: String },
}

pub struct Session {
    shared: Arc<Shared>,
    stop_capture: Arc<AtomicBool>,
    handles: Vec<JoinHandle<()>>,
    vm: Option<VirtualMic>,
}

impl Session {
    pub fn start(cfg: SessionConfig, store: &ModelStore, events: Sender<SessionEvent>) -> Result<Self> {
        let emit = |e: SessionEvent| {
            let _ = events.send(e);
        };
        let progress = |pct: u32, msg: &str| emit(SessionEvent::Progress { pct, msg: msg.into() });
        let dl = |what: &str, got: u64, total: u64| {
            let _ = events.send(SessionEvent::Download { what: what.into(), got, total });
        };
        if cfg.src == cfg.tgt {
            bail!("escolha idiomas diferentes para falar e traduzir");
        }
        let gpu = has_nvidia_gpu();
        if !cfg.allow_weak_language {
            let spoken = if cfg.bilateral { vec![cfg.src.as_str(), cfg.tgt.as_str()] } else { vec![cfg.src.as_str()] };
            for l in spoken {
                let (ok, why) = language_allowed(l, gpu);
                if !ok {
                    bail!("{why}");
                }
            }
        }
        let model = asr_model_for(&cfg.src, gpu, &cfg.model);
        let model_in = asr_model_for(&cfg.tgt, gpu, &cfg.model);
        let max_seg_s = max_segment_s(&model, gpu);
        let tr_out = translator_for(&cfg.src, &cfg.tgt, gpu, &cfg.translator);
        let tr_in = translator_for(&cfg.tgt, &cfg.src, gpu, &cfg.translator);
        emit(SessionEvent::Hardware { gpu, model: model.clone(), translator: tr_out.into(), max_seg_s });

        // os dispositivos primeiro: sem o cabo virtual não adianta baixar nada (e o erro vem na hora)
        progress(2, "Preparando o microfone virtual…");
        let vm = VirtualMic::setup(cfg.bilateral, cfg.peer_app.clone())?;
        // com o app de chamada escolhido não há nada a configurar na saída dele
        let peer = if vm.peer_app.is_some() { String::new() } else { vm.peer_label.clone() };
        emit(SessionEvent::VirtualMic { mic: vm.mic_label.clone(), peer });

        progress(5, "Preparando os modelos…");
        let ensure_asr = |m: &str| if m.starts_with("parakeet") { store.ensure_parakeet(m, &dl) } else { store.ensure_whisper(m, &dl) };
        let asr_dir = ensure_asr(&model)?;
        let asr_in_dir = if cfg.bilateral && model_in != model { Some(ensure_asr(&model_in)?) } else { None };
        let silero = store.ensure_silero(&dl)?;
        let mut need_argos: Vec<(String, String)> = vec![];
        for (tr, a, b) in [(tr_out, &cfg.src, &cfg.tgt), (tr_in, &cfg.tgt, &cfg.src)] {
            if tr == "nllb" {
                store.ensure_nllb(&dl)?;
            } else if a != "en" && b != "en" {
                need_argos.push((a.clone(), "en".into()));
                need_argos.push(("en".into(), b.clone()));
            } else {
                need_argos.push((a.clone(), b.clone()));
            }
            if !cfg.bilateral {
                break;
            }
        }
        for (a, b) in &need_argos {
            store.ensure_argos_pair(a, b, &dl)?;
        }
        // voz escolhida pelo usuário (Piper) ou a mais clara medida para o idioma
        let voice_dir = |chosen: &Option<String>, lang: &str| -> Result<PathBuf> {
            match chosen {
                Some(id) => store.ensure_voice(id, &dl),
                None => store.ensure_voice_for(lang, gpu, &dl),
            }
        };
        let voice_out_dir = voice_dir(&cfg.voice_out, &cfg.tgt)
            .map_err(|e| anyhow!("não há voz para o idioma de destino ({}): {e:#}", cfg.tgt))?;
        // no modo legenda a outra pessoa não ganha voz traduzida: nem baixa nem carrega a voz
        let voice_in_dir = if cfg.bilateral && cfg.peer_voice {
            Some(voice_dir(&cfg.voice_in, &cfg.src)
                .map_err(|e| anyhow!("não há voz para o seu idioma ({}): o modo bilateral precisa dela. {e:#}", cfg.src))?)
        } else {
            None
        };

        progress(55, "Carregando o reconhecimento de fala…");
        let threads = 0;
        let asr = Arc::new(Asr::load(&asr_dir, gpu, threads)?);
        // no bilateral a outra pessoa pode precisar de outro modelo (o Parakeet v2 só reconhece inglês)
        let asr_in = match &asr_in_dir {
            Some(d) => Arc::new(Asr::load(d, gpu, threads)?),
            None => asr.clone(),
        };
        progress(75, "Carregando a tradução…");
        // um único NLLB para os dois lados (o mesmo modelo traduz nos dois sentidos): duas cópias
        // estouravam os 6 GB da placa de vídeo no bilateral (medido no lab2, RTX 3050)
        let nllb: std::cell::OnceCell<Arc<mt::Nllb>> = std::cell::OnceCell::new();
        let make_tr = |kind: &str, a: &str, b: &str| -> Result<Arc<dyn Translate>> {
            Ok(if kind == "nllb" {
                if nllb.get().is_none() {
                    let _ = nllb.set(Arc::new(mt::Nllb::load(&store.nllb_dir(), gpu)?));
                }
                nllb.get().unwrap().clone() as Arc<dyn Translate>
            } else {
                let dir = store.argos_dir();
                let route = if a != "en" && b != "en" {
                    vec![mt::ArgosPair::load(&mt::argos_package(&dir, a, "en")?, gpu)?,
                         mt::ArgosPair::load(&mt::argos_package(&dir, "en", b)?, gpu)?]
                } else {
                    vec![mt::ArgosPair::load(&mt::argos_package(&dir, a, b)?, gpu)?]
                };
                Arc::new(ArgosRoute(route))
            })
        };
        progress(85, "Carregando a voz…");
        // o Kokoro precisa de mais núcleos (só é usado no processador para o chinês)
        let voice_threads = |dir: &Path| if dir.join("voices.bin").exists() && !gpu { 4 } else { 2 };
        // a voz da MINHA tradução é do mesmo tipo da minha voz (grave: masculina), medida na gravação
        let masculina = cfg.minha_voz.as_ref()
            .and_then(|p| crate::audio::read_wav_16k_mono(p.as_ref()).ok())
            .and_then(|x| crate::audio::tom_medio(&x, 16_000))
            .map(|tom| tom < 165.0)
            .unwrap_or(false);
        let voice_out = Arc::new(Voice::load_voz(&voice_out_dir, &cfg.tgt, voice_threads(&voice_out_dir), gpu, masculina)?);
        let shared = Shared::new();
        let stop_capture = Arc::new(AtomicBool::new(false));
        let (ptx, prx) = std::sync::mpsc::channel::<pipeline::Event>();
        let mut handles = vec![];
        let seg = SegmenterConfig { max_seg_s, ..Default::default() };
        let silero = silero.to_string_lossy().to_string();

        // ida: meu microfone → tradução → microfone virtual (+ minha saída, se pedi para ouvir)
        let mut outs = vec![OutputDevice::open(vm.target.clone())?];
        if cfg.monitor {
            outs.push(OutputDevice::open(cfg.output.clone())?);
        }
        let (mtx, mrx) = std::sync::mpsc::channel();
        handles.push(devices::spawn_capture(cfg.mic.clone(), mtx, stop_capture.clone())?);
        let out_dir = Direction { name: "out".into(), src: cfg.src.clone(), tgt: cfg.tgt.clone(),
            to_speaker: cfg.monitor,
            // o meu microfone fica surdo enquanto algo toca na caixa de som (sem fone)
            echo_gate: !cfg.headphones && (cfg.monitor || cfg.bilateral),
            leaks: cfg.monitor && !cfg.headphones, simultaneous: cfg.simultaneous };
        handles.extend(pipeline::spawn_direction(mrx, asr.clone(), make_tr(tr_out, &cfg.src, &cfg.tgt)?, Some(voice_out),
            Arc::new(Speakers(outs, stop_capture.clone())), out_dir, seg, silero.clone(), shared.clone(), ptx.clone())?);

        // volta (bilateral): a outra pessoa → tradução → minha saída
        if cfg.bilateral {
            let voice_in = match &voice_in_dir {
                Some(dir) => Some(Arc::new(Voice::load_on(dir, &cfg.src, voice_threads(dir), gpu)?)),
                None => None,
            };
            let (itx, irx) = std::sync::mpsc::channel();
            let (ctx, crx) = std::sync::mpsc::channel::<Vec<f32>>();
            handles.push(devices::spawn_peer_capture(&vm, ctx, stop_capture.clone())?);
            let my_output = OutputDevice::open(cfg.output.clone())?;
            // a voz original da outra pessoa, baixinho por baixo da tradução (se pedida). Sem
            // fone ela também sai na caixa de som: o meu microfone fica surdo enquanto ela soa.
            {
                // só legenda: a voz original inteira. No Windows o próprio app de chamada continua
                // tocando a voz original (a gravação não a desvia): o Praxis não a repete.
                let gain = if cfg!(windows) { 0.0 } else if cfg.peer_voice { cfg.original_volume.clamp(0.0, 1.0) } else { 1.0 };
                // Windows, tradução falada: o app fica no volume da voz original (mínimo 5%; a
                // gravação do app sai depois do volume dele, então não dá para emudecer) e o
                // Praxis compensa esse volume no que grava.
                let app_vol = if cfg!(windows) && vm.peer_app.is_some() && cfg.peer_voice { cfg.original_volume.clamp(0.05, 1.0) } else { 1.0 };
                #[cfg(windows)]
                if let (Some(app), true) = (vm.peer_app.clone(), app_vol < 1.0) {
                    handles.push(crate::app_audio::spawn_volume_keeper(app, app_vol, stop_capture.clone()));
                }
                // o que a pessoa ouve da voz original (para a trava de eco sem fone)
                let ouvida = if cfg!(windows) && vm.peer_app.is_some() { app_vol } else { gain };
                let (out, leaks, shared) = (my_output.clone(), !cfg.headphones, shared.clone());
                handles.push(std::thread::spawn(move || {
                    while let Ok(mut chunk) = crx.recv() {
                        if app_vol < 1.0 {
                            chunk.iter_mut().for_each(|x| *x = (*x / app_vol).clamp(-1.0, 1.0));
                        }
                        if gain > 0.0 {
                            out.feed_bed(&chunk, gain);
                        }
                        if ouvida > 0.0 {
                            let rms = (chunk.iter().map(|x| x * x).sum::<f32>() / chunk.len().max(1) as f32).sqrt();
                            if leaks && rms * ouvida > 0.002 {
                                let until = ((shared.now_s() + 0.3) * 1000.0) as u64;
                                shared.speaker_busy_until_ms.fetch_max(until, std::sync::atomic::Ordering::Relaxed);
                            }
                        }
                        if itx.send(chunk).is_err() {
                            break;
                        }
                    }
                }));
            }
            let in_dir = Direction { name: "in".into(), src: cfg.tgt.clone(), tgt: cfg.src.clone(),
                to_speaker: cfg.peer_voice, echo_gate: false, leaks: cfg.peer_voice && !cfg.headphones, simultaneous: cfg.simultaneous };
            let seg_in = SegmenterConfig { max_seg_s: max_segment_s(&model_in, gpu), ..Default::default() };
            handles.extend(pipeline::spawn_direction(irx, asr_in, make_tr(tr_in, &cfg.tgt, &cfg.src)?, voice_in,
                Arc::new(Speakers(vec![my_output], stop_capture.clone())), in_dir, seg_in, silero, shared.clone(), ptx.clone())?);
        }
        drop(ptx);
        // repassa os eventos do motor
        {
            let events = events.clone();
            handles.push(std::thread::spawn(move || {
                while let Ok(e) = prx.recv() {
                    if events.send(SessionEvent::Engine { ev: e }).is_err() {
                        break;
                    }
                }
            }));
        }
        progress(100, "Traduzindo");
        emit(SessionEvent::Ready);
        Ok(Self { shared, stop_capture, handles, vm: Some(vm) })
    }

    pub fn stop(mut self) {
        self.shared.stop.store(true, Ordering::Relaxed);
        self.stop_capture.store(true, Ordering::Relaxed);
        for h in self.handles.drain(..) {
            let _ = h.join();
        }
        if let Some(mut vm) = self.vm.take() {
            vm.teardown(); // remove os dispositivos virtuais (Linux)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn limite_de_qualidade_como_no_python() {
        assert!(language_allowed("es", true).0);
        assert!(language_allowed("en", true).0);
        let (ok, why) = language_allowed("fr", true);
        assert!(!ok && why.contains("mesmo com placa de vídeo"));
        let (ok, why) = language_allowed("ko", false);
        assert!(!ok && why.contains("sem placa de vídeo") && !why.contains("Com uma placa de vídeo"));
        assert!(language_allowed("xx", false).0, "idioma sem medição não é bloqueado");
        // com o Parakeet, cinco idiomas passam no processador
        for l in ["en", "es", "it", "de", "pt"] {
            assert!(language_allowed(l, false).0, "{l}");
        }
    }

    #[test]
    fn modelo_de_fala_por_idioma_e_hardware() {
        assert_eq!(asr_model_for("pt", true, "auto"), "large-v3-turbo");
        assert_eq!(asr_model_for("uk", true, "auto"), "large-v3");
        assert_eq!(asr_model_for("en", true, "auto"), "parakeet-tdt-0.6b-v2-int8");
        assert_eq!(asr_model_for("en", false, "auto"), "parakeet-tdt-0.6b-v2-int8");
        assert_eq!(asr_model_for("es", false, "auto"), "parakeet-ultra-int8");
        assert_eq!(asr_model_for("ru", false, "auto"), "parakeet-tdt-0.6b-v3-int8");
        assert_eq!(asr_model_for("ja", false, "auto"), "parakeet-tdt_ctc-0.6b-ja-35000-int8");
        assert_eq!(asr_model_for("ko", false, "auto"), "small");
        assert_eq!(asr_model_for("ja", false, "medium"), "medium");
        assert_eq!(max_segment_s("parakeet-tdt-0.6b-v3-int8", false), 15.0);
        assert_eq!(max_segment_s("small", false), 6.0);
        assert_eq!(max_segment_s("small", true), 15.0);
    }

    #[test]
    fn tradutor_automatico_como_no_python() {
        assert_eq!(translator_for("pt", "en", true, "auto"), "nllb");
        assert_eq!(translator_for("pt", "en", false, "auto"), "argos");
        assert_eq!(translator_for("pt", "ar", false, "auto"), "nllb");
        // pares que o motor em Rust ainda não lê no Argos vão pelo NLLB
        assert_eq!(translator_for("es", "en", false, "auto"), "nllb");
        assert_eq!(translator_for("es", "pt", false, "auto"), "nllb");
        assert_eq!(translator_for("es", "en", false, "argos"), "nllb");
    }
}
