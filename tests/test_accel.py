"""GPU/backend selection for every hardware family, with mocked detection.

CI runners have no GPUs, so the decision logic is tested exhaustively here and
the real GPU paths are exercised by benchmarks on actual hardware."""
import sys
import types

import numpy as np
import pytest

import praxis_accel as accel


@pytest.fixture
def hw(monkeypatch):
    """Configure a fake machine: hw(cuda=1, apple_silicon=True, mlx=True, wcpp='vulkan', ...)."""
    def _set(cuda=0, apple_silicon=False, intel_mac=False, mlx=False, wcpp=None,
             providers=("CPUExecutionProvider",), system=None):
        for f in (accel.cuda_device_count, accel.whispercpp_gpu_backend, accel.onnx_providers):
            f.cache_clear()
        monkeypatch.setattr(accel, "cuda_device_count", lambda: cuda)
        monkeypatch.setattr(accel, "whispercpp_gpu_backend", lambda: wcpp)
        monkeypatch.setattr(accel, "onnx_providers", lambda: tuple(providers))
        monkeypatch.setattr(accel, "IS_APPLE_SILICON", apple_silicon)
        monkeypatch.setattr(accel, "IS_INTEL_MAC", intel_mac)
        monkeypatch.setattr(accel, "SYSTEM", system or ("Darwin" if apple_silicon or intel_mac else "Linux"))
        real_has = accel._has
        monkeypatch.setattr(accel, "_has", lambda m: mlx if m == "mlx_whisper" else real_has(m))
        monkeypatch.setattr(accel, "gpu_names", lambda: ())
        monkeypatch.delenv("PRAXIS_DEVICE", raising=False)
    return _set


@pytest.mark.parametrize("cfg,expected", [
    (dict(cuda=1), "cuda"),                                            # NVIDIA Linux/Windows
    (dict(cuda=2, apple_silicon=False, wcpp="vulkan"), "cuda"),        # CUDA wins over Vulkan
    (dict(apple_silicon=True, mlx=True), "mlx"),                       # M1–M4 with mlx-whisper
    (dict(apple_silicon=True, mlx=False, wcpp="metal"), "whispercpp"), # M-series, whisper.cpp Metal
    (dict(apple_silicon=True), "cpu"),                                 # M-series, nothing extra
    (dict(intel_mac=True, wcpp="metal"), "cpu"),                       # Intel+AMD Mac: Metal measured wrong
    (dict(wcpp="vulkan", system="Windows"), "whispercpp"),             # AMD/Intel GPU on Windows
    (dict(wcpp="vulkan"), "whispercpp"),                               # AMD/Intel GPU on Linux
    (dict(wcpp="hip"), "whispercpp"),                                  # ROCm build
    (dict(), "cpu"),                                                   # no GPU
])
def test_auto_asr_choice(hw, cfg, expected):
    hw(**cfg)
    backend, reason = accel.choose_asr("auto")
    assert backend == expected, reason
    assert reason


def test_requested_backend_overrides_and_validates(hw):
    hw(cuda=1)
    assert accel.choose_asr("cpu") == ("cpu", "requested")
    with pytest.raises(ValueError):
        accel.choose_asr("opencl")


def test_env_override(hw, monkeypatch):
    hw(cuda=1)
    monkeypatch.setenv("PRAXIS_DEVICE", "cpu")
    assert accel.plan().asr == "cpu"


@pytest.mark.parametrize("cfg,first", [
    (dict(providers=("CUDAExecutionProvider", "CPUExecutionProvider")), "CUDAExecutionProvider"),
    (dict(providers=("DmlExecutionProvider", "CPUExecutionProvider"), system="Windows"), "DmlExecutionProvider"),
    (dict(apple_silicon=True, providers=("CoreMLExecutionProvider", "CPUExecutionProvider")), "CoreMLExecutionProvider"),
    (dict(intel_mac=True, providers=("CoreMLExecutionProvider", "CPUExecutionProvider")), None),
    (dict(), None),
])
def test_tts_provider_choice(hw, cfg, first):
    hw(**cfg)
    prov = accel.choose_tts_providers()
    if first is None:
        assert prov == []
    else:
        assert prov[0] == first and prov[-1] == "CPUExecutionProvider"


def test_plan_summary(hw):
    hw(cuda=1, providers=("CUDAExecutionProvider", "CPUExecutionProvider"))
    p = accel.plan()
    assert p.asr == "cuda" and p.mt_device == "cuda" and p.clone_device == "cuda"
    assert "ASR=cuda" in p.summary()


def test_mlx_adapter_contract(monkeypatch):
    calls = {}
    fake = types.ModuleType("mlx_whisper")

    def transcribe(audio, **kw):
        calls.update(kw)
        return {"segments": [{"text": " olá", "no_speech_prob": 0.1, "avg_logprob": -0.2},
                             {"text": " mundo", "no_speech_prob": 0.9, "avg_logprob": -1.5}],
                "language": "pt"}
    fake.transcribe = transcribe
    monkeypatch.setitem(sys.modules, "mlx_whisper", fake)
    m = accel.MLXWhisper("small")
    import praxis
    assert praxis.transcribe_segment(m, np.zeros(1600, np.float32), "pt") == "olá"
    assert calls["path_or_hf_repo"] == "mlx-community/whisper-small-mlx"
    assert calls["language"] == "pt" and calls["temperature"] == 0


def test_load_asr_falls_back_to_cpu(monkeypatch):
    pytest.importorskip("faster_whisper")

    class FakeWM:
        def __init__(self, name, device, compute_type):
            if device == "cuda":
                raise RuntimeError("no CUDA")
            self.device = device
    import faster_whisper
    monkeypatch.setattr(faster_whisper, "WhisperModel", FakeWM)
    logs = []
    for backend in ("cuda", "mlx", "whispercpp"):
        monkeypatch.setitem(sys.modules, "mlx_whisper", None)
        monkeypatch.setitem(sys.modules, "pywhispercpp.model", None)
        m = accel.load_asr("tiny", backend, log=logs.append)
        assert m.device == "cpu" and m.backend == "cpu"
    assert len(logs) == 3


def test_check_reports_acceleration():
    import json
    import subprocess
    from conftest import ROOT
    r = subprocess.run([sys.executable, str(ROOT / "praxis.py"), "--check"],
                       capture_output=True, text=True, timeout=120)
    acc = json.loads(r.stdout)["acceleration"]
    assert acc.get("asr") in accel.ASR_BACKENDS, acc


@pytest.mark.slow
def test_whispercpp_adapter_real_speech():
    """Real whisper.cpp run (CPU) through the adapter on a real clip."""
    pytest.importorskip("pywhispercpp")
    from conftest import BENCH_DATA
    import soundfile as sf
    import praxis
    wavs = sorted((BENCH_DATA / "en").glob("*.wav"))
    if not wavs:
        pytest.skip("corpus missing")
    w = accel.WhisperCpp("tiny", use_gpu=False)
    a, _ = sf.read(str(wavs[0]), dtype="float32")
    text = praxis.transcribe_segment(w, a, "en")
    assert len(text.split()) >= 3, text


def test_ensure_cuda_libs_never_raises(tmp_path, monkeypatch):
    """pip-installed cuBLAS/cuDNN must be registered without LD_LIBRARY_PATH
    (found on lab2: CUDA Whisper silently fell back to CPU). With no nvidia
    packages present it is a harmless no-op."""
    accel.ensure_cuda_libs.cache_clear()
    monkeypatch.setattr(sys, "path", [str(tmp_path)])
    import site
    monkeypatch.setattr(site, "getsitepackages", lambda: [str(tmp_path)])
    monkeypatch.setattr(site, "getusersitepackages", lambda: str(tmp_path))
    (tmp_path / "nvidia" / "cublas" / "lib").mkdir(parents=True)
    (tmp_path / "nvidia" / "cublas" / "lib" / "libcublas.so.12").write_bytes(b"not a real lib")
    assert isinstance(accel.ensure_cuda_libs(), list)       # bad .so is skipped, no crash
    accel.ensure_cuda_libs.cache_clear()


# ── voice speaking-rate calibration ───────────────────────────────────────────

class _RateVoice:
    """Speaks `letters_per_s` letters per second."""
    def __init__(self, letters_per_s):
        self.lps = letters_per_s
        self.config = types.SimpleNamespace(sample_rate=1000)

    def synthesize(self, text):
        letters = sum(ch.isalpha() for ch in text)
        secs = letters / self.lps
        yield types.SimpleNamespace(audio_int16_bytes=b"\0\0" * int(secs * 1000))


@pytest.mark.parametrize("lps,expected", [(20.0, 1.0), (15.0, 1.0), (12.0, 0.8), (8.5, accel.MIN_RATE_SCALE)])
def test_voice_rate_scale(lps, expected):
    """Measured: German "MLS" speaks 10.8 letters/s, "Thorsten" 19.9 → slow
    voices get a faster default speed, bounded so speech stays natural."""
    assert accel.voice_rate_scale(_RateVoice(lps), "de") == pytest.approx(expected, abs=0.01)


def test_voice_rate_scale_skips_languages_without_target():
    assert accel.voice_rate_scale(_RateVoice(3.0), "zh") == 1.0


def test_calibration_is_applied_on_top_of_adaptive_rate():
    pytest.importorskip("piper")
    import praxis
    seen = []

    class V(_RateVoice):
        def synthesize(self, text, syn_config=None):
            seen.append(None if syn_config is None else syn_config.length_scale)
            yield from super().synthesize(text)
    v = V(10.0)
    v.praxis_rate_scale = 0.8
    list(praxis._synthesize(v, "hallo welt", 1.0))
    list(praxis._synthesize(v, "hallo welt", 0.87))
    assert seen == [pytest.approx(0.8), pytest.approx(0.8 * 0.87)]


def test_german_default_voice_is_the_fast_one(cfg_module):
    assert cfg_module._best_catalog_voice("de")["speaker"] == "thorsten"


# ── automatic model choice ────────────────────────────────────────────────────

def test_recommend_model_per_hardware():
    assert accel.recommend_model("pt", "cuda")[0] == "large-v3-turbo"
    assert accel.recommend_model("pt", "mlx")[0] == "large-v3-turbo"
    assert accel.recommend_model("pt", "cpu")[0] == "small"


def test_recommend_model_warns_on_poor_languages():
    model, note = accel.recommend_model("hi", "cpu")
    assert model == "small" and "hi" in note and "70%" in note
    _, note = accel.recommend_model("fr", "cpu")
    assert "placa de vídeo" in note                 # suggests the GPU fix
    assert accel.recommend_model("pt", "cuda")[1] == ""
    assert accel.recommend_model("xx", "cpu")[1] == ""


def test_engine_cli_accepts_auto_model():
    import praxis
    assert praxis.build_parser().parse_args(["--voice-out", "v.onnx"]).model == "auto"
