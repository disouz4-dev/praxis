//! Monitor de uso na tela: processador (o computador todo e só o Praxis), memória do Praxis e
//! placas de vídeo. Placa: no Mac pelo ioreg (AMD e Intel), no Linux pelo nvidia-smi (NVIDIA) e
//! pelo /sys (AMD), no Windows pelo contador "GPU Engine" (typeperf).

use std::sync::Mutex;

use serde_json::{json, Value};
use sysinfo::{Pid, ProcessRefreshKind, ProcessesToUpdate, System};

pub struct Uso {
    sys: Mutex<System>,
}

impl Default for Uso {
    fn default() -> Self {
        Self { sys: Mutex::new(System::new()) }
    }
}

impl Uso {
    pub fn ler(&self) -> Value {
        let mut s = self.sys.lock().unwrap();
        s.refresh_cpu_usage();
        let pid = Pid::from_u32(std::process::id());
        s.refresh_processes_specifics(ProcessesToUpdate::Some(&[pid]), true, ProcessRefreshKind::nothing().with_cpu().with_memory());
        let nucleos = s.cpus().len().max(1) as f32;
        let (cpu_praxis, mem_mb) = s.process(pid).map(|p| (p.cpu_usage() / nucleos, p.memory() / 1_048_576)).unwrap_or((0.0, 0));
        json!({"cpu": s.global_cpu_usage().round(), "cpu_praxis": cpu_praxis.round(), "memoria_praxis_mb": mem_mb, "placas": placas()})
    }
}

/// [{nome, uso}] de cada placa de vídeo que o sistema informa
fn placas() -> Vec<Value> {
    let rodar = |cmd: &str, args: &[&str]| -> String {
        let mut c = std::process::Command::new(cmd);
        c.args(args);
        #[cfg(windows)]
        {
            use std::os::windows::process::CommandExt;
            c.creation_flags(0x0800_0000); // sem janela de console
        }
        c.output().ok().map(|o| String::from_utf8_lossy(&o.stdout).to_string()).unwrap_or_default()
    };
    let mut out = vec![];
    if cfg!(target_os = "macos") {
        // cada bloco "+-o <Classe>" traz "Device Utilization %"=N (o maior vale)
        let mut nome = String::new();
        let mut uso: Option<u32> = None;
        let fechar = |nome: &str, uso: Option<u32>, out: &mut Vec<Value>| {
            if let (false, Some(u)) = (nome.is_empty(), uso) {
                let n = if nome.contains("AMD") { "AMD Radeon" } else if nome.contains("Intel") { "Intel" } else if nome.contains("AGX") { "Apple" } else { nome };
                if !out.iter().any(|v| v["nome"] == n) { out.push(json!({"nome": n, "uso": u})); }
                else if let Some(v) = out.iter_mut().find(|v| v["nome"] == n) { v["uso"] = json!(v["uso"].as_u64().unwrap_or(0).max(u as u64)); }
            }
        };
        for l in rodar("ioreg", &["-r", "-d", "1", "-w", "0", "-c", "IOAccelerator"]).lines() {
            if let Some(r) = l.strip_prefix("+-o ") {
                fechar(&nome, uso, &mut out);
                nome = r.split_whitespace().next().unwrap_or("").to_string();
                uso = None;
            }
            for parte in l.split("\"Device Utilization %\"=").skip(1) {
                let n: u32 = parte.chars().take_while(|c| c.is_ascii_digit()).collect::<String>().parse().unwrap_or(0);
                uso = Some(uso.unwrap_or(0).max(n));
            }
        }
        fechar(&nome, uso, &mut out);
    } else if cfg!(target_os = "linux") {
        for l in rodar("nvidia-smi", &["--query-gpu=name,utilization.gpu", "--format=csv,noheader,nounits"]).lines() {
            if let Some((n, u)) = l.rsplit_once(',') {
                out.push(json!({"nome": n.trim(), "uso": u.trim().parse::<u32>().unwrap_or(0)}));
            }
        }
        if let Ok(rd) = std::fs::read_dir("/sys/class/drm") {
            for e in rd.flatten() {
                if let Ok(u) = std::fs::read_to_string(e.path().join("device/gpu_busy_percent")) {
                    out.push(json!({"nome": "AMD", "uso": u.trim().parse::<u32>().unwrap_or(0)}));
                }
            }
        }
    } else if cfg!(windows) {
        // soma do uso dos motores 3D/Compute, como o Gerenciador de Tarefas
        let t = rodar("typeperf", &["\\GPU Engine(*engtype_3D)\\Utilization Percentage", "\\GPU Engine(*engtype_Compute*)\\Utilization Percentage", "-sc", "1"]);
        if let Some(l) = t.lines().find(|l| l.starts_with("\"") && l.chars().nth(1).is_some_and(|c| c.is_ascii_digit())) {
            let soma: f32 = l.split(',').skip(1).filter_map(|v| v.trim_matches('"').parse::<f32>().ok()).sum();
            out.push(json!({"nome": "Placa de vídeo", "uso": soma.min(100.0).round()}));
        }
    }
    out
}
