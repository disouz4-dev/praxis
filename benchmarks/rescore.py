#!/usr/bin/env python3
"""Re-scores saved stream/asr results with the current text normalisation —
no models needed (transcripts and references are stored in the JSON).

Usage: python benchmarks/rescore.py benchmarks/results/stream-*.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import run_benchmarks as rb  # noqa: E402
import stream_test as st  # noqa: E402

for path in sys.argv[1:]:
    rep = json.loads(Path(path).read_text(encoding="utf-8"))
    for r in rep.get("results", []):
        if "reference" not in r:
            continue
        src = r["pair"].split("->")[0]
        wer, cer = rb.wer_cer([r["reference"]], [r["transcript"]])
        r["wer"], r["cer"] = round(wer, 4), round(cer, 4)
        r["error_rate"] = round(cer if src in st.CHAR_LANGS else wer, 4)
        r["errors"] = st.word_errors(r["reference"], r["transcript"], src)
        r["keeps_up"] = st.keeps_up(r)
        r["findings"] = st.findings(r)
    Path(path).write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    Path(path).with_suffix(".md").write_text(st.to_markdown(rep), encoding="utf-8")
    print("rescored", path)
