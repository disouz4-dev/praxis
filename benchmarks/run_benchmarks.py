#!/usr/bin/env python3
"""Praxis benchmarks on real human speech (see fetch_speech_corpus.py).

  asr      Transcription quality (WER / CER) per language and Whisper model,
           in two modes:
             full  — the whole utterance in one call (upper bound)
             live  — the audio is streamed through the engine's real
                     vad_worker (Silero VAD + MAX_SEG_S forced cuts), each
                     segment transcribed separately and joined — exactly what
                     happens during a call.
  latency  End-of-speech → first translated audio, per stage:
             VAD tail (silence needed to close a segment)
             ASR (Whisper)   MT (Argos)   TTS first sentence (Piper)

Every number comes from the production code paths in praxis.py
(transcribe_segment, vad_worker, do_translate, load_piper).

Usage:
  python benchmarks/run_benchmarks.py asr --models tiny base small --langs pt en es
  python benchmarks/run_benchmarks.py latency --model small --pairs pt:en en:pt es:en
Results: benchmarks/results/<name>.json + .md
"""
from __future__ import annotations

import argparse
import json
import platform
import queue
import re
import statistics
import sys
import threading
import time
import unicodedata
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import praxis  # noqa: E402

DATA = Path(__file__).resolve().parent / "data" / "speech"
RESULTS = Path(__file__).resolve().parent / "results"
VOICES = Path(__file__).resolve().parent / "data" / "voices"

PIPER_VOICES = {   # lang → (locale, speaker, quality)
    "en": ("en_US", "lessac", "medium"),
    "pt": ("pt_BR", "faber", "medium"),
    "es": ("es_ES", "sharvard", "medium"),
}


# ── text normalisation + metrics ──────────────────────────────────────────────

_ARABIC_TASHKEEL = re.compile("[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")


def normalize(text: str) -> str:
    """Lowercase, drop punctuation/symbols, collapse spaces — WITHOUT breaking
    words of scripts that use combining marks (Hindi vowel signs, Thai…).

    Arabic optional vowel marks (tashkeel) are removed and alef/yeh variants
    unified, as references include them but speech recognisers do not.
    Accents are kept (they distinguish words in pt/es/fr)."""
    t = unicodedata.normalize("NFKC", text).lower()
    t = t.replace("’", "'").replace("œ", "oe").replace("æ", "ae")
    t = _ARABIC_TASHKEEL.sub("", t)
    t = re.sub("[إأآٱ]", "ا", t).replace("ى", "ي")
    # punctuation (P*) and symbols (S*) become spaces; marks (M*) stay attached
    t = "".join(" " if unicodedata.category(ch)[0] in "PS" else ch for ch in t)
    return re.sub(r"\s+", " ", t).strip()


def wer_cer(refs: list[str], hyps: list[str]) -> tuple[float, float]:
    import jiwer
    r = [normalize(x) for x in refs]
    h = [normalize(x) or "<empty>" for x in hyps]
    return float(jiwer.wer(r, h)), float(jiwer.cer(r, h))


def load_corpus(lang: str) -> list[dict]:
    mf = DATA / lang / "manifest.json"
    if not mf.exists():
        return []
    items = json.loads(mf.read_text(encoding="utf-8"))
    for it in items:
        it["path"] = DATA / lang / it["file"]
    return [it for it in items if it["path"].exists()]


def read16k(path: Path) -> np.ndarray:
    a, sr = sf.read(str(path), dtype="float32", always_2d=True)
    a = a.mean(axis=1)
    assert sr == 16000, f"{path}: expected 16 kHz, got {sr}"
    return a


# ── live segmentation through the real vad_worker ─────────────────────────────

SEG_KW: dict = {}   # vad_worker overrides for experiments (max_seg_s, smart_cut, preroll_s)


def live_segments(audio: np.ndarray, trailing_silence_s: float = 0.6) -> list[np.ndarray]:
    """Feeds audio chunk-by-chunk through praxis.vad_worker (Silero VAD,
    production thresholds) and returns the int16 segments it emits."""
    chunk = praxis.VAD_CHUNK
    pad = np.zeros(int(trailing_silence_s * praxis.SR), np.float32)
    x = np.concatenate([audio, pad])
    audio_q: queue.Queue = queue.Queue()
    seg_q: queue.Queue = queue.Queue()
    stop = threading.Event()
    active = threading.Event()
    active.set()
    old_stop = praxis._stop
    praxis._stop = stop
    try:
        t = threading.Thread(target=praxis.vad_worker, args=(audio_q, seg_q, "vad", 0.1),
                             kwargs={"active": active, "ptt_flush": threading.Event(), **SEG_KW},
                             daemon=True)
        t.start()
        for i in range(0, len(x) - chunk + 1, chunk):
            audio_q.put(x[i:i + chunk].copy())
        while not audio_q.empty():
            time.sleep(0.01)
        time.sleep(0.3)
        stop.set()
        t.join(5)
    finally:
        praxis._stop = old_stop
    segs = []
    while not seg_q.empty():
        segs.append(seg_q.get())
    return segs


def vad_tail_ms(audio: np.ndarray) -> float | None:
    """Time between the last chunk the VAD scores as speech and the moment it
    emits "end" — the unavoidable 'wait for silence' part of the latency."""
    vad = praxis.OnnxSileroVAD(threshold=0.5, sampling_rate=praxis.SR,
                               min_silence_duration_ms=praxis.SILENCE_MS)
    chunk = praxis.VAD_CHUNK
    x = np.concatenate([audio, np.zeros(praxis.SR, np.float32)])
    last_speech = None
    end_at = None
    for i in range(0, len(x) - chunk + 1, chunk):
        piece = x[i:i + chunk]
        p = vad.prob(piece)
        if p >= vad.threshold:
            last_speech = (i + chunk) / praxis.SR
        # replay through the iterator logic without re-running the model
        vad.current_sample += chunk
        if p >= vad.threshold and vad.temp_end:
            vad.temp_end = 0
        if p >= vad.threshold and not vad.triggered:
            vad.triggered = True
        elif p < vad.threshold - 0.15 and vad.triggered:
            if not vad.temp_end:
                vad.temp_end = vad.current_sample
            if vad.current_sample - vad.temp_end >= vad.min_silence:
                vad.triggered, vad.temp_end = False, 0
                end_at = (i + chunk) / praxis.SR
    if last_speech is None or end_at is None or end_at < last_speech:
        return None
    return (end_at - last_speech) * 1000


# ── ASR benchmark ─────────────────────────────────────────────────────────────

DEVICE: str | None = None   # ASR backend override (auto/cpu/cuda/mlx/whispercpp)


def bench_asr(models: list[str], langs: list[str], live: bool = True) -> dict:
    report: dict = {"kind": "asr", "machine": machine_info(), "results": [],
                    "config": {"seg": SEG_KW, "whisper": praxis.WHISPER_OPTS,
                               "max_seg_s": SEG_KW.get("max_seg_s", praxis.MAX_SEG_S)}}
    for model_name in models:
        whisper = praxis.load_whisper(model_name, DEVICE)
        for lang in langs:
            corpus = load_corpus(lang)
            if not corpus:
                print(f"  ! no corpus for {lang} — run fetch_speech_corpus.py", file=sys.stderr)
                continue
            refs, hyp_full, hyp_live, samples = [], [], [], []
            asr_t, audio_t, live_segs = 0.0, 0.0, 0
            for it in corpus:
                a = read16k(it["path"])
                t0 = time.perf_counter()
                h = praxis.transcribe_segment(whisper, a, lang)
                dt = time.perf_counter() - t0
                asr_t += dt
                audio_t += len(a) / praxis.SR
                hl = ""
                if live:
                    segs = live_segments(a)
                    live_segs += len(segs)
                    hl = " ".join(filter(None, (
                        praxis.transcribe_segment(whisper, s.astype(np.float32) / 32768.0, lang)
                        for s in segs)))
                refs.append(it["text"])
                hyp_full.append(h)
                hyp_live.append(hl)
                w, _ = wer_cer([it["text"]], [h])
                wl = wer_cer([it["text"]], [hl])[0] if live else None
                samples.append({"file": it["file"], "speaker": it["speaker"],
                                "dur_s": round(len(a) / praxis.SR, 2), "ref": it["text"],
                                "hyp": h, "wer": round(w, 3), "asr_s": round(dt, 3),
                                **({"hyp_live": hl, "wer_live": round(wl, 3)} if live else {})})
                print(f"  {model_name:6} {lang} {it['file']}  WER {w:5.1%}"
                      + (f"  live {wl:5.1%}" if live else "") + f"  {dt:5.2f}s", file=sys.stderr)
            wer, cer = wer_cer(refs, hyp_full)
            row = {"model": model_name, "lang": lang, "n": len(corpus),
                   "backend": getattr(whisper, "backend", "cpu"),
                   "speakers": len({s["speaker"] for s in samples}),
                   "audio_s": round(audio_t, 1),
                   "wer": round(wer, 4), "cer": round(cer, 4),
                   "rtf": round(asr_t / audio_t, 3), "samples": samples}
            if live:
                wl, cl = wer_cer(refs, hyp_live)
                row.update(wer_live=round(wl, 4), cer_live=round(cl, 4),
                           live_segments=live_segs)
            report["results"].append(row)
    return report


# ── latency benchmark ─────────────────────────────────────────────────────────

def ensure_piper_voice(lang: str) -> str:
    import urllib.request
    from urllib.parse import quote
    loc, spk, q = PIPER_VOICES[lang]
    VOICES.mkdir(parents=True, exist_ok=True)
    name = f"{loc}-{spk}-{q}.onnx"
    base = "https://huggingface.co/rhasspy/piper-voices/resolve/main/" + quote(
        f"{lang}/{loc}/{spk}/{q}/{name}")
    for ext in ("", ".json"):
        dest = VOICES / f"{name}{ext}"
        if not dest.exists():
            print(f"  downloading {dest.name}", file=sys.stderr)
            urllib.request.urlretrieve(base + ext, dest)
    return str(VOICES / name)


def pct(xs: list[float], p: float) -> float:
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def bench_latency(model_name: str, pairs: list[tuple[str, str]], max_items: int) -> dict:
    report: dict = {"kind": "latency", "machine": machine_info(), "model": model_name,
                    "results": []}
    whisper = praxis.load_whisper(model_name, DEVICE)
    report["backend"] = getattr(whisper, "backend", "cpu")
    for src, tgt in pairs:
        praxis.setup_argos(src, tgt)
        voice = praxis.load_piper(ensure_piper_voice(tgt))
        praxis.do_translate("warm up.", src, tgt)               # load MT model
        b"".join(c.audio_int16_bytes for c in voice.synthesize("warm up."))
        corpus = load_corpus(src)[:max_items]
        stages: dict[str, list[float]] = {k: [] for k in
                                          ("vad_tail", "asr", "mt", "tts_first", "total")}
        samples = []
        for it in corpus:
            a = read16k(it["path"])
            # the engine only ever sees ≤ MAX_SEG_S segments
            segs = live_segments(a)
            if not segs:
                continue
            last = segs[-1].astype(np.float32) / 32768.0
            tail = vad_tail_ms(a)
            if tail is None:
                tail = float(praxis.SILENCE_MS)
                print('  ! VAD tail not measurable, using SILENCE_MS', file=sys.stderr)
            t0 = time.perf_counter()
            text = praxis.transcribe_segment(whisper, last, src)
            t1 = time.perf_counter()
            tr = praxis.do_translate(text, src, tgt) if text else ""
            t2 = time.perf_counter()
            first = praxis._split_sentences(tr)[0] if tr else ""
            if first:
                next(iter(voice.synthesize(first)))
            t3 = time.perf_counter()
            row = {"vad_tail": tail, "asr": (t1 - t0) * 1000, "mt": (t2 - t1) * 1000,
                   "tts_first": (t3 - t2) * 1000}
            row["total"] = sum(row.values())
            for k, v in row.items():
                stages[k].append(v)
            samples.append({"file": it["file"], "seg_s": round(len(last) / praxis.SR, 2),
                            "text": text, "translation": tr,
                            **{k: round(v, 1) for k, v in row.items()}})
            print(f"  {src}→{tgt} {it['file']}  total {row['total']:6.0f} ms  "
                  f"(vad {tail:.0f} asr {row['asr']:.0f} mt {row['mt']:.0f} "
                  f"tts {row['tts_first']:.0f})", file=sys.stderr)
        report["results"].append({
            "pair": f"{src}->{tgt}", "n": len(samples),
            "p50_ms": {k: round(statistics.median(v), 1) for k, v in stages.items() if v},
            "p95_ms": {k: round(pct(v, 0.95), 1) for k, v in stages.items() if v},
            "samples": samples})
    return report


# ── reporting ─────────────────────────────────────────────────────────────────

def machine_info() -> dict:
    import os
    info = {"os": platform.platform(), "cpu": platform.processor() or platform.machine(),
            "cores": os.cpu_count(), "python": platform.python_version(),
            "cuda": praxis._has_cuda()}
    try:
        import faster_whisper
        info["faster_whisper"] = faster_whisper.__version__
    except Exception:
        pass
    return info


def to_markdown(rep: dict) -> str:
    m = rep["machine"]
    lines = [f"_Machine: {m['os']} · {m['cpu']} · {m['cores']} cores · "
             f"Python {m['python']} · CUDA {m['cuda']}_", ""]
    if rep["kind"] == "asr":
        lines += ["| Model | Backend | Lang | Clips | Speakers | Audio | WER full | WER live | CER live | RTF |",
                  "|---|---|---|---:|---:|---:|---:|---:|---:|---:|"]
        for r in rep["results"]:
            lines.append(f"| {r['model']} | {r.get('backend', 'cpu')} | {r['lang']} | {r['n']} | {r['speakers']} | "
                         f"{r['audio_s']:.0f}s | {r['wer']:.1%} | {r.get('wer_live', float('nan')):.1%} | "
                         f"{r.get('cer_live', float('nan')):.1%} | {r['rtf']:.2f} |")
        lines += ["", "WER full = whole utterance in one call · WER live = streamed through the "
                  "engine's VAD (cuts at silence or every "
                  f"{praxis.MAX_SEG_S:.0f}s) · RTF = ASR time / audio time (lower is faster)."]
        worst = sorted((s for r in rep["results"] for s in r["samples"]),
                       key=lambda s: -s.get("wer_live", s["wer"]))[:5]
        lines += ["", "### Worst live transcriptions", ""]
        for s in worst:
            lines += [f"- `{s['file']}` WER {s.get('wer_live', s['wer']):.0%}",
                      f"  - ref: {s['ref']}", f"  - hyp: {s.get('hyp_live', s['hyp'])}"]
    else:
        lines += [f"Whisper model: `{rep['model']}` · backend: `{rep.get('backend', 'cpu')}`", "",
                  "| Pair | N | VAD tail | ASR | MT | TTS 1st | **Total p50** | **Total p95** |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for r in rep["results"]:
            p, q = r["p50_ms"], r["p95_ms"]
            lines.append(f"| {r['pair']} | {r['n']} | {p['vad_tail']:.0f} | {p['asr']:.0f} | "
                         f"{p['mt']:.0f} | {p['tts_first']:.0f} | **{p['total']:.0f} ms** | "
                         f"**{q['total']:.0f} ms** |")
        lines += ["", "Stage values are p50 in ms. Total = end of speech → first translated "
                  "audio sample ready (playback start)."]
    return "\n".join(lines) + "\n"


def save(rep: dict, name: str) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"{name}.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False),
                                          encoding="utf-8")
    (RESULTS / f"{name}.md").write_text(to_markdown(rep), encoding="utf-8")
    print(to_markdown(rep))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("asr")
    a.add_argument("--models", nargs="+", default=["small"])
    a.add_argument("--langs", nargs="+", default=["pt", "en", "es"])
    a.add_argument("--no-live", action="store_true")
    a.add_argument("--name", default="asr")
    a.add_argument("--device", default=None, help="auto|cpu|cuda|mlx|whispercpp")
    a.add_argument("--max-seg", type=float, help="override MAX_SEG_S")
    a.add_argument("--no-smart-cut", action="store_true")
    a.add_argument("--preroll", type=float, help="override PREROLL_S")
    a.add_argument("--no-repeat-guard", action="store_true")
    a.add_argument("--whisper", nargs="*", default=[], metavar="KEY=JSON",
                   help="override WHISPER_OPTS, e.g. vad_filter=false")
    lt = sub.add_parser("latency")
    lt.add_argument("--model", default="small")
    lt.add_argument("--pairs", nargs="+", default=["pt:en", "en:pt", "es:en"])
    lt.add_argument("--max-items", type=int, default=10)
    lt.add_argument("--name", default="latency")
    lt.add_argument("--device", default=None, help="auto|cpu|cuda|mlx|whispercpp")
    args = ap.parse_args()
    global DEVICE
    DEVICE = args.device
    if args.cmd == "asr":
        if args.max_seg is not None:
            SEG_KW["max_seg_s"] = args.max_seg
        if args.no_smart_cut:
            SEG_KW["smart_cut"] = False
        if args.preroll is not None:
            SEG_KW["preroll_s"] = args.preroll
        if args.no_repeat_guard:
            praxis.collapse_repetitions = lambda t, max_repeats=2: t
        for kv in args.whisper:
            k, v = kv.split("=", 1)
            praxis.WHISPER_OPTS[k] = json.loads(v)
        save(bench_asr(args.models, args.langs, live=not args.no_live), args.name)
    else:
        pairs = [tuple(p.split(":")) for p in args.pairs]
        save(bench_latency(args.model, pairs, args.max_items), args.name)


if __name__ == "__main__":
    main()
