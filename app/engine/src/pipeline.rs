//! Motor em tempo real: uma "direção" (quem fala → quem ouve) com quatro tarefas em
//! paralelo, como no Praxis em Python:
//!
//!   áudio (blocos de 32 ms) → detector de fala → reconhecimento + tradução + voz → reprodução
//!
//! A reprodução roda numa tarefa própria: enquanto uma frase toca, a próxima já está sendo
//! transcrita (no desenho serial antigo o processador ficava cada vez mais atrasado).
//! A voz fala mais rápido quando a tradução acumula (velocidade adaptativa) e, se a
//! tradução toca num alto-falante, o microfone fica surdo enquanto ela toca (trava de eco).

use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::mpsc::{channel, Receiver, RecvTimeoutError, Sender};
use std::sync::{Arc, Mutex};
use std::thread::JoinHandle;
use std::time::{Duration, Instant};

use anyhow::Result;

use crate::asr::Asr;
use crate::mt;
use crate::text::speech_chunks;
use crate::tts::PiperVoice;
use crate::vad::{Segmenter, SegmenterConfig, SileroV6, SR};

/// (atraso de reprodução ≤ s, length_scale): a voz acelera quando a tradução se acumula.
/// Medido (22/10/2026, Supertonic, pedaços do modo simultâneo): 1,43× fez a voz comer 55% das
/// palavras. Medido (23/10/2026, voz clonada, frases inteiras): 1,0× 2%, 1,1× 1%, 1,2× 2%,
/// 1,3× 3,9% de palavras erradas — acelera cedo e para em 1,2×.
pub const RATE_STEPS: [(f32, f32); 3] = [(0.5, 1.0), (1.5, 0.91), (f32::INFINITY, 0.83)];
/// Folga da trava de eco depois que o alto-falante para.
pub const ECHO_TAIL_S: f32 = 0.35;

pub fn speech_length_scale(backlog_s: f32) -> f32 {
    RATE_STEPS.iter().find(|(lim, _)| backlog_s <= *lim).map(|(_, s)| *s).unwrap_or(0.7)
}

pub trait Translate: Send + Sync {
    fn translate(&self, text: &str, src: &str, tgt: &str) -> Result<String>;
    /// Tradução da frase até aqui começando pelas palavras já faladas (tradução simultânea).
    /// Padrão: traduz tudo de novo e confia que o começo se repete.
    fn continue_from(&self, text: &str, spoken: &[String], src: &str, tgt: &str) -> Result<Vec<String>> {
        let _ = spoken;
        Ok(self.translate(text, src, tgt)?.split_whitespace().map(String::from).collect())
    }
}

impl Translate for mt::Nllb {
    fn translate(&self, text: &str, src: &str, tgt: &str) -> Result<String> {
        mt::Nllb::translate(self, text, src, tgt)
    }
    fn continue_from(&self, text: &str, spoken: &[String], src: &str, tgt: &str) -> Result<Vec<String>> {
        mt::Nllb::continue_from(self, text, spoken, src, tgt)
    }
}

/// Argos: par direto, ou passando pelo inglês quando nenhum lado é inglês.
pub struct ArgosRoute(pub Vec<mt::ArgosPair>);

impl Translate for ArgosRoute {
    fn translate(&self, text: &str, _src: &str, _tgt: &str) -> Result<String> {
        let mut t = text.to_string();
        for p in &self.0 {
            t = p.translate(&t)?;
        }
        Ok(t)
    }
}

/// Toca áudio e só volta quando terminar (como um alto-falante de verdade).
pub trait Speaker: Send + Sync {
    fn play(&self, samples: &[f32], sample_rate: u32);
}

#[derive(Debug, Clone, serde::Serialize)]
#[serde(tag = "e", rename_all = "snake_case")]
pub enum Event {
    Transcript { dir: String, text: String },
    Translation { dir: String, text: String },
    Error { msg: String },
    /// um trecho de fala ficou pronto (fim da fala no relógio do áudio, em segundos)
    Segment { dir: String, id: usize, speech_end_s: f32, emitted_s: f32 },
    /// começou a tocar a tradução de um trecho
    Play { dir: String, id: usize, start_s: f32, dur_s: f32 },
    /// uma etapa terminou para um trecho ("transcrito", "traduzido", "voz"), no relógio do áudio
    Stage { dir: String, id: usize, stage: String, at_s: f32 },
}

pub struct Shared {
    pub stop: AtomicBool,
    /// até quando (ms desde t0) o alto-falante está tocando — trava de eco
    pub speaker_busy_until_ms: AtomicU64,
    pub t0: Instant,
}

impl Shared {
    pub fn new() -> Arc<Self> {
        Arc::new(Self { stop: AtomicBool::new(false), speaker_busy_until_ms: AtomicU64::new(0), t0: Instant::now() })
    }
    pub fn now_s(&self) -> f32 {
        self.t0.elapsed().as_secs_f32()
    }
}

pub struct Direction {
    pub name: String, // "out" (usuário) | "in" (interlocutor)
    pub src: String,
    pub tgt: String,
    /// a tradução toca num alto-falante
    pub to_speaker: bool,
    /// a captura desta direção é o microfone do usuário: fica surda enquanto algo toca na caixa
    /// de som (trava de eco). A captura da outra pessoa é digital e nunca é travada.
    pub echo_gate: bool,
    /// o que esta direção toca vaza para o microfone do usuário (caixa de som, sem fone)
    pub leaks: bool,
    /// se presente, só vaza enquanto este sinal estiver ligado (a monitoria liga e desliga ao vivo)
    pub leak_when: Option<Arc<AtomicBool>>,
    /// tradução simultânea: fala a tradução enquanto a pessoa ainda fala (a premissa do
    /// Praxis); falso = espera o fim de cada trecho
    pub simultaneous: bool,
}

/// Fim da fala dentro do trecho: último bloco com volume (as bordas são silêncio).
fn voiced_end(audio: &[f32]) -> usize {
    let chunk = crate::vad::CHUNK;
    let env: Vec<f32> = audio.chunks(chunk).map(|c| (c.iter().map(|x| x * x).sum::<f32>() / c.len() as f32).sqrt()).collect();
    let max = env.iter().cloned().fold(0.0f32, f32::max);
    let thr = (0.1 * max).max(0.01);
    env.iter().rposition(|&e| e > thr).map(|i| (i + 1) * chunk).unwrap_or(audio.len()).min(audio.len())
}

/// Trabalho para o reconhecedor: um trecho adiantado (a fala parece ter acabado) ou o
/// trecho final (o fim se confirmou).
enum Job {
    Tentative(Vec<f32>),
    /// o trecho em curso até agora (tradução simultânea: relido a cada ~1 s enquanto se fala)
    Partial(usize, Vec<f32>),
    Final(usize, Vec<f32>),
}

/// Tradução simultânea: a cada quanto tempo de fala o trecho em curso é relido, quantas
/// palavras confirmadas novas pedem tradução e quantas das últimas traduzidas esperam (ainda
/// podem mudar quando a frase continuar).
/// Medido no lab2 (conversa pt→en): 0,6 s / 3 / 2 começa a falar ~0,8 s antes do fim da fala
/// em 7 de 13 trechos, com o último pedaço ~1,5 s depois; segurar só 1 palavra errava mais.
const PARTIAL_EVERY_S: f32 = 0.6;
const LIVE_MIN_NEW_WORDS: usize = 3;
const LIVE_HOLD_BACK: usize = 2;
/// Menor pedaço falado no modo simultâneo (palavras da tradução), fora o fim da frase. Medido:
/// a voz come 11–15% das palavras em pedaços de 4 e 1,4–5,5% em pedaços de 6.
const LIVE_MIN_SPOKEN: usize = 6;

/// Ajuste para medições: PRAXIS_RELEITURA_S, PRAXIS_PALAVRAS_MIN e PRAXIS_SEGURAR substituem
/// os três valores acima.
fn live_param<T: std::str::FromStr>(name: &str, default: T) -> T {
    std::env::var(name).ok().and_then(|v| v.parse().ok()).unwrap_or(default)
}

/// A tradução tem um tamanho plausível para o original? O NLLB, com um pedaço solto de frase,
/// às vezes inventa outra frase inteira (medido 23/10/2026, es→en: 11 palavras viraram "In this
/// context, it is important to note that the Commission has not yet adopted a proposal for a
/// regulation." — 20 palavras sem relação). Chinês e japonês não separam palavras: sem conferência.
fn plausible(src_words: usize, tgt_words: usize, src: &str, tgt: &str) -> bool {
    if src_words < 4 || ["zh", "ja"].contains(&src) || ["zh", "ja"].contains(&tgt) {
        return true;
    }
    let r = tgt_words as f32 / src_words as f32;
    (0.4..=1.7).contains(&r)
}

/// Palavra comparável (sem maiúsculas nem pontuação), para o acordo entre duas leituras.
fn norm_word(w: &str) -> String {
    w.chars().filter(|c| c.is_alphanumeric()).flat_map(char::to_lowercase).collect()
}

/// Estado da tradução simultânea do trecho em curso.
#[derive(Default)]
struct Live {
    id: usize,
    previous: Vec<String>,  // última leitura do trecho
    committed: Vec<String>, // palavras confirmadas (iguais em duas leituras seguidas)
    src_spoken: usize,      // quantas palavras confirmadas já foram traduzidas e faladas
    tgt_spoken: Vec<String>, // a tradução já falada
}

/// Resultado de um trecho: texto, tradução e a voz do 1º pedaço já pronta.
struct Done {
    text: String,
    translation: String,
    first: Option<Vec<f32>>,
    rest: Vec<String>,
}

#[allow(clippy::too_many_arguments)]
pub fn spawn_direction(
    audio_rx: Receiver<Vec<f32>>,
    asr: Arc<Asr>,
    translator: Arc<dyn Translate>,
    // sem voz = só legenda (a tradução só aparece em texto)
    voice: Option<Arc<PiperVoice>>,
    speaker: Arc<dyn Speaker>,
    dir: Direction,
    seg_cfg: SegmenterConfig,
    silero_model: String,
    shared: Arc<Shared>,
    events: Sender<Event>,
) -> Result<Vec<JoinHandle<()>>> {
    let dir = Arc::new(dir);
    let (seg_tx, seg_rx) = channel::<Job>();
    let (play_tx, play_rx) = channel::<(usize, Vec<f32>, u32)>();
    let backlog = Arc::new(Mutex::new(0f32)); // segundos de tradução ainda não tocados
    let probe = SileroV6::load(&silero_model, seg_cfg.threshold)?;
    let mut handles = vec![];

    // 1. detector de fala
    {
        let (shared, events, dir) = (shared.clone(), events.clone(), dir.clone());
        handles.push(std::thread::spawn(move || {
            let mut seg = Segmenter::new(probe, seg_cfg);
            let mut id = 0usize;
            let mut since_partial = 0usize;
            while !shared.stop.load(Ordering::Relaxed) {
                let mut chunk = match audio_rx.recv_timeout(Duration::from_millis(200)) {
                    Ok(c) => c,
                    Err(RecvTimeoutError::Timeout) => continue,
                    Err(RecvTimeoutError::Disconnected) => break,
                };
                let now_ms = (shared.now_s() * 1000.0) as u64;
                if dir.echo_gate && now_ms < shared.speaker_busy_until_ms.load(Ordering::Relaxed) {
                    chunk.iter_mut().for_each(|x| *x = 0.0); // alto-falante vazando: vira silêncio
                }
                for audio in seg.push(&chunk) {
                    let end = *seg.ends.last().unwrap_or(&0);
                    // fim da fala no relógio do aplicativo (o mesmo da reprodução): o áudio chega
                    // em tempo real, então a amostra `fim` tocou há (posição − fim) amostras. O
                    // relógio do áudio começa quando o microfone abre, depois de carregar os
                    // modelos, e a diferença aparecia como atraso falso de 2 a 5 s.
                    let fim = end - (audio.len() - voiced_end(&audio));
                    let speech_end = shared.now_s() - seg.position().saturating_sub(fim) as f32 / SR as f32;
                    let _ = events.send(Event::Segment { dir: dir.name.clone(), id, speech_end_s: speech_end, emitted_s: shared.now_s() });
                    let _ = seg_tx.send(Job::Final(id, audio));
                    id += 1;
                    since_partial = 0;
                }
                if dir.simultaneous {
                    // tradução simultânea: o trecho em curso vai para releitura a cada ~1 s de fala
                    since_partial += 1;
                    if since_partial as f32 * crate::vad::CHUNK_S >= live_param("PRAXIS_RELEITURA_S", PARTIAL_EVERY_S) {
                        if let Some(audio) = seg.current().filter(|a| a.len() >= SR) {
                            let _ = seg_tx.send(Job::Partial(id, audio));
                        }
                        since_partial = 0;
                    }
                } else if let Some(audio) = seg.tentative() {
                    // a fala parece ter acabado: adianta o trabalho enquanto o fim é confirmado
                    let _ = seg_tx.send(Job::Tentative(audio));
                }
            }
            for audio in seg.flush() {
                let _ = seg_tx.send(Job::Final(id, audio));
                id += 1;
            }
        }));
    }

    // 2. reconhecimento + tradução + voz
    {
        let (shared, events, dir, backlog) = (shared.clone(), events.clone(), dir.clone(), backlog.clone());
        handles.push(std::thread::spawn(move || {
            // reconhecer + traduzir + sintetizar o 1º pedaço da voz
            let work = |audio: &[f32]| -> Result<Option<Done>> {
                let t = asr.transcribe(audio, &dir.src)?;
                if t.text.is_empty() {
                    return Ok(None);
                }
                let tr = translator.translate(&t.text, &dir.src, &dir.tgt)?;
                let mut chunks = speech_chunks(&tr);
                let first = match &voice {
                    Some(voice) if !chunks.is_empty() => {
                        let c = chunks.remove(0);
                        let scale = speech_length_scale(*backlog.lock().unwrap());
                        Some(voice.synthesize(&c, scale)?)
                    }
                    _ => None,
                };
                Ok(Some(Done { text: t.text, translation: tr, first, rest: chunks }))
            };
            // trabalho adiantado do trecho em curso: (áudio, resultado)
            let mut spec: Option<(Vec<f32>, Result<Option<Done>>)> = None;
            let mut live = Live::default();
            let mut queue: std::collections::VecDeque<Job> = Default::default();
            let speak = |id: usize, src_words: &[String], tgt_words: &[String]| {
                if tgt_words.is_empty() {
                    return;
                }
                let (src_txt, tgt_txt) = (src_words.join(" "), tgt_words.join(" "));
                let _ = events.send(Event::Transcript { dir: dir.name.clone(), text: src_txt });
                let _ = events.send(Event::Translation { dir: dir.name.clone(), text: tgt_txt.clone() });
                let Some(voice) = &voice else { return };
                let scale = speech_length_scale(*backlog.lock().unwrap());
                match voice.synthesize(&tgt_txt, scale) {
                    Ok(pcm) if !pcm.is_empty() => {
                        *backlog.lock().unwrap() += pcm.len() as f32 / voice.sample_rate as f32;
                        let _ = play_tx.send((id, pcm, voice.sample_rate));
                    }
                    Ok(_) => {}
                    Err(e) => {
                        let _ = events.send(Event::Error { msg: format!("síntese de voz: {e:#}") });
                    }
                }
            };
            while !shared.stop.load(Ordering::Relaxed) {
                // o que chegou enquanto o trabalho anterior rodava vai para a fila
                while let Ok(j) = seg_rx.try_recv() {
                    queue.push_back(j);
                }
                let job = match queue.pop_front() {
                    Some(j) => j,
                    None => match seg_rx.recv_timeout(Duration::from_millis(200)) {
                        Ok(j) => j,
                        Err(RecvTimeoutError::Timeout) => continue,
                        Err(RecvTimeoutError::Disconnected) => break,
                    },
                };
                let (id, audio) = match job {
                    Job::Tentative(audio) => {
                        let r = work(&crate::vad::with_tail_silence(&audio));
                        spec = Some((audio, r));
                        continue;
                    }
                    Job::Partial(id, audio) => {
                        // releitura velha (já há outra mais nova ou o fim do trecho na fila): pula
                        if queue.iter().any(|j| matches!(j, Job::Partial(..) | Job::Final(..))) {
                            continue;
                        }
                        if live.id != id {
                            live = Live { id, ..Default::default() };
                        }
                        let words: Vec<String> = match asr.transcribe(&audio, &dir.src) {
                            Ok(t) => t.text.split_whitespace().map(String::from).collect(),
                            Err(e) => {
                                let _ = events.send(Event::Error { msg: format!("{e:#}") });
                                continue;
                            }
                        };
                        // acordo local: confirma o começo igual nesta leitura e na anterior
                        let agree = words.iter().zip(&live.previous).take_while(|(a, b)| norm_word(a) == norm_word(b)).count();
                        if agree > live.committed.len() {
                            live.committed = words[..agree].to_vec();
                        }
                        live.previous = words;
                        let new_src = live.committed.len().saturating_sub(live.src_spoken);
                        let pause = live.committed.last().map(|w| w.ends_with([',', '.', ';', ':', '?', '!'])).unwrap_or(false);
                        if new_src >= live_param("PRAXIS_PALAVRAS_MIN", LIVE_MIN_NEW_WORDS) || (new_src > 0 && pause) {
                            let all = match translator.continue_from(&live.committed.join(" "), &live.tgt_spoken, &dir.src, &dir.tgt) {
                                Ok(w) => w,
                                Err(e) => {
                                    let _ = events.send(Event::Error { msg: format!("{e:#}") });
                                    continue;
                                }
                            };
                            // tradução inventada (tamanho fora do normal): não fala, espera mais contexto
                            if !plausible(live.committed.len(), all.len(), &dir.src, &dir.tgt) {
                                continue;
                            }
                            let mut new_tgt: Vec<String> = all.get(live.tgt_spoken.len()..).unwrap_or(&[]).to_vec();
                            let sentence_end = live.committed.last().map(|w| crate::vad::sentence_complete(w)).unwrap_or(false);
                            if !sentence_end {
                                // as últimas palavras traduzidas ainda podem mudar: esperam
                                new_tgt.truncate(new_tgt.len().saturating_sub(live_param("PRAXIS_SEGURAR", LIVE_HOLD_BACK)));
                            }
                            // pedaço curto demais (a voz come palavras): espera juntar mais
                            let curto = !sentence_end && new_tgt.len() < live_param("PRAXIS_FALA_MIN", LIVE_MIN_SPOKEN);
                            if !new_tgt.is_empty() && !curto {
                                let src_part = live.committed[live.src_spoken..].to_vec();
                                speak(id, &src_part, &new_tgt);
                                live.src_spoken = live.committed.len();
                                live.tgt_spoken.extend(new_tgt);
                            }
                        }
                        continue;
                    }
                    Job::Final(id, audio) => (id, audio),
                };
                if dir.simultaneous {
                    // fim do trecho: o que faltou traduzir, continuando o que já foi falado
                    let _ = events.send(Event::Stage { dir: dir.name.clone(), id, stage: "transcrito".into(), at_s: shared.now_s() });
                    let spoken = if live.id == id { std::mem::take(&mut live.tgt_spoken) } else { vec![] };
                    let src_done = if live.id == id { live.src_spoken } else { 0 };
                    live = Live { id: id + 1, ..Default::default() };
                    let words: Vec<String> = match asr.transcribe(&audio, &dir.src) {
                        Ok(t) => t.text.split_whitespace().map(String::from).collect(),
                        Err(e) => {
                            let _ = events.send(Event::Error { msg: format!("{e:#}") });
                            continue;
                        }
                    };
                    if words.is_empty() {
                        continue;
                    }
                    // OmniVoice: o trecho que a pessoa acabou de falar vira a referência da voz
                    // (entonação e timbre do momento, como o Praxis antigo)
                    if let Some(o) = voice.as_ref().and_then(|v| v.omnivoice()) {
                        o.referencia_ao_vivo(&audio, &words.join(" "));
                    }
                    match translator.continue_from(&words.join(" "), &spoken, &dir.src, &dir.tgt) {
                        Ok(all) => {
                            let _ = events.send(Event::Stage { dir: dir.name.clone(), id, stage: "traduzido".into(), at_s: shared.now_s() });
                            let mut rest: Vec<String> = all.get(spoken.len()..).unwrap_or(&[]).to_vec();
                            let src_rest: Vec<String> = words.get(src_done.min(words.len())..).unwrap_or(&[]).to_vec();
                            // a continuação forçada não cobriu o que faltava do original (o tradutor
                            // deu a frase por terminada): traduz o resto sozinho em vez de perdê-lo
                            if !spoken.is_empty() && !plausible(src_rest.len(), rest.len(), &dir.src, &dir.tgt) {
                                if let Ok(t) = translator.translate(&src_rest.join(" "), &dir.src, &dir.tgt) {
                                    rest = t.split_whitespace().map(String::from).collect();
                                }
                            }
                            if std::env::var_os("PRAXIS_DEPURAR").is_some() {
                                eprintln!("[fim {id}] lido: {:?}\n  já dito ({src_done} palavras): {:?}\n  tradução inteira: {:?}\n  resto: {:?}", words, spoken, all, rest);
                            }
                            speak(id, &src_rest, &rest);
                            let _ = events.send(Event::Stage { dir: dir.name.clone(), id, stage: "voz".into(), at_s: shared.now_s() });
                        }
                        Err(e) => {
                            let _ = events.send(Event::Error { msg: format!("{e:#}") });
                        }
                    }
                    continue;
                }
                // o fim se confirmou: reaproveita o adiantado se o trecho é o mesmo
                let r = match spec.take() {
                    Some((t, r)) if crate::vad::reuse_ok(&t, &audio) => r,
                    _ => work(&audio),
                };
                let done = match r {
                    Ok(Some(d)) => d,
                    Ok(None) => continue,
                    Err(e) => {
                        let _ = events.send(Event::Error { msg: format!("{e:#}") });
                        continue; // um trecho com problema não pode derrubar a direção
                    }
                };
                for name in ["transcrito", "traduzido"] {
                    let _ = events.send(Event::Stage { dir: dir.name.clone(), id, stage: name.into(), at_s: shared.now_s() });
                }
                let _ = events.send(Event::Transcript { dir: dir.name.clone(), text: done.text.clone() });
                let _ = events.send(Event::Translation { dir: dir.name.clone(), text: done.translation.clone() });
                let Some(voice) = &voice else { continue };   // só legenda
                let send = |pcm: Vec<f32>| {
                    *backlog.lock().unwrap() += pcm.len() as f32 / voice.sample_rate as f32;
                    let _ = play_tx.send((id, pcm, voice.sample_rate));
                };
                if let Some(pcm) = done.first.filter(|p| !p.is_empty()) {
                    let _ = events.send(Event::Stage { dir: dir.name.clone(), id, stage: "voz".into(), at_s: shared.now_s() });
                    send(pcm);
                }
                // o resto, pedaço a pedaço: o primeiro já toca enquanto o próximo é sintetizado
                for sent in done.rest {
                    // a trava do atraso é solta antes de sintetizar: `send` a pega de novo
                    let scale = speech_length_scale(*backlog.lock().unwrap());
                    match voice.synthesize(&sent, scale) {
                        Ok(pcm) if !pcm.is_empty() => send(pcm),
                        Ok(_) => {}
                        Err(e) => {
                            let _ = events.send(Event::Error { msg: format!("síntese de voz: {e:#}") });
                        }
                    }
                }
            }
        }));
    }

    // 3. reprodução (em ordem, sem sobreposição)
    {
        let (shared, events, dir) = (shared.clone(), events.clone(), dir.clone());
        handles.push(std::thread::spawn(move || {
            while !shared.stop.load(Ordering::Relaxed) {
                let (id, pcm, sr) = match play_rx.recv_timeout(Duration::from_millis(200)) {
                    Ok(x) => x,
                    Err(RecvTimeoutError::Timeout) => continue,
                    Err(RecvTimeoutError::Disconnected) => break,
                };
                let dur = pcm.len() as f32 / sr as f32;
                let start = shared.now_s();
                if dir.to_speaker && dir.leaks && dir.leak_when.as_ref().is_none_or(|f| f.load(Ordering::Relaxed)) {
                    let until = ((start + dur + ECHO_TAIL_S) * 1000.0) as u64;
                    shared.speaker_busy_until_ms.fetch_max(until, Ordering::Relaxed);
                }
                let _ = events.send(Event::Play { dir: dir.name.clone(), id, start_s: start, dur_s: dur });
                speaker.play(&pcm, sr);
                let mut b = backlog.lock().unwrap();
                *b = (*b - dur).max(0.0);
            }
        }));
    }
    Ok(handles)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn traducao_inventada_e_recusada() {
        // o caso medido: 11 palavras em espanhol viraram 20 em inglês sem relação
        assert!(!plausible(11, 20, "es", "en"));
        assert!(plausible(11, 12, "es", "en"));
        // resto sem tradução nenhuma: refaz
        assert!(!plausible(20, 0, "es", "en"));
        // pedaço curto ou idioma sem espaços: sem conferência
        assert!(plausible(2, 5, "es", "en"));
        assert!(plausible(10, 1, "en", "ja"));
    }

    #[test]
    fn velocidade_adaptativa() {
        assert_eq!(speech_length_scale(0.5), 1.0);
        assert_eq!(speech_length_scale(1.0), 0.91);
        assert_eq!(speech_length_scale(3.0), 0.83);
        // nunca mais rápido que 1,2× (acelerar mais faz a voz comer palavras)
        assert_eq!(speech_length_scale(30.0), 0.83);
    }
}
