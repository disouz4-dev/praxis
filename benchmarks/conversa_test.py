#!/usr/bin/env python3
"""Teste de conversa bilateral em tempo real: duas pessoas, cada uma falando no
seu idioma, alternando a vez — como numa chamada traduzida pelo Praxis.

  pessoa A  usuário do Praxis: fala no microfone e OUVE a tradução da pessoa B
            no alto-falante (que vaza de volta para o microfone dela: eco)
  pessoa B  do outro lado da chamada: a fala dela chega limpa (pelo aplicativo
            de chamada) e ela ouve a tradução da pessoa A pelo microfone virtual

As duas direções do motor rodam ao mesmo tempo, com os workers REAIS
(vad_worker → pipeline_worker: Whisper → tradução → Piper), no ritmo real.
Cada pessoa espera a tradução da outra terminar de tocar para responder
(`--sobreposicao 0.5` = começa a falar quando metade da tradução já tocou,
como quem já entendeu e interrompe).

Mede, para cada lado: erro da transcrição, fidelidade da tradução, quanto o
ouvinte espera do fim da fala até ouvir a tradução (e até ela acabar) e eco:
palavras que o Praxis "ouviu" no microfone da pessoa A sem ela estar falando
(a tradução da pessoa B voltando e sendo mandada de novo para B).

Por que só A ↔ B e não todos os pares: entender a fala depende só do idioma
falado (run_benchmarks.py asr), a tradução só do sentido (traducao_vs_humano.py)
e a voz só do idioma de saída — este teste cobre o que só aparece com tudo
junto: atraso real, fila, eco e alternância de turnos.

Uso: python benchmarks/conversa_test.py --model small --device cpu --pares pt:en pt:de
"""
from __future__ import annotations

import argparse
import json
import queue
import statistics
import sys
import threading
import time
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "benchmarks"))
import praxis  # noqa: E402
import praxis_platform as plat  # noqa: E402
import run_benchmarks as rb  # noqa: E402
import stream_test as st  # noqa: E402

DATA = ROOT / "benchmarks" / "data" / "continuous"
RESULTS = ROOT / "benchmarks" / "results"
SPEAKER = "alto-falante"
CHUNK = praxis.VAD_CHUNK
SR = praxis.SR


def turns_for(lang: str, n_turns: int, turn_s: float) -> list[tuple[np.ndarray, str]]:
    """Turnos de fala real: frases consecutivas da gravação até ~turn_s segundos."""
    meta = json.loads((DATA / f"{lang}.json").read_text(encoding="utf-8"))
    audio, sr = sf.read(str(DATA / f"{lang}.wav"), dtype="float32")
    assert sr == SR
    out, cur = [], []
    for seg in meta["segments"]:
        cur.append(seg)
        if cur[-1]["end"] - cur[0]["start"] >= turn_s:
            out.append(cur)
            cur = []
        if len(out) == n_turns:
            break
    if cur and len(out) < n_turns:
        out.append(cur)
    turns = []
    for segs in out:
        a = audio[int(segs[0]["start"] * SR):int(segs[-1]["end"] * SR)]
        a = np.concatenate([a, np.zeros((-len(a)) % CHUNK, np.float32)])
        turns.append((a, " ".join(s["text"] for s in segs)))
    return turns


class ConvBackend:
    """Toca pela duração real; o que vai para o alto-falante volta (com eco de sala)
    no microfone da pessoa A."""
    name = "conversa-test"

    def __init__(self, clock, echo_db: float | None) -> None:
        self.clock = clock
        self.echo_db = echo_db
        self.played: dict[str, list[tuple[float, float]]] = {"out": [], "in": []}
        self.echo = np.zeros(SR * 900, np.float32)
        self.lock = threading.Lock()

    def play_pcm_multi(self, pcm, rate, devices):
        devices = list(devices)
        d = "in" if SPEAKER in devices else "out"
        dur = len(pcm) / 2 / rate
        start = self.clock()
        self.played[d].append((start, dur))
        if d == "in" and self.echo_db is not None:
            x = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768
            y = st.room_echo(plat.resample(x, rate, SR), self.echo_db)
            i = int((start + st.ECHO_DELAY_S) * SR)
            with self.lock:
                j = min(len(self.echo), i + len(y))
                if i < j:
                    self.echo[i:j] += y[:j - i]
        time.sleep(dur)

    def playing_until(self, d: str) -> float:
        return max((s + du for s, du in self.played[d]), default=0.0)

    def teardown(self):
        pass


def run_pair(a_lang: str, b_lang: str, whisper, voice_a, voice_b, echo_db, overlap: float,
             n_turns: int, turn_s: float) -> dict:
    turns = {"A": turns_for(a_lang, n_turns, turn_s), "B": turns_for(b_lang, n_turns, turn_s)}
    t0 = [0.0]
    clock = lambda: time.perf_counter() - t0[0]           # noqa: E731
    backend = ConvBackend(clock, echo_db)
    old = (praxis._backend, praxis._vmic, praxis._stop, praxis._emit,
           praxis.transcribe_segment, praxis.do_translate)
    praxis._backend = backend
    praxis._vmic = plat.VirtualMic(target="microfone-virtual", mic_label="conversa-test")
    stop = threading.Event()
    praxis._stop = stop
    praxis._emit = lambda d: None
    praxis._echo_ref = None
    praxis._speaker_busy_until[0] = 0.0
    praxis._piper_out_ref[0] = voice_b               # a direção de ida lê a voz por aqui
    echo_filter = praxis.make_echo_filter() if praxis.ECHO_MODE == "cancelar" else None

    segs = {"out": [], "in": []}            # trechos que cada direção transcreveu
    real_tr, real_mt = old[4], old[5]

    def direction() -> str:
        return "in" if threading.current_thread().name.endswith("-in") else "out"

    def transcribe(w, a, lang, **kw):
        s = {"t_asr": clock()}
        text = real_tr(w, a, lang, **kw)
        s["text"] = text
        s["dur"] = len(a) / SR
        s.update(getattr(praxis._asr_stats, "last", {}))
        segs[direction()].append(s)
        return text

    def translate(text, a, b):
        out = real_mt(text, a, b)
        d = segs[direction()]
        if d:
            d[-1]["translation"] = out
        return out

    praxis.transcribe_segment, praxis.do_translate = transcribe, translate
    q = {k: queue.Queue() for k in ("a_audio", "a_seg", "b_audio", "b_seg")}
    active = threading.Event()
    active.set()
    threads = [
        threading.Thread(target=praxis.vad_worker, name="vad-out",
                         args=(q["a_audio"], q["a_seg"], "vad", 0.1),
                         kwargs={"active": active, "ptt_flush": threading.Event(),
                                 "echo_gate": praxis.ECHO_MODE == "trava"}, daemon=True),
        threading.Thread(target=praxis.pipeline_worker, name="pipe-out",
                         args=(q["a_seg"], whisper, voice_b, a_lang, b_lang, "out"), daemon=True),
        threading.Thread(target=praxis.vad_worker, name="vad-in",
                         args=(q["b_audio"], q["b_seg"], "vad", 0.1),
                         kwargs={"active": active, "ptt_flush": threading.Event()}, daemon=True),
        threading.Thread(target=praxis.pipeline_worker, name="pipe-in",
                         args=(q["b_seg"], whisper, voice_a, b_lang, a_lang, "in", False, SPEAKER),
                         daemon=True),
    ]
    rng = np.random.default_rng(5)
    floor = lambda: (rng.standard_normal(CHUNK) * 10 ** (-60 / 20)).astype(np.float32)  # noqa: E731
    schedule: list[dict] = []
    try:
        for t in threads:
            t.start()
        time.sleep(0.5)
        t0[0] = time.perf_counter()
        k = 0

        def tick(a_piece: np.ndarray | None, b_piece: np.ndarray | None) -> None:
            nonlocal k
            target = k * CHUNK / SR
            delay = target - clock()
            if delay > 0:
                time.sleep(delay)
            a = floor() if a_piece is None else a_piece.copy()
            with backend.lock:
                a = np.clip(a + backend.echo[k * CHUNK:(k + 1) * CHUNK], -1, 1)
            if echo_filter is not None:
                a = echo_filter(a)
            q["a_audio"].put(a.astype(np.float32))
            q["b_audio"].put(floor() if b_piece is None else b_piece)
            k += 1

        order = [x for i in range(n_turns) for x in (("A", i), ("B", i))]
        for who, i in order:
            if i >= len(turns[who]):
                continue
            audio, text = turns[who][i]
            start = clock()
            for c in range(len(audio) // CHUNK):
                piece = audio[c * CHUNK:(c + 1) * CHUNK]
                tick(piece if who == "A" else None, piece if who == "B" else None)
            end = clock()
            schedule.append({"who": who, "start": start, "end": end, "text": text})
            # o ouvinte espera a tradução (ou parte dela, com sobreposição) antes de responder
            d = "out" if who == "A" else "in"
            n_before = len(backend.played[d])
            deadline = end + 25
            while clock() < deadline:
                done = [p for p in backend.played[d][n_before:]]
                pending = not q["a_seg" if who == "A" else "b_seg"].empty()
                if done and not pending:
                    s0 = done[0][0]
                    total_end = backend.playing_until(d)
                    if clock() >= s0 + overlap * (total_end - s0) and clock() > end + 1.0 and \
                            (overlap > 0 or clock() >= total_end + 0.3):
                        break
                tick(None, None)
            for _ in range(int(0.5 * SR / CHUNK)):          # tempo de reação
                tick(None, None)
        # deixa terminar o que falta
        for _ in range(int(6 * SR / CHUNK)):
            tick(None, None)
    finally:
        stop.set()
        for t in threads:
            t.join(3)
        (praxis._backend, praxis._vmic, praxis._stop, praxis._emit,
         praxis.transcribe_segment, praxis.do_translate) = old

    def belongs(s: dict, turn: dict) -> bool:
        # um trecho é transcrito depois que a fala termina; pertence ao turno se foi
        # transcrito entre o começo do turno e um pouco depois do fim
        return turn["start"] <= s["t_asr"] <= turn["end"] + 6.0

    side = {}
    for who, d, lang, tgt in (("A", "out", a_lang, b_lang), ("B", "in", b_lang, a_lang)):
        my_turns = [t for t in schedule if t["who"] == who]
        mine = [s for s in segs[d] if any(belongs(s, t) for t in my_turns)]
        stray = [s for s in segs[d] if s not in mine and s.get("text")]
        ref = " ".join(t["text"] for t in my_turns)
        hyp = " ".join(s["text"] for s in mine if s.get("text"))
        wer, _ = rb.wer_cer([ref], [hyp])
        err = rb.letter_error(ref, hyp) if lang in st.CHAR_LANGS else wer
        tr_hyp = " ".join(s.get("translation", "") for s in mine if s.get("translation"))
        tr_ref = praxis.do_translate(ref, lang, tgt)
        waits, finish = [], []
        for t in my_turns:
            plays = [p for p in backend.played[d] if p[0] >= t["start"]]
            after = [p for p in plays if p[0] + p[1] >= t["end"]]
            if after:
                waits.append(max(0.0, after[0][0] - t["end"]))
                nxt = [u for u in schedule if u["start"] > t["end"]]
                lim = nxt[0]["start"] if nxt else 1e9
                ends = [p[0] + p[1] for p in plays if p[0] < lim + 2]
                finish.append(max(ends) - t["end"])
        side[who] = {
            "lang": lang, "error_rate": round(err, 4),
            "error_metric": "characters" if lang in st.CHAR_LANGS else "words",
            "translation_chrf": round(st.chrf(tr_hyp, tr_ref), 1),
            "wait_first_audio_s": round(statistics.median(waits), 2) if waits else None,
            "wait_translation_done_s": round(statistics.median(finish), 2) if finish else None,
            "stray_segments": len(stray), "stray_words": sum(len(s["text"].split()) for s in stray),
            "stray_text": " | ".join(s["text"] for s in stray)[:400],
            "stray": [{k: s.get(k) for k in ("text", "dur", "avg_logprob", "no_speech", "rms")} for s in stray],
            "real": [{k: s.get(k) for k in ("text", "dur", "avg_logprob", "no_speech", "rms")} for s in mine],
            "reference": ref, "transcript": hyp, "translation": tr_hyp,
        }
    res = {"pair": f"{a_lang}<->{b_lang}", "A": side["A"], "B": side["B"],
           "duration_s": round(clock(), 1), "schedule": schedule}
    print(f"  {res['pair']}: A({a_lang}) erro {side['A']['error_rate']:.1%} eco {side['A']['stray_words']} palavras | "
          f"B({b_lang}) erro {side['B']['error_rate']:.1%} | espera A→B {side['A']['wait_first_audio_s']} s, "
          f"B→A {side['B']['wait_first_audio_s']} s", file=sys.stderr)
    return res


def to_markdown(rep: dict) -> str:
    out = [rb.machine_line(rep["machine"], cores=False), "",
           f"Whisper `{rep['model']}` em {rb.where(rep['backend'])} · eco no alto-falante da pessoa A: "
           f"{'sem eco' if rep['eco_db'] is None else str(rep['eco_db']) + ' dB'} · tratamento de eco: "
           f"**{rep['modo_eco']}** · sobreposição dos turnos: {rep['sobreposicao']:.0%}", "",
           "| Conversa | Erro A (fala da pessoa A) | Erro B | Fidelidade A→B | Fidelidade B→A | "
           "Espera do ouvinte A→B | Espera B→A | Eco: palavras falsas mandadas a B |",
           "|---|---:|---:|---:|---:|---:|---:|---:|"]
    rows = [r for r in rep["results"] if "A" in r]
    for r in rows:
        A, B = r["A"], r["B"]
        out.append(f"| {r['pair']} | {A['error_rate']:.1%} | {B['error_rate']:.1%} | {A['translation_chrf']} | "
                   f"{B['translation_chrf']} | {A['wait_first_audio_s']} s | {B['wait_first_audio_s']} s | "
                   f"{A['stray_words']} |")
    if rows:
        mean = lambda xs: sum(xs) / len(xs)   # noqa: E731
        out.append(f"| **média** | {mean([r['A']['error_rate'] for r in rows]):.1%} | "
                   f"{mean([r['B']['error_rate'] for r in rows]):.1%} | | | | | "
                   f"{sum(r['A']['stray_words'] for r in rows)} |")
    for r in rep["results"]:
        if "error" in r:
            out.append(f"\n- {r['pair']}: {r['error']}")
    out += ["", "Erro = parcela das palavras (letras em zh/ja/ko) transcritas errado, puladas ou "
            "inventadas. Fidelidade (0–100) compara a tradução do que foi ouvido com a tradução do "
            "texto real. Espera do ouvinte = do fim da fala até o começo da tradução (mediana). "
            "Eco = palavras transcritas no microfone da pessoa A quando ela não estava falando."]
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="small")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--pares", nargs="+", default=None,
                    help="A:B (padrão: pt com cada um dos outros 15 idiomas)")
    ap.add_argument("--eco", type=float, default=-12, help="volume do eco em dB; use 'nenhum' com --sem-eco")
    ap.add_argument("--sem-eco", action="store_true", help="pessoa A de fone (nenhum eco)")
    ap.add_argument("--modo-eco", choices=("cancelar", "trava", "nada"), default="cancelar")
    ap.add_argument("--sobreposicao", type=float, default=0.0,
                    help="fração da tradução já tocada quando o outro começa a falar (0 = espera tudo)")
    ap.add_argument("--turnos", type=int, default=3, help="turnos por pessoa")
    ap.add_argument("--duracao-turno", type=float, default=8.0)
    ap.add_argument("--name", default=None)
    a = ap.parse_args()
    praxis.ECHO_MODE = a.modo_eco
    echo_db = None if a.sem_eco else a.eco
    whisper = praxis.load_whisper(a.model, a.device)
    backend = getattr(whisper, "backend", a.device)
    pairs = [tuple(p.split(":")) for p in a.pares] if a.pares else \
        [("pt", x) for x in st.INPUT_LANGS if x != "pt"]
    rep = {"kind": "conversa", "model": a.model, "backend": backend, "machine": rb.machine_info(),
           "eco_db": echo_db, "modo_eco": a.modo_eco, "sobreposicao": a.sobreposicao, "results": []}
    name = a.name or f"conversa-{backend}-{a.model}-{a.modo_eco}"
    for x, y in pairs:
        try:
            praxis.setup_argos(x, y)
            praxis.setup_argos(y, x)
            # a pessoa A ouve a voz no idioma dela; a B ouve no idioma dela.
            # ja/ko não têm voz Piper: nesses idiomas só dá para falar, não ouvir
            va = praxis.load_piper(st.voice_for(x))
            vb = praxis.load_piper(st.voice_for(y)) if y in st.OUTPUT_LANGS else va
            for v, src, tgt in ((vb, x, y), (va, y, x)):
                praxis.do_translate("warm up.", src, tgt)
                next(iter(v.synthesize("warm up.")))
            rep["results"].append(run_pair(x, y, whisper, va, vb, echo_db, a.sobreposicao,
                                           a.turnos, a.duracao_turno))
        except Exception as e:                      # um par com problema não para os outros
            import traceback
            traceback.print_exc()
            rep["results"].append({"pair": f"{x}<->{y}", "error": f"{type(e).__name__}: {e}"})
        RESULTS.mkdir(parents=True, exist_ok=True)
        (RESULTS / f"{name}.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False,
                                                         default=lambda o: o.item() if hasattr(o, "item") else str(o)),
                                              encoding="utf-8")
        (RESULTS / f"{name}.md").write_text(to_markdown(rep), encoding="utf-8")
    print(to_markdown(rep))


if __name__ == "__main__":
    main()
