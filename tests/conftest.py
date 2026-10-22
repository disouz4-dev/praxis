"""Fixtures compartilhadas. Os testes rápidos nunca carregam modelos de IA nem mexem em dispositivos de áudio reais."""
from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

BENCH_DATA = ROOT / "benchmarks" / "data" / "speech"


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: precisa de modelos reais / downloads (rodar só sob pedido: -m slow)")
    config.addinivalue_line("markers", "gui: precisa de uma tela (display)")


class FakeSeg:
    def __init__(self, text: str, no_speech_prob: float = 0.0) -> None:
        self.text = text
        self.no_speech_prob = no_speech_prob


class FakeWhisper:
    """Devolve uma transcrição fixa; registra as chamadas."""

    def __init__(self, text: str = "olá mundo. tudo bem?", delay: float = 0.0) -> None:
        self.text, self.delay, self.calls = text, delay, []

    def transcribe(self, audio, language=None, **kw):
        import time
        self.calls.append((len(audio), language, kw))
        if self.delay:
            time.sleep(self.delay)
        return iter([FakeSeg(self.text)]), types.SimpleNamespace(language=language)


class FakeChunk:
    def __init__(self, pcm: bytes) -> None:
        self.audio_int16_bytes = pcm


class FakeVoice:
    """Compatível com o Piper: synthesize(text) gera pedaços com audio_int16_bytes."""

    def __init__(self, rate: int = 22050, delay: float = 0.0) -> None:
        self.config = types.SimpleNamespace(sample_rate=rate)
        self.delay = delay
        self.texts: list[str] = []

    def synthesize(self, text: str):
        import time
        self.texts.append(text)
        if self.delay:
            time.sleep(self.delay)
        yield FakeChunk(np.full(int(self.config.sample_rate * 0.01), 1000, np.int16).tobytes())


class FakeBackend:
    """Backend de áudio que registra a reprodução em vez de tocar som."""
    name = "fake"
    can_create_virtual_devices = True

    def __init__(self) -> None:
        self.played: list[tuple[int, int, str | None]] = []
        self.torn_down = False

    def setup_virtual_mic(self, bilateral):
        import praxis_platform as plat
        return plat.VirtualMic(target="FAKE_OUT", mic_label="Fake Mic",
                               peer_capture="FAKE_IN" if bilateral else None,
                               peer_label="Fake Peer" if bilateral else "")

    def teardown(self):
        self.torn_down = True

    def resolve_mic(self, mic):
        return mic

    def play_pcm_multi(self, pcm, rate, devices):
        import time
        for d in devices:
            self.played.append((len(pcm), rate, d, time.perf_counter()))

    def list_inputs(self):
        return [("mic1", "Mic 1")]

    def list_outputs(self):
        return [("spk1", "Speakers")]

    def setup_hint(self):
        return ""


@pytest.fixture
def engine(monkeypatch):
    """Estado limpo do módulo do motor praxis, com áudio falso + tradução que não faz nada."""
    import praxis
    fb = FakeBackend()
    monkeypatch.setattr(praxis, "_backend", fb)
    monkeypatch.setattr(praxis, "_vmic", fb.setup_virtual_mic(False))
    monkeypatch.setattr(praxis, "do_translate", lambda t, s, d: f"[{d}] {t}")
    praxis._stop.clear()
    praxis._active.set()
    praxis._peer_active.set()
    praxis._ptt_flush.clear()
    praxis._transcripts.clear()
    yield praxis, fb
    praxis._stop.set()


@pytest.fixture
def cfg_module(tmp_path, monkeypatch):
    """praxis_config com a configuração e as vozes redirecionadas para uma pasta temporária."""
    import praxis_config as pc
    monkeypatch.setattr(pc, "CONFIG_FILE", tmp_path / "cfg" / "config.json")
    monkeypatch.setattr(pc, "VOICES_DIR", tmp_path / "voices")
    return pc


@pytest.fixture(autouse=True)
def _sem_limite_de_qualidade(monkeypatch):
    """O limite de qualidade por idioma (praxis_accel.QUALITY_LIMIT) depende do hardware
    de quem roda os testes; fora dos testes dele mesmo, não pode bloquear nada."""
    import praxis_accel
    monkeypatch.setattr(praxis_accel, "QUALITY_LIMIT", 1.0)


@pytest.fixture(autouse=True)
def _comparacao_da_placa_em_arquivo_temporario(monkeypatch, tmp_path):
    """A comparação placa de vídeo × processador nunca pode rodar de verdade nem gravar
    no arquivo real de quem roda os testes."""
    import praxis_accel
    monkeypatch.setattr(praxis_accel, "_check_file", lambda: tmp_path / "placa_de_video.json")
    monkeypatch.setattr(praxis_accel, "compare_gpu_cpu",
                        lambda b: {"backend": b, "usar_gpu": True, "motivo": "teste"})
