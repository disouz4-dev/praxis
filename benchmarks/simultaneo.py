#!/usr/bin/env python3
"""Tradução SIMULTÂNEA × tradução por frase, medida no FLEURS.

Simultânea ("acordo local", como o Whisper-Streaming): a cada PASSO segundos de áudio, o
Whisper relê o trecho ainda não confirmado; as palavras que saem iguais em duas leituras
seguidas são confirmadas. Os pedaços confirmados vão para a tradução assim que chegam numa
pontuação ou juntam N palavras, e são falados na hora — sem esperar o fim da frase.

O relógio é simulado com os tempos reais de processamento: um passo só começa quando o
anterior terminou (se o processamento for mais lento que o tempo real, o atraso acumula).

Mede, por palavra dita: o ATRASO até a tradução dela começar a ser falada; e, por frase,
o erro do reconhecimento e a fidelidade da tradução (chrF, 0–100) contra a tradução humana
do FLEURS — nos dois modos.

Uso (lab2, placa de vídeo):
  python benchmarks/simultaneo.py --par pt:en --n 15 --passo 1.0 --palavras 6
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
sys.path.insert(0, str(ROOT))

FLEURS = {"pt": "pt_br", "en": "en_us", "es": "es_419", "de": "de_de", "fr": "fr_fr", "it": "it_it"}
VOZ_S = 0.28          # 1º pedaço da voz (Kokoro na placa de vídeo, medido)
SILENCIO_S = 0.5      # espera pelo silêncio no modo por frase (medido no motor em Rust)
FIM = re.compile(r"[,.;:?!…]$")


def textos_paralelos(src: str, tgt: str) -> dict[str, str]:
    """arquivo de áudio (src) → a mesma frase escrita por uma pessoa no idioma tgt."""
    def ler(lang):
        with open(ROOT / "data" / "fleurs_texto" / FLEURS[lang] / "test.tsv", encoding="utf-8") as f:
            return list(csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE))
    por_id = {r[0]: r[2] for r in ler(tgt)}
    return {r[1]: por_id[r[0]] for r in ler(src) if r[0] in por_id}


def norm(w: str) -> str:
    return re.sub(r"[^\w]", "", w.lower())


def continuar(prefixo_fonte: str, falado: list[str], src: str, tgt: str) -> list[str]:
    """Tradução da frase até aqui, OBRIGADA a começar pelo que já foi falado (o NLLB continua a
    partir dessas palavras): a qualidade fica perto da tradução da frase inteira."""
    import praxis
    tr, sp = praxis._load_nllb()
    s, t = praxis.NLLB_CODES[src], praxis.NLLB_CODES[tgt]
    alvo = [t] + (sp.encode(" ".join(falado), out_type=str) if falado else [])
    r = tr.translate_batch([[s] + sp.encode(prefixo_fonte, out_type=str) + ["</s>"]],
                           target_prefix=[alvo], beam_size=2, replace_unknowns=True)[0]
    return sp.decode([tok for tok in r.hypotheses[0] if tok != t]).split()


def simultaneo(model, audio, lang, tgt, passo, n_palavras):
    """→ (texto confirmado, [(palavras de origem, palavras ditas, momento em que começam a soar)])."""
    sr = 16000
    dur = len(audio) / sr
    confirmadas: list[tuple[str, float]] = []       # (palavra, fim no áudio)
    anterior: list[tuple[str, float]] = []
    inicio_buf = 0.0                                 # o buffer só é cortado no fim de uma frase
    livre = 0.0                                      # quando o processamento fica livre
    frase: list[tuple[str, float]] = []              # palavras da frase em curso
    falado: list[str] = []                           # tradução já dita da frase em curso
    sem_voz: list[tuple[str, float]] = []            # palavras de origem ainda sem tradução dita
    saida = []
    t = passo
    while True:
        ultimo = t >= dur
        t = min(t, dur)
        comeca = max(t, livre)
        c0 = time.perf_counter()
        buf = audio[int(inicio_buf * sr):int(t * sr)]
        segs, _ = model.transcribe(buf, language=lang, beam_size=1, word_timestamps=True,
                                   condition_on_previous_text=False, vad_filter=False)
        hip = [(w.word.strip(), inicio_buf + w.end) for s in segs for w in (s.words or []) if w.word.strip()]
        ja = len(confirmadas) - len([w for w in confirmadas if w[1] <= inicio_buf])   # confirmadas dentro do buffer
        hip_novas = hip[ja:]
        if ultimo:
            novas = hip_novas
        else:
            k = 0
            while k < min(len(hip_novas), len(anterior)) and norm(hip_novas[k][0]) == norm(anterior[k][0]):
                k += 1
            novas = hip_novas[:k]
        anterior = hip_novas[len(novas):]
        livre = comeca + (time.perf_counter() - c0)
        confirmadas += novas
        frase += novas
        sem_voz += novas
        fim_frase = ultimo or (frase and re.search(r"[.?!…]$", frase[-1][0]))
        if sem_voz and (fim_frase or len(sem_voz) >= n_palavras):
            m0 = time.perf_counter()
            trad = continuar(" ".join(w for w, _ in frase), falado, lang, tgt)
            livre += time.perf_counter() - m0
            novas_tr = trad[len(falado):]
            if not fim_frase:
                novas_tr = novas_tr[:-2]        # as últimas palavras ainda podem mudar: espera
            if novas_tr or fim_frase:
                saida.append((sem_voz, novas_tr, livre + VOZ_S))
                falado += novas_tr
                sem_voz = []
        if fim_frase and frase:
            # frase encerrada: o próximo trecho começa limpo (buffer e tradução)
            inicio_buf = frase[-1][1]
            frase, falado = [], []
            anterior = []
        if ultimo:
            break
        t += passo
    return " ".join(w for w, _ in confirmadas), saida


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--par", default="pt:en")
    ap.add_argument("--n", type=int, default=15)
    ap.add_argument("--passo", type=float, default=1.0)
    ap.add_argument("--palavras", type=int, default=6)
    ap.add_argument("--nome", default=None)
    a = ap.parse_args()
    src, tgt = a.par.split(":")
    import praxis
    import run_benchmarks as rb
    import sacrebleu
    model = praxis.load_whisper("large-v3-turbo", "cuda")
    praxis.TRANSLATOR = "nllb"
    traduzir = lambda s: praxis.do_translate(s, src, tgt) if s.strip() else ""   # noqa: E731
    traduzir("aquecimento.")
    paralelo = textos_paralelos(src, tgt)
    corpus = [it for it in json.loads((ROOT / "data" / "speech_fleurs" / src / "manifest.json").read_text())
              if it["file"] in paralelo][:a.n]
    atrasos_sim, atrasos_frase, refs_asr, hip_sim, hip_frase = [], [], [], [], []
    tr_sim, tr_frase, refs_tr, n_pedacos = [], [], [], []
    for it in corpus:
        audio = rb.read16k(ROOT / "data" / "speech_fleurs" / src / it["file"])
        dur = len(audio) / 16000
        texto, saida = simultaneo(model, audio, src, tgt, a.passo, a.palavras)
        for pedaco, _, fala in saida:
            atrasos_sim += [fala - fim for _, fim in pedaco]
        # modo por frase: espera o silêncio, reconhece tudo, traduz tudo
        c0 = time.perf_counter()
        inteira = praxis.transcribe_segment(model, audio, src)
        tr_inteira = traduzir(inteira)
        pronto = dur + SILENCIO_S + (time.perf_counter() - c0) + VOZ_S
        # cada palavra espera até a frase inteira ser falada: atraso = pronto − fim da palavra
        segs, _ = model.transcribe(audio, language=src, word_timestamps=True, beam_size=1)
        atrasos_frase += [pronto - w.end for s in segs for w in (s.words or [])]
        refs_asr.append(it["text"]); hip_sim.append(texto); hip_frase.append(inteira)
        refs_tr.append(paralelo[it["file"]]); tr_sim.append(" ".join(w for _, t, _ in saida for w in t)); tr_frase.append(tr_inteira)
        n_pedacos.append(len(saida))
        print(f"  {it['file'][:12]}  {dur:5.1f}s  {len(saida)} pedaços | {' / '.join(' '.join(t) for _, t, _ in saida)[:110]}", flush=True)
    chrf = lambda h: sacrebleu.corpus_chrf(h, [refs_tr]).score   # noqa: E731
    q = lambda xs, p: sorted(xs)[int(p * (len(xs) - 1))]          # noqa: E731
    res = {
        "par": a.par, "frases": len(corpus), "passo_s": a.passo, "palavras_por_pedaco": a.palavras,
        "simultaneo": {"atraso_medio_s": statistics.mean(atrasos_sim), "atraso_mediana_s": q(atrasos_sim, .5),
                       "atraso_p90_s": q(atrasos_sim, .9), "erro_reconhecimento": rb.wer_cer(refs_asr, hip_sim)[0],
                       "fidelidade_chrf": chrf(tr_sim), "pedacos_por_frase": statistics.mean(n_pedacos)},
        "por_frase": {"atraso_medio_s": statistics.mean(atrasos_frase), "atraso_mediana_s": q(atrasos_frase, .5),
                      "atraso_p90_s": q(atrasos_frase, .9), "erro_reconhecimento": rb.wer_cer(refs_asr, hip_frase)[0],
                      "fidelidade_chrf": chrf(tr_frase)},
        "exemplos": [{"ref": r, "simultaneo": s, "por_frase": f} for r, s, f in list(zip(refs_tr, tr_sim, tr_frase))[:5]],
    }
    nome = a.nome or f"simultaneo-{src}-{tgt}-p{a.passo}-w{a.palavras}"
    (rb.RESULTS / f"{nome}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    for modo in ("simultaneo", "por_frase"):
        r = res[modo]
        print(f"{modo:11s} atraso por palavra: médio {r['atraso_medio_s']:.2f} s, mediana {r['atraso_mediana_s']:.2f} s, "
              f"90% até {r['atraso_p90_s']:.2f} s | erro {r['erro_reconhecimento']:.1%} | fidelidade {r['fidelidade_chrf']:.1f}")


if __name__ == "__main__":
    main()
