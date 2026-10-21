#!/usr/bin/env python3
"""Prepara o Praxis logo depois da instalação, para ele já abrir funcionando.

  1. idiomas      herda o idioma do sistema ("você fala"), traduzindo para o inglês
                  (ou do inglês para o português, se o sistema estiver em inglês)
  2. vozes        baixa a melhor voz de cada um dos dois idiomas
  3. placa        compara a placa de vídeo com o processador (uma vez por máquina)
  4. Whisper      baixa o modelo de reconhecimento de fala certo para este computador
  5. tradução     baixa o NLLB (Meta) e os pacotes do Argos para os dois sentidos
  6. configuração grava tudo isso como ponto de partida

Nada aqui é obrigatório: se uma etapa falhar (sem internet, por exemplo), as outras
continuam e o Praxis baixa o que faltar na primeira vez em que for usado.

Uso: python praxis_preparar.py [--sem-nllb]
"""
from __future__ import annotations

import argparse
import sys
import traceback


def _step(name: str, fn, results: list) -> object:
    print(f"==> {name}…", flush=True)
    try:
        out = fn()
        results.append((name, True, ""))
        return out
    except (Exception, SystemExit) as e:        # uma etapa com problema não para as outras
        msg = f"{type(e).__name__}: {e}"
        print(f"  ! {name}: {msg}", flush=True)
        if "--detalhes" in sys.argv:
            traceback.print_exc()
        results.append((name, False, msg))
        return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--sem-nllb", action="store_true", help="não baixa o tradutor NLLB (uso não comercial)")
    ap.add_argument("--detalhes", action="store_true", help="mostra o erro completo das etapas que falharem")
    a = ap.parse_args(argv)

    import praxis
    import praxis_accel as accel
    import praxis_config as pc

    results: list = []
    cfg = pc.load_cfg()
    src, tgt = cfg["src"], cfg["tgt"]
    print(f"  idiomas: você fala {src} → tradução em {tgt}", flush=True)

    def voices():
        chosen = {}
        for lang in dict.fromkeys([tgt, src]):
            v = pc._best_catalog_voice(lang)
            if v is None:
                continue                       # ja/ko: só se fala, não há voz para ouvir
            path = pc.VOICES_DIR / pc._catalog_filename(v)
            if not path.exists():
                print(f"  baixando a voz {v['name']} ({lang})…", flush=True)
                pc._download_voice_files(v)
            chosen[lang] = str(path)
        if tgt in chosen:
            cfg["voice_out"] = chosen[tgt]     # a voz da tradução precisa ser do idioma de destino
        return chosen
    _step("Vozes", voices, results)

    backend = _step("Placa de vídeo × processador",
                    lambda: accel.resolve_asr("auto", log=lambda m: print("  " + m, flush=True))[0],
                    results) or "cpu"
    print(f"  reconhecimento de fala em: {'processador' if backend == 'cpu' else 'placa de vídeo (' + backend + ')'}",
          flush=True)

    def whisper():
        # o modelo do seu idioma e o da outra pessoa (bilateral); no processador podem ser diferentes
        models = list(dict.fromkeys(accel.recommend_model(lang, backend)[0] for lang in (src, tgt)))
        for model in models:
            print(f"  baixando o reconhecimento de fala {model}…", flush=True)
            accel.load_asr(model, backend, log=lambda m: print("  " + m, flush=True))
        return ", ".join(models)
    _step("Reconhecimento de fala", whisper, results)

    if not a.sem_nllb:
        _step("Tradutor NLLB (Meta, uso não comercial)",
              lambda: praxis.install_nllb(log=lambda m: print("  " + m, flush=True)), results)

    def argos():
        old = praxis.TRANSLATOR
        praxis.TRANSLATOR = "argos"            # o Argos é a reserva: sempre instalado
        try:
            praxis.setup_argos(src, tgt)
            praxis.setup_argos(tgt, src)
        finally:
            praxis.TRANSLATOR = old
    _step("Tradutor Argos", argos, results)

    cfg["model"] = "auto"
    _step("Configuração", lambda: pc.save_cfg(cfg), results)

    print("", flush=True)
    for name, ok, msg in results:
        print(f"  {'✓' if ok else '!'} {name}" + ("" if ok else f" — {msg} (será baixado ao usar)"), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
