//! Tradução: NLLB-200 (Meta) e Argos, pelo CTranslate2 — os mesmos modelos e as
//! mesmas opções do Praxis em Python (medidos contra traduções humanas).

use std::path::{Path, PathBuf};

use anyhow::{anyhow, Context, Result};
use ct2rs::sys::{TranslationOptions, Translator};
use ct2rs::{ComputeType, Config, Device};
use sentencepiece::SentencePieceProcessor;

use crate::text::mt_units;

pub const BEAM: usize = 4; // padrão do argostranslate (num_hypotheses=4)

/// Caminhos comparados pelo NLLB (PRAXIS_FEIXE_NLLB muda, para medição).
fn nllb_beam() -> usize {
    std::env::var("PRAXIS_FEIXE_NLLB").ok().and_then(|v| v.parse().ok()).unwrap_or(BEAM)
}

pub fn nllb_code(lang: &str) -> Option<&'static str> {
    Some(match lang {
        "pt" => "por_Latn", "en" => "eng_Latn", "es" => "spa_Latn", "fr" => "fra_Latn",
        "de" => "deu_Latn", "it" => "ita_Latn", "ru" => "rus_Cyrl", "zh" => "zho_Hans",
        "nl" => "nld_Latn", "pl" => "pol_Latn", "uk" => "ukr_Cyrl", "tr" => "tur_Latn",
        "ar" => "arb_Arab", "hi" => "hin_Deva", "ja" => "jpn_Jpan", "ko" => "kor_Hang",
        _ => return None,
    })
}

fn config(gpu: bool, compute: ComputeType) -> Config {
    Config {
        device: if gpu { Device::CUDA } else { Device::CPU },
        compute_type: compute,
        num_threads_per_replica: std::env::var("PRAXIS_THREADS").ok().and_then(|v| v.parse().ok()).unwrap_or(0),
        ..Default::default()
    }
}

/// Remonta o texto a partir dos pedaços do sentencepiece: "▁" marca o início de uma
/// palavra; "<0xNN>" é um byte solto (letras raras). O decodificador da biblioteca
/// deixava o "▁" grudado nos pedaços do Argos que não estão no seu vocabulário.
pub fn join_pieces(toks: &[String]) -> String {
    let mut bytes: Vec<u8> = Vec::new();
    for t in toks {
        if t.len() == 6 && t.starts_with("<0x") && t.ends_with('>') {
            if let Ok(b) = u8::from_str_radix(&t[3..5], 16) {
                bytes.push(b);
                continue;
            }
        }
        if t.starts_with('<') && t.ends_with('>') {
            continue; // marcadores especiais (<unk>, </s>…)
        }
        bytes.extend_from_slice(t.replace('▁', " ").as_bytes());
    }
    String::from_utf8_lossy(&bytes).split_whitespace().collect::<Vec<_>>().join(" ")
}

fn decode(_sp: &SentencePieceProcessor, toks: &[String]) -> Result<String> {
    Ok(join_pieces(toks))
}

/// NLLB-200: um modelo para todos os pares, sem passar pelo inglês.
pub struct Nllb {
    tr: Translator,
    sp: SentencePieceProcessor,
}

impl Nllb {
    pub fn load(dir: &Path, gpu: bool) -> Result<Self> {
        let tr = Translator::new(dir, &config(gpu, ComputeType::DEFAULT))?;
        let sp = SentencePieceProcessor::open(dir.join("sentencepiece.bpe.model"))
            .map_err(|e| anyhow!("sentencepiece do NLLB: {e}"))?;
        Ok(Self { tr, sp })
    }

    pub fn translate(&self, text: &str, src: &str, tgt: &str) -> Result<String> {
        let (s, t) = (
            nllb_code(src).ok_or_else(|| anyhow!("idioma {src} sem código NLLB"))?,
            nllb_code(tgt).ok_or_else(|| anyhow!("idioma {tgt} sem código NLLB"))?,
        );
        let units = mt_units(text);
        let batch: Vec<Vec<String>> = units
            .iter()
            .map(|u| -> Result<Vec<String>> {
                let mut v = vec![s.to_string()];
                v.extend(self.sp.encode(u).map_err(|e| anyhow!("{e}"))?.into_iter().map(|p| p.piece));
                v.push("</s>".to_string());
                Ok(v)
            })
            .collect::<Result<_>>()?;
        let prefix = vec![vec![t.to_string()]; batch.len()];
        let opts = TranslationOptions {
            beam_size: nllb_beam(),
            replace_unknowns: true,
            max_batch_size: 32,
            ..Default::default()
        };
        let res = self.tr.translate_batch_with_target_prefix(&batch, &prefix, &opts, None)?;
        let mut out = Vec::new();
        for r in res {
            let hyp: Vec<String> = r.output().cloned().unwrap_or_default().into_iter().filter(|x| x != t).collect();
            let d = decode(&self.sp, &hyp)?;
            if !d.is_empty() {
                out.push(d);
            }
        }
        Ok(out.join(" "))
    }
}

impl Nllb {
    /// Tradução da frase até aqui OBRIGADA a começar pelas palavras já faladas (`spoken`): o
    /// NLLB continua a partir delas. É o que permite falar a tradução enquanto a pessoa ainda
    /// fala, sem a qualidade cair como cai ao traduzir pedaços soltos. Devolve todas as
    /// palavras (as já faladas + as novas).
    pub fn continue_from(&self, text: &str, spoken: &[String], src: &str, tgt: &str) -> Result<Vec<String>> {
        let (s, t) = (
            nllb_code(src).ok_or_else(|| anyhow!("idioma {src} sem código NLLB"))?,
            nllb_code(tgt).ok_or_else(|| anyhow!("idioma {tgt} sem código NLLB"))?,
        );
        let mut source = vec![s.to_string()];
        source.extend(self.sp.encode(text.trim()).map_err(|e| anyhow!("{e}"))?.into_iter().map(|p| p.piece));
        source.push("</s>".to_string());
        let mut prefix = vec![t.to_string()];
        if !spoken.is_empty() {
            prefix.extend(self.sp.encode(&spoken.join(" ")).map_err(|e| anyhow!("{e}"))?.into_iter().map(|p| p.piece));
        }
        let opts = TranslationOptions { beam_size: nllb_beam(), replace_unknowns: true, ..Default::default() };
        let res = self.tr.translate_batch_with_target_prefix(&vec![source], &vec![prefix], &opts, None)?;
        let hyp: Vec<String> = res.into_iter().next().and_then(|r| r.output().cloned()).unwrap_or_default()
            .into_iter().filter(|x| x != t).collect();
        Ok(decode(&self.sp, &hyp)?.split_whitespace().map(String::from).collect())
    }
}

/// Um par do Argos (pacote extraído: model/, sentencepiece.model, metadata.json).
pub struct ArgosPair {
    tr: Translator,
    sp: SentencePieceProcessor,
    target_prefix: Option<String>,
}

impl ArgosPair {
    pub fn load(pkg: &Path, gpu: bool) -> Result<Self> {
        // "default" = o tipo com que o modelo foi salvo: "auto" escolhia int8 em muitos
        // processadores e o es→en gerava lixo repetido (medido no Praxis em Python)
        let tr = Translator::new(pkg.join("model"), &config(gpu, ComputeType::DEFAULT))?;
        let sp = SentencePieceProcessor::open(pkg.join("sentencepiece.model"))
            .map_err(|e| anyhow!("sentencepiece do Argos em {}: {e}", pkg.display()))?;
        let meta: serde_json::Value = std::fs::read_to_string(pkg.join("metadata.json"))
            .ok()
            .and_then(|s| serde_json::from_str(&s).ok())
            .unwrap_or_default();
        let target_prefix = meta["target_prefix"].as_str().filter(|s| !s.is_empty()).map(String::from);
        Ok(Self { tr, sp, target_prefix })
    }

    pub fn translate(&self, text: &str) -> Result<String> {
        let units = mt_units(text);
        let batch: Vec<Vec<String>> = units
            .iter()
            .map(|u| Ok(self.sp.encode(u).map_err(|e| anyhow!("{e}"))?.into_iter().map(|p| p.piece).collect()))
            .collect::<Result<_>>()?;
        let opts = TranslationOptions {
            beam_size: BEAM,
            length_penalty: 0.2,
            replace_unknowns: true,
            max_batch_size: 32,
            ..Default::default()
        };
        let res = match &self.target_prefix {
            Some(p) => {
                let prefix = vec![vec![p.clone()]; batch.len()];
                self.tr.translate_batch_with_target_prefix(&batch, &prefix, &opts, None)?
            }
            None => self.tr.translate_batch(&batch, &opts, None)?,
        };
        let mut out = Vec::new();
        for r in res {
            let mut d = decode(&self.sp, &r.output().cloned().unwrap_or_default())?;
            if let Some(p) = &self.target_prefix {
                if let Some(rest) = d.strip_prefix(p.as_str()) {
                    d = rest.trim().to_string();
                }
            }
            if !d.is_empty() {
                out.push(d);
            }
        }
        Ok(out.join(" "))
    }
}

/// Pasta de um pacote do Argos instalado (procura "<origem>_<destino>").
pub fn argos_package(packages_dir: &Path, src: &str, tgt: &str) -> Result<PathBuf> {
    let want = format!("{src}_{tgt}");
    std::fs::read_dir(packages_dir)
        .with_context(|| format!("pasta de pacotes do Argos {}", packages_dir.display()))?
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .find(|p| {
            p.file_name().map(|n| n.to_string_lossy().starts_with(&want)).unwrap_or(false)
                || std::fs::read_to_string(p.join("metadata.json"))
                    .ok()
                    .and_then(|s| serde_json::from_str::<serde_json::Value>(&s).ok())
                    .map(|m| m["from_code"] == src && m["to_code"] == tgt)
                    .unwrap_or(false)
        })
        .ok_or_else(|| anyhow!("pacote Argos {src}→{tgt} não instalado"))
}

#[cfg(test)]
mod tests {
    use super::join_pieces;

    #[test]
    fn remonta_palavras_do_sentencepiece() {
        let t = |v: &[&str]| join_pieces(&v.iter().map(|s| s.to_string()).collect::<Vec<_>>());
        assert_eq!(t(&["▁It", "▁is", "▁also", "▁recommended", "."]), "It is also recommended.");
        assert_eq!(t(&["▁caf", "<0xC3>", "<0xA9>"]), "café");
        assert_eq!(t(&["▁fim", "</s>"]), "fim");
    }
}
