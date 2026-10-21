//! Modelos do Praxis: onde ficam e como são baixados na primeira vez (cada um da sua
//! fonte oficial; o NLLB, da versão publicada do Praxis, com impressão digital conferida).
//! Um download interrompido nunca parece completo: tudo vai para ".part" e só é renomeado
//! no fim.

use std::io::{Read, Write};
use std::path::{Path, PathBuf};

use anyhow::{anyhow, bail, Context, Result};
use sha2::{Digest, Sha256};

/// Progresso: (o que está baixando, bytes recebidos, total de bytes; 0 se desconhecido)
pub type Progress<'a> = &'a dyn Fn(&str, u64, u64);

pub const SILERO_URL: &str = "https://github.com/SYSTRAN/faster-whisper/raw/master/faster_whisper/assets/silero_vad_v6.onnx";
pub const NLLB_URL: &str =
    "https://github.com/disouz4-dev/praxis/releases/download/modelos-nllb-v1/nllb-200-distilled-600M-ct2.zip";
pub const NLLB_SHA256: &str = "7b8208fbb38ca3eb565dc95efe4983b973912ab4298ce6fe887748ea4998a58d";
pub const ARGOS_INDEX: &str = "https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json";
const VOICES_URL: &str = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models";
const ASR_MODELS_URL: &str = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models";

/// (modelo, repositório no Hugging Face, arquivos) — os mesmos modelos do faster-whisper
pub const WHISPER_MODELS: &[(&str, &str, &[&str])] = &[
    ("small", "Systran/faster-whisper-small", &["config.json", "model.bin", "tokenizer.json", "vocabulary.txt"]),
    ("base", "Systran/faster-whisper-base", &["config.json", "model.bin", "tokenizer.json", "vocabulary.txt"]),
    ("large-v3-turbo", "mobiuslabsgmbh/faster-whisper-large-v3-turbo",
     &["config.json", "model.bin", "preprocessor_config.json", "tokenizer.json", "vocabulary.json"]),
    ("large-v3", "Systran/faster-whisper-large-v3",
     &["config.json", "model.bin", "preprocessor_config.json", "tokenizer.json", "vocabulary.json"]),
];

/// Parakeet publicado em arquivos soltos: (nome, endereço base, [(arquivo, impressão digital SHA-256)]).
/// parakeet-ultra: Moondream (CC BY 4.0), convertido para o sherpa-onnx por leogaudin.
pub const PARAKEET_FILES: &[(&str, &str, &[(&str, &str)])] = &[(
    "parakeet-ultra-int8",
    "https://huggingface.co/leogaudin/sherpa-onnx-nemo-parakeet-ultra-int8/resolve/main",
    &[
        ("encoder.int8.onnx", "8bd3b8dc07056def6dfd19910e9f90c9e1a4e7e20901f58bdfe2a570a8081a2a"),
        ("decoder.int8.onnx", "94373c6405c8149d1c9d1e9862514e0e3e88dab1c7de18fac9d5df9c6ba5efdd"),
        ("joiner.int8.onnx", "8a71aaccfdba3d451775507a889afd2257d2e754463fd81095a8c8f290f924c2"),
        ("tokens.txt", "d58544679ea4bc6ac563d1f545eb7d474bd6cfa467f0a6e2c1dc1c7d37e3c35d"),
    ],
)];

/// Voz padrão de cada idioma de saída (as mesmas do Praxis em Python, em formato sherpa-onnx;
/// a holandesa "mls" não existe nesse formato: ronnie, do mesmo nível)
pub const DEFAULT_VOICES: &[(&str, &str)] = &[
    ("pt", "pt_BR-faber-medium"), ("en", "en_US-lessac-medium"), ("es", "es_ES-sharvard-medium"),
    ("fr", "fr_FR-siwis-medium"), ("de", "de_DE-thorsten-high"), ("it", "it_IT-paola-medium"),
    ("ru", "ru_RU-dmitri-medium"), ("zh", "zh_CN-huayan-medium"), ("nl", "nl_NL-ronnie-medium"),
    ("pl", "pl_PL-gosia-medium"), ("uk", "uk_UA-lada-x_low"), ("tr", "tr_TR-dfki-medium"),
    ("ar", "ar_JO-kareem-medium"), ("hi", "hi_IN-rohan-medium"),
];

/// Pacotes de voz do sherpa-onnx que falam vários idiomas
pub const KOKORO_PKG: &str = "kokoro-multi-lang-v1_0"; // 384 MB, Apache 2.0
pub const SUPERTONIC_PKG: &str = "sherpa-onnx-supertonic-3-tts-int8-2026-05-11"; // 139 MB, OpenRAIL-M

#[derive(Debug, Clone, PartialEq)]
pub enum VoiceChoice {
    Kokoro,
    Supertonic,
    Piper(&'static str),
}

/// A voz mais clara medida para `lang` (benchmarks/vozes_inteligibilidade.py). O Kokoro só com
/// placa de vídeo (no processador leva ~1 s para a 1ª frase), menos no chinês, que o Supertonic
/// não fala. O Piper só para idioma que nenhum dos dois fale: hoje, nenhum.
pub fn voice_choice(lang: &str, gpu: bool) -> Option<VoiceChoice> {
    let kokoro = crate::tts::KOKORO_VOICES.iter().any(|(l, _, _)| *l == lang);
    if kokoro && (gpu || lang == "zh") {
        Some(VoiceChoice::Kokoro)
    } else if crate::tts::SUPERTONIC_LANGS.contains(&lang) {
        Some(VoiceChoice::Supertonic)
    } else if kokoro {
        Some(VoiceChoice::Kokoro)
    } else {
        default_voice(lang).map(VoiceChoice::Piper)
    }
}

pub fn default_voice(lang: &str) -> Option<&'static str> {
    DEFAULT_VOICES.iter().find(|(l, _)| *l == lang).map(|(_, v)| *v)
}

pub struct ModelStore {
    pub root: PathBuf,
}

impl ModelStore {
    /// Pasta de dados do sistema: macOS ~/Library/Application Support/Praxis/modelos,
    /// Linux ~/.local/share/Praxis/modelos, Windows %APPDATA%\Praxis\modelos.
    pub fn default_location() -> Result<Self> {
        let base = std::env::var_os("PRAXIS_MODELOS").map(PathBuf::from).or_else(|| {
            dirs::data_dir().map(|d| d.join("Praxis").join("modelos"))
        }).ok_or_else(|| anyhow!("pasta de dados do sistema não encontrada"))?;
        Ok(Self { root: base })
    }

    pub fn whisper_dir(&self, name: &str) -> PathBuf {
        self.root.join(format!("whisper-{name}"))
    }
    pub fn silero_path(&self) -> PathBuf {
        self.root.join("silero_vad_v6.onnx")
    }
    pub fn argos_dir(&self) -> PathBuf {
        self.root.join("argos")
    }
    pub fn nllb_dir(&self) -> PathBuf {
        self.root.join("nllb-200-distilled-600M-ct2")
    }
    pub fn voices_dir(&self) -> PathBuf {
        self.root.join("vozes")
    }
    pub fn voice_dir(&self, voice: &str) -> PathBuf {
        self.voices_dir().join(format!("vits-piper-{voice}"))
    }

    pub fn ensure_whisper(&self, name: &str, p: Progress) -> Result<PathBuf> {
        let (_, repo, files) = WHISPER_MODELS.iter().find(|(n, _, _)| *n == name)
            .ok_or_else(|| anyhow!("modelo Whisper desconhecido: {name}"))?;
        let dir = self.whisper_dir(name);
        std::fs::create_dir_all(&dir)?;
        for f in *files {
            let dest = dir.join(f);
            if !dest.exists() {
                download(&format!("https://huggingface.co/{repo}/resolve/main/{f}"), &dest, None,
                         &|_, a, b| p(&format!("Whisper {name}: {f}"), a, b))?;
            }
        }
        Ok(dir)
    }

    pub fn ensure_silero(&self, p: Progress) -> Result<PathBuf> {
        let dest = self.silero_path();
        if !dest.exists() {
            std::fs::create_dir_all(&self.root)?;
            download(SILERO_URL, &dest, None, &|_, a, b| p("detector de fala", a, b))?;
        }
        Ok(dest)
    }

    pub fn ensure_nllb(&self, p: Progress) -> Result<PathBuf> {
        let dir = self.nllb_dir();
        if dir.join("model.bin").exists() {
            return Ok(dir);
        }
        std::fs::create_dir_all(&self.root)?;
        let zip = self.root.join("nllb.zip");
        download(NLLB_URL, &zip, Some(NLLB_SHA256), &|_, a, b| p("tradutor NLLB", a, b))?;
        let tmp = self.root.join("nllb.tmp");
        let _ = std::fs::remove_dir_all(&tmp);
        extract_zip(&zip, &tmp)?;
        let _ = std::fs::remove_file(&zip);
        let model = find_dir_with(&tmp, "model.bin").ok_or_else(|| anyhow!("o pacote do NLLB veio sem model.bin"))?;
        let _ = std::fs::remove_dir_all(&dir);
        std::fs::rename(model, &dir)?;
        let _ = std::fs::remove_dir_all(&tmp);
        Ok(dir)
    }

    /// Instala um par do Argos (pacote .argosmodel do índice oficial).
    pub fn ensure_argos_pair(&self, src: &str, tgt: &str, p: Progress) -> Result<()> {
        let dir = self.argos_dir();
        if crate::mt::argos_package(&dir, src, tgt).is_ok() {
            return Ok(());
        }
        std::fs::create_dir_all(&dir)?;
        let index: serde_json::Value = serde_json::from_str(&get_text(ARGOS_INDEX)?)?;
        let pkg = index.as_array().and_then(|a| {
            a.iter().find(|x| x["from_code"] == src && x["to_code"] == tgt)
        }).ok_or_else(|| anyhow!("não existe pacote de tradução {src}→{tgt}"))?;
        let url = pkg["links"].get(0).and_then(|v| v.as_str()).ok_or_else(|| anyhow!("pacote {src}→{tgt} sem link"))?;
        let file = dir.join(format!("{src}_{tgt}.argosmodel"));
        download(url, &file, None, &|_, a, b| p(&format!("tradução {src}→{tgt}"), a, b))?;
        extract_zip(&file, &dir)?;
        let _ = std::fs::remove_file(&file);
        Ok(())
    }

    pub fn parakeet_dir(&self, name: &str) -> PathBuf {
        self.root.join(format!("sherpa-onnx-nemo-{name}"))
    }

    /// Parakeet pelo sherpa-onnx (`name`: "parakeet-tdt-0.6b-v3-int8" etc.).
    pub fn ensure_parakeet(&self, name: &str, p: Progress) -> Result<PathBuf> {
        let dir = self.parakeet_dir(name);
        if dir.join("tokens.txt").exists() {
            return Ok(dir);
        }
        std::fs::create_dir_all(&self.root)?;
        if let Some((_, base, files)) = PARAKEET_FILES.iter().find(|(n, _, _)| *n == name) {
            let tmp = self.root.join(format!("sherpa-onnx-nemo-{name}.part"));
            let _ = std::fs::remove_dir_all(&tmp);
            std::fs::create_dir_all(&tmp)?;
            for (f, sha) in *files {
                download(&format!("{base}/{f}"), &tmp.join(f), Some(sha),
                         &|_, a, b| p("reconhecimento de fala (Parakeet)", a, b))?;
            }
            let _ = std::fs::remove_dir_all(&dir);
            std::fs::rename(&tmp, &dir)?;
            return Ok(dir);
        }
        let arc = self.root.join(format!("{name}.tar.bz2"));
        download(&format!("{ASR_MODELS_URL}/sherpa-onnx-nemo-{name}.tar.bz2"), &arc, None,
                 &|_, a, b| p("reconhecimento de fala (Parakeet)", a, b))?;
        let f = std::fs::File::open(&arc)?;
        tar::Archive::new(bzip2::read::BzDecoder::new(f)).unpack(&self.root)
            .with_context(|| format!("extraindo o {name}"))?;
        let _ = std::fs::remove_file(&arc);
        let _ = std::fs::remove_dir_all(dir.join("test_wavs"));
        if !dir.join("tokens.txt").exists() {
            bail!("o pacote {name} não tinha o formato esperado");
        }
        Ok(dir)
    }

    /// Baixa (só na 1ª vez) o pacote da voz escolhida para `lang` e devolve a pasta.
    pub fn ensure_voice_for(&self, lang: &str, gpu: bool, p: Progress) -> Result<PathBuf> {
        match voice_choice(lang, gpu).ok_or_else(|| anyhow!("não há voz para o idioma {lang}"))? {
            VoiceChoice::Kokoro => self.ensure_tts_package(KOKORO_PKG, "voz (Kokoro)", "voices.bin", p),
            VoiceChoice::Supertonic => self.ensure_tts_package(SUPERTONIC_PKG, "voz (Supertonic)", "tts.json", p),
            VoiceChoice::Piper(v) => self.ensure_voice(v, p),
        }
    }

    fn ensure_tts_package(&self, pkg: &str, what: &str, marker: &str, p: Progress) -> Result<PathBuf> {
        let dir = self.voices_dir().join(pkg);
        if dir.join(marker).exists() {
            return Ok(dir);
        }
        std::fs::create_dir_all(self.voices_dir())?;
        let arc = self.voices_dir().join(format!("{pkg}.tar.bz2"));
        download(&format!("{VOICES_URL}/{pkg}.tar.bz2"), &arc, None, &|_, a, b| p(what, a, b))?;
        let f = std::fs::File::open(&arc)?;
        tar::Archive::new(bzip2::read::BzDecoder::new(f)).unpack(self.voices_dir())
            .with_context(|| format!("extraindo {pkg}"))?;
        let _ = std::fs::remove_file(&arc);
        if !dir.join(marker).exists() {
            bail!("o pacote {pkg} não tinha o formato esperado");
        }
        Ok(dir)
    }

    pub fn ensure_voice(&self, voice: &str, p: Progress) -> Result<PathBuf> {
        let dir = self.voice_dir(voice);
        if dir.join("tokens.txt").exists() {
            return Ok(dir);
        }
        std::fs::create_dir_all(self.voices_dir())?;
        let arc = self.voices_dir().join(format!("{voice}.tar.bz2"));
        download(&format!("{VOICES_URL}/vits-piper-{voice}.tar.bz2"), &arc, None,
                 &|_, a, b| p(&format!("voz {voice}"), a, b))?;
        let f = std::fs::File::open(&arc)?;
        tar::Archive::new(bzip2::read::BzDecoder::new(f)).unpack(self.voices_dir())
            .with_context(|| format!("extraindo a voz {voice}"))?;
        let _ = std::fs::remove_file(&arc);
        if !dir.join("tokens.txt").exists() {
            bail!("o pacote da voz {voice} não tinha o formato esperado");
        }
        Ok(dir)
    }
}

fn agent() -> ureq::Agent {
    ureq::Agent::config_builder()
        .timeout_connect(Some(std::time::Duration::from_secs(20)))
        .build()
        .into()
}

fn get_text(url: &str) -> Result<String> {
    Ok(agent().get(url).call().with_context(|| format!("sem acesso a {url} (internet?)"))?
        .body_mut().read_to_string()?)
}

/// Baixa para `dest` (via "dest.part"); com `sha256`, confere a impressão digital antes.
pub fn download(url: &str, dest: &Path, sha256: Option<&str>, p: Progress) -> Result<()> {
    let part = dest.with_extension(format!("{}part", dest.extension().map(|e| format!("{}.", e.to_string_lossy())).unwrap_or_default()));
    let res = (|| -> Result<()> {
        let mut resp = agent().get(url).call().with_context(|| format!("sem acesso a {url} (internet?)"))?;
        let total: u64 = resp.headers().get("content-length").and_then(|v| v.to_str().ok()).and_then(|v| v.parse().ok()).unwrap_or(0);
        let mut reader = resp.body_mut().as_reader();
        let mut out = std::fs::File::create(&part)?;
        let mut hasher = Sha256::new();
        let mut buf = vec![0u8; 1 << 16];
        let (mut got, mut last) = (0u64, 0u64);
        loop {
            let n = reader.read(&mut buf)?;
            if n == 0 {
                break;
            }
            out.write_all(&buf[..n])?;
            hasher.update(&buf[..n]);
            got += n as u64;
            if got - last > (1 << 20) || got == total {
                p(url, got, total);
                last = got;
            }
        }
        out.flush()?;
        if let Some(want) = sha256 {
            let have = hex(&hasher.finalize());
            if have != want {
                bail!("o arquivo baixado não confere (impressão digital diferente): {url}");
            }
        }
        std::fs::rename(&part, dest)?;
        Ok(())
    })();
    if res.is_err() {
        let _ = std::fs::remove_file(&part);
    }
    res
}

fn hex(b: &[u8]) -> String {
    b.iter().map(|x| format!("{x:02x}")).collect()
}

fn extract_zip(zip: &Path, dest: &Path) -> Result<()> {
    let mut a = zip::ZipArchive::new(std::fs::File::open(zip)?)?;
    a.extract(dest).with_context(|| format!("extraindo {}", zip.display()))?;
    Ok(())
}

fn find_dir_with(root: &Path, file: &str) -> Option<PathBuf> {
    if root.join(file).exists() {
        return Some(root.to_path_buf());
    }
    for e in std::fs::read_dir(root).ok()?.flatten() {
        if e.path().is_dir() {
            if let Some(d) = find_dir_with(&e.path(), file) {
                return Some(d);
            }
        }
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn voz_mais_clara_por_idioma_sem_piper() {
        assert_eq!(voice_choice("pt", true), Some(VoiceChoice::Kokoro));
        assert_eq!(voice_choice("pt", false), Some(VoiceChoice::Supertonic));
        assert_eq!(voice_choice("zh", false), Some(VoiceChoice::Kokoro));
        assert_eq!(voice_choice("de", true), Some(VoiceChoice::Supertonic));
        assert_eq!(voice_choice("ja", false), Some(VoiceChoice::Supertonic));
        // nenhum idioma do Praxis precisa mais do Piper
        for l in ["pt", "en", "es", "fr", "de", "it", "ru", "zh", "nl", "pl", "uk", "tr", "ar", "hi", "ja", "ko"] {
            for gpu in [true, false] {
                assert!(!matches!(voice_choice(l, gpu), Some(VoiceChoice::Piper(_)) | None), "{l}");
            }
        }
    }

    #[test]
    fn todo_idioma_de_saida_tem_voz_padrao() {
        for l in ["pt", "en", "es", "fr", "de", "it", "ru", "zh", "nl", "pl", "uk", "tr", "ar", "hi"] {
            assert!(default_voice(l).is_some(), "{l} sem voz");
        }
        assert!(default_voice("ja").is_none(), "japonês só se fala, não há voz");
    }

    #[test]
    fn download_com_impressao_digital_errada_nao_fica_instalado() {
        let dir = std::env::temp_dir().join(format!("praxis-teste-{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        let src = dir.join("origem.bin");
        std::fs::write(&src, b"conteudo").unwrap();
        let dest = dir.join("destino.bin");
        let url = format!("file://{}", src.display());
        // ureq não lê file://: o erro de acesso também não pode deixar resto
        let r = download(&url, &dest, Some("00"), &|_, _, _| {});
        assert!(r.is_err());
        assert!(!dest.exists());
        assert!(std::fs::read_dir(&dir).unwrap().all(|e| !e.unwrap().file_name().to_string_lossy().ends_with("part")));
        let _ = std::fs::remove_dir_all(&dir);
    }
}
