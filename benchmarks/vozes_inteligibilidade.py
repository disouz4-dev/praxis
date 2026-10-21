#!/usr/bin/env python3
"""As vozes se entendem? Cada voz lê frases do FLEURS e o Whisper (o "ouvinte")
transcreve o que ouviu; o erro de palavras mede o quanto a fala sai inteligível.

Vozes comparadas (todas pelo sherpa-onnx, no processador, como no Praxis):
  piper       a voz padrão do Praxis em cada idioma (VITS)
  supertonic  Supertonic 3 (Supertone, 31 idiomas)
  kokoro      Kokoro 82M v1.0 (8 idiomas)

Também mede a rapidez: segundos de síntese por segundo de fala gerada (abaixo de 1 =
mais rápido que o tempo real).

Uso (lab2, ouvinte na placa de vídeo):
  python benchmarks/vozes_inteligibilidade.py --pasta ~/praxis-qa/vozes-novas --n 20
Resultado: benchmarks/results/vozes-inteligibilidade.json e .md
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import run_benchmarks as rb  # noqa: E402

PIPER = {"pt": "pt_BR-faber-medium", "en": "en_US-lessac-medium", "es": "es_ES-sharvard-medium",
         "fr": "fr_FR-siwis-medium", "de": "de_DE-thorsten-high", "it": "it_IT-paola-medium"}
KOKORO = {"pt": ("pf_dora", "pt-br"), "en": ("af_heart", "en-us"), "es": ("ef_dora", "es"),
          "fr": ("ff_siwis", "fr"), "it": ("if_sara", "it")}
PIPER_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models"


def piper(pasta: Path, lang: str):
    import sherpa_onnx as so
    d = pasta / f"vits-piper-{PIPER[lang]}"
    if not d.exists():
        import io
        import tarfile
        import urllib.request
        with urllib.request.urlopen(f"{PIPER_URL}/vits-piper-{PIPER[lang]}.tar.bz2") as r:
            tarfile.open(fileobj=io.BytesIO(r.read()), mode="r:bz2").extractall(pasta, filter="data")
    model = next(d.glob("*.onnx"))
    cfg = so.OfflineTtsConfig(model=so.OfflineTtsModelConfig(
        vits=so.OfflineTtsVitsModelConfig(model=str(model), tokens=str(d / "tokens.txt"),
                                          data_dir=str(d / "espeak-ng-data")), num_threads=2))
    tts = so.OfflineTts(cfg)
    return lambda t: tts.generate(t, so.GenerationConfig())


def supertonic(pasta: Path, lang: str, sid: int = 0):
    import sherpa_onnx as so
    d = next(pasta.glob("sherpa-onnx-supertonic-3-*"))
    cfg = so.OfflineTtsConfig(model=so.OfflineTtsModelConfig(
        supertonic=so.OfflineTtsSupertonicModelConfig(
            duration_predictor=str(next(d.glob("duration_predictor*.onnx"))),
            text_encoder=str(next(d.glob("text_encoder*.onnx"))),
            vector_estimator=str(next(d.glob("vector_estimator*.onnx"))),
            vocoder=str(next(d.glob("vocoder*.onnx"))),
            tts_json=str(d / "tts.json"), unicode_indexer=str(d / "unicode_indexer.bin"),
            voice_style=str(d / "voice.bin")), num_threads=2))
    tts = so.OfflineTts(cfg)

    def gen(t):
        g = so.GenerationConfig()
        g.sid, g.num_steps = sid, 8
        g.extra["lang"] = lang
        return tts.generate(t, g)
    return gen


def kokoro(pasta: Path, lang: str):
    import sherpa_onnx as so
    d = next(pasta.glob("kokoro-*multi-lang-v1_0"))
    voz, code = KOKORO[lang]
    cfg = so.OfflineTtsConfig(model=so.OfflineTtsModelConfig(
        kokoro=so.OfflineTtsKokoroModelConfig(
            model=str(next(d.glob("model*.onnx"))), voices=str(d / "voices.bin"),
            tokens=str(d / "tokens.txt"), data_dir=str(d / "espeak-ng-data"),
            lexicon=f"{d}/lexicon-us-en.txt" if lang == "en" else "", lang=code), num_threads=2))
    tts = so.OfflineTts(cfg)
    import onnxruntime as ort
    meta = ort.InferenceSession(str(next(d.glob("model*.onnx"))),
                                providers=["CPUExecutionProvider"]).get_modelmeta().custom_metadata_map
    ids = dict(x.split("->") for x in meta["speaker2id"].split(","))

    def gen(t):
        g = so.GenerationConfig()
        g.sid = int(ids[voz])
        return tts.generate(t, g)
    return gen


def para_16k(samples, sr: int) -> np.ndarray:
    x = np.asarray(samples, np.float32)
    if sr == 16000:
        return x
    n = int(round(len(x) * 16000 / sr))
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pasta", type=Path, required=True, help="pasta com os pacotes de voz do sherpa-onnx")
    ap.add_argument("--langs", nargs="+", default=["pt", "en", "es", "fr", "de", "it"])
    ap.add_argument("--vozes", nargs="+", default=["piper", "supertonic", "kokoro"])
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--ouvinte", default="large-v3-turbo")
    ap.add_argument("--nome", default="vozes-inteligibilidade")
    a = ap.parse_args()
    import praxis
    ouvinte = praxis.load_whisper(a.ouvinte, "cuda")
    linhas = []
    for lang in a.langs:
        frases = [it["text"] for it in json.loads(
            (ROOT / "data" / "speech_fleurs" / lang / "manifest.json").read_text(encoding="utf-8"))[:a.n]]
        for voz in a.vozes:
            if voz == "kokoro" and lang not in KOKORO:
                continue
            gen = {"piper": piper, "supertonic": supertonic, "kokoro": kokoro}[voz](a.pasta, lang)
            hyps, t_sint, t_fala = [], 0.0, 0.0
            for f in frases:
                t0 = time.perf_counter()
                au = gen(f)
                t_sint += time.perf_counter() - t0
                t_fala += len(au.samples) / au.sample_rate
                hyps.append(praxis.transcribe_segment(ouvinte, para_16k(au.samples, au.sample_rate), lang))
            if t_fala == 0:
                print(f"  {voz:10s} {lang}  não gerou áudio", flush=True)
                continue
            wer, _ = rb.wer_cer(frases, hyps)
            linhas.append({"voz": voz, "lang": lang, "erro": round(wer, 4),
                           "rapidez": round(t_sint / max(t_fala, 1e-9), 3),
                           "exemplos": [{"texto": f, "ouvido": h} for f, h in zip(frases[:3], hyps[:3])]})
            print(f"  {voz:10s} {lang}  erro {wer:6.1%}  síntese {t_sint / t_fala:.2f} s por s de fala", flush=True)
    out = ["# As vozes se entendem? (Whisper como ouvinte)", "",
           f"{a.n} frases do FLEURS por idioma; erro = palavras que o ouvinte entendeu errado; "
           "rapidez = segundos de síntese por segundo de fala (processador, 2 núcleos).", "",
           "| Idioma | " + " | ".join(a.vozes) + " |", "|---|" + "---:|" * len(a.vozes)]
    for lang in a.langs:
        cel = []
        for voz in a.vozes:
            r = next((x for x in linhas if x["voz"] == voz and x["lang"] == lang), None)
            cel.append("—" if r is None else f"{r['erro']:.1%} · {r['rapidez']:.2f}")
        out.append(f"| {lang} | " + " | ".join(cel) + " |")
    rb.RESULTS.mkdir(parents=True, exist_ok=True)
    (rb.RESULTS / f"{a.nome}.json").write_text(json.dumps(linhas, ensure_ascii=False, indent=1), encoding="utf-8")
    (rb.RESULTS / f"{a.nome}.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out))


if __name__ == "__main__":
    main()
