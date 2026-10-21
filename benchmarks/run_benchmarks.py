#!/usr/bin/env python3
"""Benchmarks do Praxis com fala humana real (veja fetch_speech_corpus.py).

  asr      Qualidade da transcrição (taxa de erro de palavras / de caracteres)
           por idioma e modelo Whisper, em dois modos:
             full  — a frase inteira em uma única chamada (limite superior)
             live  — o áudio passa pelo vad_worker real do motor (detector de
                     fala Silero + cortes forçados a cada MAX_SEG_S), cada
                     trecho é transcrito separadamente e depois unido —
                     exatamente o que acontece durante uma chamada.
  latency  Do fim da fala ao primeiro áudio traduzido, por etapa:
             espera pelo silêncio (silêncio necessário para fechar um trecho)
             transcrição (Whisper)   tradução (Argos)   voz da 1ª frase (Piper)

Todos os números vêm dos mesmos caminhos de código usados em produção no
praxis.py (transcribe_segment, vad_worker, do_translate, load_piper).

Uso:
  python benchmarks/run_benchmarks.py asr --models tiny base small --langs pt en es
  python benchmarks/run_benchmarks.py latency --model small --pairs pt:en en:pt es:en
Resultados: benchmarks/results/<nome>.json + .md
"""
from __future__ import annotations

import argparse
import json
import platform
import queue
import re
import statistics
import sys
import threading
import time
import unicodedata
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import praxis  # noqa: E402

DATA = Path(__file__).resolve().parent / "data" / "speech"
ONLY_LIVE = False
CONTEXT_LIVE = False
RESULTS = Path(__file__).resolve().parent / "results"
VOICES = Path(__file__).resolve().parent / "data" / "voices"

PIPER_VOICES = {   # idioma → (localidade, locutor, qualidade)
    "en": ("en_US", "lessac", "medium"),
    "pt": ("pt_BR", "faber", "medium"),
    "es": ("es_ES", "sharvard", "medium"),
}


# ── normalização de texto + métricas ──────────────────────────────────────────

_ARABIC_TASHKEEL = re.compile("[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")


def normalize(text: str) -> str:
    """Minúsculas, remove pontuação/símbolos, junta espaços — SEM quebrar
    palavras de escritas que usam sinais combinantes (sinais vocálicos do
    hindi, tailandês…).

    Os sinais vocálicos opcionais do árabe (tashkeel) são removidos e as
    variantes de alef/yeh unificadas, pois as referências os incluem mas os
    reconhecedores de fala não. Os acentos são mantidos (distinguem palavras
    em pt/es/fr)."""
    t = unicodedata.normalize("NFKC", text).lower()
    t = t.replace("’", "'").replace("œ", "oe").replace("æ", "ae")
    t = _ARABIC_TASHKEEL.sub("", t)
    t = re.sub("[إأآٱ]", "ا", t).replace("ى", "ي")
    # pontuação (P*) e símbolos (S*) viram espaços; sinais (M*) continuam grudados
    t = "".join(" " if unicodedata.category(ch)[0] in "PS" else ch for ch in t)
    return re.sub(r"\s+", " ", t).strip()


def wer_cer(refs: list[str], hyps: list[str]) -> tuple[float, float]:
    import jiwer
    r = [normalize(x) for x in refs]
    h = [normalize(x) or "<empty>" for x in hyps]
    return float(jiwer.wer(r, h)), float(jiwer.cer(r, h))


def letter_error(ref: str, hyp: str) -> float:
    """Taxa de erro por letra, ignorando espaços: justa para idiomas em que o
    limite das palavras é ambíguo (chinês, japonês, coreano) e mostra que um
    erro de grafia (híndi) é uma letra errada, não uma palavra perdida."""
    import jiwer
    r = normalize(ref).replace(" ", "")
    h = normalize(hyp).replace(" ", "") or "∅"
    return float(jiwer.cer(r, h)) if r else 0.0


def load_corpus(lang: str) -> list[dict]:
    mf = DATA / lang / "manifest.json"
    if not mf.exists():
        return []
    items = json.loads(mf.read_text(encoding="utf-8"))
    for it in items:
        it["path"] = DATA / lang / it["file"]
    return [it for it in items if it["path"].exists()]


def read16k(path: Path) -> np.ndarray:
    a, sr = sf.read(str(path), dtype="float32", always_2d=True)
    a = a.mean(axis=1)
    assert sr == 16000, f"{path}: esperado 16 kHz, veio {sr}"
    return a


# ── segmentação ao vivo pelo vad_worker real ──────────────────────────────────

SEG_KW: dict = {}   # substituições do vad_worker para experimentos (max_seg_s, smart_cut, preroll_s)


def live_segments(audio: np.ndarray, trailing_silence_s: float = 0.6) -> list[np.ndarray]:
    """Passa o áudio bloco a bloco pelo praxis.vad_worker (detector de fala
    Silero, limiares de produção) e devolve os trechos int16 que ele emite."""
    chunk = praxis.VAD_CHUNK
    pad = np.zeros(int(trailing_silence_s * praxis.SR), np.float32)
    x = np.concatenate([audio, pad])
    audio_q: queue.Queue = queue.Queue()
    seg_q: queue.Queue = queue.Queue()
    stop = threading.Event()
    active = threading.Event()
    active.set()
    old_stop = praxis._stop
    praxis._stop = stop
    try:
        t = threading.Thread(target=praxis.vad_worker, args=(audio_q, seg_q, "vad", 0.1),
                             kwargs={"active": active, "ptt_flush": threading.Event(), **SEG_KW},
                             daemon=True)
        t.start()
        for i in range(0, len(x) - chunk + 1, chunk):
            audio_q.put(x[i:i + chunk].copy())
        while not audio_q.empty():
            time.sleep(0.01)
        time.sleep(0.3)
        stop.set()
        t.join(5)
    finally:
        praxis._stop = old_stop
    segs = []
    while not seg_q.empty():
        segs.append(seg_q.get())
    return segs


def vad_tail_ms(audio: np.ndarray) -> float | None:
    """Tempo entre o último bloco que o detector de fala considera fala e o
    momento em que ele emite "end" — a parte inevitável de 'esperar o
    silêncio' no atraso."""
    vad = praxis.OnnxSileroVAD(threshold=0.5, sampling_rate=praxis.SR,
                               min_silence_duration_ms=praxis.SILENCE_MS)
    chunk = praxis.VAD_CHUNK
    x = np.concatenate([audio, np.zeros(praxis.SR, np.float32)])
    last_speech = None
    end_at = None
    for i in range(0, len(x) - chunk + 1, chunk):
        piece = x[i:i + chunk]
        p = vad.prob(piece)
        if p >= vad.threshold:
            last_speech = (i + chunk) / praxis.SR
        # repete a lógica do iterador sem rodar o modelo de novo
        vad.current_sample += chunk
        if p >= vad.threshold and vad.temp_end:
            vad.temp_end = 0
        if p >= vad.threshold and not vad.triggered:
            vad.triggered = True
        elif p < vad.threshold - 0.15 and vad.triggered:
            if not vad.temp_end:
                vad.temp_end = vad.current_sample
            if vad.current_sample - vad.temp_end >= vad.min_silence:
                vad.triggered, vad.temp_end = False, 0
                end_at = (i + chunk) / praxis.SR
    if last_speech is None or end_at is None or end_at < last_speech:
        return None
    return (end_at - last_speech) * 1000


# ── benchmark de transcrição ──────────────────────────────────────────────────

DEVICE: str | None = None   # força o backend de transcrição (auto/cpu/cuda/mlx/whispercpp)


def bench_asr(models: list[str], langs: list[str], live: bool = True) -> dict:
    report: dict = {"kind": "asr", "machine": machine_info(), "results": [],
                    "config": {"seg": SEG_KW, "whisper": praxis.WHISPER_OPTS,
                               "max_seg_s": SEG_KW.get("max_seg_s", praxis.MAX_SEG_S)}}
    for model_name in models:
        whisper = praxis.load_whisper(model_name, DEVICE)
        for lang in langs:
            corpus = load_corpus(lang)
            if not corpus:
                print(f"  ! sem corpus para {lang} — rode fetch_speech_corpus.py", file=sys.stderr)
                continue
            refs, hyp_full, hyp_live, samples = [], [], [], []
            asr_t, audio_t, live_segs = 0.0, 0.0, 0
            live_t = 0.0
            for it in corpus:
                a = read16k(it["path"])
                t0 = time.perf_counter()
                h = "" if ONLY_LIVE else praxis.transcribe_segment(whisper, a, lang)
                dt = time.perf_counter() - t0
                asr_t += dt
                audio_t += len(a) / praxis.SR
                hl = ""
                if live:
                    segs = live_segments(a)
                    live_segs += len(segs)
                    t1 = time.perf_counter()
                    if CONTEXT_LIVE:
                        # o fim do que já foi transcrito vai como dica para o próximo trecho
                        parts: list[str] = []
                        for s_ in segs:
                            prev = " ".join(parts)[-praxis.CONTEXT_CHARS:] or None
                            parts.append(praxis.transcribe_segment(whisper, s_.astype(np.float32) / 32768.0,
                                                                   lang, prompt=prev))
                        hl = " ".join(filter(None, parts))
                    else:
                        hl = " ".join(filter(None, (
                            praxis.transcribe_segment(whisper, s.astype(np.float32) / 32768.0, lang)
                            for s in segs)))
                    live_t += time.perf_counter() - t1
                refs.append(it["text"])
                hyp_full.append(h)
                hyp_live.append(hl)
                w, _ = wer_cer([it["text"]], [h])
                wl = wer_cer([it["text"]], [hl])[0] if live else None
                samples.append({"file": it["file"], "speaker": it["speaker"],
                                "dur_s": round(len(a) / praxis.SR, 2), "ref": it["text"],
                                "hyp": h, "wer": round(w, 3), "asr_s": round(dt, 3),
                                **({"hyp_live": hl, "wer_live": round(wl, 3)} if live else {})})
                print(f"  {model_name:6} {lang} {it['file']}  erro de palavras {w:5.1%}"
                      + (f"  ao vivo {wl:5.1%}" if live else "") + f"  {dt:5.2f}s", file=sys.stderr)
            wer, cer = wer_cer(refs, hyp_full)
            row = {"model": model_name, "lang": lang, "n": len(corpus),
                   "backend": getattr(whisper, "backend", "cpu"),
                   "speakers": len({s["speaker"] for s in samples}),
                   "audio_s": round(audio_t, 1),
                   "wer": round(wer, 4), "cer": round(cer, 4),
                   "rtf": round(asr_t / audio_t, 3), "samples": samples}
            if live:
                wl, cl = wer_cer(refs, hyp_live)
                row.update(wer_live=round(wl, 4), cer_live=round(cl, 4),
                           live_segments=live_segs,
                           # tempo de transcrição por segundo de fala, no modo ao vivo
                           rtf_live=round(live_t / audio_t, 3),
                           s_per_segment_live=round(live_t / max(live_segs, 1), 3))
            report["results"].append(row)
    return report


# ── benchmark de atraso ───────────────────────────────────────────────────────

def ensure_piper_voice(lang: str) -> str:
    import urllib.request
    from urllib.parse import quote
    loc, spk, q = PIPER_VOICES[lang]
    VOICES.mkdir(parents=True, exist_ok=True)
    name = f"{loc}-{spk}-{q}.onnx"
    base = "https://huggingface.co/rhasspy/piper-voices/resolve/main/" + quote(
        f"{lang}/{loc}/{spk}/{q}/{name}")
    for ext in ("", ".json"):
        dest = VOICES / f"{name}{ext}"
        if not dest.exists():
            print(f"  baixando {dest.name}", file=sys.stderr)
            urllib.request.urlretrieve(base + ext, dest)
    return str(VOICES / name)


def pct(xs: list[float], p: float) -> float:
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * p
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def bench_latency(model_name: str, pairs: list[tuple[str, str]], max_items: int) -> dict:
    report: dict = {"kind": "latency", "machine": machine_info(), "model": model_name,
                    "results": []}
    whisper = praxis.load_whisper(model_name, DEVICE)
    report["backend"] = getattr(whisper, "backend", "cpu")
    for src, tgt in pairs:
        praxis.setup_argos(src, tgt)
        voice = praxis.load_piper(ensure_piper_voice(tgt))
        praxis.do_translate("warm up.", src, tgt)               # carrega o modelo de tradução
        b"".join(c.audio_int16_bytes for c in voice.synthesize("warm up."))
        corpus = load_corpus(src)[:max_items]
        stages: dict[str, list[float]] = {k: [] for k in
                                          ("vad_tail", "asr", "mt", "tts_first", "total")}
        samples = []
        for it in corpus:
            a = read16k(it["path"])
            # o motor só recebe trechos de no máximo MAX_SEG_S
            segs = live_segments(a)
            if not segs:
                continue
            last = segs[-1].astype(np.float32) / 32768.0
            tail = vad_tail_ms(a)
            if tail is None:
                tail = float(praxis.SILENCE_MS)
                print('  ! espera pelo silêncio não mensurável, usando SILENCE_MS', file=sys.stderr)
            t0 = time.perf_counter()
            text = praxis.transcribe_segment(whisper, last, src)
            t1 = time.perf_counter()
            tr = praxis.do_translate(text, src, tgt) if text else ""
            t2 = time.perf_counter()
            first = praxis._split_sentences(tr)[0] if tr else ""
            if first:
                next(iter(voice.synthesize(first)))
            t3 = time.perf_counter()
            row = {"vad_tail": tail, "asr": (t1 - t0) * 1000, "mt": (t2 - t1) * 1000,
                   "tts_first": (t3 - t2) * 1000}
            row["total"] = sum(row.values())
            for k, v in row.items():
                stages[k].append(v)
            samples.append({"file": it["file"], "seg_s": round(len(last) / praxis.SR, 2),
                            "text": text, "translation": tr,
                            **{k: round(v, 1) for k, v in row.items()}})
            print(f"  {src}→{tgt} {it['file']}  total {row['total']:6.0f} ms  "
                  f"(silêncio {tail:.0f} transcrição {row['asr']:.0f} tradução {row['mt']:.0f} "
                  f"voz {row['tts_first']:.0f})", file=sys.stderr)
        report["results"].append({
            "pair": f"{src}->{tgt}", "n": len(samples),
            "p50_ms": {k: round(statistics.median(v), 1) for k, v in stages.items() if v},
            "p95_ms": {k: round(pct(v, 0.95), 1) for k, v in stages.items() if v},
            "samples": samples})
    return report


# ── relatórios ────────────────────────────────────────────────────────────────

def machine_info() -> dict:
    import os
    info = {"os": platform.platform(), "cpu": platform.processor() or platform.machine(),
            "cores": os.cpu_count(), "python": platform.python_version(),
            "cuda": praxis._has_cuda()}
    try:
        import faster_whisper
        info["faster_whisper"] = faster_whisper.__version__
    except Exception:
        pass
    return info


BACKEND_NAMES = {"cpu": "processador", "cuda": "placa de vídeo (CUDA)",
                 "mlx": "Apple Silicon (MLX)", "whispercpp": "whisper.cpp"}


def where(backend: str | None) -> str:
    """Nome legível de onde a transcrição roda (processador, placa de vídeo…)."""
    b = backend or "cpu"
    return BACKEND_NAMES.get(b, b)


def machine_line(m: dict, cores: bool = True) -> str:
    """Linha de cabeçalho com a máquina usada, sem siglas soltas."""
    parts = [m["os"], f"processador {m['cpu']}"]
    if cores:
        parts.append(f"{m['cores']} núcleos")
    parts += [f"Python {m['python']}",
              f"placa de vídeo CUDA: {'sim' if m['cuda'] else 'não'}"]
    return "_Máquina: " + " · ".join(parts) + "_"


def to_markdown(rep: dict) -> str:
    m = rep["machine"]
    lines = [machine_line(m), ""]
    if rep["kind"] == "asr":
        lines += ["| Modelo | Onde roda | Idioma | Gravações | Falantes | Áudio | "
                  "Erro de palavras (frase inteira) | Erro de palavras (ao vivo) | "
                  "Erro de caracteres (ao vivo) | Velocidade de transcrição |",
                  "|---|---|---|---:|---:|---:|---:|---:|---:|---:|"]
        for r in rep["results"]:
            lines.append(f"| {r['model']} | {where(r.get('backend', 'cpu'))} | {r['lang']} | {r['n']} | {r['speakers']} | "
                         f"{r['audio_s']:.0f}s | {r['wer']:.1%} | {r.get('wer_live', float('nan')):.1%} | "
                         f"{r.get('cer_live', float('nan')):.1%} | {r['rtf']:.2f} |")
        lines += ["", "Erro de palavras = parcela das palavras transcritas errado, puladas ou inventadas "
                  "(erro de caracteres = o mesmo, contado por letra). "
                  "Frase inteira = a gravação toda transcrita de uma vez (melhor resultado possível) · "
                  "ao vivo = o áudio passa pelo detector de fala do motor (corta nas pausas ou a cada "
                  f"{praxis.MAX_SEG_S:.0f}s), como numa chamada · velocidade de transcrição = tempo "
                  "transcrevendo ÷ duração do áudio (menor = mais rápido; abaixo de 1 = mais rápido que a fala)."]
        worst = sorted((s for r in rep["results"] for s in r["samples"]),
                       key=lambda s: -s.get("wer_live", s["wer"]))[:5]
        lines += ["", "### Piores transcrições ao vivo", ""]
        for s in worst:
            lines += [f"- `{s['file']}` erro de palavras {s.get('wer_live', s['wer']):.0%}",
                      f"  - texto real: {s['ref']}", f"  - transcrito: {s.get('hyp_live', s['hyp'])}"]
    else:
        lines += [f"Modelo Whisper: `{rep['model']}` · roda em: {where(rep.get('backend', 'cpu'))}", "",
                  "| Par | Gravações | Espera pelo silêncio | Transcrição | Tradução | Voz (1ª frase) | "
                  "**Total, atraso típico** | **Total, pior caso comum (1 em 20)** |",
                  "|---|---:|---:|---:|---:|---:|---:|---:|"]
        for r in rep["results"]:
            p, q = r["p50_ms"], r["p95_ms"]
            lines.append(f"| {r['pair']} | {r['n']} | {p['vad_tail']:.0f} | {p['asr']:.0f} | "
                         f"{p['mt']:.0f} | {p['tts_first']:.0f} | **{p['total']:.0f} ms** | "
                         f"**{q['total']:.0f} ms** |")
        lines += ["", "Valores por etapa em ms, atraso típico (mediana: metade das gravações é mais rápida). "
                  "Pior caso comum = 1 em cada 20 gravações demora mais que isso. "
                  "Espera pelo silêncio = quanto o detector de fala aguarda para ter certeza de que a frase acabou. "
                  "Total = do fim da fala até a primeira amostra de áudio traduzido pronta (início da reprodução)."]
    return "\n".join(lines) + "\n"


def save(rep: dict, name: str) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / f"{name}.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False),
                                          encoding="utf-8")
    (RESULTS / f"{name}.md").write_text(to_markdown(rep), encoding="utf-8")
    print(to_markdown(rep))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("asr")
    a.add_argument("--models", nargs="+", default=["small"])
    a.add_argument("--langs", nargs="+", default=["pt", "en", "es"])
    a.add_argument("--no-live", action="store_true", help="só o modo frase inteira (sem o modo ao vivo)")
    a.add_argument("--name", default="asr")
    a.add_argument("--corpus", default="speech",
                   help="pasta em benchmarks/data com <idioma>/manifest.json (ex.: speech_fleurs)")
    a.add_argument("--device", default=None, help="onde transcrever: auto|cpu|cuda|mlx|whispercpp")
    a.add_argument("--max-seg", type=float, help="substitui MAX_SEG_S (duração máxima de um trecho, em s)")
    a.add_argument("--silence-ms", type=int, help="substitui SILENCE_MS (silêncio que encerra um trecho, em ms)")
    a.add_argument("--so-ao-vivo", action="store_true", help="só o modo ao vivo (pula a frase inteira)")
    a.add_argument("--contexto", action="store_true", help="no modo ao vivo, passa o texto anterior como dica")
    a.add_argument("--feixe", type=int, help="substitui beam_size do Whisper (1 = guloso; 5 = compara 5 caminhos)")
    a.add_argument("--no-smart-cut", action="store_true", help="desliga o corte no ponto mais silencioso")
    a.add_argument("--preroll", type=float, help="substitui PREROLL_S (áudio guardado antes do início da fala, em s)")
    a.add_argument("--no-repeat-guard", action="store_true", help="desliga a proteção contra repetições em loop")
    a.add_argument("--whisper", nargs="*", default=[], metavar="KEY=JSON",
                   help="substitui WHISPER_OPTS, ex.: vad_filter=false")
    lt = sub.add_parser("latency")
    lt.add_argument("--model", default="small")
    lt.add_argument("--pairs", nargs="+", default=["pt:en", "en:pt", "es:en"])
    lt.add_argument("--max-items", type=int, default=10)
    lt.add_argument("--name", default="latency")
    lt.add_argument("--device", default=None, help="onde transcrever: auto|cpu|cuda|mlx|whispercpp")
    args = ap.parse_args()
    global DEVICE
    DEVICE = args.device
    if args.cmd == "asr":
        global DATA
        DATA = DATA.parent / args.corpus
        if args.max_seg is not None:
            SEG_KW["max_seg_s"] = args.max_seg
        if args.silence_ms is not None:
            praxis.SILENCE_MS = args.silence_ms
        if args.feixe is not None:
            praxis.WHISPER_OPTS["beam_size"] = args.feixe
        global ONLY_LIVE, CONTEXT_LIVE
        ONLY_LIVE = args.so_ao_vivo
        CONTEXT_LIVE = args.contexto
        if args.no_smart_cut:
            SEG_KW["smart_cut"] = False
        if args.preroll is not None:
            SEG_KW["preroll_s"] = args.preroll
        if args.no_repeat_guard:
            praxis.collapse_repetitions = lambda t, max_repeats=2: t
        for kv in args.whisper:
            k, v = kv.split("=", 1)
            praxis.WHISPER_OPTS[k] = json.loads(v)
        save(bench_asr(args.models, args.langs, live=not args.no_live), args.name)
    else:
        pairs = [tuple(p.split(":")) for p in args.pairs]
        save(bench_latency(args.model, pairs, args.max_items), args.name)


if __name__ == "__main__":
    main()
