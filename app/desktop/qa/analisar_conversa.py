#!/usr/bin/env python3
"""Análise da conversa bilateral: fala por fala, o que o Praxis entendeu e traduziu, o erro,
o atraso e os defeitos (fala perdida, partida demais, tradução que não tocou).

Uso: python analisar_conversa.py <eventos.jsonl> /tmp/conversa.json <run_benchmarks.py dir>
"""
import json
import statistics
import sys

sys.path.insert(0, sys.argv[3])
import run_benchmarks as rb  # noqa: E402

eventos = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
roteiro = json.load(open(sys.argv[2]))
ev = [e["ev"] for e in eventos if e.get("e") == "engine"]
outros = [e for e in eventos if e.get("e") in ("error", "stopped")]
defeitos = []
for dir_, quem, lang in (("out", "eu", "pt"), ("in", "outro", "en")):
    refs = [r for r in roteiro if r["quem"] == quem]
    tr = [x["text"] for x in ev if x.get("e") == "transcript" and x.get("dir") == dir_]
    tl = [x["text"] for x in ev if x.get("e") == "translation" and x.get("dir") == dir_]
    segs = {x["id"]: x for x in ev if x.get("e") == "segment" and x.get("dir") == dir_}
    plays = {}
    for x in ev:
        if x.get("e") == "play" and x.get("dir") == dir_:
            plays.setdefault(x["id"], x["start_s"])
    lat = [(plays[i] - s["speech_end_s"]) for i, s in segs.items() if i in plays]
    wer, _ = rb.wer_cer([" ".join(r["texto"] for r in refs)], [" ".join(tr)])
    nome = "EU (pt → en, vai para o app de chamada)" if quem == "eu" else "OUTRA PESSOA (en → pt, toca na minha saída)"
    print(f"\n== {nome}")
    print(f"falas no roteiro: {len(refs)} | trechos entendidos: {len(tr)} | traduções: {len(tl)} | trechos tocados: {len(plays)}")
    print(f"erro de palavras do reconhecimento (sem auditar): {wer:.1%}")
    if lat:
        print(f"atraso fim da fala → som: típico {statistics.median(lat):.2f} s, máximo {max(lat):.2f} s")
    if len(tl) < len(tr):
        defeitos.append(f"{quem}: {len(tr) - len(tl)} trecho(s) entendido(s) sem tradução")
    if len(plays) < len(tl):
        defeitos.append(f"{quem}: {len(tl) - len(plays)} tradução(ões) que não tocaram")
    if len(tr) > 2 * len(refs):
        defeitos.append(f"{quem}: falas partidas demais ({len(tr)} trechos para {len(refs)} falas)")
    if lat and max(lat) > 4:
        defeitos.append(f"{quem}: atraso máximo alto ({max(lat):.1f} s)")
    for t_, l_ in zip(tr, tl):
        print(f"  · {t_[:70]}\n    → {l_[:70]}")
erros = [e for e in outros if e.get("e") == "error"] + [x for x in ev if x.get("e") == "error"]
if erros:
    defeitos += [f"erro: {e.get('msg')}" for e in erros]
print("\n== DEFEITOS" if defeitos else "\n== Nenhum defeito encontrado")
for d in defeitos:
    print(" -", d)
