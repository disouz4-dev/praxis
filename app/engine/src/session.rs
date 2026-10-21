//! Sessão do Praxis: escolhe modelo e tradutor pelo computador (as regras medidas do
//! Praxis em Python), aplica o limite de qualidade por idioma, baixa o que faltar e liga o
//! motor. A janela (Tauri) e a linha de comando usam a mesma sessão.

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::mpsc::Sender;
use std::sync::Arc;
use std::thread::JoinHandle;

use anyhow::{anyhow, bail, Result};
use serde::{Deserialize, Serialize};

use crate::asr::WhisperAsr;
use crate::devices::{self, OutputDevice, Speakers, VirtualMic};
use crate::models::{self, ModelStore};
use crate::mt;
use crate::pipeline::{self, ArgosRoute, Direction, Shared, Translate};
use crate::tts::PiperVoice;
use crate::vad::SegmenterConfig;

/// Meta do produto: 1% de erro; teto de 3%. Idioma acima disso neste hardware não é oferecido.
pub const QUALITY_LIMIT: f32 = 0.03;

/// Erro REAL da transcrição no modo ao vivo, medido com 40 frases de vários falantes por
/// idioma (Google FLEURS) e auditado (inglês com 100 frases) — mesma tabela do Python.
pub const MEASURED_ERROR_GPU: &[(&str, f32)] = &[
    ("pt", 0.024), ("en", 0.028), ("es", 0.017), ("fr", 0.057), ("de", 0.019), ("it", 0.024),
    ("ru", 0.038), ("zh", 0.113), ("nl", 0.054), ("pl", 0.055), ("uk", 0.047), ("tr", 0.058),
    ("ar", 0.092), ("hi", 0.304), ("ja", 0.055), ("ko", 0.151),
];
pub const MEASURED_ERROR_CPU: &[(&str, f32)] = &[
    ("pt", 0.078), ("en", 0.075), ("es", 0.060), ("fr", 0.159), ("de", 0.091), ("it", 0.086),
    ("ru", 0.106), ("zh", 0.173), ("nl", 0.227), ("pl", 0.192), ("uk", 0.211), ("tr", 0.166),
    ("ar", 0.293), ("hi", 0.745), ("ja", 0.168), ("ko", 0.252),
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
    /// estou de fone: sem trava de eco
    #[serde(default)]
    pub headphones: bool,
    /// vozes (pacotes sherpa-onnx); vazio = a padrão de cada idioma
    #[serde(default)]
    pub voice_out: Option<String>,
    #[serde(default)]
    pub voice_in: Option<String>,
    /// ignora o limite de qualidade (só para testes)
    #[serde(default)]
    pub allow_weak_language: bool,
}

fn auto() -> String {
    "auto".into()
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
        let model = if cfg.model == "auto" { if gpu { "large-v3-turbo" } else { "small" } } else { cfg.model.as_str() }.to_string();
        // com placa de vídeo o trecho vai até 15 s (o corte no meio da fala era a maior fonte
        // de erro); no processador, 6 s (trecho longo atrasa demais)
        let max_seg_s = if gpu { 15.0 } else { 6.0 };
        let tr_out = translator_for(&cfg.src, &cfg.tgt, gpu, &cfg.translator);
        let tr_in = translator_for(&cfg.tgt, &cfg.src, gpu, &cfg.translator);
        emit(SessionEvent::Hardware { gpu, model: model.clone(), translator: tr_out.into(), max_seg_s });

        progress(5, "Preparando os modelos…");
        let whisper_dir = store.ensure_whisper(&model, &dl)?;
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
        let voice_out_id = cfg.voice_out.clone().or_else(|| models::default_voice(&cfg.tgt).map(String::from))
            .ok_or_else(|| anyhow!("não há voz para o idioma de destino ({})", cfg.tgt))?;
        let voice_out_dir = store.ensure_voice(&voice_out_id, &dl)?;
        let voice_in_dir = if cfg.bilateral {
            let id = cfg.voice_in.clone().or_else(|| models::default_voice(&cfg.src).map(String::from))
                .ok_or_else(|| anyhow!("não há voz para o seu idioma ({}): o modo bilateral precisa dela", cfg.src))?;
            Some(store.ensure_voice(&id, &dl)?)
        } else {
            None
        };

        progress(40, "Preparando o microfone virtual…");
        let vm = VirtualMic::setup(cfg.bilateral)?;
        emit(SessionEvent::VirtualMic { mic: vm.mic_label.clone(), peer: vm.peer_label.clone() });

        progress(55, "Carregando o reconhecimento de fala…");
        let threads = 0;
        let asr = Arc::new(WhisperAsr::load(&whisper_dir, gpu, threads)?);
        progress(75, "Carregando a tradução…");
        let make_tr = |kind: &str, a: &str, b: &str| -> Result<Arc<dyn Translate>> {
            Ok(if kind == "nllb" {
                Arc::new(mt::Nllb::load(&store.nllb_dir(), gpu)?)
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
        let voice_out = Arc::new(PiperVoice::load(&voice_out_dir, 2)?);
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
            to_speaker: cfg.monitor, echo_gate: cfg.monitor && !cfg.headphones };
        handles.extend(pipeline::spawn_direction(mrx, asr.clone(), make_tr(tr_out, &cfg.src, &cfg.tgt)?, voice_out,
            Arc::new(Speakers(outs)), out_dir, seg, silero.clone(), shared.clone(), ptx.clone())?);

        // volta (bilateral): a outra pessoa → tradução → minha saída
        if let Some(dir) = voice_in_dir {
            let voice_in = Arc::new(PiperVoice::load(&dir, 2)?);
            let (itx, irx) = std::sync::mpsc::channel();
            handles.push(devices::spawn_capture(vm.peer_capture.clone(), itx, stop_capture.clone())?);
            let in_dir = Direction { name: "in".into(), src: cfg.tgt.clone(), tgt: cfg.src.clone(),
                to_speaker: true, echo_gate: !cfg.headphones };
            handles.extend(pipeline::spawn_direction(irx, asr.clone(), make_tr(tr_in, &cfg.tgt, &cfg.src)?, voice_in,
                Arc::new(Speakers(vec![OutputDevice::open(cfg.output.clone())?])), in_dir, seg, silero, shared.clone(), ptx.clone())?);
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
        let (ok, why) = language_allowed("pt", false);
        assert!(!ok && why.contains("sem placa de vídeo") && why.contains("Com uma placa de vídeo"));
        assert!(language_allowed("xx", false).0, "idioma sem medição não é bloqueado");
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
