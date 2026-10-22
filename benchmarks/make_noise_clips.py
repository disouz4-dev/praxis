#!/usr/bin/env python3
"""Monta áudios para medir como o Praxis lida com ruído e com a ausência de fala.

  silencio/    20 s de silêncio digital            → nada deveria ser traduzido
  ruido/       20 s de ruído ambiente (chiado)      → nada deveria ser traduzido
  falatorio/   20 s de vozes de fundo misturadas    → mostra se o Praxis traduz conversa de fundo
  fala_ruido_20db/ 10db/ 5db/  a fala normal de ~20 s dos 16 idiomas com ruído ambiente
               (20 dB = ruído fraco, 10 dB = médio, 5 dB = forte, quase tão alto quanto a voz)

Os de "sem fala" têm texto de referência vazio (pt e en, para testar o Whisper nos
dois idiomas). Saída: benchmarks/data/ruido/<caso>/<idioma>.wav/.json

Uso: python benchmarks/make_noise_clips.py   (depois de make_speed_clips.py)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent
FALA = ROOT / "data" / "velocidade" / "normal20"
CONT = ROOT / "data" / "continuous"
OUT = ROOT / "data" / "ruido"
SR = 16000
DUR = 20.0
RNG = np.random.default_rng(7)


def ruido_rosa(n: int) -> np.ndarray:
    """Ruído "rosa" (1/f): parecido com o chiado de ar-condicionado e ambiente."""
    branco = RNG.standard_normal(n)
    espectro = np.fft.rfft(branco)
    f = np.fft.rfftfreq(n)
    f[0] = f[1]
    rosa = np.fft.irfft(espectro / np.sqrt(f), n)
    return (rosa / np.sqrt(np.mean(rosa ** 2))).astype(np.float32)   # volume médio = 1


def volume(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(x ** 2)))


def salvar(caso: str, lang: str, audio: np.ndarray, texto: str) -> None:
    d = OUT / caso
    d.mkdir(parents=True, exist_ok=True)
    audio = np.clip(audio, -1, 1).astype(np.float32)
    sf.write(str(d / f"{lang}.wav"), audio, SR, subtype="PCM_16")
    dur = round(len(audio) / SR, 2)
    (d / f"{lang}.json").write_text(json.dumps({
        "lang": lang, "text": texto, "speaker": caso, "source": caso, "license": "—",
        "duration": dur, "segments": [{"start": 0.0, "end": dur, "text": texto}]},
        ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    n = int(DUR * SR)
    for lang in ("pt", "en"):
        salvar("silencio", lang, np.zeros(n, np.float32), "")
        salvar("ruido", lang, ruido_rosa(n) * 10 ** (-35 / 20), "")        # chiado de sala (-35 dB)
        # falatório: 6 vozes reais em outros idiomas, misturadas bem baixinho
        vozes = [l for l in ("ru", "de", "it", "tr", "uk", "pl") if l != lang]
        mix = np.zeros(n, np.float32)
        for k, v in enumerate(vozes):
            a, _ = sf.read(str(CONT / f"{v}.wav"), dtype="float32")
            a = a[k * SR * 3:k * SR * 3 + n]
            a = np.pad(a, (0, n - len(a)))
            mix += a / max(volume(a), 1e-6) * 10 ** (-32 / 20)
        salvar("falatorio", lang, mix, "")
    for snr in (20, 10, 5):
        for jf in sorted(FALA.glob("*.json")):
            meta = json.loads(jf.read_text(encoding="utf-8"))
            fala, _ = sf.read(str(FALA / f"{jf.stem}.wav"), dtype="float32")
            voz = volume(fala[np.abs(fala) > 0.01]) if np.any(np.abs(fala) > 0.01) else volume(fala)
            ruido = ruido_rosa(len(fala)) * voz * 10 ** (-snr / 20)
            salvar(f"fala_ruido_{snr}db", jf.stem, fala + ruido, meta["text"])
    print("áudios criados em", OUT)


if __name__ == "__main__":
    main()
