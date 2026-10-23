//! Identificação do hardware da máquina e uso dele, perguntando ao próprio sistema (nada fica
//! escrito no Praxis): processador (nome e núcleos), placas de vídeo (nome e memória), memória
//! (total, tipo DDR, velocidade, fabricante) e o uso de cada um.
//!   Mac: sysinfo + system_profiler (placas e memória) + ioreg (uso das placas)
//!   Windows: sysinfo + Win32_VideoController / Win32_PhysicalMemory + contador "GPU Engine"
//!   Linux: sysinfo + nvidia-smi / lspci / /sys (AMD) + dmidecode quando o sistema deixa
//! Este arquivo só usa sysinfo, serde_json e a biblioteca padrão (o teste em
//! app/tools/hardware o inclui direto para rodar em qualquer máquina).

use std::sync::{Mutex, OnceLock};

use serde_json::{json, Value};
use sysinfo::{CpuRefreshKind, MemoryRefreshKind, RefreshKind, System};

fn rodar(cmd: &str, args: &[&str]) -> String {
    let mut c = std::process::Command::new(cmd);
    c.args(args);
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        c.creation_flags(0x0800_0000); // sem janela de console
    }
    c.output().ok().map(|o| String::from_utf8_lossy(&o.stdout).to_string()).unwrap_or_default()
}

fn powershell(cmd: &str) -> String {
    rodar("powershell", &["-NoProfile", "-NonInteractive", "-Command", cmd])
}

/// "Intel(R) Core(TM) i9-9980HK CPU @ 2.40GHz" → "Intel Core i9-9980HK"
pub fn nome_curto(n: &str) -> String {
    let n = n.replace("(R)", "").replace("(TM)", "").replace("(tm)", "");
    let n = n.split(" @ ").next().unwrap_or(&n).replace(" CPU", "").replace(" Processor", "");
    n.split_whitespace().collect::<Vec<_>>().join(" ")
}

/// Tipo de memória pelo código SMBIOS (Win32_PhysicalMemory.SMBIOSMemoryType)
pub fn tipo_smbios(c: u64) -> Option<&'static str> {
    Some(match c {
        20 => "DDR", 21 => "DDR2", 24 => "DDR3", 26 => "DDR4", 27 => "LPDDR", 28 => "LPDDR2",
        29 => "LPDDR3", 30 => "LPDDR4", 34 => "DDR5", 35 => "LPDDR5", _ => return None,
    })
}

/// O que a máquina tem (lido uma vez: não muda com o Praxis aberto)
pub fn identificar() -> &'static Value {
    static H: OnceLock<Value> = OnceLock::new();
    H.get_or_init(|| {
        let s = System::new_with_specifics(RefreshKind::nothing().with_cpu(CpuRefreshKind::nothing()).with_memory(MemoryRefreshKind::nothing().with_ram()));
        let cpu = json!({
            "nome": s.cpus().first().map(|c| nome_curto(c.brand())).filter(|n| !n.is_empty()).unwrap_or_else(|| "?".into()),
            "nucleos": s.cpus().len(),
            "nucleos_fisicos": System::physical_core_count(),
        });
        json!({"processador": cpu, "placas": placas(), "memoria": memoria(s.total_memory() / 1_048_576), "sistema": sistema()})
    })
}

fn sistema() -> String {
    System::long_os_version().unwrap_or_default()
}

/// [{nome, memoria_mb}]
fn placas() -> Vec<Value> {
    let mut v = vec![];
    if cfg!(target_os = "macos") {
        if let Ok(j) = serde_json::from_str::<Value>(&rodar("system_profiler", &["SPDisplaysDataType", "-json"])) {
            for g in j["SPDisplaysDataType"].as_array().into_iter().flatten() {
                let Some(n) = g["sppci_model"].as_str() else { continue };
                let mem = g["sppci_vram"].as_str().or(g["spdisplays_vram"].as_str()).and_then(mb_de_texto);
                v.push(json!({"nome": n, "memoria_mb": mem}));
            }
        }
    } else if cfg!(windows) {
        let s = powershell("Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM | ConvertTo-Json -Compress");
        for g in lista_json(&s) {
            let n = g["Name"].as_str().unwrap_or("").to_string();
            if n.is_empty() || n.contains("Basic Display") { continue; }
            // AdapterRAM é de 32 bits (para em 4 GB): só vale abaixo disso
            let mem = g["AdapterRAM"].as_u64().filter(|&b| b > 0 && b < 4_294_967_295).map(|b| b / 1_048_576);
            v.push(json!({"nome": n, "memoria_mb": mem}));
        }
    } else {
        for l in rodar("nvidia-smi", &["--query-gpu=name,memory.total", "--format=csv,noheader,nounits"]).lines() {
            if let Some((n, m)) = l.rsplit_once(',') {
                v.push(json!({"nome": n.trim(), "memoria_mb": m.trim().parse::<u64>().ok()}));
            }
        }
        for l in rodar("lspci", &[]).lines().filter(|l| l.contains("VGA") || l.contains("3D controller") || l.contains("Display controller")) {
            if l.contains("NVIDIA") && !v.is_empty() { continue; }
            let n = l.split(": ").nth(1).unwrap_or(l).trim().to_string();
            v.push(json!({"nome": n, "memoria_mb": Value::Null}));
        }
    }
    v
}

fn mb_de_texto(t: &str) -> Option<u64> {
    let n: f64 = t.split_whitespace().next()?.replace(',', ".").parse().ok()?;
    Some(if t.contains("GB") { (n * 1024.0) as u64 } else { n as u64 })
}

fn lista_json(s: &str) -> Vec<Value> {
    match serde_json::from_str::<Value>(s.trim()) {
        Ok(Value::Array(a)) => a,
        Ok(o @ Value::Object(_)) => vec![o],
        _ => vec![],
    }
}

/// {total_mb, tipo, velocidade_mhz, fabricante, modulos}
fn memoria(total_mb: u64) -> Value {
    let (mut tipo, mut vel, mut fab, mut modulos): (Option<String>, Option<u64>, Option<String>, usize) = (None, None, None, 0);
    if cfg!(target_os = "macos") {
        if let Ok(j) = serde_json::from_str::<Value>(&rodar("system_profiler", &["SPMemoryDataType", "-json"])) {
            for b in j["SPMemoryDataType"].as_array().into_iter().flatten() {
                // Macs com chip Apple: um bloco só, sem módulos ("dimm_type" direto)
                if let Some(t) = b["dimm_type"].as_str() { tipo = Some(t.into()); }
                if let Some(f) = b["dimm_manufacturer"].as_str() { fab = Some(f.into()); }
                for m in b["_items"].as_array().into_iter().flatten() {
                    modulos += 1;
                    tipo = tipo.or(m["dimm_type"].as_str().map(String::from));
                    fab = fab.or(m["dimm_manufacturer"].as_str().map(String::from));
                    vel = vel.or(m["dimm_speed"].as_str().and_then(|s| s.split_whitespace().next()?.parse().ok()));
                }
            }
        }
    } else if cfg!(windows) {
        let s = powershell("Get-CimInstance Win32_PhysicalMemory | Select-Object Manufacturer,Speed,SMBIOSMemoryType | ConvertTo-Json -Compress");
        for m in lista_json(&s) {
            modulos += 1;
            tipo = tipo.or(m["SMBIOSMemoryType"].as_u64().and_then(tipo_smbios).map(String::from));
            vel = vel.or(m["Speed"].as_u64().filter(|&v| v > 0));
            fab = fab.or(m["Manufacturer"].as_str().map(str::trim).filter(|f| !f.is_empty() && *f != "Unknown").map(String::from));
        }
    } else {
        // Linux: o udev expõe a tabela de memória (DMI) sem precisar de administrador
        // (MEMORY_DEVICE_<n>_TYPE / _SPEED_MTS / _MANUFACTURER / _SIZE)
        let udev = rodar("udevadm", &["info", "/sys/devices/virtual/dmi/id"]);
        let campo = |n: &str, k: &str| udev.lines().find_map(|l| l.strip_prefix(&format!("E: MEMORY_DEVICE_{n}_{k}=")).map(|v| v.trim().to_string()));
        for n in 0..64 {
            let n = n.to_string();
            if campo(&n, "SIZE").is_none() { continue; }
            modulos += 1;
            tipo = tipo.or(campo(&n, "TYPE").filter(|t| t != "Unknown"));
            vel = vel.or(campo(&n, "SPEED_MTS").and_then(|v| v.parse().ok()));
            fab = fab.or(campo(&n, "MANUFACTURER").filter(|f| f != "Unknown" && !f.is_empty()));
        }
        // sem udev: o dmidecode, que só responde com permissão de administrador
        let dmi = if modulos == 0 { rodar("dmidecode", &["-t", "memory"]) } else { String::new() };
        for bloco in dmi.split("Memory Device").skip(1) {
            let campo = |k: &str| bloco.lines().find_map(|l| l.trim().strip_prefix(k).map(|v| v.trim().to_string()));
            if campo("Size:").is_some_and(|s| s.contains("No Module")) { continue; }
            modulos += 1;
            tipo = tipo.or(campo("Type:").filter(|t| t != "Unknown"));
            vel = vel.or(campo("Speed:").and_then(|s| s.split_whitespace().next()?.parse().ok()));
            fab = fab.or(campo("Manufacturer:").filter(|f| f != "Unknown"));
        }
    }
    json!({"total_mb": total_mb, "tipo": tipo, "velocidade_mhz": vel, "fabricante": fab, "modulos": modulos})
}

/// Uso agora: processador (%), memória (MB usados) e cada placa (%, ou nulo = em repouso)
pub struct Monitor {
    sys: Mutex<System>,
}

impl Default for Monitor {
    fn default() -> Self {
        Self { sys: Mutex::new(System::new_with_specifics(RefreshKind::nothing().with_cpu(CpuRefreshKind::nothing().with_cpu_usage()).with_memory(MemoryRefreshKind::nothing().with_ram()))) }
    }
}

impl Monitor {
    pub fn ler(&self) -> Value {
        let mut s = self.sys.lock().unwrap();
        s.refresh_cpu_usage();
        s.refresh_memory_specifics(MemoryRefreshKind::nothing().with_ram());
        let usos = uso_das_placas();
        let placas: Vec<Value> = identificar()["placas"].as_array().cloned().unwrap_or_default().iter().map(|p| {
            let n = p["nome"].as_str().unwrap_or("");
            let u = usos.iter().find(|(pista, _)| !pista.is_empty() && n.contains(pista.as_str()))
                .or_else(|| if identificar()["placas"].as_array().is_some_and(|a| a.len() == 1) { usos.first() } else { None })
                .map(|(_, u)| *u);
            json!({"nome": n, "uso": u})
        }).collect();
        json!({"cpu": s.global_cpu_usage().round(), "memoria_usada_mb": s.used_memory() / 1_048_576,
               "memoria_total_mb": s.total_memory() / 1_048_576, "placas": placas})
    }
}

/// (pista do nome da placa, uso %)
fn uso_das_placas() -> Vec<(String, u32)> {
    let mut usos: Vec<(String, u32)> = vec![];
    if cfg!(target_os = "macos") {
        // cada bloco "+-o <Classe>" traz "Device Utilization %"=N enquanto a placa está ligada
        let mut classe = String::new();
        for l in rodar("ioreg", &["-r", "-d", "1", "-w", "0", "-c", "IOAccelerator"]).lines() {
            if let Some(r) = l.strip_prefix("+-o ") {
                classe = r.split_whitespace().next().unwrap_or("").to_string();
            }
            for parte in l.split("\"Device Utilization %\"=").skip(1) {
                let n: u32 = parte.chars().take_while(|c| c.is_ascii_digit()).collect::<String>().parse().unwrap_or(0);
                let pista = if classe.contains("AMD") { "AMD" } else if classe.contains("Intel") { "Intel" } else if classe.contains("AGX") { "Apple" } else { "" };
                match usos.iter_mut().find(|(p, _)| p == pista) {
                    Some(u) => u.1 = u.1.max(n),
                    None => usos.push((pista.into(), n)),
                }
            }
        }
    } else if cfg!(windows) {
        let t = rodar("typeperf", &["\\GPU Engine(*engtype_3D)\\Utilization Percentage", "\\GPU Engine(*engtype_Compute*)\\Utilization Percentage", "-sc", "1"]);
        if let Some(l) = t.lines().find(|l| l.starts_with('"') && l.chars().nth(1).is_some_and(|c| c.is_ascii_digit())) {
            let soma: f32 = l.split(',').skip(1).filter_map(|v| v.trim_matches('"').parse::<f32>().ok()).sum();
            usos.push((String::new(), soma.min(100.0).round() as u32));
        }
    } else {
        for l in rodar("nvidia-smi", &["--query-gpu=name,utilization.gpu", "--format=csv,noheader,nounits"]).lines() {
            if let Some((n, u)) = l.rsplit_once(',') { usos.push((n.trim().into(), u.trim().parse().unwrap_or(0))); }
        }
        if let Ok(rd) = std::fs::read_dir("/sys/class/drm") {
            for e in rd.flatten() {
                if let Ok(u) = std::fs::read_to_string(e.path().join("device/gpu_busy_percent")) {
                    usos.push(("AMD".into(), u.trim().parse().unwrap_or(0)));
                }
            }
        }
    }
    usos
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn nomes_e_tipos() {
        assert_eq!(nome_curto("Intel(R) Core(TM) i9-9980HK CPU @ 2.40GHz"), "Intel Core i9-9980HK");
        assert_eq!(nome_curto("AMD Ryzen 7 5800X 8-Core Processor"), "AMD Ryzen 7 5800X 8-Core");
        assert_eq!(tipo_smbios(26), Some("DDR4"));
        assert_eq!(tipo_smbios(0), None);
        assert_eq!(mb_de_texto("8 GB"), Some(8192));
    }
}
