#!/usr/bin/env python3
"""Frases do FLEURS com ruído, e as mesmas frases depois do removedor de ruído.

Para cada idioma, mistura às frases de benchmarks/data/speech_fleurs/<idioma>/:
  chiado10   chiado de sala (ruído rosa) 10 dB abaixo da voz (médio)
  chiado5    chiado 5 dB abaixo da voz (forte, quase tão alto quanto a voz)
  conversa10 vozes de fundo (frases de outros idiomas misturadas) 10 dB abaixo
e, com --limpar <modelo.onnx>, gera também <caso>-<nome do modelo> com o áudio
passado pelo removedor de ruído do sherpa-onnx (GTCRN ou DPDFNet).

Saída: benchmarks/data/speech_fleurs_<caso>/<idioma>/ (wav + manifest.json), no formato
que run_benchmarks.py --corpus lê.

Uso:
  python benchmarks/fleurs_com_ruido.py --langs pt en es
  python benchmarks/fleurs_com_ruido.py --langs pt en es --limpar gtcrn_simple.onnx
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf

DATA = Path(__file__).resolve().parent / "data"
SR = 16000
CASOS = {"chiado10": ("rosa", 10), "chiado5": ("rosa", 5), "conversa10": ("conversa", 10)}


def ruido_rosa(n: int, rng: np.random.Generator) -> np.ndarray:
    branco = np.fft.rfft(rng.standard_normal(n))
    f = np.arange(len(branco)) + 1.0
    x = np.fft.irfft(branco / np.sqrt(f), n)
    return (x / (np.sqrt(np.mean(x ** 2)) + 1e-9)).astype(np.float32)


def volume(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(x ** 2)) + 1e-9)


def conversa(n: int, lang: str, rng: np.random.Generator) -> np.ndarray:
    """Três frases de outros idiomas tocando ao mesmo tempo (falatório de fundo)."""
    outros = [d for d in (DATA / "speech_fleurs").iterdir() if d.is_dir() and d.name != lang]
    mix = np.zeros(n, np.float32)
    for d in rng.choice(outros, 3, replace=False):
        wavs = sorted(d.glob("*.wav"))
        a, _ = sf.read(wavs[rng.integers(len(wavs))], dtype="float32")
        a = np.tile(a, int(np.ceil(n / len(a))))[:n]
        mix += a / volume(a)
    return mix / volume(mix)


def misturar(langs: list[str]) -> None:
    rng = np.random.default_rng(7)
    for caso, (tipo, snr) in CASOS.items():
        for lang in langs:
            src = DATA / "speech_fleurs" / lang
            out = DATA / f"speech_fleurs_{caso}" / lang
            out.mkdir(parents=True, exist_ok=True)
            man = json.loads((src / "manifest.json").read_text(encoding="utf-8"))
            for it in man:
                fala, sr = sf.read(src / it["file"], dtype="float32")
                assert sr == SR
                r = ruido_rosa(len(fala), rng) if tipo == "rosa" else conversa(len(fala), lang, rng)
                x = fala + r * volume(fala) * 10 ** (-snr / 20)
                sf.write(out / it["file"], np.clip(x, -1, 1), SR)
            (out / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  {caso}/{lang}: {len(man)} frases", flush=True)


def limpar(langs: list[str], modelo: Path) -> None:
    import sherpa_onnx as so
    nome = modelo.stem.split(".")[0]
    mc = so.OfflineSpeechDenoiserModelConfig(num_threads=4)
    if "gtcrn" in nome:
        mc.gtcrn = so.OfflineSpeechDenoiserGtcrnModelConfig(model=str(modelo))
    else:
        mc.dpdfnet = so.OfflineSpeechDenoiserDpdfNetModelConfig(model=str(modelo))
    den = so.OfflineSpeechDenoiser(so.OfflineSpeechDenoiserConfig(model=mc))
    for caso in [*CASOS, "limpo"]:
        for lang in langs:
            src = DATA / ("speech_fleurs" if caso == "limpo" else f"speech_fleurs_{caso}") / lang
            out = DATA / f"speech_fleurs_{caso}-{nome}" / lang
            out.mkdir(parents=True, exist_ok=True)
            man = json.loads((src / "manifest.json").read_text(encoding="utf-8"))
            for it in man:
                x, sr = sf.read(src / it["file"], dtype="float32")
                r = den.run(x, sr)
                y = np.asarray(r.samples, np.float32)
                if r.sample_rate != SR:          # DPDFNet de 48 kHz devolve noutra taxa
                    import scipy.signal as ss
                    y = ss.resample_poly(y, SR, r.sample_rate).astype(np.float32)
                sf.write(out / it["file"], y, SR)
            (out / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  {caso}-{nome}/{lang}: {len(man)} frases", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--langs", nargs="+", default=["pt", "en", "es", "de", "it", "fr"])
    ap.add_argument("--limpar", type=Path, help="modelo do removedor de ruído (.onnx do sherpa-onnx)")
    a = ap.parse_args()
    if a.limpar:
        limpar(a.langs, a.limpar)
    else:
        misturar(a.langs)


if __name__ == "__main__":
    main()
