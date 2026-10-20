#!/usr/bin/env python3
"""Real-time test: can Praxis keep up with a real speaker talking continuously?

A ~1 min recording of one real speaker (fetch_continuous_speech.py) is fed to
the REAL engine workers (vad_worker → pipeline_worker: Whisper → Argos → Piper)
in real time — 32 ms chunks at the pace they would arrive from a microphone.
The test knows the script in advance and monitors every segment the engine
produces:

  accuracy   WER/CER of everything Whisper transcribed vs the reference text;
             translation chrF of MT(transcript) vs MT(reference) (how much the
             ASR errors hurt the translation the listener hears)
  latency    per segment: end of that speech → transcript / translation /
             first translated audio
  keep-up    does the lag grow over the minute? backlog when the speaker stops
             (drain time) — translated speech is "played" for its real
             duration, exactly like the engine blocks on playback

Usage:
  python benchmarks/stream_test.py --model small --device cpu --pairs pt:en en:pt es:en
Results: benchmarks/results/stream-<device>-<model>.json/.md
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
CHAR_LANGS = {"zh", "ja"}          # no spaces between words → character error rate is the metric
OUTPUT_LANGS = ["pt", "en", "es", "fr", "de", "it", "ru", "zh", "nl", "pl", "uk", "tr", "ar", "hi"]
INPUT_LANGS = OUTPUT_LANGS + ["ja", "ko"]


def voice_for(lang: str) -> str:
    """Piper voice the app would pick for `lang` (best catalog voice), downloaded once."""
    import urllib.request
    import praxis_config as pc
    v = pc._best_catalog_voice(lang)
    if v is None:
        raise LookupError(f"no Piper voice for {lang}")
    rb.VOICES.mkdir(parents=True, exist_ok=True)
    dest = rb.VOICES / pc._catalog_filename(v)
    for ext in (".json", ""):
        f = Path(str(dest) + ext)
        if not f.exists():
            urllib.request.urlretrieve(pc._catalog_url(v, ext), f)
    return str(dest)
RESULTS = ROOT / "benchmarks" / "results"


class TimedBackend:
    """Records translated audio; blocks for its real duration like a speaker would."""
    name = "stream-test"

    def __init__(self, clock) -> None:
        self.clock = clock
        self.played: list[tuple[float, float]] = []      # (start, duration)

    def play_pcm_multi(self, pcm, rate, devices):
        dur = len(pcm) / 2 / rate
        self.played.append((self.clock(), dur))
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
    """Kinds of transcription errors + the longest run of skipped words
    (a run ≥ 6 means a whole phrase was dropped)."""
    import jiwer
    r, h = rb.normalize(ref), rb.normalize(hyp) or "<empty>"
    if lang in CHAR_LANGS:                 # align characters, not "words"
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


def findings(r: dict) -> list[str]:
    """Plain-language problems detected in one run (pt-BR, for the report)."""
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
        f.append(f"não acompanha o falante: o atraso cresce {r['lag_slope_ms_per_s']:+.0f} ms a cada segundo "
                 f"e sobram {r['drain_s']:.0f} s de tradução quando ele para")
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


def run_stream(src: str, tgt: str, whisper, voice, verbose: bool = True) -> dict:
    meta = json.loads((DATA / f"{src}.json").read_text(encoding="utf-8"))
    audio, sr = sf.read(str(DATA / f"{src}.wav"), dtype="float32")
    assert sr == praxis.SR
    chunk = praxis.VAD_CHUNK
    n_chunks = len(audio) // chunk
    stream = audio[: n_chunks * chunk]
    tail = np.zeros(int(3 * praxis.SR) // chunk * chunk, np.float32)   # speaker stops: 3 s silence
    feed = np.concatenate([stream, tail])

    # chunk → stream index, to locate every emitted segment exactly
    i16 = (feed * 32767).clip(-32768, 32767).astype(np.int16)
    index: dict[bytes, list[int]] = {}
    for k in range(len(feed) // chunk):
        index.setdefault(i16[k * chunk:(k + 1) * chunk].tobytes(), []).append(k)
    fed = {"k": -1}                                      # last chunk handed to the VAD

    def locate(item: np.ndarray) -> int | None:
        """Stream chunk where `item` starts: the LATEST full match that had
        already been fed (silent chunks repeat, so first-chunk lookups lie)."""
        n = len(item) // chunk
        for c in reversed(index.get(item[:chunk].tobytes(), [])):
            if c + n - 1 > fed["k"] + 1:
                continue
            if np.array_equal(i16[c * chunk:(c + n) * chunk], item[:n * chunk]):
                return c
        return None

    t0 = [0.0]
    clock = lambda: time.perf_counter() - t0[0]           # noqa: E731
    backend = TimedBackend(clock)
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
        def put(self, item, *a, **k):                    # VAD emits a segment
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

    def transcribe(w, a, lang):
        cur["i"] += 1
        s = segs[cur["i"]]
        s["asr_start"] = clock()
        text = real_transcribe(w, a, lang)
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
        """Same voice; records when the first sentence of each segment is synthesized."""
        def __init__(self, v):
            self.v, self.config = v, v.config

        def __getattr__(self, name):           # e.g. praxis_rate_scale (voice calibration)
            return getattr(self.v, name)

        def synthesize(self, text, **kw):
            s = segs[cur["i"]]
            t = clock()
            first = True
            if kw.get("syn_config") is not None:
                s["sped_up"] = s.get("sped_up", 0) + 1     # adaptive speaking rate kicked in
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
        time.sleep(0.5)                                   # VAD model loaded
        t0[0] = time.perf_counter()
        for k in range(len(feed) // chunk):               # real-time microphone
            target = k * chunk / praxis.SR
            delay = target - clock()
            if delay > 0:
                time.sleep(delay)
            fed["k"] = k
            audio_q.put(feed[k * chunk:(k + 1) * chunk].copy())
        speech_over = len(stream) / praxis.SR
        # wait for the backlog to drain (max 120 s)
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

    # attach first translated audio of each segment
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
            s["queue_wait_ms"] = (s["asr_start"] - s["emitted"]) * 1000          # waiting for the worker
            s["asr_ms"] = (s["asr_end"] - s["asr_start"]) * 1000
        if "mt_end" in s:
            s["mt_ms"] = (s["mt_end"] - s["asr_end"]) * 1000
        if "audio_start" in s and "tts_first" in s:
            s["wait_for_speaker_ms"] = (s["audio_start"] - s["tts_first"]) * 1000  # previous speech still playing
        s["forced_cut"] = s["dur"] >= praxis.MAX_SEG_S - 0.05                       # cut mid-speech by the limit

    hyp = " ".join(s.get("text", "") for s in segs if s.get("text"))
    wer, cer = rb.wer_cer([meta["text"]], [hyp])
    errors = word_errors(meta["text"], hyp, src)
    tr_hyp = " ".join(s.get("translation", "") for s in segs if s.get("translation"))
    tr_ref = praxis.do_translate(meta["text"], src, tgt)
    lats = [s["lat_audio_ms"] for s in segs if s.get("lat_audio_ms") is not None]
    ends = [s["speech_end_s"] for s in segs if s.get("lat_audio_ms") is not None]
    slope = float(np.polyfit(ends, lats, 1)[0]) if len(lats) >= 3 else float("nan")  # ms of lag per s
    last_audio_end = max((st + d for st, d in backend.played), default=finished)
    stage = {k: round(statistics.median([s[k] for s in segs if s.get(k) is not None]), 0)
             if any(s.get(k) is not None for s in segs) else None
             for k in ("queue_wait_ms", "asr_ms", "mt_ms", "tts_first_ms", "wait_for_speaker_ms")}
    tts_ratio = sum(d for _, d in backend.played) / speech_over if speech_over else float("nan")
    res = {
        "pair": f"{src}->{tgt}", "speaker": meta["speaker"], "speech_s": round(speech_over, 1),
        "words": len(meta["text"].split()), "segments": len(segs),
        "wer": round(wer, 4), "cer": round(cer, 4),
        "error_rate": round(cer if src in CHAR_LANGS else wer, 4),
        "error_metric": "characters" if src in CHAR_LANGS else "words",
        "errors": errors,
        "stage_ms_p50": stage,
        "translated_speech_ratio": round(tts_ratio, 2),
        "forced_cuts": sum(1 for s in segs if s["forced_cut"]),
        "empty_segments": sum(1 for s in segs if "text" in s and not s["text"]),
        "sped_up_sentences": sum(s.get("sped_up", 0) for s in segs),
        "translation_chrf": round(chrf(tr_hyp, tr_ref), 1),
        "latency_audio_ms": {"p50": round(statistics.median(lats), 0) if lats else None,
                             "p95": round(rb.pct(lats, 0.95), 0) if lats else None,
                             "max": round(max(lats), 0) if lats else None},
        "lag_slope_ms_per_s": round(slope, 1),
        "drain_s": round(max(0.0, last_audio_end - speech_over), 2),
        "translated_audio_s": round(sum(d for _, d in backend.played), 1),
        "keeps_up": bool(lats and slope < 15 and max(lats) < 6000),
        "reference": meta["text"], "transcript": hyp,
        "translation": tr_hyp, "translation_of_reference": tr_ref,
        "timeline": [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in s.items()}
                     for s in segs],
    }
    res["findings"] = findings(res)
    if verbose:
        print(f"  {res['pair']}: error {res['error_rate']:.1%} ({res['error_metric']}) | chrF {res['translation_chrf']} | "
              f"latency p50 {res['latency_audio_ms']['p50']} ms max {res['latency_audio_ms']['max']} ms | "
              f"lag slope {res['lag_slope_ms_per_s']} ms/s | drain {res['drain_s']} s | "
              f"{'KEEPS UP' if res['keeps_up'] else 'FALLS BEHIND'}", file=sys.stderr)
    return res


def to_markdown(rep: dict) -> str:
    m = rep["machine"]
    out = [f"_Machine: {m['os']} · {m['cpu']} · Python {m['python']} · CUDA {m['cuda']}_", "",
           f"Whisper `{rep['model']}` on `{rep['backend']}` — ~1 min of continuous real speech per pair, "
           "fed in real time", "",
           "| Pair | Speech | Error rate | Translation fidelity (0–100) | Typical latency | 1-in-20 worst | "
           "Lag growth | Backlog when speaker stops | Translated / original speech | Keeps up |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for r in rep["results"]:
        if "error" in r and "latency_audio_ms" not in r:
            out.append(f"| {r['pair']} | — | — | — | — | — | — | — | — | ⚠️ {r['error']} |")
            continue
        la = r["latency_audio_ms"]
        unit = "chars" if r["error_metric"] == "characters" else "words"
        out.append(f"| {r['pair']} | {r['speech_s']:.0f}s | {r['error_rate']:.1%} {unit} | {r['translation_chrf']} | "
                   f"{(la['p50'] or 0) / 1000:.1f} s | {(la['p95'] or 0) / 1000:.1f} s | "
                   f"{r['lag_slope_ms_per_s']:+.0f} ms/s | {r['drain_s']:.1f} s | "
                   f"{r['translated_speech_ratio']:.0%} | {'✅' if r['keeps_up'] else '❌'} |")
    out += ["", "### Where the time goes (typical, per segment)", "",
            "| Pair | Waiting in queue | Transcription | Translation | Voice (1st sentence) | Waiting for previous speech |",
            "|---|---:|---:|---:|---:|---:|"]
    for r in rep["results"]:
        st = r.get("stage_ms_p50")
        if not st:
            continue
        fmt = lambda v: "—" if v is None else f"{v:.0f} ms"  # noqa: E731
        out.append(f"| {r['pair']} | {fmt(st['queue_wait_ms'])} | {fmt(st['asr_ms'])} | {fmt(st['mt_ms'])} | "
                   f"{fmt(st['tts_first_ms'])} | {fmt(st['wait_for_speaker_ms'])} |")
    out += ["", "### Problems found", ""]
    for r in rep["results"]:
        fs = r.get("findings") or []
        out.append(f"- **{r['pair']}**: " + ("; ".join(fs) if fs else "nenhum problema detectado"))
    out += ["", "Error rate = share of words (characters for zh/ja) transcribed wrong, skipped or invented. "
            "Translation fidelity compares the translation of what was heard with the translation of the true "
            "script. Latency = end of a speech segment → first translated audio. Lag growth ≈ 0 means it keeps pace."]
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="small")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--pairs", nargs="+", default=None,
                    help="src:tgt list; default = every input language → en (en → pt)")
    ap.add_argument("--output-langs", action="store_true",
                    help="test en → every output language (translation + voice of each language)")
    ap.add_argument("--name", default=None)
    a = ap.parse_args()
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
        except Exception as e:                      # one broken language must not stop the run
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
