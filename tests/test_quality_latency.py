"""Limites de qualidade e de atraso com fala humana REAL (rodar só sob pedido: pytest -m slow).

Precisa do corpus de fala (benchmarks/fetch_speech_corpus.py), do faster-whisper,
dos pacotes do Argos e de uma voz do Piper (baixada na primeira execução). Os
limites vêm de benchmarks/results/ (CPU, Whisper `small`) com folga, para pegar
regressões — e não diferenças de hardware.
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

# Taxa máxima de erro de palavras (WER) no caminho AO VIVO (divisão em trechos
# pela detecção de voz + Whisper), por idioma.
# Medido (small, CPU, configuração padrão): pt 16.7% · en 5.3% · es 6.9%
# (benchmarks/results/exp_E_smart6.md) — os limites deixam ~5 pontos de folga.
MAX_WER_LIVE = {"pt": 0.22, "en": 0.09, "es": 0.12}
# O caminho ao vivo não pode ser muito pior do que transcrever a fala inteira de uma vez
MAX_LIVE_PENALTY = 0.08
# Fim da fala → primeiro áudio traduzido pronto (mediana/p50, CPU). Generoso: as máquinas da CI são lentas.
MAX_LATENCY_P50_MS = float(os.environ.get("PRAXIS_MAX_LATENCY_MS", "2500"))


@pytest.fixture(scope="module")
def rb():
    pytest.importorskip("faster_whisper")
    pytest.importorskip("jiwer")
    import run_benchmarks
    if not any(run_benchmarks.load_corpus(lang) for lang in LANGS):
        pytest.skip("corpus de fala ausente — python benchmarks/fetch_speech_corpus.py")
    return run_benchmarks


@pytest.fixture(scope="module")
def whisper(rb):
    return rb.praxis.load_whisper(MODEL)


@pytest.mark.parametrize("lang", LANGS)
def test_qualidade_da_transcricao_ao_vivo(rb, whisper, lang):
    corpus = rb.load_corpus(lang)
    if not corpus:
        pytest.skip(f"sem corpus para {lang}")
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
    print(f"\n{lang}: taxa de erro de palavras inteira {wer_full:.1%}  ao vivo {wer_live:.1%}  ({len(corpus)} falantes)")
    assert wer_live <= MAX_WER_LIVE[lang], f"{lang}: taxa de erro de palavras ao vivo {wer_live:.1%}"
    assert wer_live - wer_full <= MAX_LIVE_PENALTY, \
        f"{lang}: a divisão ao vivo custa {wer_live - wer_full:+.1%} na taxa de erro de palavras"


def test_sem_loops_de_alucinacao(rb, whisper):
    """Nenhuma transcrição pode ter uma frase repetida 3 ou mais vezes seguidas."""
    import re
    p = rb.praxis
    for lang in LANGS:
        for it in rb.load_corpus(lang):
            a = rb.read16k(it["path"])
            for s in rb.live_segments(a):
                t = p.transcribe_segment(whisper, s.astype(np.float32) / 32768.0, lang)
                assert not re.search(r"\b((?:\w+\W+){1,6}?)\1{2,}", t.lower() + " "), \
                    f"{it['file']}: loop em {t!r}"


@pytest.mark.parametrize("src,tgt", [("pt", "en"), ("en", "pt"), ("es", "en"), ("es", "pt")])
def test_sanidade_da_traducao(rb, src, tgt):
    """Traduz as transcrições de referência feitas por humanos: a saída não pode
    ser vazia, precisa ter tamanho plausível e não pode ter repetições em loop
    (isso pegou o bug do int8 em espanhol→inglês)."""
    p = rb.praxis
    p.setup_argos(src, tgt)
    corpus = rb.load_corpus(src)[:6]
    if not corpus:
        pytest.skip(f"sem corpus para {src}")
    for it in corpus:
        out = p.do_translate(it["text"], src, tgt)
        ratio = len(out) / max(1, len(it["text"]))
        assert out.strip(), it["file"]
        assert 0.4 < ratio < 2.5, f"{src}->{tgt} {it['file']}: proporção de tamanho {ratio:.2f}: {out[:120]!r}"
        assert p.collapse_repetitions(out) == out, f"loop: {out[:120]!r}"


def test_atraso_de_ponta_a_ponta(rb, whisper):
    """Fim da fala → primeiro áudio traduzido pronto, com falas reais."""
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
    print(f"\natraso mediano (p50) {p50:.0f} ms  máximo {max(totals):.0f} ms")
    assert p50 <= MAX_LATENCY_P50_MS
