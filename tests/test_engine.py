"""Motor (praxis.py): funções auxiliares puras, linha de comando (CLI), divisão da fala em trechos pela detecção de voz (VAD) e o fluxo completo com componentes falsos."""
import json
import os
import queue
import subprocess
import sys
import threading
import time
import types

import numpy as np
import pytest

from conftest import ROOT, FakeVoice, FakeWhisper

import praxis


# ── funções auxiliares ────────────────────────────────────────────────────────

@pytest.mark.parametrize("text,expected", [
    ("Hello. How are you?", ["Hello.", "How are you?"]),
    ("One sentence", ["One sentence"]),
    ("Wait… what! Really?", ["Wait…", "what!", "Really?"]),
    ("", [""]),
])
def test_divide_frases(text, expected):
    assert praxis._split_sentences(text) == expected


def test_transcrever_trecho_filtra_ruido_e_nao_fala():
    w = FakeWhisper("...")
    assert praxis.transcribe_segment(w, np.zeros(1600, np.float32), "pt") == ""
    w = FakeWhisper(" bom dia ")
    assert praxis.transcribe_segment(w, np.zeros(1600, np.float32), "pt") == "bom dia"
    # as opções de decodificação de produção são as que são passadas
    assert w.calls[0][1] == "pt" and w.calls[0][2]["beam_size"] == 1


def test_transcrever_trecho_descarta_so_nao_fala_incerta():
    """Regra do próprio Whisper: descartar só quando ele acha que não é fala E o
    texto tem baixa confiança. Usar só no_speech_prob (0.53–0.59) jogava fora
    frases reais no teste de fala contínua."""
    from conftest import FakeSeg
    noise = FakeSeg("ruído", 0.9); noise.avg_logprob = -1.6
    unsure_but_real = FakeSeg("estático errante", 0.59); unsure_but_real.avg_logprob = -0.4
    speech = FakeSeg("fala", 0.1); speech.avg_logprob = -0.2

    class W:
        def transcribe(self, a, language=None, **kw):
            return iter([noise, unsure_but_real, speech]), None
    assert praxis.transcribe_segment(W(), np.zeros(10, np.float32), "pt") == "estático errante fala"


def test_sobra_curta_se_junta_ao_proximo_trecho():
    """Um pedacinho que sobra depois de um corte é colado ao próximo trecho em vez
    de ser enviado sozinho (o Whisper não devolve nada para ele e a sílaba se perde)."""
    tiny = _speech(int(0.4 / (praxis.VAD_CHUNK / praxis.SR)))
    longer = _speech(40)
    segs = _run_vad(tiny + _silence(4) + longer + _silence(5))
    assert len(segs) == 1
    assert len(segs[0]) >= (len(tiny) + len(longer)) * praxis.VAD_CHUNK


def test_fala_curta_sozinha_ainda_e_enviada_apos_silencio():
    """"Sim." seguido de silêncio não pode ficar travado esperando mais fala."""
    tiny = _speech(int(0.4 / (praxis.VAD_CHUNK / praxis.SR)))
    segs = _run_vad(tiny + _silence(int(1.5 / (praxis.VAD_CHUNK / praxis.SR))))
    assert len(segs) == 1


def test_traducao_passa_pelo_ingles(monkeypatch):
    calls = []
    monkeypatch.setattr(praxis, "_translate_pair",
                        lambda t, s, d: calls.append((s, d)) or f"{t}>{d}")
    assert praxis.do_translate("oi", "pt", "it") == "oi>en>it"
    assert calls == [("pt", "en"), ("en", "it")]
    calls.clear()
    assert praxis.do_translate("oi", "pt", "en") == "oi>en"
    assert calls == [("pt", "en")]
    assert praxis.do_translate("oi", "pt", "pt") == "oi"


def test_traduzir_par_usa_ct2_por_frase(monkeypatch):
    class Tok:
        def encode(self, s): return s.split()
        def decode(self, toks): return " " + " ".join(t.upper() for t in toks)

    class Res:
        def __init__(self, toks): self.hypotheses = [toks]

    class Tr:
        def __init__(self): self.batches = []
        def translate_batch(self, toks, **kw):
            self.batches.append((toks, kw))
            return [Res(t) for t in toks]
    pkg = types.SimpleNamespace(tokenizer=Tok(), target_prefix="")
    tr = Tr()
    monkeypatch.setattr(praxis, "_argos_translator", lambda s, d: (pkg, tr))
    assert praxis._translate_pair("olá mundo. tudo bem?", "pt", "en") == "OLÁ MUNDO. TUDO BEM?"
    toks, kw = tr.batches[0]
    assert toks == [["olá", "mundo."], ["tudo", "bem?"]]
    assert kw["beam_size"] == praxis.ARGOS_BEAM and kw["target_prefix"] is None


def test_importar_motor_nao_carrega_torch():
    """PyTorch + CTranslate2 no mesmo processo derrubam o Whisper no macOS (duas
    versões do OpenMP carregadas). O motor não pode importar o torch, a menos
    que o OmniVoice seja usado."""
    code = ("import sys, praxis; praxis.build_parser(); "
            "print('torch' in sys.modules, 'stanza' in sys.modules)")
    r = subprocess.run([sys.executable, "-c", code], cwd=str(ROOT), capture_output=True,
                       text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    assert r.stdout.split() == ["False", "False"]


def test_configurar_argos_instala_pares_intermediarios(monkeypatch):
    pairs = []
    monkeypatch.setattr(praxis, "_download_argos_pair", lambda s, t: pairs.append((s, t)))
    praxis.setup_argos("pt", "de")
    praxis.setup_argos("en", "es")
    praxis.setup_argos("fr", "fr")
    assert pairs == [("pt", "en"), ("en", "de"), ("en", "es")]


def test_carregar_piper_direciona_clone_omnivoice(tmp_path):
    wav = tmp_path / "me.wav"
    wav.write_bytes(b"RIFF")
    (tmp_path / "me.json").write_text(json.dumps({"type": "omnivoice", "name": "me"}))
    eng = praxis.load_piper(str(wav))
    assert isinstance(eng, praxis.OmniVoiceEngine)
    assert eng.config.sample_rate == 24000
    eng.set_live_reference("/tmp/x.wav", "texto")
    assert eng._live_ref == "/tmp/x.wav"


# ── linha de comando (CLI) ────────────────────────────────────────────────────

def test_parser_valores_padrao_e_opcoes():
    a = praxis.build_parser().parse_args(["--voice-out", "v.onnx"])
    assert (a.src, a.tgt, a.mode, a.model, a.gate_threshold) == ("pt", "en", "vad", "auto", 0.10)
    with pytest.raises(SystemExit):
        praxis.build_parser().parse_args(["--mode", "bogus"])


def test_cli_exige_voice_out():
    r = subprocess.run([sys.executable, str(ROOT / "praxis.py")], capture_output=True, text=True)
    assert r.returncode == 2 and "voice-out" in r.stderr


def test_cli_rejeita_limiar_de_porta_invalido():
    r = subprocess.run([sys.executable, str(ROOT / "praxis.py"), "--voice-out", "v",
                        "--gate-threshold", "3"], capture_output=True, text=True)
    assert r.returncode == 2


def test_cli_check_relata_o_ambiente():
    """Teste de fumaça: o motor inicia, importa, inspeciona o áudio e sai com código 0 em todo sistema."""
    r = subprocess.run([sys.executable, str(ROOT / "praxis.py"), "--check"],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    rep = json.loads(r.stdout)
    assert rep["platform"] in ("Linux", "Darwin", "Windows")
    assert rep["modules"]["numpy"] is True
    assert "audio_backend" in rep


def test_falha_na_inicializacao_ainda_desmonta_o_audio(engine, monkeypatch):
    p, fb = engine
    monkeypatch.setattr(p, "setup_argos", lambda s, t: (_ for _ in ()).throw(RuntimeError("no net")))
    monkeypatch.setattr(p.signal, "signal", lambda *a: None)
    rc = p.main(["--voice-out", "x.onnx"])
    assert rc == 1 and fb.torn_down


# ── divisão em trechos pela detecção de voz (VAD) ─────────────────────────────

class FakeVAD:
    """Substituto do VADIterator do Silero: considera 'fala' quando a amplitude do pedaço é > 0.05."""

    def __init__(self, silence_chunks: int = 3) -> None:
        self.speaking, self.quiet, self.silence_chunks = False, 0, silence_chunks

    def __call__(self, chunk, return_seconds=False):
        loud = float(np.abs(chunk.numpy() if hasattr(chunk, "numpy") else chunk).max()) > 0.05
        if loud and not self.speaking:
            self.speaking, self.quiet = True, 0
            return {"start": 0}
        if self.speaking and not loud:
            self.quiet += 1
            if self.quiet >= self.silence_chunks:
                self.speaking = False
                return {"end": 0}
        if loud:
            self.quiet = 0
        return None

    def reset_states(self):
        self.speaking, self.quiet = False, 0


def _run_vad(chunks, mode="vad", gate=0.1, ptt_events=None, active=None):
    audio_q, seg_q = queue.Queue(), queue.Queue()
    active = active or threading.Event()
    active.set()
    flush = threading.Event()
    praxis._stop.clear()
    t = threading.Thread(target=praxis.vad_worker,
                         args=(audio_q, seg_q, mode, gate),
                         kwargs=dict(active=active, ptt_flush=flush, vad_factory=FakeVAD),
                         daemon=True)
    t.start()
    for i, c in enumerate(chunks):
        audio_q.put(c)
        if ptt_events and i in ptt_events:
            time.sleep(0.05)
            flush.set()
    time.sleep(0.4)
    praxis._stop.set()
    t.join(2)
    segs = []
    while not seg_q.empty():
        segs.append(seg_q.get())
    return segs


def _speech(n):
    return [np.full(praxis.VAD_CHUNK, 0.3, np.float32) for _ in range(n)]


def _silence(n):
    return [np.zeros(praxis.VAD_CHUNK, np.float32) for _ in range(n)]


def test_vad_emite_um_trecho_por_fala():
    segs = _run_vad(_silence(3) + _speech(30) + _silence(5) + _speech(30) + _silence(5))
    assert len(segs) == 2
    assert segs[0].dtype == np.int16


def test_vad_forca_corte_no_tamanho_maximo_do_trecho():
    n = int(praxis.MAX_SEG_S * praxis.SR / praxis.VAD_CHUNK) * 2 + 5   # > 2 × MAX_SEG_S
    segs = _run_vad(_speech(n) + _silence(5))
    assert len(segs) >= 2
    longest = max(len(s) for s in segs) / praxis.SR
    assert longest <= praxis.MAX_SEG_S + praxis.VAD_CHUNK / praxis.SR + 1e-6


def test_modo_porta_ignora_fala_baixa():
    quiet = [np.full(praxis.VAD_CHUNK, 0.06, np.float32) for _ in range(10)]
    assert _run_vad(quiet + _silence(5), mode="gate", gate=0.2) == []
    assert len(_run_vad(_speech(30) + _silence(5), mode="gate", gate=0.2)) == 1


def test_soltar_ptt_envia_e_desativa():
    active = threading.Event()
    segs = _run_vad(_speech(8), mode="ptt", ptt_events={7}, active=active)
    assert len(segs) == 1 and not active.is_set()


# ── fluxo completo (com componentes falsos) ───────────────────────────────────

def _run_pipeline(p, seg, whisper, voice, direction="out", monitor=False, out=None):
    q = queue.Queue()
    q.put(seg)
    t = threading.Thread(target=p.pipeline_worker,
                         args=(q, whisper, voice, "pt", "en", direction, monitor, out),
                         daemon=True)
    p._piper_out_ref[0] = voice
    t.start()
    deadline = time.time() + 5
    while time.time() < deadline and not p._transcripts:
        time.sleep(0.01)
    time.sleep(0.3)
    p._stop.set()
    t.join(2)


def test_fluxo_completo_toca_no_microfone_virtual(engine):
    p, fb = engine
    voice = FakeVoice()
    _run_pipeline(p, np.ones(16000, np.int16), FakeWhisper("olá. tudo bem?"), voice)
    assert list(p._transcripts) == [("out", "olá. tudo bem?", "[en] olá. tudo bem?")]
    assert voice.texts == ["[en] olá.", "tudo bem?"]                # síntese de voz frase a frase
    assert {d for _, _, d, _ in fb.played} == {"FAKE_OUT"}
    assert all(r == 22050 for _, r, _, _ in fb.played)


def test_fluxo_com_retorno_toca_nos_dois(engine):
    p, fb = engine
    _run_pipeline(p, np.ones(1600, np.int16), FakeWhisper("oi"), FakeVoice(),
                  monitor=True, out="spk1")
    assert {d for _, _, d, _ in fb.played} == {"FAKE_OUT", "spk1"}


def test_fluxo_do_interlocutor_nunca_vai_para_o_microfone_virtual(engine):
    p, fb = engine
    _run_pipeline(p, np.ones(1600, np.int16), FakeWhisper("hi"), FakeVoice(),
                  direction="in", out="spk1")
    assert {d for _, _, d, _ in fb.played} == {"spk1"}


def test_fluxo_sobrevive_a_erro_de_traducao(engine, monkeypatch):
    p, fb = engine
    monkeypatch.setattr(p, "do_translate", lambda *a: (_ for _ in ()).throw(ValueError("boom")))
    q = queue.Queue()
    q.put(np.ones(1600, np.int16))
    t = threading.Thread(target=p.pipeline_worker,
                         args=(q, FakeWhisper("x"), FakeVoice(), "pt", "en", "out"), daemon=True)
    t.start()
    time.sleep(0.5)
    assert t.is_alive()            # o worker continua rodando depois de um trecho com problema
    p._stop.set()
    t.join(2)


def test_eventos_json_emitidos(engine, capsys, monkeypatch):
    p, fb = engine
    monkeypatch.setattr(p, "_json_out", True)
    _run_pipeline(p, np.ones(1600, np.int16), FakeWhisper("bom dia"), FakeVoice())
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.startswith("{")]
    kinds = [(e["e"], e["dir"]) for e in events]
    assert ("transcript", "out") in kinds and ("translation", "out") in kinds


def test_atraso_extra_do_fluxo(engine):
    """O atraso extra da orquestração (filas, threads, divisão em frases) além dos
    modelos precisa ser pequeno: entrada do trecho → primeiro áudio de saída,
    descontado o tempo dos modelos."""
    p, fb = engine
    asr_s, tts_s = 0.05, 0.03
    q = queue.Queue()
    t = threading.Thread(target=p.pipeline_worker,
                         args=(q, FakeWhisper("um. dois. três.", delay=asr_s),
                               FakeVoice(delay=tts_s), "pt", "en", "out"), daemon=True)
    p._piper_out_ref[0] = FakeVoice(delay=tts_s)
    t.start()
    t0 = time.perf_counter()
    q.put(np.ones(16000, np.int16))
    deadline = time.time() + 5
    while not fb.played and time.time() < deadline:
        time.sleep(0.001)
    first_audio = fb.played[0][3] - t0
    p._stop.set()
    t.join(2)
    overhead = first_audio - asr_s - tts_s
    assert overhead < 0.05, f"atraso extra do fluxo {overhead * 1000:.1f} ms"


# ── VAD real do Silero (ONNX) ─────────────────────────────────────────────────

def test_vad_silero_onnx_detecta_fala_real():
    pytest.importorskip("onnxruntime")
    pytest.importorskip("faster_whisper")
    from conftest import BENCH_DATA
    wavs = sorted(BENCH_DATA.glob("*/*.wav"))
    if not wavs:
        pytest.skip("corpus de fala não baixado (benchmarks/fetch_speech_corpus.py)")
    import soundfile as sf
    vad = praxis.OnnxSileroVAD(min_silence_duration_ms=praxis.SILENCE_MS)
    silence = np.zeros(praxis.SR, np.float32)
    events = [vad(silence[i:i + 512]) for i in range(0, len(silence) - 511, 512)]
    assert not any(events), "o VAD disparou em silêncio digital"
    audio, sr = sf.read(str(wavs[0]), dtype="float32")
    x = np.concatenate([silence, audio, silence])
    vad.reset_states()
    evs = [e for i in range(0, len(x) - 511, 512) if (e := vad(x[i:i + 512]))]
    assert evs and "start" in evs[0] and any("end" in e for e in evs)
    first_start = evs[0]["start"] / praxis.SR
    assert 0.7 < first_start < 2.2, f"início da fala detectado em {first_start:.2f}s"


def test_proximo_trecho_e_processado_enquanto_traducao_anterior_toca(engine):
    """Encontrado por benchmarks/stream_test.py: o fluxo em série esperava cada
    tradução terminar de tocar antes de transcrever o próximo trecho, então um
    processador comum ficava para trás com fala contínua. Agora a reprodução
    acontece ao mesmo tempo que o processamento, mantém a ordem e nunca se
    sobrepõe a si mesma."""
    p, fb = engine
    plays = []

    def slow_play(pcm, rate, devices):
        start = time.perf_counter()
        time.sleep(0.4)                                   # falando a tradução
        plays.append((start, time.perf_counter(), pcm))
    fb.play_pcm_multi = slow_play
    asr_starts = []

    class W(FakeWhisper):
        def transcribe(self, audio, language=None, **kw):
            asr_starts.append(time.perf_counter())
            return super().transcribe(audio, language, **kw)

    q = queue.Queue()
    voice = FakeVoice()
    p._piper_out_ref[0] = voice
    t = threading.Thread(target=p.pipeline_worker,
                         args=(q, W("uma frase."), voice, "pt", "en", "out"), daemon=True)
    t.start()
    q.put(np.ones(1600, np.int16))
    q.put(np.ones(1600, np.int16))
    deadline = time.time() + 5
    while len(plays) < 2 and time.time() < deadline:
        time.sleep(0.01)
    p._stop.set()
    t.join(3)
    assert len(asr_starts) == 2 and len(plays) == 2
    assert asr_starts[1] < plays[0][1], "o 2º trecho esperou a 1ª tradução terminar de tocar"
    assert plays[1][0] >= plays[0][1] - 0.01, "as traduções se sobrepuseram"


# ── texto longo sem pontuação precisa ser dividido antes da tradução ──────────

def test_divisao_para_traducao_mantem_frases_curtas():
    assert praxis._chunk_for_mt("uma frase curta.") == ["uma frase curta."]


def test_divisao_para_traducao_quebra_texto_longo_sem_pontuacao():
    """Um trecho de 175 palavras sem pontuação fazia o tradutor repetir texto em loop."""
    text = " ".join(f"palavra{i}" for i in range(175))
    pieces = praxis._chunk_for_mt(text)
    assert all(len(p.split()) <= praxis.MT_MAX_WORDS for p in pieces)
    assert " ".join(pieces).split() == text.split()            # nada perdido nem fora de ordem


def test_divisao_para_traducao_prefere_virgulas_e_junta_pedacinhos():
    text = ", ".join(" ".join(f"w{i}_{j}" for j in range(12)) for i in range(5)) + ", fim"
    pieces = praxis._chunk_for_mt(text)
    assert len(pieces) == 5 and pieces[-1].endswith("fim")


def test_divisao_para_traducao_lida_com_escritas_sem_espacos():
    text = "这是一个很长的句子" * 20
    pieces = praxis._chunk_for_mt(text)
    assert all(len(p) <= praxis.MT_MAX_CHARS_NOSPACE + 8 for p in pieces)
    assert "".join(pieces) == text



# ── velocidade de fala adaptativa ─────────────────────────────────────────────

@pytest.mark.parametrize("backlog,expected", [(0.0, 1.0), (1.5, 1.0), (2.0, 0.87), (4.0, 0.87),
                                              (6.0, 0.77), (9.0, 0.7)])
def test_escala_de_duracao_da_fala(backlog, expected):
    assert praxis.speech_length_scale(backlog) == expected


def test_voz_acelera_quando_fala_traduzida_se_acumula(engine):
    """A fala traduzida de inglês→árabe dura ~121% da original, então a reprodução
    se acumula; a voz precisa acelerar em vez de ficar cada vez mais atrasada."""
    p, fb = engine
    pytest.importorskip("piper")
    calls = []

    def slow_play(pcm, rate, devices):
        time.sleep(0.05)
    fb.play_pcm_multi = slow_play
    long_pcm = np.full(1000 * 3, 1000, np.int16).tobytes()   # 3 s de fala por frase a 1 kHz

    class LongVoice(FakeVoice):
        def synthesize(self, text, syn_config=None):
            calls.append(None if syn_config is None else syn_config.length_scale)
            from conftest import FakeChunk
            yield FakeChunk(long_pcm)
    v = LongVoice(rate=1000)
    q = queue.Queue()
    p._piper_out_ref[0] = v
    t = threading.Thread(target=p.pipeline_worker,
                         args=(q, FakeWhisper("um. dois. três. quatro."), v, "pt", "en", "out"),
                         daemon=True)
    t.start()
    q.put(np.ones(1600, np.int16))
    deadline = time.time() + 3
    while len(calls) < 4 and time.time() < deadline:
        time.sleep(0.01)
    p._stop.set()
    t.join(3)
    assert calls[0] is None                      # nada na fila ainda → velocidade normal
    assert any(c is not None and c < 1.0 for c in calls[1:]), calls



def test_transcrever_trecho_remove_caracteres_quebrados():
    """O Whisper partia um caractere devanágari entre pedaços de texto (tokens) → "प्रद�" em hindi."""
    w = FakeWhisper("प्रद\ufffd तो  ग्रीनलैंड")
    assert praxis.transcribe_segment(w, np.zeros(1600, np.float32), "hi") == "प्रद तो ग्रीनलैंड"



def test_chines_tradicional_vira_simplificado():
    """Encontrado no teste com fala real: o Whisper misturou caracteres
    tradicionais (學生) com simplificados (学生) em chinês."""
    pytest.importorskip("opencc")
    w = FakeWhisper("適當使用博客可以使學生變得更善於分析")
    assert praxis.transcribe_segment(w, np.zeros(1600, np.float32), "zh") == "适当使用博客可以使学生变得更善于分析"
    w = FakeWhisper("學生")
    assert praxis.transcribe_segment(w, np.zeros(1600, np.float32), "ja") == "學生"   # japonês não muda



def test_instala_pacote_de_traducao_sem_stanza(tmp_path, monkeypatch):
    """Encontrado no teste de velocidade: a 1ª instalação de japonês/coreano
    falhava com "No module named 'stanza'" (o Praxis não instala o PyTorch)."""
    import zipfile
    pytest.importorskip("argostranslate")
    import argostranslate.settings
    monkeypatch.setattr(argostranslate.settings, "package_data_dir", tmp_path / "pacotes")
    monkeypatch.setitem(sys.modules, "stanza", None)        # simula o stanza ausente
    pacote = tmp_path / "translate-ja_en.argosmodel"
    with zipfile.ZipFile(pacote, "w") as zf:
        zf.writestr("translate-ja_en/metadata.json", '{"from_code": "ja", "to_code": "en"}')
    praxis._install_argos_package(pacote)
    assert (tmp_path / "pacotes" / "translate-ja_en" / "metadata.json").exists()
    falso = tmp_path / "falso.argosmodel"
    falso.write_text("não é zip")
    with pytest.raises(ValueError):
        praxis._install_argos_package(falso)



# ── primeiro uso sem internet ─────────────────────────────────────────────────

def test_sem_internet_explica_em_vez_de_travar(monkeypatch):
    """Antes: RecursionError (rede recusada) ou travado para sempre (rede muda)."""
    pytest.importorskip("argostranslate")
    import argostranslate.package
    import requests
    monkeypatch.setattr(argostranslate.package, "get_installed_packages", lambda: [])
    eventos = []
    monkeypatch.setattr(praxis, "_emit", eventos.append)

    def sem_rede(*a, **k):
        raise requests.ConnectionError("sem rede")
    monkeypatch.setattr(requests, "get", sem_rede)
    with pytest.raises(praxis.SemInternet) as erro:
        praxis._download_argos_pair("fr", "en")
    assert "internet" in str(erro.value) and "fr→en" in str(erro.value)
    assert any("Baixando pacote de tradução" in e.get("msg", "") for e in eventos)


def test_main_mostra_a_mensagem_de_sem_internet(engine, monkeypatch):
    p, fb = engine
    eventos = []
    monkeypatch.setattr(p, "_emit", eventos.append)
    monkeypatch.setattr(p.signal, "signal", lambda *a: None)
    monkeypatch.setattr(p, "setup_argos", lambda s, t: (_ for _ in ()).throw(p.SemInternet("Sem conexão com a internet: teste")))
    assert p.main(["--voice-out", "x.onnx", "--json-out"]) == 1
    assert eventos[-1] == {"e": "error", "msg": "Sem conexão com a internet: teste"}
    assert fb.torn_down


# ── clonagem de voz no Mac ────────────────────────────────────────────────────

def _clone(tmp_path):
    wav = tmp_path / "eu.wav"
    wav.write_bytes(b"RIFF")
    (tmp_path / "eu.json").write_text(json.dumps({"type": "omnivoice"}))
    return str(wav)


def test_clonagem_no_mac_liga_o_modo_de_compatibilidade(tmp_path, monkeypatch):
    import praxis_platform as plat
    monkeypatch.setattr(plat, "IS_MAC", True)
    monkeypatch.delenv("KMP_DUPLICATE_LIB_OK", raising=False)
    monkeypatch.delenv("OMP_NUM_THREADS", raising=False)
    assert praxis.prepare_clone_on_mac("voz.onnx", None) is False          # voz comum: nada muda
    assert "OMP_NUM_THREADS" not in os.environ
    assert praxis.prepare_clone_on_mac(_clone(tmp_path)) is True
    assert os.environ["KMP_DUPLICATE_LIB_OK"] == "TRUE" and os.environ["OMP_NUM_THREADS"] == "1"


def test_clonagem_fora_do_mac_nao_muda_nada(tmp_path, monkeypatch):
    import praxis_platform as plat
    monkeypatch.setattr(plat, "IS_MAC", False)
    monkeypatch.delenv("OMP_NUM_THREADS", raising=False)
    assert praxis.prepare_clone_on_mac(_clone(tmp_path)) is False
    assert "OMP_NUM_THREADS" not in os.environ


# ── eco e laços sem espaço ────────────────────────────────────────────────────

@pytest.mark.parametrize("texto,esperado", [
    ("少し少し少し少し少しスターバー", "少し少しスターバー"),
    ("अपना बवाश्वावावावावावावावा", "अपना बवाश्वावा"),
    ("hahaha que engraçado", "hahaha que engraçado"),          # 3 repetições: normal, fica
    ("custou 1000000 de reais em 2000", "custou 1000000 de reais em 2000"),   # números intactos
])
def test_guarda_pega_lacos_sem_espaco(texto, esperado):
    """Medido com eco: laços dentro de uma 'palavra' em escritas sem espaço."""
    assert praxis.collapse_repetitions(texto) == esperado


def test_trava_de_eco_ignora_o_microfone_enquanto_o_alto_falante_toca():
    """Com a tradução tocando no alto-falante, o que chega ao microfone é tratado
    como silêncio (medido sem a trava: erro 18% → 104% e laços sem fim)."""
    praxis._speaker_busy_until[0] = time.monotonic() + 60
    try:
        audio_q, seg_q = queue.Queue(), queue.Queue()
        active = threading.Event()
        active.set()
        praxis._stop.clear()
        t = threading.Thread(target=praxis.vad_worker, args=(audio_q, seg_q, "vad", 0.1),
                             kwargs=dict(active=active, ptt_flush=threading.Event(),
                                         vad_factory=FakeVAD, echo_gate=True), daemon=True)
        t.start()
        for c in _speech(40) + _silence(5):
            audio_q.put(c)
        time.sleep(0.4)
        praxis._stop.set()
        t.join(2)
        assert seg_q.empty(), "o eco virou um trecho para traduzir"
    finally:
        praxis._speaker_busy_until[0] = 0.0


def test_parser_aceita_fones():
    assert praxis.build_parser().parse_args(["--voice-out", "v", "--fones"]).fones is True



# ── escolha do tradutor ───────────────────────────────────────────────────────

@pytest.mark.parametrize("instalado,gpu,par,esperado", [
    (False, True, ("pt", "en"), "argos"),          # sem NLLB instalado: sempre Argos
    (True, True, ("pt", "en"), "nllb"),            # placa de vídeo: NLLB em tudo
    (True, False, ("pt", "en"), "argos"),          # processador, par forte: Argos (8× mais rápido)
    (True, False, ("en", "ar"), "nllb"),           # processador, idioma fraco: NLLB
    (True, False, ("ko", "en"), "nllb"),
])
def test_tradutor_automatico(monkeypatch, tmp_path, instalado, gpu, par, esperado):
    import praxis_accel
    d = tmp_path / "nllb"
    d.mkdir()
    if instalado:
        (d / "model.bin").write_bytes(b"x")
    monkeypatch.setattr(praxis, "TRANSLATOR", "auto")
    monkeypatch.setattr(praxis, "NLLB_MODEL", str(d))
    monkeypatch.setattr(praxis_accel, "cuda_device_count", lambda: 1 if gpu else 0)
    assert praxis.translator_for(*par) == esperado


def test_tradutor_pedido_tem_prioridade(monkeypatch):
    monkeypatch.setattr(praxis, "TRANSLATOR", "argos")
    assert praxis.translator_for("en", "ar") == "argos"


@pytest.mark.parametrize("backend, pedido, esperado", [
    ("cuda", None, 15.0),      # placa de vídeo: trecho maior (menos cortes no meio da fala)
    ("mlx", None, 15.0),
    ("cpu", None, 6.0),        # processador: trecho longo atrasaria demais
    ("cuda", 8.0, 8.0),        # o que o usuário pediu sempre vale
])
def test_trecho_maximo_depende_do_hardware(monkeypatch, backend, pedido, esperado):
    import praxis_accel
    monkeypatch.setattr(praxis, "MAX_SEG_S", 6.0)
    monkeypatch.setattr(praxis, "_max_seg_from_user", False)
    monkeypatch.setattr(praxis, "prepare_clone_on_mac", lambda *a: False)
    monkeypatch.setattr(praxis, "setup_argos", lambda *a: None)
    monkeypatch.setattr(praxis, "_emit", lambda d: None)

    class W:
        pass
    w = W()
    w.backend = backend
    monkeypatch.setattr(praxis, "load_whisper", lambda *a, **k: w)

    class Parar(Exception):
        pass

    def parar(*a, **k):
        raise Parar
    monkeypatch.setattr(praxis, "load_piper", parar)        # só interessa o que vem antes da voz
    argv = ["--voice-out", "v.onnx", "--model", "small"]
    if pedido is not None:
        argv += ["--max-segment", str(pedido)]
    monkeypatch.setattr(praxis_accel, "choose_asr", lambda *a, **k: (backend, "teste"))
    args = praxis.build_parser().parse_args(argv)
    if pedido is not None:
        monkeypatch.setattr(praxis, "MAX_SEG_S", pedido)
        monkeypatch.setattr(praxis, "_max_seg_from_user", True)
    with pytest.raises(Parar):
        praxis._run(args, bilateral=False)
    assert praxis.MAX_SEG_S == esperado
