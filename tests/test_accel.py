"""Escolha de placa de vídeo (GPU)/backend para cada família de hardware, com a detecção simulada.

As máquinas da integração contínua (CI) não têm GPU, então a lógica de decisão é
testada a fundo aqui e os caminhos reais de GPU são exercitados pelos benchmarks
em hardware de verdade."""
import sys
import types

import numpy as np
import pytest

import praxis_accel as accel

_COMPARE_REAL = accel.compare_gpu_cpu      # o conftest troca por um dublê em todos os testes


@pytest.fixture
def hw(monkeypatch):
    """Configura uma máquina falsa: hw(cuda=1, apple_silicon=True, mlx=True, wcpp='vulkan', ...)."""
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
        monkeypatch.setattr(accel, "gpu_check_cached", lambda b: None)    # nada medido ainda
        monkeypatch.delenv("PRAXIS_DEVICE", raising=False)
    return _set


@pytest.mark.parametrize("cfg,expected", [
    (dict(cuda=1), "cuda"),                                            # NVIDIA no Linux/Windows
    (dict(cuda=2, apple_silicon=False, wcpp="vulkan"), "cuda"),        # CUDA ganha do Vulkan
    (dict(apple_silicon=True, mlx=True), "mlx"),                       # M1–M4 com mlx-whisper
    (dict(apple_silicon=True, mlx=False, wcpp="metal"), "whispercpp"), # série M, whisper.cpp com Metal
    (dict(apple_silicon=True), "cpu"),                                 # série M, nada extra
    (dict(intel_mac=True, wcpp="metal"), "whispercpp"),                # Mac Intel+AMD: tenta a placa (a medição decide)
    (dict(wcpp="vulkan", system="Windows"), "whispercpp"),             # GPU AMD/Intel no Windows
    (dict(wcpp="vulkan"), "whispercpp"),                               # GPU AMD/Intel no Linux
    (dict(wcpp="hip"), "whispercpp"),                                  # versão compilada com ROCm
    (dict(), "cpu"),                                                   # sem GPU
])
def test_escolha_automatica_do_reconhecimento_de_fala(hw, cfg, expected):
    hw(**cfg)
    backend, reason = accel.choose_asr("auto")
    assert backend == expected, reason
    assert reason


def test_backend_pedido_tem_prioridade_e_e_validado(hw):
    hw(cuda=1)
    assert accel.choose_asr("cpu") == ("cpu", "pedido pelo usuário")
    with pytest.raises(ValueError):
        accel.choose_asr("opencl")


def test_variavel_de_ambiente_tem_prioridade(hw, monkeypatch):
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
def test_escolha_do_provedor_de_sintese_de_voz(hw, cfg, first):
    hw(**cfg)
    prov = accel.choose_tts_providers()
    if first is None:
        assert prov == []
    else:
        assert prov[0] == first and prov[-1] == "CPUExecutionProvider"


def test_resumo_do_plano(hw):
    hw(cuda=1, providers=("CUDAExecutionProvider", "CPUExecutionProvider"))
    p = accel.plan()
    assert p.asr == "cuda" and p.mt_device == "cuda" and p.clone_device == "cuda"
    assert "ASR=cuda" in p.summary()


def test_contrato_do_adaptador_mlx(monkeypatch):
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


def test_carregar_reconhecimento_de_fala_recorre_a_cpu(monkeypatch):
    pytest.importorskip("faster_whisper")

    class FakeWM:
        def __init__(self, name, device, compute_type, cpu_threads=0):
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


def test_check_relata_aceleracao():
    import json
    import subprocess
    from conftest import ROOT
    r = subprocess.run([sys.executable, str(ROOT / "praxis.py"), "--check"],
                       capture_output=True, text=True, timeout=120)
    acc = json.loads(r.stdout)["acceleration"]
    assert acc.get("asr") in accel.ASR_BACKENDS, acc


@pytest.mark.slow
def test_adaptador_whispercpp_com_fala_real():
    """Execução real do whisper.cpp (na CPU) pelo adaptador, com um áudio real."""
    pytest.importorskip("pywhispercpp")
    from conftest import BENCH_DATA
    import soundfile as sf
    import praxis
    wavs = sorted((BENCH_DATA / "en").glob("*.wav"))
    if not wavs:
        pytest.skip("corpus ausente")
    w = accel.WhisperCpp("tiny", use_gpu=False)
    a, _ = sf.read(str(wavs[0]), dtype="float32")
    text = praxis.transcribe_segment(w, a, "en")
    assert len(text.split()) >= 3, text


def test_garantir_bibliotecas_cuda_nunca_da_erro(tmp_path, monkeypatch):
    """cuBLAS/cuDNN instalados via pip precisam ser registrados sem LD_LIBRARY_PATH
    (achado no lab2: o Whisper com CUDA voltava para a CPU sem avisar). Sem
    pacotes nvidia instalados, não faz nada e não causa problema."""
    accel.ensure_cuda_libs.cache_clear()
    monkeypatch.setattr(sys, "path", [str(tmp_path)])
    import site
    monkeypatch.setattr(site, "getsitepackages", lambda: [str(tmp_path)])
    monkeypatch.setattr(site, "getusersitepackages", lambda: str(tmp_path))
    (tmp_path / "nvidia" / "cublas" / "lib").mkdir(parents=True)
    (tmp_path / "nvidia" / "cublas" / "lib" / "libcublas.so.12").write_bytes(b"not a real lib")
    assert isinstance(accel.ensure_cuda_libs(), list)       # .so inválido é ignorado, sem travar
    accel.ensure_cuda_libs.cache_clear()


# ── calibração da velocidade de fala da voz ───────────────────────────────────

class _RateVoice:
    """Fala `letters_per_s` letras por segundo."""
    def __init__(self, letters_per_s):
        self.lps = letters_per_s
        self.config = types.SimpleNamespace(sample_rate=1000)

    def synthesize(self, text):
        letters = sum(ch.isalpha() for ch in text)
        secs = letters / self.lps
        yield types.SimpleNamespace(audio_int16_bytes=b"\0\0" * int(secs * 1000))


@pytest.mark.parametrize("lps,expected", [(20.0, 1.0), (15.0, 1.0), (12.0, 0.8), (8.5, accel.MIN_RATE_SCALE)])
def test_escala_de_velocidade_da_voz(lps, expected):
    """Medido: a voz alemã "MLS" fala 10.8 letras/s, a "Thorsten" 19.9 → vozes
    lentas ganham uma velocidade padrão maior, com limite para a fala continuar natural."""
    assert accel.voice_rate_scale(_RateVoice(lps), "de") == pytest.approx(expected, abs=0.01)


def test_escala_de_velocidade_ignora_idiomas_sem_meta():
    assert accel.voice_rate_scale(_RateVoice(3.0), "zh") == 1.0


def test_calibracao_e_aplicada_sobre_a_velocidade_adaptativa():
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


def test_voz_alema_padrao_e_a_rapida(cfg_module):
    assert cfg_module._best_catalog_voice("de")["speaker"] == "thorsten"


# ── escolha automática do modelo ──────────────────────────────────────────────

def test_recomenda_modelo_por_hardware():
    assert accel.recommend_model("pt", "cuda")[0] == "large-v3-turbo"
    assert accel.recommend_model("pt", "mlx")[0] == "large-v3-turbo"
    assert accel.recommend_model("pt", "cpu")[0] == "small"


def test_recomenda_modelo_avisa_sobre_idiomas_fracos():
    model, note = accel.recommend_model("hi", "cpu")
    assert model == "small" and "hi" in note and f"{accel.MEASURED_ERROR['cpu']['hi']:.0%}" in note
    _, note = accel.recommend_model("nl", "cpu")
    assert "placa de vídeo" in note                 # sugere a solução com GPU
    assert accel.recommend_model("pt", "cuda")[1] == ""
    assert accel.recommend_model("xx", "cpu")[1] == ""


def test_cli_do_motor_aceita_modelo_auto():
    import praxis
    assert praxis.build_parser().parse_args(["--voice-out", "v.onnx"]).model == "auto"


def test_limite_de_qualidade_bloqueia_idioma_que_erra_demais(monkeypatch):
    monkeypatch.setattr(accel, "QUALITY_LIMIT", 0.15)
    monkeypatch.setitem(accel.MEASURED_ERROR, "cpu", {"model": "small", "pt": 0.05, "hi": 0.70, "fr": 0.25})
    monkeypatch.setitem(accel.MEASURED_ERROR, "gpu", {"model": "large-v3-turbo", "pt": 0.03, "hi": 0.34, "fr": 0.08})
    assert accel.language_allowed("pt", "cpu") == (True, "")
    ok, why = accel.language_allowed("fr", "cpu")
    assert not ok and "francês" in why and "25%" in why and "placa de vídeo" in why and "8%" in why
    ok, why = accel.language_allowed("hi", "cuda")
    assert not ok and "mesmo com placa de vídeo" in why
    assert accel.language_allowed("fr", "cuda")[0]
    assert set(accel.blocked_languages("cpu")) == {"hi", "fr"}
    assert accel.language_allowed("xx", "cpu")[0], "idioma sem medição não é bloqueado"


def test_motor_recusa_idioma_fraco_e_permite_forcar(monkeypatch):
    import praxis
    monkeypatch.setattr(accel, "QUALITY_LIMIT", 0.03)
    monkeypatch.setitem(accel.MEASURED_ERROR, "cpu", {"model": "small", "hi": 0.70})
    monkeypatch.setattr(accel, "choose_asr", lambda *a, **k: ("cpu", "teste"))
    events = []
    monkeypatch.setattr(praxis, "_emit", events.append)
    monkeypatch.setattr(praxis, "prepare_clone_on_mac", lambda *a: False)
    args = praxis.build_parser().parse_args(["--voice-out", "v.onnx", "--src", "hi", "--tgt", "en"])
    assert praxis._run(args, bilateral=False) == 2
    assert events[-1]["code"] == "idioma_fraco" and events[-1]["lang"] == "hi"
    # no bilateral o destino também é falado (pela outra pessoa)
    events.clear()
    args = praxis.build_parser().parse_args(["--voice-out", "v.onnx", "--src", "en", "--tgt", "hi"])
    assert praxis._run(args, bilateral=True) == 2 and events[-1]["lang"] == "hi"
    args = praxis.build_parser().parse_args(["--voice-out", "v.onnx", "--src", "hi", "--tgt", "en",
                                             "--permitir-idioma-fraco"])
    assert args.permitir_idioma_fraco


def test_placa_mais_fraca_medida_volta_para_o_processador(hw, monkeypatch):
    """Regra: com placa de vídeo usa a placa, a não ser que ela seja mais fraca que o processador."""
    hw(intel_mac=True, wcpp="metal")
    monkeypatch.setattr(accel, "gpu_check_cached",
                        lambda b: {"usar_gpu": False, "motivo": "placa de vídeo erra mais que o processador"})
    backend, why = accel.choose_asr("auto")
    assert backend == "cpu" and "erra mais" in why
    assert accel.choose_asr("whispercpp")[0] == "whispercpp"      # pedido explícito sempre vale


@pytest.mark.parametrize("gpu, cpu, usar", [
    ((0.2, 0.0), (1.0, 0.0), True),        # mais rápida e certa
    ((2.0, 0.0), (1.0, 0.0), False),       # mais lenta
    ((0.2, 0.5), (1.0, 0.0), False),       # rápida, mas errando (o caso do Metal no Mac Intel)
    ((0.2, 0.03), (1.0, 0.02), True),      # diferença mínima de erro é tolerada
])
def test_comparacao_placa_de_video_contra_processador(monkeypatch, gpu, cpu, usar):
    monkeypatch.setattr(accel, "_time_backend", lambda b, a: gpu if b != "cpu" else cpu)
    assert _COMPARE_REAL("cuda")["usar_gpu"] is usar


def test_comparacao_e_feita_uma_vez_e_guardada(hw, monkeypatch, tmp_path):
    hw(cuda=1)
    monkeypatch.setattr(accel, "_check_file", lambda: tmp_path / "placa_de_video.json")
    calls = []
    monkeypatch.setattr(accel, "compare_gpu_cpu",
                        lambda b: calls.append(b) or {"usar_gpu": False, "motivo": "placa de vídeo mais lenta que o processador"})
    monkeypatch.setattr(accel, "gpu_check_cached", _cached_from(tmp_path))
    assert accel.resolve_asr("auto", log=lambda m: None)[0] == "cpu"
    assert accel.resolve_asr("auto", log=lambda m: None)[0] == "cpu"
    assert accel.choose_asr("auto")[0] == "cpu"
    assert calls == ["cuda"]


def _cached_from(tmp_path):
    import json

    def f(backend):
        p = tmp_path / "placa_de_video.json"
        return json.loads(p.read_text()).get(accel._hw_key(backend)) if p.exists() else None
    return f
