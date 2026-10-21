#!/usr/bin/env python3
"""Baixa frases do FLEURS (Google) nos 16 idiomas do Praxis para medir a
transcrição de cada idioma com VÁRIOS falantes — uma medição de um falante só
pode condenar (ou salvar) um idioma por acaso.

O FLEURS é o mesmo conjunto de frases (artigos da Wikipédia) lido por pessoas
diferentes em cada idioma, então a dificuldade do texto é parecida entre os
idiomas. Licença CC BY 4.0. Só o começo do arquivo de teste de cada idioma é
baixado (para assim que juntar `--per-lang` frases distintas).

Saída: benchmarks/data/speech_fleurs/<idioma>/*.wav + manifest.json
       (mesmo formato de fetch_speech_corpus.py; use run_benchmarks.py asr --corpus speech_fleurs)

Uso: python benchmarks/fetch_fleurs_corpus.py [--langs pt en] [--per-lang 40]
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import sys
import tarfile
import urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf

BASE = "https://huggingface.co/datasets/google/fleurs/resolve/main/data"
OUT = Path(__file__).resolve().parent / "data" / "speech_fleurs"
SR = 16000
CFG = {"pt": "pt_br", "en": "en_us", "es": "es_419", "fr": "fr_fr", "de": "de_de", "it": "it_it",
       "nl": "nl_nl", "pl": "pl_pl", "ru": "ru_ru", "zh": "cmn_hans_cn", "uk": "uk_ua",
       "tr": "tr_tr", "ar": "ar_eg", "hi": "hi_in", "ja": "ja_jp", "ko": "ko_kr"}


def fetch(lang: str, per_lang: int) -> int:
    cfg = CFG[lang]
    d = OUT / lang
    d.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(f"{BASE}/{cfg}/test.tsv", timeout=120) as r:
        tsv = r.read().decode("utf-8")
    meta = {}
    for row in csv.reader(io.StringIO(tsv), delimiter="\t", quoting=csv.QUOTE_NONE):
        if len(row) >= 7:
            # id da frase, arquivo, texto original, normalizado, fonemas, amostras, gênero
            meta[row[1]] = {"id": row[0], "text": row[2], "gender": row[6]}
    items, used = [], set()
    with urllib.request.urlopen(f"{BASE}/{cfg}/audio/test.tar.gz", timeout=600) as resp, \
            tarfile.open(fileobj=resp, mode="r|gz") as tar:
        for m in tar:
            name = m.name.rsplit("/", 1)[-1]
            if not m.isfile() or name not in meta or meta[name]["id"] in used:
                continue
            a, sr = sf.read(io.BytesIO(tar.extractfile(m).read()), dtype="float32", always_2d=True)
            a = a.mean(axis=1)
            if sr != SR:
                a = np.interp(np.linspace(0, len(a) - 1, int(round(len(a) * SR / sr))),
                              np.arange(len(a)), a).astype(np.float32)
            if len(a) / SR > 25:
                continue
            used.add(meta[name]["id"])
            fname = name.replace(".wav", "") + ".wav"
            sf.write(str(d / fname), a, SR, subtype="PCM_16")
            # o FLEURS não publica quem é o falante; cada frase vem de uma gravação
            # diferente, então "falante" aqui é a própria gravação
            items.append({"file": fname, "text": meta[name]["text"], "speaker": name,
                          "gender": meta[name]["gender"], "duration": round(len(a) / SR, 2),
                          "source": f"google/fleurs {cfg} (test)", "license": "CC BY 4.0"})
            if len(items) >= per_lang:
                break
    (d / "manifest.json").write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(items)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", nargs="+", default=list(CFG))
    ap.add_argument("--per-lang", type=int, default=40)
    a = ap.parse_args()
    for lang in a.langs:
        try:
            print(f"{lang}: {fetch(lang, a.per_lang)} frases", file=sys.stderr)
        except Exception as e:                       # um idioma com problema não para os outros
            print(f"{lang}: falhou ({type(e).__name__}: {e})", file=sys.stderr)


if __name__ == "__main__":
    main()
