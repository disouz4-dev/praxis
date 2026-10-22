#!/usr/bin/env python3
"""Reconhecimento EM FLUXO (transcreve enquanto a pessoa fala) no FLEURS, para comparar o
erro com o reconhecimento por trecho que o Praxis usa hoje.

Cada frase entra em pedaços de 0,1 s, no ritmo do áudio (sem esperar o tempo real),
seguida de 1 s de silêncio. Mede:
  erro      com o mesmo formato de run_benchmarks.py (auditável por auditar_erros.py)
  atraso    quanto falta reconhecer quando a fala acaba: tempo de processamento do que
            sobrou depois do fim do áudio (o resto já foi processado durante a fala)

Uso (lab2, sherpa-onnx com placa de vídeo):
  python benchmarks/fluxo_asr.py --modelo <pasta do pacote> --langs pt en es --nome fluxo-560
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
sys.path.insert(0, str(ROOT))   # o run_benchmarks.py desta pasta vem primeiro


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--modelo", type=Path, required=True)
    ap.add_argument("--langs", nargs="+", default=["pt", "en", "es", "de", "it", "fr"])
    ap.add_argument("--corpus", default="speech_fleurs")
    ap.add_argument("--placa", default="cuda")
    ap.add_argument("--nome", required=True)
    a = ap.parse_args()
    import sherpa_onnx as so
    import run_benchmarks as rb
    d = a.modelo
    pick = lambda p: str(sorted(d.glob(p))[0])        # noqa: E731
    rec = so.OnlineRecognizer.from_transducer(
        tokens=str(d / "tokens.txt"), encoder=pick("encoder*.onnx"), decoder=pick("decoder*.onnx"),
        joiner=pick("joiner*.onnx"), num_threads=4, provider=a.placa)
    rep = {"kind": "asr", "machine": rb.machine_info(), "results": []}
    for lang in a.langs:
        corpus = json.loads((ROOT / "data" / a.corpus / lang / "manifest.json").read_text(encoding="utf-8"))
        samples, lags, refs, hyps = [], [], [], []
        for it in corpus:
            x = rb.read16k(ROOT / "data" / a.corpus / lang / it["file"])
            st = rec.create_stream()
            st.set_option("language", lang)
            step = 1600
            for i in range(0, len(x), step):
                st.accept_waveform(16000, x[i:i + step])
                while rec.is_ready(st):
                    rec.decode_stream(st)
            # a fala acabou: o que falta é o atraso do reconhecimento
            t0 = time.perf_counter()
            st.accept_waveform(16000, np.zeros(16000, np.float32))
            st.input_finished()
            while rec.is_ready(st):
                rec.decode_stream(st)
            lags.append(time.perf_counter() - t0)
            h = rec.get_result(st).strip()
            refs.append(it["text"])
            hyps.append(h)
            samples.append({"file": it["file"], "speaker": it.get("speaker"), "ref": it["text"],
                            "hyp": "", "hyp_live": h, "wer_live": round(rb.wer_cer([it["text"]], [h])[0], 3)})
        wer, cer = rb.wer_cer(refs, hyps)
        lags.sort()
        rep["results"].append({"model": d.name, "lang": lang, "n": len(samples), "backend": a.placa,
                               "wer_live": wer, "cer_live": cer, "lag_p50_s": lags[len(lags) // 2],
                               "samples": samples})
        print(f"  {lang}: erro {wer:.1%} (letras {cer:.1%}) · atraso no fim {lags[len(lags) // 2] * 1000:.0f} ms",
              flush=True)
    rb.RESULTS.mkdir(parents=True, exist_ok=True)
    (rb.RESULTS / f"{a.nome}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
