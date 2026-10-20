"""Quality and latency gates on REAL human speech (opt-in: pytest -m slow).

Needs the speech corpus (benchmarks/fetch_speech_corpus.py), faster-whisper,
Argos packages and a Piper voice (downloaded on first run). Thresholds come
from benchmarks/results/ (CPU, Whisper `small`) with headroom so they catch
regressions — not hardware differences.
"""
from __future__ import annotations

import os
import statistics
import sys
import time
from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.slow

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "benchmarks"))

LANGS = ["pt", "en", "es"]
MODEL = os.environ.get("PRAXIS_BENCH_MODEL", "small")

# Max WER for the LIVE path (VAD segmentation + Whisper), per language.
# Measured (small, CPU, default settings): pt 16.7% · en 5.3% · es 6.9%
# (benchmarks/results/exp_E_smart6.md) — thresholds leave ~5 points of headroom.
MAX_WER_LIVE = {"pt": 0.22, "en": 0.09, "es": 0.12}
# The live path may not be much worse than transcribing the whole utterance
MAX_LIVE_PENALTY = 0.08
# End-of-speech → first translated audio ready (p50, CPU). Generous: CI runners are slow.
MAX_LATENCY_P50_MS = float(os.environ.get("PRAXIS_MAX_LATENCY_MS", "2500"))


@pytest.fixture(scope="module")
def rb():
    pytest.importorskip("faster_whisper")
    pytest.importorskip("jiwer")
    import run_benchmarks
    if not any(run_benchmarks.load_corpus(lang) for lang in LANGS):
        pytest.skip("speech corpus missing — python benchmarks/fetch_speech_corpus.py")
    return run_benchmarks


@pytest.fixture(scope="module")
def whisper(rb):
    return rb.praxis.load_whisper(MODEL)


@pytest.mark.parametrize("lang", LANGS)
def test_live_transcription_quality(rb, whisper, lang):
    corpus = rb.load_corpus(lang)
    if not corpus:
        pytest.skip(f"no corpus for {lang}")
    p = rb.praxis
    refs, full, live = [], [], []
    for it in corpus:
        a = rb.read16k(it["path"])
        refs.append(it["text"])
        full.append(p.transcribe_segment(whisper, a, lang))
        segs = rb.live_segments(a)
        live.append(" ".join(filter(None, (
            p.transcribe_segment(whisper, s.astype(np.float32) / 32768.0, lang) for s in segs))))
    wer_full, _ = rb.wer_cer(refs, full)
    wer_live, _ = rb.wer_cer(refs, live)
    print(f"\n{lang}: WER full {wer_full:.1%}  live {wer_live:.1%}  ({len(corpus)} speakers)")
    assert wer_live <= MAX_WER_LIVE[lang], f"{lang} live WER {wer_live:.1%}"
    assert wer_live - wer_full <= MAX_LIVE_PENALTY, \
        f"{lang}: live segmentation costs {wer_live - wer_full:+.1%} WER"


def test_no_hallucination_loops(rb, whisper):
    """No transcript may contain a phrase repeated 3+ times in a row."""
    import re
    p = rb.praxis
    for lang in LANGS:
        for it in rb.load_corpus(lang):
            a = rb.read16k(it["path"])
            for s in rb.live_segments(a):
                t = p.transcribe_segment(whisper, s.astype(np.float32) / 32768.0, lang)
                assert not re.search(r"\b((?:\w+\W+){1,6}?)\1{2,}", t.lower() + " "), \
                    f"{it['file']}: loop in {t!r}"


@pytest.mark.parametrize("src,tgt", [("pt", "en"), ("en", "pt"), ("es", "en"), ("es", "pt")])
def test_translation_sanity(rb, src, tgt):
    """Translates the human reference transcripts: output must be non-empty,
    of plausible length and free of degenerate loops (caught the int8 es→en bug)."""
    p = rb.praxis
    p.setup_argos(src, tgt)
    corpus = rb.load_corpus(src)[:6]
    if not corpus:
        pytest.skip(f"no corpus for {src}")
    for it in corpus:
        out = p.do_translate(it["text"], src, tgt)
        ratio = len(out) / max(1, len(it["text"]))
        assert out.strip(), it["file"]
        assert 0.4 < ratio < 2.5, f"{src}->{tgt} {it['file']}: length ratio {ratio:.2f}: {out[:120]!r}"
        assert p.collapse_repetitions(out) == out, f"loop: {out[:120]!r}"


def test_end_to_end_latency(rb, whisper):
    """End of speech → first translated audio ready, on real utterances."""
    p = rb.praxis
    p.setup_argos("pt", "en")
    voice = p.load_piper(rb.ensure_piper_voice("en"))
    p.do_translate("aquecimento.", "pt", "en")
    next(iter(voice.synthesize("warm up.")))
    totals = []
    for it in rb.load_corpus("pt")[:6]:
        a = rb.read16k(it["path"])
        segs = rb.live_segments(a)
        if not segs:
            continue
        last = segs[-1].astype(np.float32) / 32768.0
        t0 = time.perf_counter()
        text = p.transcribe_segment(whisper, last, "pt")
        tr = p.do_translate(text, "pt", "en") if text else ""
        if tr:
            next(iter(voice.synthesize(p._split_sentences(tr)[0])))
        totals.append((time.perf_counter() - t0) * 1000 + p.SILENCE_MS)
    p50 = statistics.median(totals)
    print(f"\nlatency p50 {p50:.0f} ms  max {max(totals):.0f} ms")
    assert p50 <= MAX_LATENCY_P50_MS
