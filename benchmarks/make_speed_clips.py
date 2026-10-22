#!/usr/bin/env python3
"""Monta trechos de fala real em quatro versões, para medir o efeito da
velocidade e das pausas na transcrição (a partir do corpus contínuo de
fetch_continuous_speech.py):

  normal20   ~20 s de fala na velocidade original
  normal15   ~15 s de fala na velocidade original (o mesmo texto das duas abaixo)
  lenta20    os mesmos ~15 s desacelerados para ~20 s, sem mudar o tom (ffmpeg atempo)
  pausada20  os mesmos ~15 s na velocidade normal, com as pausas naturais
             (entre frases e palavras) alongadas até somar ~20 s

Os cortes são sempre em limites de frase do corpus, para que o texto de
referência continue exato. Saída: benchmarks/data/velocidade/<versão>/<idioma>.wav/.json

Uso: python benchmarks/make_speed_clips.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "data" / "continuous"
OUT = ROOT / "data" / "velocidade"
SR = 16000
SLOW = 0.75                      # 15 s de fala → 20 s


def _pick(segments: list[dict], target: float) -> tuple[float, float, str]:
    """Sequência de frases consecutivas com duração mais próxima de `target`."""
    best = None
    for i in range(len(segments)):
        for j in range(i, len(segments)):
            dur = segments[j]["end"] - segments[i]["start"]
            score = abs(dur - target)
            if best is None or score < best[0]:
                text = " ".join(s["text"] for s in segments[i:j + 1])
                best = (score, segments[i]["start"], segments[j]["end"], text)
            if dur > target + 8:
                break
    _, start, end, text = best
    return start, end, text


def _slow_down(audio: np.ndarray, factor: float) -> np.ndarray:
    with tempfile.TemporaryDirectory() as d:
        src, dst = Path(d) / "in.wav", Path(d) / "out.wav"
        sf.write(str(src), audio, SR, subtype="PCM_16")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src),
                        "-filter:a", f"atempo={factor}", "-ar", str(SR), "-ac", "1", str(dst)],
                       check=True)
        out, _ = sf.read(str(dst), dtype="float32")
    return out


def _add_pauses(audio: np.ndarray, target_s: float) -> np.ndarray:
    """Alonga as pausas naturais (trechos baixos ≥ 60 ms) até a duração desejada."""
    frame = int(0.02 * SR)
    n = len(audio) // frame
    energy = np.array([np.sqrt(np.mean(audio[i * frame:(i + 1) * frame] ** 2)) for i in range(n)])
    voiced = energy[energy > np.percentile(energy, 30)]
    quiet = energy < (0.15 * np.median(voiced) if len(voiced) else 0.01)
    gaps, i = [], 0
    while i < n:
        if quiet[i]:
            j = i
            while j < n and quiet[j]:
                j += 1
            if j - i >= 3 and i > 0 and j < n:            # pausa interna de pelo menos 60 ms
                gaps.append((i, j))
            i = j
        else:
            i += 1
    extra = max(0.0, target_s - len(audio) / SR)
    if not gaps or extra <= 0:
        return np.concatenate([audio, np.zeros(int(extra * SR), np.float32)])
    total_gap = sum(j - i for i, j in gaps)
    pieces, last = [], 0
    for i, j in gaps:
        mid = (i + j) // 2 * frame
        pieces.append(audio[last:mid])
        pieces.append(np.zeros(int(extra * SR * (j - i) / total_gap), np.float32))
        last = mid
    pieces.append(audio[last:])
    return np.concatenate(pieces).astype(np.float32)


def _save(version: str, lang: str, audio: np.ndarray, text: str, meta: dict) -> float:
    d = OUT / version
    d.mkdir(parents=True, exist_ok=True)
    sf.write(str(d / f"{lang}.wav"), audio, SR, subtype="PCM_16")
    dur = round(len(audio) / SR, 2)
    (d / f"{lang}.json").write_text(json.dumps({
        "lang": lang, "text": text, "speaker": meta["speaker"], "source": meta["source"],
        "license": meta["license"], "duration": dur, "version": version,
        "segments": [{"start": 0.0, "end": dur, "text": text}]}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return dur


def main() -> None:
    for jf in sorted(SRC.glob("*.json")):
        lang = jf.stem
        meta = json.loads(jf.read_text(encoding="utf-8"))
        audio, sr = sf.read(str(SRC / f"{lang}.wav"), dtype="float32")
        assert sr == SR
        cut = lambda a, b, audio=audio: audio[int(a * SR):int(b * SR)]       # noqa: E731
        s20, e20, t20 = _pick(meta["segments"], 20.0)
        s15, e15, t15 = _pick(meta["segments"], 20.0 * SLOW)
        base = cut(s15, e15)
        durs = {
            "normal20": _save("normal20", lang, cut(s20, e20), t20, meta),
            "normal15": _save("normal15", lang, base, t15, meta),
            "lenta20": _save("lenta20", lang, _slow_down(base, SLOW), t15, meta),
            "pausada20": _save("pausada20", lang, _add_pauses(base, len(base) / SR / SLOW), t15, meta),
        }
        print(f"{lang}: " + "  ".join(f"{k} {v:.1f}s" for k, v in durs.items()), file=sys.stderr)


if __name__ == "__main__":
    main()
