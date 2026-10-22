#!/usr/bin/env python3
"""Conversa bilateral de ~5 min para a verificação de qualidade do Praxis.

Duas trilhas que tocam ao mesmo tempo: "eu" (português, no microfone de teste) e "a
outra pessoa" (inglês, na entrada do app de chamada). As falas se alternam e, depois de
cada uma, há uma pausa do tamanho da fala + 3 s: o tempo de a tradução ser falada, como
numa conversa de verdade. Saída: /tmp/conversa-eu.wav, /tmp/conversa-outro.wav e
/tmp/conversa.json (o texto e o horário de cada fala).

Uso: python montar_conversa.py <pasta speech_fleurs> [--turnos 7]
"""
import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 16000
ap = argparse.ArgumentParser()
ap.add_argument("fleurs", type=Path)
ap.add_argument("--turnos", type=int, default=7)
a = ap.parse_args()
falas = {lang: json.loads((a.fleurs / lang / "manifest.json").read_text())[10:10 + a.turnos] for lang in ("pt", "en")}
eu, outro, roteiro, t = [], [], [], 0.0
for i in range(a.turnos):
    for lang, minha in (("pt", True), ("en", False)):
        it = falas[lang][i]
        x, sr = sf.read(a.fleurs / lang / it["file"], dtype="float32")
        assert sr == SR
        pausa = np.zeros(int((len(x) / SR + 3.0) * SR), np.float32)
        zeros = np.zeros(len(x) + len(pausa), np.float32)
        fala = np.concatenate([x, pausa])
        (eu if minha else outro).append(fala)
        (outro if minha else eu).append(zeros)
        roteiro.append({"quem": "eu" if minha else "outro", "lang": lang, "inicio_s": round(t, 2),
                        "fim_s": round(t + len(x) / SR, 2), "texto": it["text"]})
        t += len(fala) / SR
sf.write("/tmp/conversa-eu.wav", np.concatenate(eu), SR)
sf.write("/tmp/conversa-outro.wav", np.concatenate(outro), SR)
json.dump(roteiro, open("/tmp/conversa.json", "w"), ensure_ascii=False, indent=1)
print(f"{len(roteiro)} falas, {t / 60:.1f} min")
