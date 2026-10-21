//! Regras de texto do Praxis (as mesmas do motor em Python, medidas com fala real).

/// Divide em frases depois de . ! ? … seguidos de espaço.
/// Pedaços para a voz: as frases, com a primeira cortada na primeira vírgula quando os dois
/// lados são longos o bastante. A voz só começa a tocar depois de sintetizar o 1º pedaço; um
/// pedaço menor = menos espera (medido: a 1ª frase inteira levava de 0,3 a 0,95 s).
pub fn speech_chunks(text: &str) -> Vec<String> {
    let mut out = split_sentences(text);
    if let Some(first) = out.first().cloned() {
        // pelo menos n palavras (ou 8 letras em chinês/japonês, sem espaços)
        let long = |t: &str, n: usize| t.split_whitespace().count() >= n || t.chars().count() >= 8 && !t.contains(' ');
        if let Some(pos) = first.find([',', '，', '،', '、']) {
            let comma = first[pos..].chars().next().map(char::len_utf8).unwrap_or(1);
            let (a, b) = (first[..pos + comma].trim(), first[pos + comma..].trim());
            if long(a, 2) && long(b, 3) {
                out.splice(0..1, [a.to_string(), b.to_string()]);
            }
        }
    }
    out
}

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

/// Só pontuação: o Whisper às vezes devolve isso para ruído — não é fala.
pub fn is_noise_only(text: &str) -> bool {
    matches!(text.trim(), "" | "." | "," | "..." | "!" | "?" | "…")
}

/// Laços dentro de uma "palavra" em escritas sem espaço (medido com eco: "少し少し少し…",
/// "वावावावा…"): um pedaço de 1–8 letras repetido 4+ vezes vira 2. Nunca mexe em números.
fn collapse_char_loops(text: &str) -> String {
    let c: Vec<char> = text.chars().collect();
    let mut out = String::new();
    let mut i = 0;
    'outer: while i < c.len() {
        for len in 1..=8usize {
            if i + len > c.len() {
                break;
            }
            let chunk = &c[i..i + len];
            if chunk.iter().any(|ch| ch.is_ascii_digit()) {
                continue;
            }
            let mut reps = 1;
            while i + (reps + 1) * len <= c.len() && &c[i + reps * len..i + (reps + 1) * len] == chunk {
                reps += 1;
            }
            if reps >= 4 {
                out.extend(chunk.iter());
                out.extend(chunk.iter());
                i += reps * len;
                continue 'outer;
            }
        }
        out.push(c[i]);
        i += 1;
    }
    out
}

/// Remove os laços de alucinação do Whisper ("o que é o que é o que é …"): qualquer
/// sequência de 1 a 8 palavras repetida mais de `max_repeats` vezes fica `max_repeats` vezes.
pub fn collapse_repetitions(text: &str, max_repeats: usize) -> String {
    let text = collapse_char_loops(text);
    let mut words: Vec<String> = text.split_whitespace().map(String::from).collect();
    if words.len() < 4 {
        return text;
    }
    let norm = |w: &String| w.to_lowercase().trim_matches(|ch| ".,!?¿¡;:…".contains(ch)).to_string();
    let mut changed = true;
    while changed {
        changed = false;
        for n in 1..=8usize {
            let mut out: Vec<String> = Vec::new();
            let mut i = 0;
            while i < words.len() {
                let gram: Vec<String> = words[i..(i + n).min(words.len())].iter().map(norm).collect();
                let mut reps = 1;
                while i + (reps + 1) * n <= words.len()
                    && words[i + reps * n..i + (reps + 1) * n].iter().map(norm).collect::<Vec<_>>() == gram
                {
                    reps += 1;
                }
                if reps > max_repeats && gram.len() == n {
                    out.extend_from_slice(&words[i..i + n * max_repeats]);
                    i += reps * n;
                    changed = true;
                } else {
                    out.push(words[i].clone());
                    i += 1;
                }
            }
            words = out;
        }
    }
    words.join(" ")
}

/// Limpeza do que o Whisper devolveu, como no Praxis em Python: tira o "�" (um
/// caractere de vários bytes partido entre pedaços, visto em hindi), espaços duplos,
/// laços de repetição e trechos que são só pontuação.
pub fn clean_transcript(text: &str) -> String {
    let t = text.replace('\u{fffd}', "");
    let t = t.split_whitespace().collect::<Vec<_>>().join(" ");
    let t = collapse_repetitions(&t, 2);
    if is_noise_only(&t) { String::new() } else { t }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn primeiro_pedaco_para_a_voz_corta_na_virgula() {
        assert_eq!(speech_chunks("Segundo informações, ele estava na casa dos 20 anos. Depois saiu."),
                   vec!["Segundo informações,", "ele estava na casa dos 20 anos.", "Depois saiu."]);
        // lado curto demais: não corta
        assert_eq!(speech_chunks("Sim, claro que sim."), vec!["Sim, claro que sim."]);
        // chinês, sem espaços
        assert_eq!(speech_chunks("医院遵循了感染控制规程，包括将病人与他人隔离。").len(), 2);
    }

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
    fn guarda_pega_lacos_sem_espaco_como_no_python() {
        assert_eq!(collapse_repetitions("少し少し少し少し少しスターバー", 2), "少し少しスターバー");
        assert_eq!(collapse_repetitions("अपना बवाश्वावावावावावावावा", 2), "अपना बवाश्वावा");
        assert_eq!(collapse_repetitions("hahaha que engraçado", 2), "hahaha que engraçado");
        assert_eq!(collapse_repetitions("custou 1000000 de reais em 2000", 2), "custou 1000000 de reais em 2000");
    }

    #[test]
    fn guarda_pega_lacos_de_palavras() {
        assert_eq!(collapse_repetitions("o que é o que é o que é o que é isso", 2), "o que é o que é isso");
        assert_eq!(collapse_repetitions("sim sim sim sim", 2), "sim sim");
        assert_eq!(collapse_repetitions("uma frase normal sem laço", 2), "uma frase normal sem laço");
    }

    #[test]
    fn limpeza_tira_caractere_quebrado_e_pontuacao_sozinha() {
        assert_eq!(clean_transcript("प्रद\u{fffd} तो  ग्रीनलैंड"), "प्रद तो ग्रीनलैंड");
        assert_eq!(clean_transcript(" ... "), "");
    }

    #[test]
    fn frase_curta_fica_inteira() {
        assert_eq!(chunk_for_mt("uma frase curta"), vec!["uma frase curta"]);
    }
}
