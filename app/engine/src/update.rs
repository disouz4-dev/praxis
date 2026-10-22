//! Atualização: pergunta à página de versões do GitHub qual é a última versão publicada.
//! No Linux (.deb) quem troca o programa é o apt (repositório do Praxis registrado pelo
//! pacote); o aplicativo só avisa e, com um clique, pede a senha e chama o apt.
//! No Windows o aplicativo baixa o instalador da versão nova e o roda sem perguntas.

use anyhow::{anyhow, Result};

pub const REPO: &str = "disouz4-dev/praxis";

/// Última versão publicada (ex.: "0.3.1"), sem o "v" da etiqueta.
pub fn latest_version() -> Result<String> {
    let url = format!("https://api.github.com/repos/{REPO}/releases/latest");
    let agent: ureq::Agent = ureq::Agent::config_builder()
        .timeout_global(Some(std::time::Duration::from_secs(10)))
        .build()
        .into();
    let body = agent.get(&url).header("User-Agent", "praxis").call()?.body_mut().read_to_string()?;
    let v: serde_json::Value = serde_json::from_str(&body)?;
    let tag = v["tag_name"].as_str().ok_or_else(|| anyhow!("resposta sem versão"))?;
    Ok(tag.trim_start_matches('v').to_string())
}

/// Baixa o instalador do Windows da versão `version` para a pasta temporária.
pub fn download_windows_setup(version: &str) -> Result<std::path::PathBuf> {
    let name = format!("Praxis_{version}_x64-setup.exe");
    let url = format!("https://github.com/{REPO}/releases/download/v{version}/{name}");
    let agent: ureq::Agent = ureq::Agent::config_builder()
        .timeout_global(Some(std::time::Duration::from_secs(600)))
        .build()
        .into();
    let mut resp = agent.get(&url).header("User-Agent", "praxis").call()?;
    let bytes = resp.body_mut().with_config().limit(500 * 1024 * 1024).read_to_vec()?;
    if bytes.len() < 1024 * 1024 || &bytes[..2] != b"MZ" {
        return Err(anyhow!("o instalador baixado não é um programa do Windows"));
    }
    let dest = std::env::temp_dir().join(name);
    std::fs::write(&dest, bytes)?;
    Ok(dest)
}

/// `latest` é mais nova que `current`? Compara número a número ("0.10.0" > "0.9.3").
pub fn is_newer(latest: &str, current: &str) -> bool {
    let parse = |s: &str| -> Vec<u64> { s.split(['.', '-']).map(|p| p.parse().unwrap_or(0)).collect() };
    parse(latest) > parse(current)
}

#[cfg(test)]
mod tests {
    use super::is_newer;

    #[test]
    fn compara_versoes_numero_a_numero() {
        assert!(is_newer("0.3.1", "0.3.0"));
        assert!(is_newer("0.10.0", "0.9.3"));
        assert!(!is_newer("0.3.0", "0.3.0"));
        assert!(!is_newer("0.2.9", "0.3.0"));
    }
}
