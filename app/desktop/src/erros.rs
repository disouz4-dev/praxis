//! Monitor de erros: guarda os erros e travamentos no próprio computador (nada sai sozinho).
//! O usuário vê o relatório inteiro e, se quiser, abre um relato pronto nos Issues do GitHub.
//! O relatório nunca leva áudio nem o texto das conversas.

use std::io::Write;
use std::path::PathBuf;

use serde_json::{json, Value};

const REPO: &str = "disouz4-dev/praxis";
/// o arquivo passa disso: fica só a metade mais nova
const MAX_BYTES: u64 = 256 * 1024;

pub fn path() -> PathBuf {
    dirs::data_dir().unwrap_or_else(std::env::temp_dir).join("Praxis").join("erros.log")
}

/// "2026-10-22 13:10" (UTC), sem depender de biblioteca de datas.
fn agora() -> String {
    let s = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0) as i64;
    let (dias, resto) = (s.div_euclid(86_400), s.rem_euclid(86_400));
    // dias desde 1970 → data civil (algoritmo de Howard Hinnant)
    let z = dias + 719_468;
    let era = z.div_euclid(146_097);
    let doe = z - era * 146_097;
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = doy - (153 * mp + 2) / 5 + 1;
    let m = if mp < 10 { mp + 3 } else { mp - 9 };
    let y = yoe + era * 400 + i64::from(m <= 2);
    format!("{y:04}-{m:02}-{d:02} {:02}:{:02} UTC", resto / 3600, resto % 3600 / 60)
}

/// Tira do texto o nome da pasta do usuário (que costuma ser o nome da pessoa).
fn limpar(msg: &str) -> String {
    let mut s = msg.to_string();
    if let Some(home) = dirs::home_dir() {
        let h = home.to_string_lossy().to_string();
        if h.len() > 3 {
            s = s.replace(&h, "~");
        }
    }
    s
}

/// Guarda um erro ("erro") ou travamento ("travamento").
pub fn registrar(tipo: &str, msg: &str) {
    let p = path();
    let _ = std::fs::create_dir_all(p.parent().unwrap());
    if std::fs::metadata(&p).map(|m| m.len() > MAX_BYTES).unwrap_or(false) {
        if let Ok(txt) = std::fs::read_to_string(&p) {
            let linhas: Vec<&str> = txt.lines().collect();
            let _ = std::fs::write(&p, linhas[linhas.len() / 2..].join("\n") + "\n");
        }
    }
    let linha = json!({"quando": agora(), "versao": env!("CARGO_PKG_VERSION"), "tipo": tipo, "msg": limpar(msg)});
    if let Ok(mut f) = std::fs::OpenOptions::new().create(true).append(true).open(&p) {
        let _ = writeln!(f, "{linha}");
    }
}

/// Erros vindos do motor (o mesmo evento que vai para a janela).
pub fn registrar_evento(e: &Value) {
    match e["e"].as_str() {
        Some("error") => registrar("erro", e["msg"].as_str().unwrap_or("")),
        Some("engine") if e["ev"]["e"] == "error" => registrar("erro", e["ev"]["msg"].as_str().unwrap_or("")),
        _ => {}
    }
}

/// Travamentos (pânico em qualquer tarefa) também vão para o arquivo.
pub fn instalar_gancho() {
    let padrao = std::panic::take_hook();
    std::panic::set_hook(Box::new(move |info| {
        let onde = info.location().map(|l| format!(" ({}:{})", l.file(), l.line())).unwrap_or_default();
        let msg = info.payload().downcast_ref::<&str>().map(|s| s.to_string())
            .or_else(|| info.payload().downcast_ref::<String>().cloned())
            .unwrap_or_else(|| "travamento".into());
        registrar("travamento", &format!("{msg}{onde}"));
        padrao(info);
    }));
}

/// O relatório em texto (Markdown), exatamente o que vai para o GitHub.
pub fn relatorio(config: &Value, gpu: bool) -> String {
    let sim = |b: bool| if b { "sim" } else { "não" };
    let c = |k: &str| config[k].as_str().unwrap_or("?").to_string();
    let b = |k: &str| config[k].as_bool().unwrap_or(false);
    let mut modo = format!("{} → {}", c("src"), c("tgt"));
    if b("bilateral") {
        modo += if config["peer_voice"] == false { " · bilateral só legenda" } else { " · bilateral com voz" };
        modo += if config["peer_app"].is_string() { " · app escolhido na lista" } else { " · saída do app no Praxis Speaker" };
    }
    modo += &format!(" · fone: {} · ouvir a tradução: {}", sim(b("headphones")), sim(b("monitor")));
    let erros: Vec<String> = std::fs::read_to_string(path()).unwrap_or_default().lines().rev().take(20)
        .filter_map(|l| serde_json::from_str::<Value>(l).ok())
        .map(|v| format!("- {} · {} · {} · `{}`", v["quando"].as_str().unwrap_or(""), v["versao"].as_str().unwrap_or(""),
                         v["tipo"].as_str().unwrap_or(""), v["msg"].as_str().unwrap_or("").replace('`', "'")))
        .collect();
    format!(
        "**Versão:** {} · **Sistema:** {} {} · **Placa de vídeo NVIDIA:** {}\n**Modo:** {}\n\n### Últimos erros (do mais novo para o mais antigo)\n{}\n",
        env!("CARGO_PKG_VERSION"), std::env::consts::OS, std::env::consts::ARCH, sim(gpu), modo,
        if erros.is_empty() { "(nenhum erro registrado)".into() } else { erros.join("\n") })
}

fn codificar(s: &str) -> String {
    s.bytes().map(|c| match c {
        b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9' | b'-' | b'_' | b'.' | b'~' => (c as char).to_string(),
        _ => format!("%{c:02X}"),
    }).collect()
}

/// Abre no navegador um relato pronto nos Issues do GitHub (o usuário confere e envia lá).
pub fn abrir_relato(corpo: &str) -> Result<(), String> {
    let mut corpo = corpo.to_string();
    // endereços muito longos são recusados pelo navegador: corta o fim (os erros mais antigos)
    while codificar(&corpo).len() > 6000 {
        let corte = corpo.char_indices().rev().nth(200).map(|(i, _)| i).unwrap_or(0);
        corpo.truncate(corte);
    }
    let url = format!("https://github.com/{REPO}/issues/new?labels={}&title={}&body={}",
        codificar("relatório do app"), codificar(&format!("[{}] Problema no Praxis {}", std::env::consts::OS, env!("CARGO_PKG_VERSION"))),
        codificar(&corpo));
    abrir_navegador(&url)
}

/// Abre um endereço no navegador padrão do sistema.
pub fn abrir_navegador(url: &str) -> Result<(), String> {
    let r = if cfg!(windows) {
        std::process::Command::new("rundll32").args(["url.dll,FileProtocolHandler", url]).spawn()
    } else if cfg!(target_os = "macos") {
        std::process::Command::new("open").arg(url).spawn()
    } else {
        std::process::Command::new("xdg-open").arg(url).spawn()
    };
    r.map(|_| ()).map_err(|e| format!("não foi possível abrir o navegador: {e}"))
}

#[cfg(test)]
mod tests {
    #[test]
    fn data_e_codificacao() {
        assert_eq!(super::agora().len(), "2026-10-22 13:10 UTC".len());
        assert_eq!(super::codificar("a b/ç"), "a%20b%2F%C3%A7");
    }
}
