#!/usr/bin/env python3
"""Separa o erro de verdade da diferença de escrita num resultado de
run_benchmarks.py asr (ex.: benchmarks/results/fleurs-gpu.json).

Para cada palavra que não bate com a transcrição humana:
  número       um dos lados tem algarismos ("3" × "três", "1990" × "mil novecentos e noventa")
  escrita      mesma palavra escrita de outro jeito: hífen/apóstrofo ("e-mail" × "email"),
               junção ("guarda chuva" × "guarda-chuva"), ou diferença de 1 letra numa palavra
               de 7+ letras ("colour" × "color"; curtas ficam como engano: "falo" × "falou") — o ouvinte entende igual
  nome         nome próprio (maiúscula no meio da frase na transcrição humana): o leitor
               pronuncia nomes estrangeiros do jeito dele; contado à parte
  engano       palavra trocada, faltando ou inventada: erro de verdade

"Erro real" = só os enganos, sobre o total de palavras da transcrição humana.
Em zh/ja (sem espaços) a conta é por letra e só há "engano".

Uso: python benchmarks/auditar_erros.py benchmarks/results/fleurs-gpu.json [--modelo large-v3-turbo] [--ao-vivo]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_benchmarks as rb  # noqa: E402

LETTER_LANGS = {"zh", "ja"}


def _lev(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _squash(s: str) -> str:
    return "".join(ch for ch in s if ch.isalnum())


def _no_accents(s: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c))


def proper_names(raw: str) -> set[str]:
    """Palavras com maiúscula no meio da frase na transcrição humana: nomes próprios
    (pessoas, lugares) — o leitor costuma pronunciá-los do jeito do idioma dele."""
    import re
    names = set()
    for sent in re.split(r"(?<=[.!?])\s+", raw):
        words = sent.split()
        for w in words[1:]:
            w2 = w.strip(".,;:!?\"'()«»“”")
            if w2[:1].isupper():
                names.update(rb.normalize(w2).split())
    return names


def classify(ref_words: list[str], hyp_words: list[str], names: set[str] | None = None) -> Counter:
    """Alinha palavra a palavra (jiwer) e classifica cada diferença."""
    import jiwer
    names = names or set()
    out = Counter()
    al = jiwer.process_words(" ".join(ref_words), " ".join(hyp_words))
    for chunk in al.alignments[0]:
        r = ref_words[chunk.ref_start_idx:chunk.ref_end_idx]
        h = hyp_words[chunk.hyp_start_idx:chunk.hyp_end_idx]
        if chunk.type == "equal":
            continue
        rs, hs = " ".join(r), " ".join(h)
        n_ref = max(len(r), 1) if chunk.type != "insert" else len(h)
        if any(c.isdigit() for c in rs + hs):
            out["número"] += n_ref
        elif _squash(rs) and _squash(rs) == _squash(hs):
            out["escrita"] += n_ref
        elif r and all(w in names for w in r):
            out["nome"] += n_ref
        elif chunk.type == "substitute" and len(r) == len(h) and all(
                len(a) >= 4 and _no_accents(a) == _no_accents(b) for a, b in zip(r, h)):
            out["escrita"] += n_ref
        elif chunk.type == "substitute" and len(r) == len(h) and all(
                len(a) >= 7 and _lev(a, b) <= 1 for a, b in zip(r, h)):
            out["escrita"] += n_ref
        else:
            out["engano"] += n_ref
    return out


def audit(path: Path, model: str | None, live: bool) -> list[dict]:
    rep = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for r in rep["results"]:
        if model and r["model"] != model:
            continue
        lang = r["lang"]
        tot, words = Counter(), 0
        examples = []
        for s in r["samples"]:
            hyp = s.get("hyp_live" if live else "hyp", "")
            if lang in LETTER_LANGS:
                ref_c = [c for c in rb.normalize(s["ref"]) if not c.isspace()]
                hyp_c = [c for c in rb.normalize(hyp) if not c.isspace()]
                c = classify(ref_c, hyp_c)
                words += len(ref_c)
            else:
                ref_w, hyp_w = rb.normalize(s["ref"]).split(), rb.normalize(hyp).split()
                c = classify(ref_w, hyp_w, proper_names(s["ref"]))
                words += len(ref_w)
            tot += c
            if c.get("engano") and len(examples) < 4:
                examples.append({"humano": s["ref"], "praxis": hyp})
        total = sum(tot.values())
        rows.append({"model": r["model"], "lang": lang, "unidade": "letras" if lang in LETTER_LANGS else "palavras",
                     "erro_total": round(total / words, 4) if words else None,
                     "numero": round(tot["número"] / words, 4) if words else None,
                     "escrita": round(tot["escrita"] / words, 4) if words else None,
                     "nome": round(tot["nome"] / words, 4) if words else None,
                     "erro_real": round(tot["engano"] / words, 4) if words else None,
                     "exemplos": examples})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("arquivo")
    ap.add_argument("--modelo", default=None)
    ap.add_argument("--ao-vivo", action="store_true", help="audita o modo ao vivo (fala cortada em trechos)")
    a = ap.parse_args()
    rows = audit(Path(a.arquivo), a.modelo, a.ao_vivo)
    print("| Modelo | Idioma | Erro como medido | Número escrito diferente | Escrita diferente | Nome próprio | **Erro real** |")
    print("|---|---|---:|---:|---:|---:|---:|")
    for r in rows:
        print(f"| {r['model']} | {r['lang']} ({r['unidade']}) | {r['erro_total']:.1%} | {r['numero']:.1%} | "
              f"{r['escrita']:.1%} | {r['nome']:.1%} | **{r['erro_real']:.1%}** |")
    out = Path(a.arquivo).with_suffix("").as_posix() + ("-auditoria-ao-vivo.json" if a.ao_vivo else "-auditoria.json")
    Path(out).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
