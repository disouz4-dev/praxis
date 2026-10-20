#!/usr/bin/env python3
"""Praxis — hardware acceleration (GPU) detection and backend selection.

Picks the fastest *correct* backend for each stage on the current machine:

  Stage   NVIDIA (Linux/Win)   Apple Silicon      AMD/Intel GPU (Linux/Win)   Fallback
  ASR     faster-whisper CUDA  mlx-whisper(Metal) whisper.cpp (Vulkan build)  faster-whisper CPU
  MT      CTranslate2 CUDA     CPU (Accelerate)   CPU                         CPU
  TTS     onnxruntime CUDA     onnxruntime CoreML onnxruntime DirectML (Win)  CPU
  Clone   PyTorch CUDA         PyTorch MPS        PyTorch MPS (AMD Mac)       CPU

Measured exclusions (see docs/QA_REPORT.md):
  * whisper.cpp Metal on Intel Macs with AMD GPUs returned wrong text ("," for a
    full sentence) and was slower than CPU → never auto-selected there.

Nothing here imports PyTorch (see OnnxSileroVAD in praxis.py for why).
Override with PRAXIS_DEVICE=cpu|cuda|mlx|whispercpp or `praxis.py --device`.
"""
from __future__ import annotations

import functools
import importlib.util
import os
import platform
import shutil
import subprocess
from dataclasses import dataclass, field

SYSTEM = platform.system()
MACHINE = platform.machine().lower()
IS_APPLE_SILICON = SYSTEM == "Darwin" and MACHINE in ("arm64", "aarch64")
IS_INTEL_MAC = SYSTEM == "Darwin" and not IS_APPLE_SILICON

ASR_BACKENDS = ("cuda", "mlx", "whispercpp", "cpu")


def _has(mod: str) -> bool:
    try:
        return importlib.util.find_spec(mod) is not None
    except (ImportError, ValueError):
        return False


@functools.lru_cache(maxsize=1)
def cuda_device_count() -> int:
    try:
        import ctranslate2
        return int(ctranslate2.get_cuda_device_count())
    except Exception:
        return 0


@functools.lru_cache(maxsize=1)
def gpu_names() -> tuple[str, ...]:
    """Best-effort human-readable GPU names (for --check / logs only)."""
    names: list[str] = []
    try:
        if SYSTEM == "Darwin":
            out = subprocess.check_output(["system_profiler", "SPDisplaysDataType"],
                                          text=True, timeout=10, stderr=subprocess.DEVNULL)
            names = [ln.split(":", 1)[1].strip() for ln in out.splitlines()
                     if "Chipset Model" in ln]
        elif SYSTEM == "Windows":
            out = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance Win32_VideoController).Name"],
                text=True, timeout=15, stderr=subprocess.DEVNULL)
            names = [ln.strip() for ln in out.splitlines() if ln.strip()]
        elif shutil.which("lspci"):
            out = subprocess.check_output(["lspci"], text=True, timeout=5,
                                          stderr=subprocess.DEVNULL)
            names = [ln.split(": ", 1)[1] for ln in out.splitlines()
                     if any(k in ln for k in ("VGA", "3D controller", "Display controller"))]
    except Exception:
        pass
    return tuple(names)


@functools.lru_cache(maxsize=1)
def onnx_providers() -> tuple[str, ...]:
    try:
        import onnxruntime
        return tuple(onnxruntime.get_available_providers())
    except Exception:
        return ()


@functools.lru_cache(maxsize=1)
def whispercpp_gpu_backend() -> str | None:
    """GPU backend compiled into the installed pywhispercpp, if any.

    The PyPI wheels are CPU (+Metal on macOS). Vulkan/CUDA/HIP need a source
    build: GGML_VULKAN=1 pip install --no-binary pywhispercpp pywhispercpp"""
    if not _has("_pywhispercpp"):
        return None
    try:
        import _pywhispercpp as pw
        info = pw.whisper_print_system_info().upper()
    except Exception:
        return None
    for key in ("CUDA", "VULKAN", "HIP", "SYCL"):
        if f"{key} = 1" in info or f"{key} : " in info:
            return key.lower()
    if "MTL" in info or "METAL" in info:
        return "metal"
    return None


@dataclass
class AccelPlan:
    asr: str                      # cuda | mlx | whispercpp | cpu
    asr_reason: str
    mt_device: str                # cuda | cpu
    tts_providers: list[str] = field(default_factory=list)
    clone_device: str = "cpu"     # cuda | mps | cpu
    gpus: tuple[str, ...] = ()

    def summary(self) -> str:
        return (f"ASR={self.asr} ({self.asr_reason}) · MT={self.mt_device} · "
                f"TTS={self.tts_providers[0] if self.tts_providers else 'CPU'} · "
                f"clone={self.clone_device}")


def choose_asr(requested: str = "auto") -> tuple[str, str]:
    """→ (backend, reason). Never auto-selects a backend known to be wrong/slow."""
    req = (requested or "auto").lower()
    if req != "auto":
        if req not in ASR_BACKENDS:
            raise ValueError(f"unknown ASR device {requested!r}; choose from {ASR_BACKENDS}")
        return req, "requested"
    if cuda_device_count() > 0:
        return "cuda", f"{cuda_device_count()} CUDA device(s)"
    if IS_APPLE_SILICON and _has("mlx_whisper"):
        return "mlx", "Apple Silicon GPU (MLX)"
    wb = whispercpp_gpu_backend()
    if wb in ("vulkan", "cuda", "hip", "sycl"):
        return "whispercpp", f"whisper.cpp {wb}"
    if wb == "metal" and IS_APPLE_SILICON:
        return "whispercpp", "whisper.cpp Metal"
    if IS_APPLE_SILICON:
        return "cpu", "Apple Silicon CPU (install mlx-whisper for GPU)"
    if IS_INTEL_MAC:
        return "cpu", "Intel Mac — Metal whisper.cpp measured wrong/slower; CPU is best"
    return "cpu", "no supported GPU"


def choose_tts_providers() -> list[str]:
    avail = onnx_providers()
    order = ["CUDAExecutionProvider", "DmlExecutionProvider"]
    if IS_APPLE_SILICON:   # CoreML on Intel Macs is CPU-bound and slower for Piper
        order.append("CoreMLExecutionProvider")
    chosen = [p for p in order if p in avail]
    return chosen + ["CPUExecutionProvider"] if chosen else []


def choose_clone_device() -> str:
    """Device for OmniVoice (PyTorch). Probed lazily: only called when the user
    actually uses a cloned voice (which loads torch anyway)."""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        mps = getattr(torch.backends, "mps", None)
        if mps is not None and mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"


def plan(requested_asr: str | None = None) -> AccelPlan:
    req = requested_asr or os.environ.get("PRAXIS_DEVICE", "auto")
    asr, why = choose_asr(req)
    return AccelPlan(asr=asr, asr_reason=why,
                     mt_device="cuda" if cuda_device_count() > 0 else "cpu",
                     tts_providers=choose_tts_providers(),
                     # predicted; resolved by choose_clone_device() when torch loads
                     clone_device="cuda" if cuda_device_count() > 0 else
                     ("mps" if SYSTEM == "Darwin" else "cpu"),
                     gpus=gpu_names())


# ── ASR adapters: same .transcribe() contract as faster_whisper.WhisperModel ──

class _Seg:
    __slots__ = ("text", "no_speech_prob")

    def __init__(self, text: str, no_speech_prob: float = 0.0) -> None:
        self.text = text
        self.no_speech_prob = no_speech_prob


MLX_REPOS = {"tiny": "mlx-community/whisper-tiny-mlx", "base": "mlx-community/whisper-base-mlx",
             "small": "mlx-community/whisper-small-mlx",
             "medium": "mlx-community/whisper-medium-mlx",
             "large-v2": "mlx-community/whisper-large-v2-mlx"}


class MLXWhisper:
    """mlx-whisper (Apple Silicon GPU) behind the faster-whisper interface."""
    backend = "mlx"

    def __init__(self, model_name: str) -> None:
        import mlx_whisper
        self._mlx = mlx_whisper
        self.repo = MLX_REPOS.get(model_name, model_name)

    def transcribe(self, audio, language=None, **opts):
        r = self._mlx.transcribe(
            audio, path_or_hf_repo=self.repo, language=language,
            temperature=opts.get("temperature", 0),
            condition_on_previous_text=opts.get("condition_on_previous_text", False),
            no_speech_threshold=opts.get("no_speech_threshold", 0.5),
            logprob_threshold=opts.get("log_prob_threshold", -1.0),
            compression_ratio_threshold=opts.get("compression_ratio_threshold", 2.4),
            verbose=None)
        segs = [_Seg(s.get("text", ""), float(s.get("no_speech_prob", 0.0)))
                for s in r.get("segments", [])]
        return iter(segs), {"language": r.get("language", language)}


class WhisperCpp:
    """whisper.cpp (pywhispercpp) — GPU via whichever backend it was built with."""
    backend = "whispercpp"

    def __init__(self, model_name: str, use_gpu: bool = True) -> None:
        from pywhispercpp.model import Model
        self.model = Model(model_name, redirect_whispercpp_logs_to=None,
                           context_params={"use_gpu": use_gpu},
                           print_progress=False, print_realtime=False,
                           no_context=True, single_segment=False)

    def transcribe(self, audio, language=None, **opts):
        segs = self.model.transcribe(audio, language=language or "auto",
                                     temperature=float(opts.get("temperature", 0) or 0))
        return iter([_Seg(s.text, 0.0) for s in segs]), {"language": language}


def load_asr(model_name: str, backend: str, log=print):
    """Instantiates the ASR backend; on any failure falls back to faster-whisper CPU."""
    from faster_whisper import WhisperModel
    if backend == "mlx":
        try:
            return MLXWhisper(model_name)
        except Exception as e:
            log(f"mlx-whisper unavailable ({e}); falling back to CPU")
    elif backend == "whispercpp":
        try:
            return WhisperCpp(model_name)
        except Exception as e:
            log(f"whisper.cpp unavailable ({e}); falling back to CPU")
    elif backend == "cuda":
        try:
            m = WhisperModel(model_name, device="cuda", compute_type="int8_float16")
            import numpy as np
            list(m.transcribe(np.zeros(1600, dtype=np.float32), language="en")[0])
            m.backend = "cuda"
            return m
        except Exception as e:
            log(f"CUDA Whisper failed ({type(e).__name__}: {e}); falling back to CPU")
    m = WhisperModel(model_name, device="cpu", compute_type="int8")
    m.backend = "cpu"
    return m


def load_piper_accelerated(path: str, providers: list[str] | None = None):
    """PiperVoice on the best ONNX Runtime provider (CUDA / DirectML / CoreML)."""
    from piper import PiperVoice
    providers = choose_tts_providers() if providers is None else providers
    if "CUDAExecutionProvider" in providers:
        try:
            return PiperVoice.load(path, use_cuda=True)
        except Exception:
            pass
    voice = PiperVoice.load(path)
    if providers and providers[0] != "CPUExecutionProvider":
        try:
            import onnxruntime
            voice.session = onnxruntime.InferenceSession(str(path), providers=providers)
        except Exception:
            pass   # keep the CPU session
    return voice
