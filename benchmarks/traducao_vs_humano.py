#!/usr/bin/env python3
"""Qualidade REAL da tradução do Praxis comparada com traduções feitas por pessoas.

De onde vêm as traduções humanas
  O conjunto Google FLEURS tem a mesma frase (do conjunto FLoRes) escrita e lida
  em dezenas de idiomas. A coluna 0 dos arquivos test.tsv é o número da frase:
  o mesmo número = a mesma frase em cada idioma. Baixamos só o texto (sem áudio)
  dos 16 idiomas do Praxis e ficamos com as frases que existem em todos eles.

O que é medido
  a) idioma X → inglês, para os 15 idiomas de entrada que não são inglês;
  b) inglês → idioma X, para os 13 idiomas de saída que não são inglês;
  c) custo de passar pelo inglês: pares sem inglês (pt→es, es→pt, ...) são
     traduzidos em duas etapas (X → inglês → Y); comparamos a nota com a das
     traduções de uma etapa só que chegam no mesmo idioma;
  d) variante do português: nas saídas inglês → português, contamos marcas de
     português de Portugal ("estás", "está a fazer", "ecrã", "equipa"...) e
     marcas do português do Brasil ("você", "está fazendo", "tela", "equipe"...);
  e) tempo por frase no processador (sem placa de vídeo), em cada direção.

As duas notas (as duas vão de 0 a 100; quanto maior, melhor)
  fidelidade da tradução (chrF): compara a tradução do Praxis com a humana
    letra a letra, em pedaços de poucas letras. Tolera variações de flexão
    ("traduzido"/"traduzida") e é a nota mais confiável para frases soltas.
  coincidência de trechos (BLEU): conta quantas sequências de 1 a 4 palavras
    seguidas da tradução do Praxis aparecem iguais na tradução humana. É mais
    rígida: um sinônimo correto já tira pontos. Notas de 30 a 40 já são boas.

As traduções usam exatamente o caminho de produção: praxis.setup_argos (baixa
os pacotes que faltam) e praxis.do_translate (passa pelo inglês quando nenhum
dos lados é inglês).

Uso:
  .venv312/bin/python benchmarks/traducao_vs_humano.py [--n 60]
Resultados: benchmarks/results/traducao-vs-humano.json e .md
"""
from __future__ import annotations

import argparse
import csv
import json
import platform
import re
import sys
import time
import urllib.request
from pathlib import Path

import sacrebleu

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import praxis  # noqa: E402

DATA = ROOT / "benchmarks" / "data" / "fleurs_texto"
RESULTS = ROOT / "benchmarks" / "results"
URL = "https://huggingface.co/datasets/google/fleurs/resolve/main/data/{cfg}/{split}.tsv"

# código do Praxis → nome da configuração no FLEURS
FLEURS = {
    "pt": "pt_br", "en": "en_us", "es": "es_419", "fr": "fr_fr", "de": "de_de",
    "it": "it_it", "ru": "ru_ru", "zh": "cmn_hans_cn", "nl": "nl_nl", "pl": "pl_pl",
    "uk": "uk_ua", "tr": "tr_tr", "ar": "ar_eg", "hi": "hi_in", "ja": "ja_jp", "ko": "ko_kr",
}
NOMES = {
    "pt": "português", "en": "inglês", "es": "espanhol", "fr": "francês", "de": "alemão",
    "it": "italiano", "ru": "russo", "zh": "chinês", "nl": "holandês", "pl": "polonês",
    "uk": "ucraniano", "tr": "turco", "ar": "árabe", "hi": "hindi", "ja": "japonês",
    "ko": "coreano",
}
SAIDA = ["pt", "en", "es", "fr", "de", "it", "ru", "zh", "nl", "pl", "uk", "tr", "ar", "hi"]
ENTRADA = SAIDA + ["ja", "ko"]
PARES_PIVO = [("pt", "es"), ("es", "pt"), ("pt", "fr"), ("fr", "pt"), ("de", "pt"),
              ("pt", "it"), ("it", "pt"), ("ru", "uk")]

# Em chinês a fidelidade (chrF) não é comparável com os outros idiomas: ela olha
# pedaços de até 6 caracteres, e um único caractere chinês já é uma palavra
# inteira, então a nota fica baixa mesmo com tradução razoável. Para o chinês
# como destino, a nota que vale é a coincidência de trechos (cortada por caractere).
SEM_COMPARACAO_CHRF = {"zh"}


def comparavel(r: dict) -> bool:
    return r["tgt"] not in SEM_COMPARACAO_CHRF


# Marcas de português de Portugal (PT-PT) e do Brasil (PT-BR)
MARCAS_PT_PT = {
    "estás": r"\bestás\b",
    "estar a + verbo (ex.: está a fazer)":
        r"\b(estou|estás|está|estamos|estão|estava|estavam|estive|esteve)\s+a\s+\w+(ar|er|ir)\b",
    "autocarro": r"\bautocarros?\b",
    "comboio": r"\bcomboios?\b",
    "ecrã": r"\becrãs?\b",
    "telemóvel": r"\btelemóve(l|is)\b",
    "equipa": r"\bequipas?\b",
    "utilizador": r"\butilizador(es|a|as)?\b",
    "facto": r"\bfactos?\b",
    "connosco": r"\bconnosco\b",
    "registo": r"\bregistos?\b",
    "receção": r"\breceç(ão|ões)\b",
    "contacto": r"\bcontactos?\b",
    "actual/acção (grafia antiga)": r"\b(actual\w*|acção|acções|direcção|óptim\w*)\b",
}
MARCAS_PT_BR = {
    "você": r"\bvocês?\b",
    "estar + gerúndio (ex.: está fazendo)":
        r"\b(estou|está|estamos|estão|estava|estavam)\s+\w+ndo\b",
    "ônibus": r"\bônibus\b",
    "trem": r"\btrens?\b",
    "tela": r"\btelas?\b",
    "celular": r"\bcelulares?\b",
    "equipe": r"\bequipes?\b",
    "usuário": r"\busuári[oa]s?\b",
    "fato": r"\bfatos?\b",
    "conosco": r"\bconosco\b",
    "registro": r"\bregistros?\b",
    "recepção": r"\brecepção\b",
    "contato": r"\bcontatos?\b",
}


# ---------------------------------------------------------------- dados

def baixar(cfg: str, split: str = "test") -> Path:
    """Baixa (uma vez) o arquivo de texto do FLEURS para um idioma."""
    destino = DATA / cfg / f"{split}.tsv"
    if destino.exists() and destino.stat().st_size > 0:
        return destino
    destino.parent.mkdir(parents=True, exist_ok=True)
    print(f"  baixando {cfg}/{split}.tsv ...", flush=True)
    with urllib.request.urlopen(URL.format(cfg=cfg, split=split), timeout=60) as r:
        destino.write_bytes(r.read())
    return destino


def ler_frases(path: Path) -> dict[int, str]:
    """Lê o TSV e devolve {número da frase: texto com pontuação}. Várias linhas
    repetem a mesma frase (pessoas diferentes lendo); fica a primeira."""
    frases: dict[int, str] = {}
    with path.open(encoding="utf-8", newline="") as f:
        for linha in csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            if len(linha) < 3 or not linha[0].strip().isdigit():
                continue
            fid = int(linha[0])
            texto = linha[2].strip()
            if texto and fid not in frases:
                frases[fid] = texto
    return frases


def montar_conjunto(n: int) -> tuple[list[int], dict[str, list[str]]]:
    """Frases presentes nos 16 idiomas (test; completa com dev se faltar)."""
    por_lang: dict[str, dict[int, str]] = {lang: {} for lang in FLEURS}
    for split in ("test", "dev"):
        for lang, cfg in FLEURS.items():
            for fid, t in ler_frases(baixar(cfg, split)).items():
                por_lang[lang].setdefault(fid, t)
        comuns = set.intersection(*(set(d) for d in por_lang.values()))
        if len(comuns) >= n:
            break
    ids = sorted(comuns)[:n]
    return ids, {lang: [por_lang[lang][i] for i in ids] for lang in FLEURS}


# ---------------------------------------------------------------- medidas

def tokenizacao(tgt: str) -> str:
    """Chinês e japonês não separam palavras com espaço: a coincidência de
    trechos precisa cortar por caractere nesses idiomas."""
    return {"zh": "zh", "ja": "char", "ko": "char"}.get(tgt, "13a")


def notas(hipoteses: list[str], referencias: list[str], tgt: str) -> dict:
    chrf = sacrebleu.corpus_chrf(hipoteses, [referencias])
    bleu = sacrebleu.corpus_bleu(hipoteses, [referencias], tokenize=tokenizacao(tgt))
    return {"fidelidade_chrf": round(chrf.score, 1), "coincidencia_bleu": round(bleu.score, 1)}


# Letras esperadas em cada idioma de destino (para achar saída na escrita errada)
ESCRITA = {
    "ru": r"[\u0400-\u04FF]", "uk": r"[\u0400-\u04FF]", "ar": r"[\u0600-\u06FF]",
    "hi": r"[\u0900-\u097F]", "zh": r"[\u4E00-\u9FFF]",
}
LETRAS_LATINAS = r"[A-Za-zÀ-ÿ]"
NAO_LATINAS = r"[\u0400-\u04FF\u0600-\u06FF\u0900-\u097F\u3040-\u30FF\u4E00-\u9FFF\uAC00-\uD7AF]"


def problemas(saida: str, ref: str, origem: str = "", tgt: str = "") -> list[str]:
    """Sinais de saída quebrada: vazia, repetição em laço, comprimento absurdo,
    escrita errada (ex.: ficou em inglês quando devia sair em árabe), letras do
    idioma de origem que vazaram, ou frase sem nenhuma relação com a humana."""
    p = []
    if not saida.strip():
        return ["vazia"]
    if tgt in ESCRITA:
        alvo = len(re.findall(ESCRITA[tgt], saida))
        latinas = len(re.findall(LETRAS_LATINAS, saida))
        # em chinês cada caractere já é uma palavra; nomes próprios em letras latinas
        # são comuns, então só acusa quando quase não há caracteres chineses
        if (alvo < 5) if tgt == "zh" else (alvo < latinas):
            p.append("escrita errada (não traduziu)")
    elif re.search(NAO_LATINAS, saida):
        p.append("letras do idioma de origem vazaram")
    if tgt not in SEM_COMPARACAO_CHRF and sacrebleu.sentence_chrf(saida, [ref]).score < 20:
        p.append("quase nada em comum com a humana (possível frase inventada)")
    pal = saida.split()
    if len(pal) >= 9:
        trigramas = [" ".join(pal[i:i + 3]).lower() for i in range(len(pal) - 2)]
        if max(trigramas.count(t) for t in set(trigramas)) >= 3:
            p.append("repetição em laço")
    elif len(saida) >= 30:  # escrita sem espaços (chinês): procura um pedaço repetido
        if re.search(r"(.{4,}?)\1{2,}", saida):
            p.append("repetição em laço")
    if len(saida) > 2.5 * max(len(ref), 1):
        p.append("muito mais longa que a humana")
    if len(saida) < 0.3 * len(ref):
        p.append("muito mais curta que a humana")
    return p


def traduzir_direcao(src: str, tgt: str, frases: dict[str, list[str]]) -> dict:
    nome = f"{src}→{tgt}"
    try:
        praxis.setup_argos(src, tgt)
    except SystemExit as e:  # setup_argos encerra o programa se o par não existe
        return {"direcao": nome, "erro": f"instalação falhou: {e}"}
    except Exception as e:
        return {"direcao": nome, "erro": f"instalação falhou: {type(e).__name__}: {e}"}
    fontes, refs = frases[src], frases[tgt]
    try:
        praxis.do_translate(fontes[0], src, tgt)  # aquecimento: carrega o modelo
        saidas, tempos = [], []
        for s in fontes:
            t0 = time.perf_counter()
            saidas.append(praxis.do_translate(s, src, tgt))
            tempos.append(time.perf_counter() - t0)
    except Exception as e:
        return {"direcao": nome, "erro": f"tradução falhou: {type(e).__name__}: {e}"}
    quebradas = []
    for i, (s, r, o) in enumerate(zip(fontes, refs, saidas)):
        p = problemas(o, r, s, tgt)
        if p:
            quebradas.append({"i": i, "problemas": p, "origem": s, "praxis": o})
    tempos_ord = sorted(tempos)
    res = {
        "direcao": nome, "src": src, "tgt": tgt,
        "passa_pelo_ingles": src != "en" and tgt != "en",
        **notas(saidas, refs, tgt),
        "tempo_medio_s": round(sum(tempos) / len(tempos), 3),
        "tempo_mediano_s": round(tempos_ord[len(tempos_ord) // 2], 3),
        "tempo_max_s": round(tempos_ord[-1], 3),
        "saidas_suspeitas": quebradas,
        "saidas": saidas,
    }
    print(f"  {nome:7s} fidelidade {res['fidelidade_chrf']:5.1f}  "
          f"coincidência {res['coincidencia_bleu']:5.1f}  "
          f"{res['tempo_medio_s'] * 1000:6.0f} ms/frase  suspeitas {len(quebradas)}", flush=True)
    return res


def contar_variante(textos: list[str]) -> dict:
    """Quantas frases têm marcas de PT-PT e de PT-BR, e quais marcas apareceram."""
    def achar(marcas: dict[str, str], t: str) -> list[str]:
        return [nome for nome, rx in marcas.items() if re.search(rx, t, re.IGNORECASE)]
    com_pt, com_br, achados_pt, achados_br, exemplos = 0, 0, {}, {}, []
    for t in textos:
        pt, br = achar(MARCAS_PT_PT, t), achar(MARCAS_PT_BR, t)
        com_pt += bool(pt)
        com_br += bool(br)
        for m in pt:
            achados_pt[m] = achados_pt.get(m, 0) + 1
        for m in br:
            achados_br[m] = achados_br.get(m, 0) + 1
        if pt and len(exemplos) < 5:
            exemplos.append({"texto": t, "marcas": pt})
    n = max(len(textos), 1)
    return {
        "frases": len(textos),
        "frases_com_marca_pt_pt": com_pt, "parcela_pt_pt_pct": round(100 * com_pt / n, 1),
        "frases_com_marca_pt_br": com_br, "parcela_pt_br_pct": round(100 * com_br / n, 1),
        "marcas_pt_pt": achados_pt, "marcas_pt_br": achados_br, "exemplos_pt_pt": exemplos,
    }


# ---------------------------------------------------------------- relatório

def tabela(linhas: list[dict], frases_n: int) -> list[str]:
    out = ["| Direção | Fidelidade da tradução (0–100) | Coincidência de trechos (0–100) "
           "| Tempo médio por frase | Saídas suspeitas |",
           "|---|---:|---:|---:|---:|"]
    for r in linhas:
        if "erro" in r:
            out.append(f"| {r['direcao']} | — | — | — | {r['erro']} |")
            continue
        out.append(f"| {r['direcao']} ({NOMES[r['src']]} → {NOMES[r['tgt']]}) "
                   f"| {r['fidelidade_chrf']:.1f} | {r['coincidencia_bleu']:.1f} "
                   f"| {r['tempo_medio_s'] * 1000:.0f} ms | {len(r['saidas_suspeitas'])}/{frases_n} |")
    return out


def relatorio(res: dict) -> str:
    n = res["frases"]
    md = ["# Tradução do Praxis comparada com tradução humana", "",
          f"Data: {res['data']} · Máquina: {res['maquina']} · só processador (sem placa de vídeo) · "
          f"{n} frases do conjunto FLEURS/FLoRes, as mesmas nos 16 idiomas.", "",
          "## Como ler as notas", "",
          "- **Fidelidade da tradução (0–100)** — nome técnico chrF. Compara a tradução do Praxis "
          "com a de uma pessoa, em pedaços de poucas letras. Tolera pequenas diferenças de "
          "flexão. Como referência: acima de 60 costuma ser uma tradução boa e fácil de "
          "entender; entre 45 e 60, entende-se a ideia com erros; abaixo de 45, há perda séria "
          "de sentido.",
          "- **Coincidência de trechos (0–100)** — nome técnico BLEU. Conta sequências de 1 a 4 "
          "palavras iguais às da tradução humana. É rígida (um sinônimo correto já tira pontos), "
          "então números de 30 a 40 já indicam boa tradução.",
          "- **Saídas suspeitas** — traduções vazias; que repetem o mesmo trecho em laço; com "
          "comprimento muito diferente da humana (mais de 2,5 vezes maior ou menos de 30%); na "
          "escrita errada (ex.: saiu em inglês quando devia sair em árabe); com letras do "
          "idioma de origem no meio do inglês; ou com fidelidade da frase abaixo de 20, sinal "
          "de frase inventada sem relação com o original (este último pode acusar também uma "
          "tradução certa escrita de um jeito bem diferente da humana; confira o exemplo).",
          "- **Chinês como destino (en→zh):** a fidelidade fica baixa por construção (um "
          "caractere chinês já é uma palavra inteira), então não dá para compará-la com a dos "
          "outros idiomas; para o chinês olhe a coincidência de trechos. Por isso o en→zh fica "
          "fora da lista de piores direções.",
          "- O tempo é medido por frase, depois de o modelo já estar carregado.", ""]
    for chave, titulo in (("x_para_en", "a) De cada idioma para o inglês"),
                          ("en_para_x", "b) Do inglês para cada idioma"),
                          ("pivo", "c) Pares sem inglês (passam pelo inglês: duas traduções seguidas)")):
        md += [f"## {titulo}", ""] + tabela(res[chave], n) + [""]

    md += ["### Quanto se perde ao passar pelo inglês", "",
           "Comparamos cada par sem inglês com a tradução de uma etapa só que chega no mesmo "
           "idioma (inglês → destino), porque as notas só são comparáveis quando a tradução "
           "humana de referência é a mesma. Também mostramos a primeira etapa (origem → inglês).",
           "",
           "| Par | Fidelidade do par | inglês → destino | Diferença | origem → inglês | Diferença |",
           "|---|---:|---:|---:|---:|---:|"]
    for c in res["custo_pivo"]:
        md.append(f"| {c['par']} | {c['fidelidade']:.1f} | {c['en_para_destino']:.1f} | "
                  f"{c['perda_vs_en_para_destino']:+.1f} | {c['origem_para_en']:.1f} | "
                  f"{c['perda_vs_origem_para_en']:+.1f} |")
    md += ["", f"Perda média contra inglês → destino: **{res['custo_pivo_medio']:+.1f} pontos** "
           "de fidelidade.", ""]

    v, vh = res["variante_pt"], res["variante_pt_humano"]
    md += ["## d) Português de Portugal ou do Brasil? (saídas inglês → português)", "",
           f"- Frases do Praxis com alguma marca de **português de Portugal**: "
           f"**{v['frases_com_marca_pt_pt']} de {v['frases']} ({v['parcela_pt_pt_pct']:.0f}%)**.",
           f"- Frases do Praxis com alguma marca de **português do Brasil**: "
           f"{v['frases_com_marca_pt_br']} de {v['frases']} ({v['parcela_pt_br_pct']:.0f}%).",
           f"- Para comparar, a tradução humana brasileira das mesmas frases: "
           f"{vh['frases_com_marca_pt_pt']} com marca de Portugal, "
           f"{vh['frases_com_marca_pt_br']} com marca do Brasil.",
           f"- Marcas de Portugal encontradas no Praxis: "
           f"{', '.join(f'{k} ({q})' for k, q in v['marcas_pt_pt'].items()) or 'nenhuma'}.",
           f"- Marcas do Brasil encontradas no Praxis: "
           f"{', '.join(f'{k} ({q})' for k, q in v['marcas_pt_br'].items()) or 'nenhuma'}.", ""]
    if v["exemplos_pt_pt"]:
        md += ["Exemplos:", ""]
        md += [f"- “{e['texto']}” — marcas: {', '.join(e['marcas'])}" for e in v["exemplos_pt_pt"]]
        md.append("")

    validas = [r for r in res["x_para_en"] + res["en_para_x"] + res["pivo"] if "erro" not in r]
    md += ["## e) Tempo por frase", ""]
    lentas = sorted(validas, key=lambda r: -r["tempo_medio_s"])[:5]
    md += ["- Mais lentas: " + "; ".join(
        f"{r['direcao']} {r['tempo_medio_s'] * 1000:.0f} ms (máx. {r['tempo_max_s'] * 1000:.0f} ms)"
        for r in lentas) + ".",
        f"- Média geral: {1000 * sum(r['tempo_medio_s'] for r in validas) / len(validas):.0f} ms por frase.",
        ""]

    piores = sorted(filter(comparavel, validas), key=lambda r: r["fidelidade_chrf"])[:5]
    md += ["## Piores direções", ""]
    md += [f"{i}. {r['direcao']} — fidelidade {r['fidelidade_chrf']:.1f}, "
           f"coincidência {r['coincidencia_bleu']:.1f}" for i, r in enumerate(piores, 1)]
    pior = piores[0]
    md += ["", f"### Exemplos da pior direção ({pior['direcao']})", ""]
    for ex in res["exemplos_pior"]:
        md += [f"- **Original:** {ex['origem']}", f"  - **Humano:** {ex['humano']}",
               f"  - **Praxis:** {ex['praxis']}", ""]

    suspeitas = [(r["direcao"], s) for r in validas for s in r["saidas_suspeitas"]]
    md += ["## Saídas suspeitas", ""]
    if not suspeitas:
        md += ["Nenhuma.", ""]
    else:
        md += [f"Total: {len(suspeitas)} saídas em {len({d for d, _ in suspeitas})} direções.", ""]
        md += [f"- {d}: {', '.join(s['problemas'])} — original “{s['origem'][:160]}” → "
               f"Praxis “{s['praxis'][:200]}”" for d, s in suspeitas[:25]]
        md.append("")
    erros = [r for r in res["x_para_en"] + res["en_para_x"] + res["pivo"] if "erro" in r]
    if erros:
        md += ["## Direções que falharam", ""] + [f"- {r['direcao']}: {r['erro']}" for r in erros] + [""]

    md += ["## O que isso significa", "", res["significado"], ""]
    return "\n".join(md)


def significado(res: dict) -> str:
    validas = [r for r in res["x_para_en"] + res["en_para_x"] if "erro" not in r]
    validas = [r for r in validas if comparavel(r)]
    boas = [r["direcao"] for r in validas if r["fidelidade_chrf"] >= 60]
    fracas = [r["direcao"] for r in validas if r["fidelidade_chrf"] < 50]
    v = res["variante_pt"]
    partes = [
        f"Das {len(validas)} direções de uma etapa só (sem contar o en→zh, medido à parte), {len(boas)} ficaram com fidelidade de 60 "
        f"ou mais (tradução boa e fácil de entender)"
        + (f"; {len(fracas)} ficaram abaixo de 50 ({', '.join(fracas)}), faixa em que quem "
           "ouve entende a ideia geral mas perde detalhes e às vezes o sentido" if fracas else "")
        + ".",
        f"Passar pelo inglês custa em média {abs(res['custo_pivo_medio']):.1f} pontos de "
        "fidelidade frente à tradução direta do inglês para o mesmo idioma: os erros das "
        "duas etapas se somam.",
        f"No português, {v['parcela_pt_pt_pct']:.0f}% das frases traduzidas do inglês têm "
        "alguma marca de português de Portugal"
        + (" — para quem ouve no Brasil isso soa estrangeiro, mas raramente atrapalha o "
           "entendimento." if v["parcela_pt_pt_pct"] > 0 else "."),
        "Lembre que estas frases são textos de notícia e enciclopédia, mais difíceis que "
        "conversa do dia a dia, e que aqui o texto entra perfeito: numa chamada real, os "
        "erros da transcrição da fala somam-se a estes.",
    ]
    return " ".join(partes)


# ---------------------------------------------------------------- principal

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--n", type=int, default=60, help="número de frases (padrão 60)")
    ap.add_argument("--tradutor", default=None, choices=["argos", "nllb"],
                    help="tradutor do Praxis a medir (padrão: o configurado, Argos)")
    ap.add_argument("--nome", default="traducao-vs-humano", help="nome dos arquivos de resultado")
    args = ap.parse_args()
    if args.tradutor:
        praxis.TRANSLATOR = args.tradutor

    print("Montando o conjunto de frases paralelas...", flush=True)
    ids, frases = montar_conjunto(args.n)
    print(f"  {len(ids)} frases presentes nos 16 idiomas", flush=True)

    res: dict = {
        "data": time.strftime("%Y-%m-%d %H:%M"),
        "maquina": f"{platform.system()} {platform.machine()} · {platform.processor() or ''}".strip(" ·"),
        "fonte": "Google FLEURS (texto de test.tsv/dev.tsv, coluna raw_transcription)",
        "frases": len(ids), "ids": ids,
        "notas": {"fidelidade_chrf": "chrF de corpus (sacrebleu), 0–100",
                  "coincidencia_bleu": "BLEU de corpus (sacrebleu), 0–100; "
                                       "tokenização por caractere em chinês"},
    }
    print("\na) idioma → inglês", flush=True)
    res["x_para_en"] = [traduzir_direcao(s, "en", frases) for s in ENTRADA if s != "en"]
    print("\nb) inglês → idioma", flush=True)
    res["en_para_x"] = [traduzir_direcao("en", t, frases) for t in SAIDA if t != "en"]
    print("\nc) pares que passam pelo inglês", flush=True)
    res["pivo"] = [traduzir_direcao(s, t, frases) for s, t in PARES_PIVO]

    por_dir = {r["direcao"]: r for r in res["x_para_en"] + res["en_para_x"] + res["pivo"]
               if "erro" not in r}
    custo = []
    for s, t in PARES_PIVO:
        p, a, b = por_dir.get(f"{s}→{t}"), por_dir.get(f"en→{t}"), por_dir.get(f"{s}→en")
        if not (p and a and b):
            continue
        custo.append({
            "par": f"{s}→{t}", "fidelidade": p["fidelidade_chrf"],
            "en_para_destino": a["fidelidade_chrf"], "origem_para_en": b["fidelidade_chrf"],
            "perda_vs_en_para_destino": round(p["fidelidade_chrf"] - a["fidelidade_chrf"], 1),
            "perda_vs_origem_para_en": round(p["fidelidade_chrf"] - b["fidelidade_chrf"], 1),
            "coincidencia": p["coincidencia_bleu"], "coincidencia_en_para_destino": a["coincidencia_bleu"],
        })
    res["custo_pivo"] = custo
    res["custo_pivo_medio"] = round(sum(c["perda_vs_en_para_destino"] for c in custo)
                                    / max(len(custo), 1), 1)

    en_pt = por_dir.get("en→pt")
    res["variante_pt"] = contar_variante(en_pt["saidas"] if en_pt else [])
    res["variante_pt_humano"] = contar_variante(frases["pt"])

    validas = list(por_dir.values())
    pior = min(filter(comparavel, validas), key=lambda r: r["fidelidade_chrf"])
    # 5 exemplos da pior direção: as frases em que a saída mais se afasta da humana
    refs = frases[pior["tgt"]]
    notas_frase = [sacrebleu.sentence_chrf(o, [r]).score for o, r in zip(pior["saidas"], refs)]
    ordem = sorted(range(len(refs)), key=lambda i: notas_frase[i])[:5]
    res["exemplos_pior"] = [{"origem": frases[pior["src"]][i], "humano": refs[i],
                             "praxis": pior["saidas"][i],
                             "fidelidade_frase": round(notas_frase[i], 1)} for i in ordem]
    res["significado"] = significado(res)

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"{args.nome}.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    (RESULTS / f"{args.nome}.md").write_text(relatorio(res), encoding="utf-8")
    print(f"\nResultados em {RESULTS}/{args.nome}.(json|md)")


if __name__ == "__main__":
    main()
