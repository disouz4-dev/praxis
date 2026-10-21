//! Regras de texto do Praxis (as mesmas do motor em Python, medidas com fala real).

/// Divide em frases depois de . ! ? … seguidos de espaço.
pub fn split_sentences(text: &str) -> Vec<String> {
    let mut out = Vec::new();
    let mut cur = String::new();
    let chars: Vec<char> = text.chars().collect();
    let mut i = 0;
    while i < chars.len() {
        let c = chars[i];
        cur.push(c);
        if matches!(c, '.' | '!' | '?' | '…') && i + 1 < chars.len() && chars[i + 1].is_whitespace() {
            let s = cur.trim().to_string();
            if !s.is_empty() {
                out.push(s);
            }
            cur.clear();
            while i + 1 < chars.len() && chars[i + 1].is_whitespace() {
                i += 1;
            }
        }
        i += 1;
    }
    let s = cur.trim().to_string();
    if !s.is_empty() {
        out.push(s);
    }
    if out.is_empty() {
        out.push(text.to_string());
    }
    out
}

pub const MT_MAX_WORDS: usize = 30;
pub const MT_MAX_CHARS_NOSPACE: usize = 60;

/// Frases longas demais são divididas antes da tradução: os modelos degeneram com
/// entradas longas sem pontuação (achado com fala real: 175 palavras em italiano sem
/// pontuação saíram como uma frase repetida). Corta em vírgulas, depois por tamanho,
/// e junta pedaços minúsculos ao vizinho.
pub fn chunk_for_mt(sentence: &str) -> Vec<String> {
    let words: Vec<&str> = sentence.split_whitespace().collect();
    let spaced = words.len() > 1;
    let too_long = if spaced { words.len() > MT_MAX_WORDS } else { sentence.chars().count() > MT_MAX_CHARS_NOSPACE };
    if !too_long {
        return vec![sentence.to_string()];
    }
    // divide depois de , ; : (e as vírgulas do chinês/japonês)
    let mut parts = Vec::new();
    let mut cur = String::new();
    for c in sentence.chars() {
        cur.push(c);
        if matches!(c, ',' | ';' | ':' | '，' | '、' | '；' | '：') {
            parts.push(std::mem::take(&mut cur));
        }
    }
    parts.push(cur);
    let mut pieces = Vec::new();
    for part in parts.iter().map(|p| p.trim()).filter(|p| !p.is_empty()) {
        if spaced {
            let w: Vec<&str> = part.split_whitespace().collect();
            for c in w.chunks(MT_MAX_WORDS) {
                pieces.push(c.join(" "));
            }
        } else {
            let ch: Vec<char> = part.chars().collect();
            for c in ch.chunks(MT_MAX_CHARS_NOSPACE) {
                pieces.push(c.iter().collect::<String>());
            }
        }
    }
    let mut merged: Vec<String> = Vec::new();
    for p in pieces {
        let small = if spaced { p.split_whitespace().count() < 4 } else { p.chars().count() < 8 };
        match merged.last_mut() {
            Some(last) if small => {
                if spaced {
                    last.push(' ');
                }
                last.push_str(&p);
            }
            _ => merged.push(p),
        }
    }
    merged
}

/// Frases prontas para traduzir: divididas e, se longas, cortadas.
pub fn mt_units(text: &str) -> Vec<String> {
    split_sentences(text.trim()).iter().flat_map(|s| chunk_for_mt(s)).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn divide_frases_como_o_python() {
        assert_eq!(split_sentences("Olá. Tudo bem? Sim!"), vec!["Olá.", "Tudo bem?", "Sim!"]);
        assert_eq!(split_sentences("sem ponto"), vec!["sem ponto"]);
        assert_eq!(split_sentences("3.5 metros. Fim."), vec!["3.5 metros.", "Fim."]);
    }

    #[test]
    fn corta_frase_longa_sem_pontuacao() {
        let longa = (0..70).map(|i| format!("palavra{i}")).collect::<Vec<_>>().join(" ");
        let p = chunk_for_mt(&longa);
        assert!(p.len() >= 2 && p.iter().all(|x| x.split_whitespace().count() <= MT_MAX_WORDS + 3));
        assert_eq!(p.join(" "), longa);
    }

    #[test]
    fn frase_curta_fica_inteira() {
        assert_eq!(chunk_for_mt("uma frase curta"), vec!["uma frase curta"]);
    }
}
