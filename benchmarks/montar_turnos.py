#!/usr/bin/env python3
"""Gravações de "turnos de conversa" para o teste de latência do motor em Rust (comando
stream): N frases do FLEURS de pessoas diferentes, com uma pausa entre elas, como alguém
que fala e espera a tradução.

Saída: benchmarks/data/turnos/<idioma>.wav + .json (texto de referência)
Uso: python benchmarks/montar_turnos.py --langs pt en es de fr it --n 10 --pausa 2
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf

DATA = Path(__file__).resolve().parent / "data"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--langs", nargs="+", default=["pt", "en", "es", "de", "fr", "it"])
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--pausa", type=float, default=2.0, help="silêncio entre as frases (s)")
    ap.add_argument("--espera-traducao", action="store_true",
                    help="a pausa também espera a tradução falada (≈ duração da frase), como numa conversa")
    a = ap.parse_args()
    out = DATA / ("turnos-conversa" if a.espera_traducao else "turnos")
    out.mkdir(parents=True, exist_ok=True)
    for lang in a.langs:
        src = DATA / "speech_fleurs" / lang
        man = json.loads((src / "manifest.json").read_text(encoding="utf-8"))[:a.n]
        pausa = np.zeros(int(a.pausa * 16000), np.float32)
        partes, textos = [], []
        for it in man:
            x, sr = sf.read(src / it["file"], dtype="float32")
            assert sr == 16000
            extra = np.zeros(len(x) if a.espera_traducao else 0, np.float32)
            partes += [x, pausa, extra]
            textos.append(it["text"])
        sf.write(out / f"{lang}.wav", np.concatenate(partes), 16000)
        (out / f"{lang}.json").write_text(json.dumps({"text": " ".join(textos), "frases": len(textos)},
                                                     ensure_ascii=False), encoding="utf-8")
        print(f"  {lang}: {len(textos)} frases", flush=True)


if __name__ == "__main__":
    main()
