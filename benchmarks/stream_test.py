#!/usr/bin/env python3
"""Teste em tempo real: o Praxis acompanha um falante real falando sem parar?

Uma gravação de ~1 min de um falante real (fetch_continuous_speech.py) é
entregue aos workers REAIS do motor (vad_worker → pipeline_worker: Whisper →
Argos → Piper) em tempo real — blocos de 32 ms no ritmo em que chegariam de um
microfone. O teste conhece o texto de antemão e acompanha cada trecho que o
motor produz:

  precisão      taxa de erro de palavras/caracteres de tudo que o Whisper
                transcreveu em relação ao texto de referência; fidelidade da
                tradução (chrF, 0–100) de tradução(transcrição) vs
                tradução(referência) (quanto os erros de transcrição estragam
                a tradução que o ouvinte escuta)
  atraso        por trecho: fim daquela fala → transcrição / tradução /
                primeiro áudio traduzido
  acompanhar    o atraso cresce ao longo do minuto? quanto fica pendente quando
                o falante para (tempo para esvaziar a fila) — a fala traduzida é
                "tocada" pela sua duração real, exatamente como o motor fica
                bloqueado na reprodução

Uso:
  python benchmarks/stream_test.py --model small --device cpu --pairs pt:en en:pt es:en
Resultados: benchmarks/results/stream-<dispositivo>-<modelo>.json/.md
"""
from __future__ import annotations

import argparse
import json
import queue
import statistics
import sys
import threading
import time
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "benchmarks"))
import praxis  # noqa: E402
import praxis_platform as plat  # noqa: E402
import run_benchmarks as rb  # noqa: E402

DATA = ROOT / "benchmarks" / "data" / "continuous"
# Idiomas em que o limite das palavras é ambíguo (zh e ja não usam espaços; o
# coreano espaça de formas variadas): a métrica principal é o erro por letra.
CHAR_LANGS = {"zh", "ja", "ko"}
OUTPUT_LANGS = ["pt", "en", "es", "fr", "de", "it", "ru", "zh", "nl", "pl", "uk", "tr", "ar", "hi"]
INPUT_LANGS = OUTPUT_LANGS + ["ja", "ko"]


def voice_for(lang: str) -> str:
    """Voz Piper que o app escolheria para `lang` (melhor voz do catálogo), baixada uma vez."""
    import urllib.request
    import praxis_config as pc
    v = pc._best_catalog_voice(lang)
    if v is None:
        raise LookupError(f"nenhuma voz Piper para {lang}")
    rb.VOICES.mkdir(parents=True, exist_ok=True)
    dest = rb.VOICES / pc._catalog_filename(v)
    for ext in (".json", ""):
        f = Path(str(dest) + ext)
        if not f.exists():
            urllib.request.urlretrieve(pc._catalog_url(v, ext), f)
    return str(dest)
RESULTS = ROOT / "benchmarks" / "results"


class TimedBackend:
    """Grava o áudio traduzido; bloqueia pela duração real, como um alto-falante faria."""
    name = "stream-test"

    def __init__(self, clock, on_play=None) -> None:
        self.clock = clock
        self.on_play = on_play                         # simula a caixa de som vazando no microfone
        self.played: list[tuple[float, float]] = []      # (início, duração)

    def play_pcm_multi(self, pcm, rate, devices):
        dur = len(pcm) / 2 / rate
        start = self.clock()
        self.played.append((start, dur))
        if self.on_play:
            self.on_play(pcm, rate, start)
        time.sleep(dur)

    def teardown(self):
        pass


def chrf(hyp: str, ref: str) -> float:
    try:
        import sacrebleu
        return float(sacrebleu.sentence_chrf(hyp, [ref]).score)
    except ImportError:
        return float("nan")


def word_errors(ref: str, hyp: str, lang: str) -> dict:
    """Tipos de erro de transcrição + a maior sequência de palavras puladas
    (uma sequência ≥ 6 significa que uma frase inteira foi perdida)."""
    import jiwer
    r, h = rb.normalize(ref), rb.normalize(hyp) or "<empty>"
    if lang in CHAR_LANGS:                 # alinha caracteres, não "palavras"
        r, h = " ".join(r.replace(" ", "")), " ".join(h.replace(" ", ""))
    out = jiwer.process_words(r, h)
    deletes = [c.ref_end_idx - c.ref_start_idx for c in out.alignments[0] if c.type == "delete"]
    longest = max(deletes, default=0)
    rw = r.split()
    dropped = []
    for chunk in out.alignments[0]:
        if chunk.type == "delete" and chunk.ref_end_idx - chunk.ref_start_idx >= 6:
            dropped.append(" ".join(rw[chunk.ref_start_idx:chunk.ref_end_idx]))
    return {"reference_units": len(rw), "substituted": out.substitutions, "skipped": out.deletions,
            "invented": out.insertions, "longest_skipped_run": longest, "dropped_phrases": dropped}


def keeps_up(r: dict) -> bool:
    """Fica para trás = o atraso na segunda metade da fala é >1,5 s maior que
    na primeira, ou sobram >8 s de tradução quando o falante para, ou o atraso
    típico passa de 4 s (lento demais para uma conversa).
    (Uma inclinação sobre ~12 pontos marcava picos isolados como "ficar para
    trás".)"""
    pts = [(s["speech_end_s"], s["lat_audio_ms"]) for s in r.get("timeline", [])
           if s.get("lat_audio_ms") is not None and s.get("speech_end_s") is not None]
    if len(pts) < 2:
        return False
    half = r["speech_s"] / 2
    first = [v for t, v in pts if t <= half] or [pts[0][1]]
    second = [v for t, v in pts if t > half] or [pts[-1][1]]
    trend = statistics.median(second) - statistics.median(first)
    r["lag_trend_ms"] = round(trend, 0)
    typical = statistics.median(v for _, v in pts)
    # também inutilizável para conversa se o atraso típico passar de 4 s
    return trend <= 1500 and r["drain_s"] <= 8.0 and typical <= 4000


def findings(r: dict) -> list[str]:
    """Problemas em linguagem simples detectados em uma execução (pt-BR, para o relatório)."""
    f = []
    e, st, la = r["errors"], r["stage_ms_p50"], r["latency_audio_ms"]
    unit = "caracteres" if r["error_metric"] == "characters" else "palavras"
    if r["error_rate"] > 0.20:
        art = "dos" if unit == "caracteres" else "das"
        f.append(f"transcrição ruim: {r['error_rate']:.0%} {art} {unit} erradas")
    if e["dropped_phrases"]:
        f.append(f"pulou {len(e['dropped_phrases'])} trecho(s) inteiro(s) da fala "
                 f"(maior: {e['longest_skipped_run']} {unit} seguidas)")
    if e["invented"] > max(3, 0.05 * e["reference_units"]):
        f.append(f"inventou {e['invented']} {unit} que não foram faladas")
    if not r["keeps_up"]:
        f.append(f"não acompanha o falante: atraso típico {(r['latency_audio_ms']['p50'] or 0) / 1000:.1f} s, "
                 f"sobe {r.get('lag_trend_ms', 0) / 1000:+.1f} s da 1ª para a 2ª metade e sobram "
                 f"{r['drain_s']:.0f} s de tradução quando ele para")
    if st.get("queue_wait_ms") and st["queue_wait_ms"] > 500:
        f.append(f"trechos esperam {st['queue_wait_ms']:.0f} ms na fila antes de serem transcritos "
                 "(a transcrição é mais lenta que a fala)")
    if st.get("wait_for_speaker_ms") and st["wait_for_speaker_ms"] > 800:
        f.append(f"a tradução pronta espera {st['wait_for_speaker_ms']:.0f} ms a fala anterior terminar de tocar")
    if r["translated_speech_ratio"] > 0.95:
        f.append(f"a fala traduzida dura {r['translated_speech_ratio']:.0%} da original — "
                 "quase não sobra folga para acompanhar")
    if r["forced_cuts"] > 0:
        f.append(f"{r['forced_cuts']} trecho(s) cortado(s) no meio por excesso de duração sem pausa")
    if r["empty_segments"] > 0:
        f.append(f"{r['empty_segments']} trecho(s) com fala viraram texto vazio")
    if la.get("p95") and la["p95"] > 3000 and r["keeps_up"]:
        f.append(f"picos de atraso: 1 em cada 20 trechos demora mais de {la['p95'] / 1000:.1f} s")
    return f


ECHO_DB: float | None = None      # eco: volume (dB) com que a tradução tocada volta pelo microfone
ECHO_DELAY_S = 0.1


def run_stream(src: str, tgt: str, whisper, voice, verbose: bool = True) -> dict:
    meta = json.loads((DATA / f"{src}.json").read_text(encoding="utf-8"))
    audio, sr = sf.read(str(DATA / f"{src}.wav"), dtype="float32")
    assert sr == praxis.SR
    chunk = praxis.VAD_CHUNK
    n_chunks = len(audio) // chunk
    stream = audio[: n_chunks * chunk]
    silent_ref = not meta["text"].strip()               # silêncio/ruído: nada deveria ser traduzido
    tail_s = 8 if (ECHO_DB is not None or silent_ref) else 3
    tail = np.zeros(int(tail_s * praxis.SR) // chunk * chunk, np.float32)   # falante para
    feed = np.concatenate([stream, tail])

    # eco: o áudio traduzido volta pelo microfone (atenuado e um pouco atrasado)
    echo = np.zeros(len(feed) + 60 * praxis.SR, np.float32)
    echo_lock = threading.Lock()

    def on_play(pcm, rate, start):
        x = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768
        x = plat.resample(x, rate, praxis.SR) * (10 ** (ECHO_DB / 20))
        i = int((start + ECHO_DELAY_S) * praxis.SR)
        with echo_lock:
            j = min(len(echo), i + len(x))
            if i < j:
                echo[i:j] += x[:j - i]

    # bloco → índice no fluxo, montado conforme os blocos são entregues (com eco o
    # áudio entregue não é igual ao original), para localizar cada trecho emitido
    i16 = np.zeros(len(feed), np.int16)
    index: dict[bytes, list[int]] = {}
    fed = {"k": -1}                                      # último bloco entregue ao detector de fala

    def locate(item: np.ndarray) -> int | None:
        """Bloco do fluxo onde `item` começa: a ÚLTIMA correspondência completa
        que já tinha sido entregue (blocos de silêncio se repetem, então buscar
        só pelo primeiro bloco engana)."""
        n = len(item) // chunk
        for c in reversed(index.get(item[:chunk].tobytes(), [])):
            if c + n - 1 > fed["k"] + 1:
                continue
            if np.array_equal(i16[c * chunk:(c + n) * chunk], item[:n * chunk]):
                return c
        return None

    t0 = [0.0]
    clock = lambda: time.perf_counter() - t0[0]           # noqa: E731
    backend = TimedBackend(clock, on_play if ECHO_DB is not None else None)
    old = (praxis._backend, praxis._vmic, praxis._stop, praxis._emit,
           praxis.transcribe_segment, praxis.do_translate)
    praxis._backend = backend
    praxis._vmic = plat.VirtualMic(target="stream-test", mic_label="stream-test")
    stop = threading.Event()
    praxis._stop = stop
    praxis._piper_out_ref[0] = voice

    segs: list[dict] = []
    seg_q: "queue.Queue" = queue.Queue()
    audio_q: "queue.Queue" = queue.Queue()
    real_transcribe, real_translate = old[4], old[5]

    class SegQueue(queue.Queue):
        def put(self, item, *a, **k):                    # o detector de fala emite um trecho
            start_k = locate(item)
            x = item.astype(np.float32) / 32768
            env = np.array([np.sqrt(np.mean(x[i:i + chunk] ** 2))
                            for i in range(0, len(x) - chunk + 1, chunk)])
            voiced = np.nonzero(env > max(0.01, 0.1 * env.max()))[0] if len(env) else []
            last_voiced = (voiced[-1] + 1) * chunk if len(voiced) else len(item)
            speech_end = ((start_k * chunk + last_voiced) / praxis.SR) if start_k is not None else None
            segs.append({"emitted": clock(), "dur": len(item) / praxis.SR,
                         "start_s": None if start_k is None else start_k * chunk / praxis.SR,
                         "speech_end_s": speech_end})
            super().put(item, *a, **k)

    seg_q = SegQueue()
    cur = {"i": -1}

    def transcribe(w, a, lang, **kw):
        cur["i"] += 1
        s = segs[cur["i"]]
        s["asr_start"] = clock()
        text = real_transcribe(w, a, lang, **kw)
        s["asr_end"] = clock()
        s["text"] = text
        s["n_audio_before"] = len(backend.played)
        return text

    def translate(text, a, b):
        out = real_translate(text, a, b)
        s = segs[cur["i"]]
        s["mt_end"] = clock()
        s["translation"] = out
        return out

    class TimedVoice:
        """Mesma voz; registra quando a primeira frase de cada trecho é sintetizada."""
        def __init__(self, v):
            self.v, self.config = v, v.config

        def __getattr__(self, name):           # ex.: praxis_rate_scale (calibração da voz)
            return getattr(self.v, name)

        def synthesize(self, text, **kw):
            s = segs[cur["i"]]
            t = clock()
            first = True
            if kw.get("syn_config") is not None:
                s["sped_up"] = s.get("sped_up", 0) + 1     # a velocidade de fala adaptativa entrou em ação
            for c in self.v.synthesize(text, **kw):
                if first and "tts_first" not in s:
                    s["tts_first"] = clock()
                    s["tts_first_ms"] = (s["tts_first"] - t) * 1000
                first = False
                yield c

    voice = TimedVoice(voice)
    praxis._piper_out_ref[0] = voice
    praxis.transcribe_segment, praxis.do_translate = transcribe, translate
    praxis._emit = lambda d: None
    active = threading.Event()
    active.set()
    vad_t = threading.Thread(target=praxis.vad_worker, args=(audio_q, seg_q, "vad", 0.1),
                             kwargs={"active": active, "ptt_flush": threading.Event()}, daemon=True)
    pipe_t = threading.Thread(target=praxis.pipeline_worker,
                              args=(seg_q, whisper, voice, src, tgt, "out"), daemon=True)
    try:
        vad_t.start()
        pipe_t.start()
        time.sleep(0.5)                                   # modelo do detector de fala carregado
        t0[0] = time.perf_counter()
        for k in range(len(feed) // chunk):               # microfone em tempo real
            target = k * chunk / praxis.SR
            delay = target - clock()
            if delay > 0:
                time.sleep(delay)
            piece = feed[k * chunk:(k + 1) * chunk].copy()
            if ECHO_DB is not None:
                with echo_lock:
                    piece = np.clip(piece + echo[k * chunk:(k + 1) * chunk], -1, 1)
            q16 = (piece * 32767).clip(-32768, 32767).astype(np.int16)
            i16[k * chunk:(k + 1) * chunk] = q16
            index.setdefault(q16.tobytes(), []).append(k)
            fed["k"] = k
            audio_q.put(piece)
        speech_over = len(stream) / praxis.SR
        # espera a fila pendente esvaziar (máx. 120 s)
        deadline = time.perf_counter() + 120
        while time.perf_counter() < deadline:
            busy = (not seg_q.empty()) or (cur["i"] < len(segs) - 1) or \
                (backend.played and backend.played[-1][0] + backend.played[-1][1] > clock())
            if not busy:
                time.sleep(0.5)
                if not ((not seg_q.empty()) or (cur["i"] < len(segs) - 1)):
                    break
            time.sleep(0.05)
        finished = clock()
    finally:
        stop.set()
        vad_t.join(3)
        pipe_t.join(5)
        (praxis._backend, praxis._vmic, praxis._stop, praxis._emit,
         praxis.transcribe_segment, praxis.do_translate) = old

    # associa o primeiro áudio traduzido de cada trecho
    for i, s in enumerate(segs):
        k = s.get("n_audio_before")
        nxt = segs[i + 1].get("n_audio_before") if i + 1 < len(segs) else len(backend.played)
        if k is not None and k < len(backend.played) and (nxt is None or k < nxt):
            s["audio_start"] = backend.played[k][0]
        if s.get("speech_end_s") is not None:
            e = s["speech_end_s"]
            s["lat_transcript_ms"] = (s["asr_end"] - e) * 1000 if "asr_end" in s else None
            s["lat_translation_ms"] = (s["mt_end"] - e) * 1000 if "mt_end" in s else None
            s["lat_audio_ms"] = (s["audio_start"] - e) * 1000 if "audio_start" in s else None

    for s in segs:
        if "asr_start" in s:
            s["queue_wait_ms"] = (s["asr_start"] - s["emitted"]) * 1000          # esperando o worker
            s["asr_ms"] = (s["asr_end"] - s["asr_start"]) * 1000
        if "mt_end" in s:
            s["mt_ms"] = (s["mt_end"] - s["asr_end"]) * 1000
        if "audio_start" in s and "tts_first" in s:
            s["wait_for_speaker_ms"] = (s["audio_start"] - s["tts_first"]) * 1000  # fala anterior ainda tocando
        s["forced_cut"] = s["dur"] >= praxis.MAX_SEG_S - 0.05                       # cortado no meio da fala pelo limite

    hyp = " ".join(s.get("text", "") for s in segs if s.get("text"))
    after_speech = [s for s in segs if s.get("text") and s.get("start_s") is not None
                    and s["start_s"] >= speech_over - 0.2]
    if silent_ref:
        # Sem fala: tudo o que foi transcrito é inventado (ruído, silêncio, falatório)
        res = {"pair": f"{src}->{tgt}", "kind": "sem_fala", "speech_s": round(speech_over, 1),
               "segments": len(segs), "invented_words": len(hyp.split()),
               "invented_text": hyp, "translation": " ".join(s.get("translation", "") for s in segs),
               "timeline": [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in s.items()}
                            for s in segs]}
        if verbose:
            print(f"  {res['pair']} (sem fala): {res['invented_words']} palavras inventadas: "
                  f"{hyp[:120]!r}", file=sys.stderr)
        return res
    wer, cer = rb.wer_cer([meta["text"]], [hyp])
    errors = word_errors(meta["text"], hyp, src)
    tr_hyp = " ".join(s.get("translation", "") for s in segs if s.get("translation"))
    tr_ref = praxis.do_translate(meta["text"], src, tgt)
    lats = [s["lat_audio_ms"] for s in segs if s.get("lat_audio_ms") is not None]
    ends = [s["speech_end_s"] for s in segs if s.get("lat_audio_ms") is not None]
    slope = float(np.polyfit(ends, lats, 1)[0]) if len(lats) >= 3 else float("nan")  # ms de atraso por s
    last_audio_end = max((st + d for st, d in backend.played), default=finished)
    stage = {k: round(statistics.median([s[k] for s in segs if s.get(k) is not None]), 0)
             if any(s.get(k) is not None for s in segs) else None
             for k in ("queue_wait_ms", "asr_ms", "mt_ms", "tts_first_ms", "wait_for_speaker_ms")}
    tts_ratio = sum(d for _, d in backend.played) / speech_over if speech_over else float("nan")
    res = {
        "pair": f"{src}->{tgt}", "speaker": meta["speaker"], "speech_s": round(speech_over, 1),
        "words": len(meta["text"].split()), "segments": len(segs),
        "wer": round(wer, 4), "cer": round(cer, 4),
        "letter_error_rate": round(rb.letter_error(meta["text"], hyp), 4),
        "error_rate": round(rb.letter_error(meta["text"], hyp) if src in CHAR_LANGS else wer, 4),
        "error_metric": "characters" if src in CHAR_LANGS else "words",
        "errors": errors,
        "stage_ms_p50": stage,
        "translated_speech_ratio": round(tts_ratio, 2),
        "forced_cuts": sum(1 for s in segs if s["forced_cut"]),
        "empty_segments": sum(1 for s in segs if "text" in s and not s["text"]),
        "sped_up_sentences": sum(s.get("sped_up", 0) for s in segs),
        "echo_segments": len(after_speech) if ECHO_DB is not None else None,
        "echo_words": sum(len(s["text"].split()) for s in after_speech) if ECHO_DB is not None else None,
        "translation_chrf": round(chrf(tr_hyp, tr_ref), 1),
        "latency_audio_ms": {"p50": round(statistics.median(lats), 0) if lats else None,
                             "p95": round(rb.pct(lats, 0.95), 0) if lats else None,
                             "max": round(max(lats), 0) if lats else None},
        "lag_slope_ms_per_s": round(slope, 1),
        "drain_s": round(max(0.0, last_audio_end - speech_over), 2),
        "translated_audio_s": round(sum(d for _, d in backend.played), 1),
        "keeps_up": False,                      # definido abaixo por keeps_up()
        "reference": meta["text"], "transcript": hyp,
        "translation": tr_hyp, "translation_of_reference": tr_ref,
        "timeline": [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in s.items()}
                     for s in segs],
    }
    res["keeps_up"] = keeps_up(res)
    res["findings"] = findings(res)
    if verbose:
        unit = "caracteres" if res["error_metric"] == "characters" else "palavras"
        print(f"  {res['pair']}: erro {res['error_rate']:.1%} ({unit}) | fidelidade da tradução {res['translation_chrf']} | "
              f"atraso típico {res['latency_audio_ms']['p50']} ms, máx. {res['latency_audio_ms']['max']} ms | "
              f"crescimento do atraso {res['lag_slope_ms_per_s']} ms/s | pendente ao final {res['drain_s']} s | "
              f"{'ACOMPANHA' if res['keeps_up'] else 'FICA PARA TRÁS'}", file=sys.stderr)
    return res


ERROR_NAMES = {"no recording": "sem gravação"}   # valores de "error" guardados no JSON


def to_markdown(rep: dict) -> str:
    m = rep["machine"]
    out = [rb.machine_line(m, cores=False), "",
           f"Whisper `{rep['model']}` rodando em: {rb.where(rep['backend'])} — ~1 min de fala real contínua "
           "por par, entregue em tempo real", "",
           "| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | "
           "Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | "
           "Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    sem_fala = [r for r in rep["results"] if r.get("kind") == "sem_fala"]
    rep = dict(rep, results=[r for r in rep["results"] if r.get("kind") != "sem_fala"])
    for r in rep["results"]:
        if "error" in r and "latency_audio_ms" not in r:
            out.append(f"| {r['pair']} | — | — | — | — | — | — | — | — | — | ⚠️ {ERROR_NAMES.get(r['error'], r['error'])} |")
            continue
        la = r["latency_audio_ms"]
        unit = "caracteres" if r["error_metric"] == "characters" else "palavras"
        out.append(f"| {r['pair']} | {r['speech_s']:.0f}s | {r['error_rate']:.1%} {unit} | "
                   f"{r.get('letter_error_rate', float('nan')):.1%} | {r['translation_chrf']} | "
                   f"{(la['p50'] or 0) / 1000:.1f} s | {(la['p95'] or 0) / 1000:.1f} s | "
                   f"{r.get('lag_trend_ms', 0) / 1000:+.1f} s | {r['drain_s']:.1f} s | "
                   f"{r['translated_speech_ratio']:.0%} | {'✅' if r['keeps_up'] else '❌'} |")
    if sem_fala:
        out += ["", "### Sem fala (silêncio, ruído, falatório): nada deveria ser traduzido", "",
                "| Caso | Duração | Palavras inventadas | Texto inventado |", "|---|---:|---:|---|"]
        for r in sem_fala:
            out.append(f"| {r['pair']} | {r['speech_s']:.0f}s | {r['invented_words']} | {r['invented_text'][:80]} |")
    echo_rows = [r for r in rep["results"] if r.get("echo_segments") is not None]
    if echo_rows:
        out += ["", "### Eco (a tradução tocada volta pelo microfone)", "",
                "| Par | Trechos traduzidos depois que o falante parou | Palavras nesses trechos |", "|---|---:|---:|"]
        for r in echo_rows:
            out.append(f"| {r['pair']} | {r['echo_segments']} | {r['echo_words']} |")
    out += ["", "### Para onde vai o tempo (típico, por trecho)", "",
            "| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |",
            "|---|---:|---:|---:|---:|---:|"]
    for r in rep["results"]:
        st = r.get("stage_ms_p50")
        if not st:
            continue
        fmt = lambda v: "—" if v is None else f"{v:.0f} ms"  # noqa: E731
        out.append(f"| {r['pair']} | {fmt(st['queue_wait_ms'])} | {fmt(st['asr_ms'])} | {fmt(st['mt_ms'])} | "
                   f"{fmt(st['tts_first_ms'])} | {fmt(st['wait_for_speaker_ms'])} |")
    out += ["", "### Problemas encontrados", ""]
    for r in rep["results"]:
        fs = r.get("findings") or []
        out.append(f"- **{r['pair']}**: " + ("; ".join(fs) if fs else "nenhum problema detectado"))
    out += ["", "Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou "
            "inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução "
            "do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio "
            "traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em "
            "cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo."]
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="small")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--pairs", nargs="+", default=None,
                    help="lista origem:destino; padrão = cada idioma de entrada → en (en → pt)")
    ap.add_argument("--output-langs", action="store_true",
                    help="testa en → cada idioma de saída (tradução + voz de cada idioma)")
    ap.add_argument("--eco", type=float, default=None, metavar="DB",
                    help="simula eco: a tradução tocada volta pelo microfone com este volume (ex.: -12)")
    ap.add_argument("--contexto", action="store_true",
                    help="liga o contexto entre trechos (o fim do que já foi dito vai como dica ao Whisper)")
    ap.add_argument("--data-dir", default=None,
                    help="pasta com <idioma>.wav/.json (padrão: benchmarks/data/continuous)")
    ap.add_argument("--name", default=None)
    a = ap.parse_args()
    global DATA, ECHO_DB
    if a.data_dir:
        DATA = Path(a.data_dir)
    ECHO_DB = a.eco
    praxis.USE_CONTEXT = bool(a.contexto)
    whisper = praxis.load_whisper(a.model, a.device)
    backend = getattr(whisper, "backend", a.device)
    rep = {"kind": "stream", "model": a.model, "backend": backend,
           "machine": rb.machine_info(), "results": []}
    if a.pairs:
        pairs = [tuple(p.split(":")) for p in a.pairs]
    elif a.output_langs:
        pairs = [("en", t) for t in OUTPUT_LANGS if t != "en"]
    else:
        pairs = [(s_, "pt" if s_ == "en" else "en") for s_ in INPUT_LANGS]
    for src, tgt in pairs:
        if not (DATA / f"{src}.json").exists():
            rep["results"].append({"pair": f"{src}->{tgt}", "error": "no recording"})
            continue
        try:
            praxis.setup_argos(src, tgt)
            voice = praxis.load_piper(voice_for(tgt))
            praxis.do_translate("warm up.", src, tgt)
            next(iter(voice.synthesize("warm up.")))
            rep["results"].append(run_stream(src, tgt, whisper, voice))
        except Exception as e:                      # um idioma com problema não pode parar a execução
            import traceback
            traceback.print_exc()
            rep["results"].append({"pair": f"{src}->{tgt}", "error": f"{type(e).__name__}: {e}"})
        save_report(rep, a, backend)


def save_report(rep: dict, a, backend: str) -> None:
    name = a.name or f"stream-{backend}-{a.model}" + ("-out" if a.output_langs else "")
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"{name}.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False,
                                                         default=lambda o: o.item() if hasattr(o, "item") else str(o)), encoding="utf-8")
    (RESULTS / f"{name}.md").write_text(to_markdown(rep), encoding="utf-8")
    print(to_markdown(rep))


if __name__ == "__main__":
    main()
