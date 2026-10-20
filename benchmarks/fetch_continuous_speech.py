#!/usr/bin/env python3
"""Builds ~60 s of CONTINUOUS real speech per language — one speaker reading
on, with the exact reference text and the time each sentence is spoken.

  pt, es  Multilingual LibriSpeech (test): consecutive segments of the same
          audiobook file, ordered by their original begin_time; the real
          pause between segments (end → next begin) is kept.
  en      LibriSpeech test-clean: consecutive utterance ids of one chapter
          joined with a 0.4 s pause (utterances were cut at pauses).

All CC BY 4.0. Output: benchmarks/data/continuous/<lang>.wav (16 kHz mono) and
<lang>.json = {text, speaker, source, license, duration, segments:[{start, end, text}]}

Usage: python benchmarks/fetch_continuous_speech.py [--langs pt en es] [--seconds 60]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np
import soundfile as sf

API = "https://datasets-server.huggingface.co"
OUT = Path(__file__).resolve().parent / "data" / "continuous"
SR = 16000
MLS = {"pt": "portuguese", "es": "spanish", "fr": "french", "de": "german", "it": "italian"}


def _get(url: str, tries: int = 7) -> bytes:
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(min(60, 3 * 2 ** i))
    raise RuntimeError


def _rows(ds: str, cfg: str, off: int, n: int = 100) -> list[dict]:
    q = urllib.parse.urlencode({"dataset": ds, "config": cfg, "split": "test",
                                "offset": off, "length": n})
    return [r["row"] for r in json.loads(_get(f"{API}/rows?{q}"))["rows"]]


def _audio(row: dict) -> np.ndarray:
    a, sr = sf.read(io.BytesIO(_get(row["audio"][0]["src"])), dtype="float32", always_2d=True)
    a = a.mean(axis=1)
    if sr != SR:
        a = np.interp(np.linspace(0, len(a) - 1, int(round(len(a) * SR / sr))),
                      np.arange(len(a)), a).astype(np.float32)
    return a


def _mls_chain(lang: str, seconds: float, max_gap: float = 1.2, scan_rows: int = 600):
    """Longest run of consecutive segments (same book file) ≥ `seconds`."""
    by_file: dict[str, list[dict]] = defaultdict(list)
    for off in range(0, scan_rows, 100):
        for r in _rows("facebook/multilingual_librispeech", MLS[lang], off):
            # keep the signed audio URL: rows are re-fetched only if it expires
            by_file[r["original_path"]].append(r)
        time.sleep(0.5)
    best: list[dict] = []
    for segs in by_file.values():
        segs.sort(key=lambda r: r["begin_time"])
        run = [segs[0]]
        for prev, cur in zip(segs, segs[1:]):
            gap = cur["begin_time"] - prev["end_time"]
            if 0 <= gap <= max_gap and cur["speaker_id"] == prev["speaker_id"]:
                run.append(cur)
            else:
                run = [cur]
            if run[-1]["end_time"] - run[0]["begin_time"] >= seconds:
                best = run
                break
        if best:
            break
    if not best:
        raise RuntimeError(f"no continuous {seconds}s run found for {lang}; raise --scan")
    return best


def build(lang: str, seconds: float) -> dict:
    pieces, segments, texts, t = [], [], [], 0.0
    if lang == "en":
        rows = _rows("openslr/librispeech_asr", "clean", 0, 100)
        first = rows[0]
        chap = [r for r in rows if r["chapter_id"] == first["chapter_id"]
                and r["speaker_id"] == first["speaker_id"]]
        chap.sort(key=lambda r: r["id"])
        speaker, source = str(first["speaker_id"]), "openslr/librispeech_asr (test-clean)"
        for r in chap:
            a = _audio(r)
            if pieces:
                pieces.append(np.zeros(int(0.4 * SR), np.float32))
                t += 0.4
            segments.append({"start": round(t, 3), "end": round(t + len(a) / SR, 3), "text": r["text"].lower()})
            pieces.append(a)
            texts.append(r["text"].lower())
            t += len(a) / SR
            if t >= seconds:
                break
    else:
        chain = _mls_chain(lang, seconds)
        speaker, source = str(chain[0]["speaker_id"]), "facebook/multilingual_librispeech (test)"
        prev_end = None
        for r in chain:
            if prev_end is not None:
                gap = max(0.0, r["begin_time"] - prev_end)
                pieces.append(np.zeros(int(gap * SR), np.float32))
                t += gap
            a = _audio(r)
            segments.append({"start": round(t, 3), "end": round(t + len(a) / SR, 3), "text": r["transcript"]})
            pieces.append(a)
            texts.append(r["transcript"])
            t += len(a) / SR
            prev_end = r["end_time"]
    audio = np.concatenate(pieces)
    OUT.mkdir(parents=True, exist_ok=True)
    sf.write(str(OUT / f"{lang}.wav"), audio, SR, subtype="PCM_16")
    meta = {"lang": lang, "text": " ".join(texts), "speaker": speaker, "source": source,
            "license": "CC BY 4.0", "duration": round(len(audio) / SR, 2), "segments": segments}
    (OUT / f"{lang}.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{lang}: {meta['duration']:.1f}s, speaker {speaker}, {len(segments)} segments, "
          f"{len(meta['text'].split())} words", file=sys.stderr)
    return meta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", nargs="+", default=["pt", "en", "es"])
    ap.add_argument("--seconds", type=float, default=60.0)
    a = ap.parse_args()
    for lang in a.langs:
        build(lang, a.seconds)


if __name__ == "__main__":
    main()
