"""Engine (praxis.py): pure helpers, CLI, VAD segmentation, full pipeline with fakes."""
import json
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


# ── helpers ───────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text,expected", [
    ("Hello. How are you?", ["Hello.", "How are you?"]),
    ("One sentence", ["One sentence"]),
    ("Wait… what! Really?", ["Wait…", "what!", "Really?"]),
    ("", [""]),
])
def test_split_sentences(text, expected):
    assert praxis._split_sentences(text) == expected


def test_transcribe_segment_filters_noise_and_nonspeech():
    w = FakeWhisper("...")
    assert praxis.transcribe_segment(w, np.zeros(1600, np.float32), "pt") == ""
    w = FakeWhisper(" bom dia ")
    assert praxis.transcribe_segment(w, np.zeros(1600, np.float32), "pt") == "bom dia"
    # production decoding options are what's passed
    assert w.calls[0][1] == "pt" and w.calls[0][2]["beam_size"] == 1


def test_transcribe_segment_drops_only_unsure_nonspeech():
    """Whisper's own rule: drop only when it thinks it is not speech AND the
    text is low-confidence. no_speech_prob alone (0.53–0.59) threw away real
    phrases in the streaming test."""
    from conftest import FakeSeg
    noise = FakeSeg("ruído", 0.9); noise.avg_logprob = -1.6
    unsure_but_real = FakeSeg("estático errante", 0.59); unsure_but_real.avg_logprob = -0.4
    speech = FakeSeg("fala", 0.1); speech.avg_logprob = -0.2

    class W:
        def transcribe(self, a, language=None, **kw):
            return iter([noise, unsure_but_real, speech]), None
    assert praxis.transcribe_segment(W(), np.zeros(10, np.float32), "pt") == "estático errante fala"


def test_short_leftover_joins_next_segment():
    """A tiny piece left after a cut is glued to the next segment instead of
    being sent alone (Whisper returns nothing for it and the syllable is lost)."""
    tiny = _speech(int(0.4 / (praxis.VAD_CHUNK / praxis.SR)))
    longer = _speech(40)
    segs = _run_vad(tiny + _silence(4) + longer + _silence(5))
    assert len(segs) == 1
    assert len(segs[0]) >= (len(tiny) + len(longer)) * praxis.VAD_CHUNK


def test_short_utterance_alone_is_still_sent_after_silence():
    """"Sim." followed by silence must not stay stuck waiting for more speech."""
    tiny = _speech(int(0.4 / (praxis.VAD_CHUNK / praxis.SR)))
    segs = _run_vad(tiny + _silence(int(1.5 / (praxis.VAD_CHUNK / praxis.SR))))
    assert len(segs) == 1


def test_translation_pivots_through_english(monkeypatch):
    calls = []
    monkeypatch.setattr(praxis, "_translate_pair",
                        lambda t, s, d: calls.append((s, d)) or f"{t}>{d}")
    assert praxis.do_translate("oi", "pt", "it") == "oi>en>it"
    assert calls == [("pt", "en"), ("en", "it")]
    calls.clear()
    assert praxis.do_translate("oi", "pt", "en") == "oi>en"
    assert calls == [("pt", "en")]
    assert praxis.do_translate("oi", "pt", "pt") == "oi"


def test_translate_pair_uses_ct2_per_sentence(monkeypatch):
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


def test_engine_import_does_not_pull_torch():
    """PyTorch + CTranslate2 in one process crash Whisper on macOS (two OpenMP
    runtimes). The engine must not import torch unless OmniVoice is used."""
    code = ("import sys, praxis; praxis.build_parser(); "
            "print('torch' in sys.modules, 'stanza' in sys.modules)")
    r = subprocess.run([sys.executable, "-c", code], cwd=str(ROOT), capture_output=True,
                       text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    assert r.stdout.split() == ["False", "False"]


def test_setup_argos_installs_pivot_pairs(monkeypatch):
    pairs = []
    monkeypatch.setattr(praxis, "_download_argos_pair", lambda s, t: pairs.append((s, t)))
    praxis.setup_argos("pt", "de")
    praxis.setup_argos("en", "es")
    praxis.setup_argos("fr", "fr")
    assert pairs == [("pt", "en"), ("en", "de"), ("en", "es")]


def test_load_piper_dispatches_omnivoice_clone(tmp_path):
    wav = tmp_path / "me.wav"
    wav.write_bytes(b"RIFF")
    (tmp_path / "me.json").write_text(json.dumps({"type": "omnivoice", "name": "me"}))
    eng = praxis.load_piper(str(wav))
    assert isinstance(eng, praxis.OmniVoiceEngine)
    assert eng.config.sample_rate == 24000
    eng.set_live_reference("/tmp/x.wav", "texto")
    assert eng._live_ref == "/tmp/x.wav"


# ── CLI ───────────────────────────────────────────────────────────────────────

def test_parser_defaults_and_choices():
    a = praxis.build_parser().parse_args(["--voice-out", "v.onnx"])
    assert (a.src, a.tgt, a.mode, a.model, a.gate_threshold) == ("pt", "en", "vad", "small", 0.10)
    with pytest.raises(SystemExit):
        praxis.build_parser().parse_args(["--mode", "bogus"])


def test_cli_requires_voice_out():
    r = subprocess.run([sys.executable, str(ROOT / "praxis.py")], capture_output=True, text=True)
    assert r.returncode == 2 and "voice-out" in r.stderr


def test_cli_rejects_bad_gate_threshold():
    r = subprocess.run([sys.executable, str(ROOT / "praxis.py"), "--voice-out", "v",
                        "--gate-threshold", "3"], capture_output=True, text=True)
    assert r.returncode == 2


def test_cli_check_reports_environment():
    """Smoke: the engine starts, imports, inspects audio and exits 0 on every OS."""
    r = subprocess.run([sys.executable, str(ROOT / "praxis.py"), "--check"],
                       capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    rep = json.loads(r.stdout)
    assert rep["platform"] in ("Linux", "Darwin", "Windows")
    assert rep["modules"]["numpy"] is True
    assert "audio_backend" in rep


def test_startup_failure_still_tears_down(engine, monkeypatch):
    p, fb = engine
    monkeypatch.setattr(p, "setup_argos", lambda s, t: (_ for _ in ()).throw(RuntimeError("no net")))
    monkeypatch.setattr(p.signal, "signal", lambda *a: None)
    rc = p.main(["--voice-out", "x.onnx"])
    assert rc == 1 and fb.torn_down


# ── VAD segmentation ──────────────────────────────────────────────────────────

class FakeVAD:
    """Silero VADIterator stand-in: 'speech' when chunk amplitude > 0.05."""

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


def test_vad_emits_one_segment_per_utterance():
    segs = _run_vad(_silence(3) + _speech(30) + _silence(5) + _speech(30) + _silence(5))
    assert len(segs) == 2
    assert segs[0].dtype == np.int16


def test_vad_forces_cut_at_max_segment_length():
    n = int(praxis.MAX_SEG_S * praxis.SR / praxis.VAD_CHUNK) * 2 + 5   # > 2 × MAX_SEG_S
    segs = _run_vad(_speech(n) + _silence(5))
    assert len(segs) >= 2
    longest = max(len(s) for s in segs) / praxis.SR
    assert longest <= praxis.MAX_SEG_S + praxis.VAD_CHUNK / praxis.SR + 1e-6


def test_gate_mode_ignores_quiet_speech():
    quiet = [np.full(praxis.VAD_CHUNK, 0.06, np.float32) for _ in range(10)]
    assert _run_vad(quiet + _silence(5), mode="gate", gate=0.2) == []
    assert len(_run_vad(_speech(30) + _silence(5), mode="gate", gate=0.2)) == 1


def test_ptt_release_flushes_and_deactivates():
    active = threading.Event()
    segs = _run_vad(_speech(8), mode="ptt", ptt_events={7}, active=active)
    assert len(segs) == 1 and not active.is_set()


# ── full pipeline (fakes) ─────────────────────────────────────────────────────

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


def test_pipeline_end_to_end_plays_into_virtual_mic(engine):
    p, fb = engine
    voice = FakeVoice()
    _run_pipeline(p, np.ones(16000, np.int16), FakeWhisper("olá. tudo bem?"), voice)
    assert list(p._transcripts) == [("out", "olá. tudo bem?", "[en] olá. tudo bem?")]
    assert voice.texts == ["[en] olá.", "tudo bem?"]                # per-sentence TTS
    assert {d for _, _, d, _ in fb.played} == {"FAKE_OUT"}
    assert all(r == 22050 for _, r, _, _ in fb.played)


def test_pipeline_monitor_plays_on_both(engine):
    p, fb = engine
    _run_pipeline(p, np.ones(1600, np.int16), FakeWhisper("oi"), FakeVoice(),
                  monitor=True, out="spk1")
    assert {d for _, _, d, _ in fb.played} == {"FAKE_OUT", "spk1"}


def test_pipeline_peer_direction_never_goes_to_virtual_mic(engine):
    p, fb = engine
    _run_pipeline(p, np.ones(1600, np.int16), FakeWhisper("hi"), FakeVoice(),
                  direction="in", out="spk1")
    assert {d for _, _, d, _ in fb.played} == {"spk1"}


def test_pipeline_survives_translation_error(engine, monkeypatch):
    p, fb = engine
    monkeypatch.setattr(p, "do_translate", lambda *a: (_ for _ in ()).throw(ValueError("boom")))
    q = queue.Queue()
    q.put(np.ones(1600, np.int16))
    t = threading.Thread(target=p.pipeline_worker,
                         args=(q, FakeWhisper("x"), FakeVoice(), "pt", "en", "out"), daemon=True)
    t.start()
    time.sleep(0.5)
    assert t.is_alive()            # worker keeps running after a bad segment
    p._stop.set()
    t.join(2)


def test_json_events_emitted(engine, capsys, monkeypatch):
    p, fb = engine
    monkeypatch.setattr(p, "_json_out", True)
    _run_pipeline(p, np.ones(1600, np.int16), FakeWhisper("bom dia"), FakeVoice())
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line.startswith("{")]
    kinds = [(e["e"], e["dir"]) for e in events]
    assert ("transcript", "out") in kinds and ("translation", "out") in kinds


def test_pipeline_overhead_latency(engine):
    """Orchestration overhead (queues, threads, sentence split) on top of the
    models must stay small: segment-in → first audio-out minus model time."""
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
    assert overhead < 0.05, f"pipeline overhead {overhead * 1000:.1f} ms"


# ── real Silero ONNX VAD ──────────────────────────────────────────────────────

def test_onnx_silero_vad_detects_real_speech():
    pytest.importorskip("onnxruntime")
    pytest.importorskip("faster_whisper")
    from conftest import BENCH_DATA
    wavs = sorted(BENCH_DATA.glob("*/*.wav"))
    if not wavs:
        pytest.skip("speech corpus not downloaded (benchmarks/fetch_speech_corpus.py)")
    import soundfile as sf
    vad = praxis.OnnxSileroVAD(min_silence_duration_ms=praxis.SILENCE_MS)
    silence = np.zeros(praxis.SR, np.float32)
    events = [vad(silence[i:i + 512]) for i in range(0, len(silence) - 511, 512)]
    assert not any(events), "VAD fired on digital silence"
    audio, sr = sf.read(str(wavs[0]), dtype="float32")
    x = np.concatenate([silence, audio, silence])
    vad.reset_states()
    evs = [e for i in range(0, len(x) - 511, 512) if (e := vad(x[i:i + 512]))]
    assert evs and "start" in evs[0] and any("end" in e for e in evs)
    first_start = evs[0]["start"] / praxis.SR
    assert 0.7 < first_start < 2.2, f"speech start detected at {first_start:.2f}s"


def test_next_segment_is_processed_while_previous_translation_plays(engine):
    """Found by benchmarks/stream_test.py: the serial pipeline waited for each
    translation to finish playing before transcribing the next segment, so a
    CPU fell behind continuous speech. Playback now overlaps processing, keeps
    order and never overlaps itself."""
    p, fb = engine
    plays = []

    def slow_play(pcm, rate, devices):
        start = time.perf_counter()
        time.sleep(0.4)                                   # speaking the translation
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
    assert asr_starts[1] < plays[0][1], "2nd segment waited for the 1st translation to finish playing"
    assert plays[1][0] >= plays[0][1] - 0.01, "translations overlapped"


# ── long unpunctuated input must be split before translation ──────────────────

def test_chunk_for_mt_keeps_short_sentences():
    assert praxis._chunk_for_mt("uma frase curta.") == ["uma frase curta."]


def test_chunk_for_mt_splits_long_unpunctuated_text():
    """A 175-word unpunctuated passage made the translator output a loop."""
    text = " ".join(f"palavra{i}" for i in range(175))
    pieces = praxis._chunk_for_mt(text)
    assert all(len(p.split()) <= praxis.MT_MAX_WORDS for p in pieces)
    assert " ".join(pieces).split() == text.split()            # nothing lost or reordered


def test_chunk_for_mt_prefers_commas_and_merges_tiny_pieces():
    text = ", ".join(" ".join(f"w{i}_{j}" for j in range(12)) for i in range(5)) + ", fim"
    pieces = praxis._chunk_for_mt(text)
    assert len(pieces) == 5 and pieces[-1].endswith("fim")


def test_chunk_for_mt_handles_scripts_without_spaces():
    text = "这是一个很长的句子" * 20
    pieces = praxis._chunk_for_mt(text)
    assert all(len(p) <= praxis.MT_MAX_CHARS_NOSPACE + 8 for p in pieces)
    assert "".join(pieces) == text
