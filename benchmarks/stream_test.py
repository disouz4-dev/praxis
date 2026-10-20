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

    hyp = " ".join(s.get("text", "") for s in segs if s.get("text"))
    wer, cer = rb.wer_cer([meta["text"]], [hyp])
    tr_hyp = " ".join(s.get("translation", "") for s in segs if s.get("translation"))
    tr_ref = praxis.do_translate(meta["text"], src, tgt)
    lats = [s["lat_audio_ms"] for s in segs if s.get("lat_audio_ms") is not None]
    ends = [s["speech_end_s"] for s in segs if s.get("lat_audio_ms") is not None]
    slope = float(np.polyfit(ends, lats, 1)[0]) if len(lats) >= 3 else float("nan")  # ms of lag per s
    last_audio_end = max((st + d for st, d in backend.played), default=finished)
    res = {
        "pair": f"{src}->{tgt}", "speaker": meta["speaker"], "speech_s": round(speech_over, 1),
        "words": len(meta["text"].split()), "segments": len(segs),
        "wer": round(wer, 4), "cer": round(cer, 4),
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
    if verbose:
        print(f"  {res['pair']}: WER {wer:.1%} | chrF {res['translation_chrf']} | "
              f"latency p50 {res['latency_audio_ms']['p50']} ms max {res['latency_audio_ms']['max']} ms | "
              f"lag slope {res['lag_slope_ms_per_s']} ms/s | drain {res['drain_s']} s | "
              f"{'KEEPS UP' if res['keeps_up'] else 'FALLS BEHIND'}", file=sys.stderr)
    return res


def to_markdown(rep: dict) -> str:
    m = rep["machine"]
    out = [f"_Machine: {m['os']} · {m['cpu']} · Python {m['python']} · CUDA {m['cuda']}_", "",
           f"Whisper `{rep['model']}` on `{rep['backend']}` — ~1 min of continuous real speech per pair, fed in real time", "",
           "| Pair | Speech | WER | chrF (translation) | Latency p50 | p95 | max | Lag drift | Drain after speaker stops | Keeps up |",
           "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for r in rep["results"]:
        la = r["latency_audio_ms"]
        out.append(f"| {r['pair']} | {r['speech_s']:.0f}s | {r['wer']:.1%} | {r['translation_chrf']} | "
                   f"{la['p50']:.0f} ms | {la['p95']:.0f} ms | {la['max']:.0f} ms | "
                   f"{r['lag_slope_ms_per_s']:+.0f} ms/s | {r['drain_s']:.1f} s | "
                   f"{'✅' if r['keeps_up'] else '❌'} |")
    out += ["", "Latency = end of each speech segment → first translated audio. Lag drift = slope of latency "
            "over the minute (≈0 means it keeps pace; positive means it falls further behind). "
            "chrF compares the translation of what Whisper heard with the translation of the true script (100 = identical)."]
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="small")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--pairs", nargs="+", default=["pt:en", "en:pt", "es:en"])
    ap.add_argument("--name", default=None)
    a = ap.parse_args()
    whisper = praxis.load_whisper(a.model, a.device)
    backend = getattr(whisper, "backend", a.device)
    rep = {"kind": "stream", "model": a.model, "backend": backend,
           "machine": rb.machine_info(), "results": []}
    for pair in a.pairs:
        src, tgt = pair.split(":")
        praxis.setup_argos(src, tgt)
        voice = praxis.load_piper(rb.ensure_piper_voice(tgt))
        praxis.do_translate("warm up.", src, tgt)
        next(iter(voice.synthesize("warm up.")))
        rep["results"].append(run_stream(src, tgt, whisper, voice))
    name = a.name or f"stream-{backend}-{a.model}"
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"{name}.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False,
                                                         default=lambda o: o.item() if hasattr(o, "item") else str(o)), encoding="utf-8")
    (RESULTS / f"{name}.md").write_text(to_markdown(rep), encoding="utf-8")
    print(to_markdown(rep))


if __name__ == "__main__":
    main()
