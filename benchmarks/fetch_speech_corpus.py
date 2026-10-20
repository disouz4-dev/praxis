#!/usr/bin/env python3
"""Downloads a small multi-speaker corpus of real human speech with reference
transcripts, used by the ASR-quality and latency benchmarks.

Sources (all CC BY 4.0, read speech from volunteer speakers):
  en          openslr/librispeech_asr        (test-clean)
  pt es fr de it nl pl
              facebook/multilingual_librispeech (test)

Files land in benchmarks/data/speech/<lang>/ with a manifest.json:
  [{"file", "text", "speaker", "duration", "source", "license"}]

Usage:  python benchmarks/fetch_speech_corpus.py [--langs pt en es] [--per-lang 12]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://datasets-server.huggingface.co"
OUT = Path(__file__).resolve().parent / "data" / "speech"

MLS_CONFIG = {"pt": "portuguese", "es": "spanish", "fr": "french", "de": "german",
              "it": "italian", "nl": "dutch", "pl": "polish"}


def _get(url: str, tries: int = 7) -> bytes:
    """GET with exponential backoff (the datasets-server rate-limits with 429)."""
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(min(60, 3 * 2 ** i))
    raise RuntimeError("unreachable")


def _get_json(url: str) -> dict:
    return json.loads(_get(url))


def _save_wav16k(blob: bytes, dest: Path) -> None:
    """Decodes whatever the API serves (WAV/FLAC/Opus) → 16 kHz mono PCM WAV."""
    import io

    import numpy as np
    import soundfile as sf
    data, sr = sf.read(io.BytesIO(blob), dtype="float32", always_2d=True)
    mono = data.mean(axis=1)
    if sr != 16000:
        n = int(round(len(mono) * 16000 / sr))
        mono = np.interp(np.linspace(0, len(mono) - 1, n), np.arange(len(mono)), mono)
    sf.write(str(dest), mono.astype("float32"), 16000, subtype="PCM_16")


def _source(lang: str) -> tuple[str, str, str, str]:
    """(dataset, config, split, text_field)"""
    if lang == "en":
        return "openslr/librispeech_asr", "clean", "test", "text"
    return "facebook/multilingual_librispeech", MLS_CONFIG[lang], "test", "transcript"


def fetch_lang(lang: str, per_lang: int, max_dur: float = 12.0) -> list[dict]:
    dataset, config, split, text_field = _source(lang)
    q = urllib.parse.urlencode({"dataset": dataset, "config": config, "split": split})
    total = _get_json(f"{API}/size?dataset={urllib.parse.quote(dataset)}")
    n_rows = next((c["num_rows"] for c in total["size"]["splits"]
                   if c["config"] == config and c["split"] == split), 2000)

    out_dir = OUT / lang
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = out_dir / "manifest.json"
    items: list[dict] = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else []
    items = [it for it in items if (out_dir / it["file"]).exists()]
    speakers: set[str] = {it["speaker"] for it in items}
    done_files = {it["file"] for it in items}
    # Walk the split at evenly spaced offsets → many different speakers
    stride = max(1, n_rows // (per_lang * 3))
    offset = 0
    while len(items) < per_lang and offset < n_rows:
        page = _get_json(f"{API}/rows?{q}&offset={offset}&length=10")
        for row in page.get("rows", []):
            r = row["row"]
            spk = str(r.get("speaker_id"))
            dur = float(r.get("audio_duration") or 0) or None
            fname = f"{lang}_{row['row_idx']:06d}.wav"
            if spk in speakers or fname in done_files or (dur and dur > max_dur):
                continue
            src = r["audio"][0]["src"]
            _save_wav16k(_get(src), out_dir / fname)
            items.append({"file": fname, "text": r[text_field].strip(), "speaker": spk,
                          "duration": dur, "source": dataset, "license": "CC BY 4.0"})
            speakers.add(spk)
            manifest.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"  {lang} {len(items):2d}/{per_lang}  spk={spk}  {r[text_field][:60]}",
                  file=sys.stderr)
            break   # one per page → spread across speakers
        offset += stride
        time.sleep(0.5)   # be polite to the API
    manifest.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    return items


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", nargs="+", default=["pt", "en", "es"])
    ap.add_argument("--per-lang", type=int, default=12)
    a = ap.parse_args()
    for lang in a.langs:
        print(f"[{lang}]", file=sys.stderr)
        fetch_lang(lang, a.per_lang)


if __name__ == "__main__":
    main()
