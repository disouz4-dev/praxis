#!/usr/bin/env python3
"""Monta ~60 s de fala real CONTÍNUA por idioma — um falante lendo sem
parar, com o texto de referência exato e o momento em que cada frase é dita.

  pt, es  Multilingual LibriSpeech (test): trechos consecutivos do mesmo
          arquivo de audiolivro, ordenados pelo begin_time original; a pausa
          real entre os trechos (fim → início do próximo) é mantida.
  en      LibriSpeech test-clean: ids de falas consecutivas de um capítulo,
          unidos com uma pausa de 0,4 s (as falas foram cortadas nas pausas).
  ru zh uk tr ar hi ja ko
          FLEURS (test): frases reais lidas, uma gravação por frase, unidas
          com uma pausa de 0,4 s. Os falantes se alternam entre as frases
          (o FLEURS não tem leituras longas de um só falante nesses idiomas).
          Só os primeiros MB do arquivo de cada idioma são baixados.

Tudo CC BY 4.0. Saída: benchmarks/data/continuous/<idioma>.wav (16 kHz mono) e
<idioma>.json = {text, speaker, source, license, duration, segments:[{start, end, text}]}

Uso: python benchmarks/fetch_continuous_speech.py [--langs pt en es] [--seconds 60]
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np
import soundfile as sf

API = "https://datasets-server.huggingface.co"
OUT = Path(__file__).resolve().parent / "data" / "continuous"
SR = 16000
MLS = {"pt": "portuguese", "es": "spanish", "fr": "french", "de": "german", "it": "italian",
       "nl": "dutch", "pl": "polish"}
FLEURS = {"ru": "ru_ru", "zh": "cmn_hans_cn", "uk": "uk_ua", "tr": "tr_tr", "ar": "ar_eg",
          "hi": "hi_in", "ja": "ja_jp", "ko": "ko_kr"}
FLEURS_BASE = "https://huggingface.co/datasets/google/fleurs/resolve/main/data"
ALL_LANGS = ["pt", "en", "es", "fr", "de", "it", "nl", "pl", "ru", "zh", "uk", "tr", "ar", "hi",
             "ja", "ko"]


def _get(url: str, tries: int = 7) -> bytes:
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return r.read()
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(min(60, 3 * 2 ** i))
    raise RuntimeError


def _rows(ds: str, cfg: str, off: int, n: int = 100) -> list[dict]:
    q = urllib.parse.urlencode({"dataset": ds, "config": cfg, "split": "test",
                                "offset": off, "length": n})
    return [r["row"] for r in json.loads(_get(f"{API}/rows?{q}"))["rows"]]


def _audio(row: dict) -> np.ndarray:
    a, sr = sf.read(io.BytesIO(_get(row["audio"][0]["src"])), dtype="float32", always_2d=True)
    a = a.mean(axis=1)
    if sr != SR:
        a = np.interp(np.linspace(0, len(a) - 1, int(round(len(a) * SR / sr))),
                      np.arange(len(a)), a).astype(np.float32)
    return a


def _mls_chain(lang: str, seconds: float, max_gap: float = 1.2, scan_rows: int = 600):
    """Maior sequência de trechos consecutivos (mesmo arquivo do livro) ≥ `seconds`."""
    by_file: dict[str, list[dict]] = defaultdict(list)
    for off in range(0, scan_rows, 100):
        for r in _rows("facebook/multilingual_librispeech", MLS[lang], off):
            # guarda a URL assinada do áudio: as linhas só são buscadas de novo se ela expirar
            by_file[r["original_path"]].append(r)
        time.sleep(0.5)
    best: list[dict] = []
    for segs in by_file.values():
        segs.sort(key=lambda r: r["begin_time"])
        run = [segs[0]]
        for prev, cur in zip(segs, segs[1:]):
            gap = cur["begin_time"] - prev["end_time"]
            if 0 <= gap <= max_gap and cur["speaker_id"] == prev["speaker_id"]:
                run.append(cur)
            else:
                run = [cur]
            if run[-1]["end_time"] - run[0]["begin_time"] >= seconds:
                best = run
                break
        if best:
            break
    if not best:
        raise RuntimeError(f"nenhuma sequência contínua de {seconds}s encontrada para {lang}; aumente --scan")
    return best


def _fleurs(lang: str, seconds: float):
    """Lê o arquivo de teste do FLEURS em fluxo e para assim que `seconds` de
    frases distintas forem coletados (baixa só o começo)."""
    import csv
    import tarfile
    cfg = FLEURS[lang]
    tsv = _get(f"{FLEURS_BASE}/{cfg}/test.tsv").decode("utf-8")
    meta = {}
    for row in csv.reader(io.StringIO(tsv), delimiter="\t", quoting=csv.QUOTE_NONE):
        if len(row) >= 4:
            meta[row[1]] = (row[0], row[2], row[3])          # arquivo → (id da frase, bruto, normalizado)
    out, used, total = [], set(), 0.0
    with urllib.request.urlopen(f"{FLEURS_BASE}/{cfg}/audio/test.tar.gz", timeout=300) as resp, \
            tarfile.open(fileobj=resp, mode="r|gz") as tar:
        for m in tar:
            name = m.name.rsplit("/", 1)[-1]
            if not m.isfile() or name not in meta or meta[name][0] in used:
                continue
            a, sr = sf.read(io.BytesIO(tar.extractfile(m).read()), dtype="float32", always_2d=True)
            a = a.mean(axis=1)
            if sr != SR:
                a = np.interp(np.linspace(0, len(a) - 1, int(round(len(a) * SR / sr))),
                              np.arange(len(a)), a).astype(np.float32)
            used.add(meta[name][0])
            out.append((a, meta[name][1]))
            total += len(a) / SR + 0.4
            if total >= seconds:
                break
    return out


def build(lang: str, seconds: float) -> dict:
    pieces, segments, texts, t = [], [], [], 0.0
    if lang in FLEURS:
        speaker, source = "multiple (FLEURS)", "google/fleurs (test)"
        for a, text in _fleurs(lang, seconds):
            if pieces:
                pieces.append(np.zeros(int(0.4 * SR), np.float32))
                t += 0.4
            segments.append({"start": round(t, 3), "end": round(t + len(a) / SR, 3), "text": text})
            pieces.append(a)
            texts.append(text)
            t += len(a) / SR
    elif lang == "en":
        rows = _rows("openslr/librispeech_asr", "clean", 0, 100)
        first = rows[0]
        chap = [r for r in rows if r["chapter_id"] == first["chapter_id"]
                and r["speaker_id"] == first["speaker_id"]]
        chap.sort(key=lambda r: r["id"])
        speaker, source = str(first["speaker_id"]), "openslr/librispeech_asr (test-clean)"
        for r in chap:
            a = _audio(r)
            if pieces:
                pieces.append(np.zeros(int(0.4 * SR), np.float32))
                t += 0.4
            segments.append({"start": round(t, 3), "end": round(t + len(a) / SR, 3), "text": r["text"].lower()})
            pieces.append(a)
            texts.append(r["text"].lower())
            t += len(a) / SR
            if t >= seconds:
                break
    else:
        chain = _mls_chain(lang, seconds)
        speaker, source = str(chain[0]["speaker_id"]), "facebook/multilingual_librispeech (test)"
        prev_end = None
        for r in chain:
            if prev_end is not None:
                gap = max(0.0, r["begin_time"] - prev_end)
                pieces.append(np.zeros(int(gap * SR), np.float32))
                t += gap
            a = _audio(r)
            segments.append({"start": round(t, 3), "end": round(t + len(a) / SR, 3), "text": r["transcript"]})
            pieces.append(a)
            texts.append(r["transcript"])
            t += len(a) / SR
            prev_end = r["end_time"]
    audio = np.concatenate(pieces)
    OUT.mkdir(parents=True, exist_ok=True)
    sf.write(str(OUT / f"{lang}.wav"), audio, SR, subtype="PCM_16")
    meta = {"lang": lang, "text": " ".join(texts), "speaker": speaker, "source": source,
            "license": "CC BY 4.0", "duration": round(len(audio) / SR, 2), "segments": segments}
    (OUT / f"{lang}.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{lang}: {meta['duration']:.1f}s, falante {speaker}, {len(segments)} trechos, "
          f"{len(meta['text'].split())} palavras", file=sys.stderr)
    return meta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", nargs="+", default=ALL_LANGS, help="idiomas a montar")
    ap.add_argument("--seconds", type=float, default=60.0, help="duração mínima de fala por idioma, em s")
    a = ap.parse_args()
    for lang in a.langs:
        if (OUT / f"{lang}.json").exists():
            print(f"{lang}: já montado", file=sys.stderr)
            continue
        try:
            build(lang, a.seconds)
        except Exception as e:
            print(f"{lang}: FALHOU {type(e).__name__}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
