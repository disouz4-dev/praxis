#!/usr/bin/env python3
"""Praxis — detecção de aceleração por hardware (placa de vídeo) e escolha do backend.

Escolhe, para cada etapa, o backend (motor de execução) mais rápido que ainda
dá resultado *correto* nesta máquina:

  Etapa   NVIDIA (Linux/Win)   Apple Silicon      GPU AMD/Intel (Linux/Win)   Alternativa
  ASR     faster-whisper CUDA  mlx-whisper(Metal) whisper.cpp (Vulkan build)  faster-whisper CPU
  MT      CTranslate2 CUDA     CPU (Accelerate)   CPU                         CPU
  TTS     onnxruntime CUDA     onnxruntime CoreML onnxruntime DirectML (Win)  CPU
  Clonar  PyTorch CUDA         PyTorch MPS        PyTorch MPS (AMD Mac)       CPU

(ASR = reconhecimento de fala; MT = tradução automática; TTS = síntese de voz.)

Exclusões medidas (veja docs/QA_REPORT.md):
  * whisper.cpp com Metal em Macs Intel com placa AMD devolveu texto errado
    ("," no lugar de uma frase inteira) e foi mais lento que a CPU → nunca é
    escolhido automaticamente nessas máquinas.

Nada aqui importa o PyTorch (o motivo está em OnnxSileroVAD, no praxis.py).
Para forçar, use PRAXIS_DEVICE=cpu|cuda|mlx|whispercpp ou `praxis.py --device`.
"""
from __future__ import annotations

import functools
import json
import importlib.util
import os
import platform
import shutil
import subprocess
from pathlib import Path
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
def ensure_cuda_libs() -> list[str]:
    """Deixa o cuBLAS/cuDNN instalados pelo PyPI (nvidia-cublas-cu12,
    nvidia-cudnn-cu12 — os que os instaladores usam) acessíveis ao CTranslate2
    sem precisar de LD_LIBRARY_PATH: no Linux carrega as bibliotecas antes, de
    forma global; no Windows registra as pastas das DLLs. Devolve as
    bibliotecas/pastas registradas."""
    import glob
    import site
    import sys
    roots = [*site.getsitepackages(), site.getusersitepackages(), *sys.path]
    done: list[str] = []
    for root in dict.fromkeys(roots):
        base = os.path.join(root, "nvidia")
        if not os.path.isdir(base):
            continue
        if SYSTEM == "Windows":
            for d in glob.glob(os.path.join(base, "*", "bin")):
                try:
                    os.add_dll_directory(d)
                    os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
                    done.append(d)
                except OSError:
                    pass
        elif SYSTEM == "Linux":
            import ctypes
            # a ordem importa: cuBLASLt antes do cuBLAS, núcleo do cuDNN antes das sub-bibliotecas
            for pat in ("cublas/lib/libcublasLt.so*", "cublas/lib/libcublas.so*",
                        "cudnn/lib/libcudnn.so*", "cudnn/lib/libcudnn_*.so*"):
                for lib in sorted(glob.glob(os.path.join(base, pat))):
                    try:
                        ctypes.CDLL(lib, mode=ctypes.RTLD_GLOBAL)
                        done.append(lib)
                    except OSError:
                        pass
    return done


@functools.lru_cache(maxsize=1)
def cuda_device_count() -> int:
    try:
        import ctranslate2
        return int(ctranslate2.get_cuda_device_count())
    except Exception:
        return 0


@functools.lru_cache(maxsize=1)
def gpu_names() -> tuple[str, ...]:
    """Nomes legíveis das placas de vídeo, quando possível (só para --check / logs)."""
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
    """Backend de placa de vídeo compilado no pywhispercpp instalado, se houver.

    Os pacotes prontos do PyPI usam só CPU (+Metal no macOS). Vulkan/CUDA/HIP
    exigem compilar a partir do código-fonte:
    GGML_VULKAN=1 pip install --no-binary pywhispercpp pywhispercpp"""
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
    """→ (backend, motivo). Nunca escolhe sozinho um backend que se sabe errado/lento."""
    req = (requested or "auto").lower()
    if req != "auto":
        if req not in ASR_BACKENDS:
            raise ValueError(f"dispositivo de ASR desconhecido {requested!r}; escolha entre {ASR_BACKENDS}")
        return req, "pedido pelo usuário"
    gpu = _gpu_candidate()
    if gpu is None:
        if IS_APPLE_SILICON:
            return "cpu", "CPU do Apple Silicon (instale o mlx-whisper para usar a placa de vídeo)"
        return "cpu", "nenhuma placa de vídeo compatível"
    # Regra: com placa de vídeo, usa a placa — a não ser que ela tenha se mostrado mais
    # fraca que o processador nesta máquina (comparação guardada; ver resolve_asr)
    checked = gpu_check_cached(gpu[0])
    if checked is not None and not checked.get("usar_gpu", True):
        return "cpu", f"medido nesta máquina: {checked.get('motivo', 'placa de vídeo mais fraca')}"
    return gpu


def _gpu_candidate() -> tuple[str, str] | None:
    if cuda_device_count() > 0:
        return "cuda", f"{cuda_device_count()} dispositivo(s) CUDA"
    if IS_APPLE_SILICON and _has("mlx_whisper"):
        return "mlx", "placa de vídeo do Apple Silicon (MLX)"
    wb = whispercpp_gpu_backend()
    if wb in ("vulkan", "cuda", "hip", "sycl", "metal"):
        return "whispercpp", f"whisper.cpp {wb}"
    return None


def resolve_asr(requested: str = "auto", log=print) -> tuple[str, str]:
    """Como choose_asr, mas na primeira vez com uma placa de vídeo mede se ela não é
    mais fraca que o processador (e guarda o resultado)."""
    backend, why = choose_asr(requested)
    if (requested or "auto").lower() == "auto" and backend != "cpu":
        res = ensure_gpu_check(backend, log=log)
        if not res.get("usar_gpu", True):
            return "cpu", f"medido nesta máquina: {res.get('motivo')}"
    return backend, why


# ── Placa de vídeo × processador: a placa só é usada se não for mais fraca ──
# Na primeira execução com uma placa de vídeo, a mesma frase curta (texto conhecido)
# é transcrita nos dois, com o mesmo modelo; a placa só é usada se for mais rápida E
# não errar mais. O resultado fica guardado (uma vez por máquina e placa).
CALIBRATION_WAV = Path(__file__).resolve().parent / "assets" / "calibracao_fala.wav"
CALIBRATION_REF = ("i must come another day and see your husband i want to have a "
                   "consultation with him about horses")      # LibriSpeech test-clean, CC BY 4.0
CHECK_MODEL = "base"


def _check_file() -> Path:
    import praxis_platform as plat
    return plat.config_dir() / "placa_de_video.json"


def _letters(t: str) -> str:
    return "".join(c for c in t.lower() if c.isalnum())


def _letter_error(ref: str, hyp: str) -> float:
    a, b = _letters(ref), _letters(hyp)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1] / max(len(a), 1)


def _time_backend(backend: str, audio) -> tuple[float, float]:
    """(segundos por transcrição, erro por letra) da frase de calibração."""
    import time
    m = load_asr(CHECK_MODEL, backend, log=lambda *_: None)
    if getattr(m, "backend", "cpu") != backend:
        raise RuntimeError(f"{backend} indisponível")
    seg, _ = m.transcribe(audio, language="en", beam_size=1, without_timestamps=True)
    " ".join(s.text for s in seg)                            # aquecimento
    t0 = time.perf_counter()
    seg, _ = m.transcribe(audio, language="en", beam_size=1, without_timestamps=True)
    text = " ".join(s.text for s in seg)
    return time.perf_counter() - t0, _letter_error(CALIBRATION_REF, text)


def compare_gpu_cpu(backend: str) -> dict:
    """Mede a placa de vídeo (`backend`) contra o processador na frase de calibração."""
    import soundfile as sf
    audio, _ = sf.read(str(CALIBRATION_WAV), dtype="float32")
    res = {"backend": backend}
    try:
        res["gpu_s"], res["gpu_err"] = _time_backend(backend, audio)
    except Exception as e:
        res.update(usar_gpu=False, motivo=f"a placa de vídeo falhou ({type(e).__name__})")
        return res
    res["cpu_s"], res["cpu_err"] = _time_backend("cpu", audio)
    faster = res["gpu_s"] < res["cpu_s"]
    as_good = res["gpu_err"] <= res["cpu_err"] + 0.02
    res["usar_gpu"] = bool(faster and as_good)
    res["motivo"] = ("placa de vídeo mais rápida e tão precisa quanto o processador" if res["usar_gpu"] else
                     "placa de vídeo mais lenta e errando mais que o processador" if not (faster or as_good) else
                     "placa de vídeo mais lenta que o processador" if not faster else
                     "placa de vídeo erra mais que o processador")
    return res


def _hw_key(backend: str) -> str:
    return f"{backend}|{SYSTEM}|{platform.machine()}|{platform.processor()}"


def gpu_check_cached(backend: str) -> dict | None:
    try:
        return json.loads(_check_file().read_text(encoding="utf-8")).get(_hw_key(backend))
    except Exception:
        return None


def ensure_gpu_check(backend: str, log=print) -> dict:
    """Resultado guardado da comparação; mede na primeira vez."""
    cached = gpu_check_cached(backend)
    if cached is not None:
        return cached
    log("Comparando placa de vídeo e processador (só na primeira vez)…")
    res = compare_gpu_cpu(backend)
    try:
        f = _check_file()
        data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        data[_hw_key(backend)] = res
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass
    return res


def choose_tts_providers() -> list[str]:
    avail = onnx_providers()
    order = ["CUDAExecutionProvider", "DmlExecutionProvider"]
    if IS_APPLE_SILICON:   # em Macs Intel o CoreML depende da CPU e fica mais lento para o Piper
        order.append("CoreMLExecutionProvider")
    chosen = [p for p in order if p in avail]
    return chosen + ["CPUExecutionProvider"] if chosen else []


def choose_clone_device() -> str:
    """Dispositivo para o OmniVoice (PyTorch). Só é verificado quando necessário:
    é chamado apenas quando o usuário usa de fato uma voz clonada (que carrega
    o torch de qualquer jeito)."""
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
                     # previsão; o valor real vem de choose_clone_device() quando o torch carrega
                     clone_device="cuda" if cuda_device_count() > 0 else
                     ("mps" if SYSTEM == "Darwin" else "cpu"),
                     gpus=gpu_names())


# ── Escolha automática do modelo (teste com fala real ao vivo na máquina lab2) ──
# Taxa de erro da transcrição ao vivo (palavras; caracteres para zh/ja), com
# ~1 min de fala real contínua por idioma, enviada em tempo real. Fonte:
# benchmarks/results/stream-cuda-large-v3-turbo.json / stream-cpu-small.json.
# Erro REAL da transcrição no modo ao vivo (palavras; letras em zh/ja), medido com 40
# frases de vários falantes por idioma (Google FLEURS) e auditado: diferença de escrita,
# número escrito de outro jeito e nome próprio estrangeiro não contam (benchmarks/auditar_erros.py).
# gpu: large-v3-turbo com trecho de até 15 s · cpu: small com trecho de até 6 s.
MEASURED_ERROR = {
    "gpu": {"model": "large-v3-turbo",
            "pt": 0.022, "en": 0.032, "es": 0.016, "fr": 0.064, "de": 0.020, "it": 0.017, "ru": 0.038, "zh": 0.113, "nl": 0.054, "pl": 0.055, "uk": 0.047, "tr": 0.058, "ar": 0.092, "hi": 0.304, "ja": 0.055, "ko": 0.151},
    "cpu": {"model": "small",
            "pt": 0.078, "en": 0.075, "es": 0.060, "fr": 0.159, "de": 0.091, "it": 0.086, "ru": 0.106, "zh": 0.173, "nl": 0.227, "pl": 0.192, "uk": 0.211, "tr": 0.166, "ar": 0.293, "hi": 0.745, "ja": 0.168, "ko": 0.252},
}
POOR_QUALITY = 0.20      # acima desta proporção de erros o usuário recebe um aviso
# Limite de qualidade: um idioma que erra mais que isto neste hardware NÃO é oferecido
# Meta do produto: 1% de erro; teto de 3% (decisão do Diego, 2026-10-20).
QUALITY_LIMIT = float(os.environ.get("PRAXIS_LIMITE_ERRO", "0.03"))
LANG_NAMES_PT = {"pt": "português", "en": "inglês", "es": "espanhol", "fr": "francês",
                 "de": "alemão", "it": "italiano", "ru": "russo", "zh": "chinês",
                 "nl": "holandês", "pl": "polonês", "uk": "ucraniano", "tr": "turco",
                 "ar": "árabe", "hi": "hindi", "ja": "japonês", "ko": "coreano"}


def hardware_kind(asr_backend: str) -> str:
    return "cpu" if asr_backend == "cpu" else "gpu"


def language_allowed(lang: str, asr_backend: str) -> tuple[bool, str]:
    """→ (liberado, explicação em linguagem simples). Um idioma é bloqueado neste
    hardware quando o erro medido da transcrição passa de QUALITY_LIMIT."""
    kind = hardware_kind(asr_backend)
    err = MEASURED_ERROR[kind].get(lang)
    if err is None or err <= QUALITY_LIMIT:
        return True, ""
    name = LANG_NAMES_PT.get(lang, lang)
    msg = (f"O reconhecimento de {name} erra cerca de {err:.0%} das palavras "
           f"{'neste computador sem placa de vídeo' if kind == 'cpu' else 'mesmo com placa de vídeo'} "
           f"— acima do limite de qualidade do Praxis ({QUALITY_LIMIT:.0%}).")
    gpu_err = MEASURED_ERROR["gpu"].get(lang)
    if kind == "cpu" and gpu_err is not None and gpu_err <= QUALITY_LIMIT:
        msg += f" Com uma placa de vídeo o erro cai para cerca de {gpu_err:.0%} e o idioma fica disponível."
    return False, msg


def blocked_languages(asr_backend: str) -> dict[str, str]:
    """{idioma: explicação} dos idiomas indisponíveis neste hardware."""
    out = {}
    for lang in MEASURED_ERROR[hardware_kind(asr_backend)]:
        if lang == "model":
            continue
        ok, why = language_allowed(lang, asr_backend)
        if not ok:
            out[lang] = why
    return out


def recommend_model(src_lang: str, asr_backend: str) -> tuple[str, str]:
    """→ (modelo Whisper, aviso em linguagem simples) para este hardware e idioma.

    Placa de vídeo: large-v3-turbo — o mais preciso, e acompanha fala contínua
    nos 16 idiomas. CPU: small — o modelo mais preciso que ainda acompanha
    (medium/large-v3-turbo ficam 4–26 s atrasados numa CPU)."""
    kind = "cpu" if asr_backend == "cpu" else "gpu"
    table = MEASURED_ERROR[kind]
    model = table["model"]
    err = table.get(src_lang)
    note = ""
    if err is not None and err > POOR_QUALITY:
        if kind == "cpu" and MEASURED_ERROR["gpu"].get(src_lang, 1) <= POOR_QUALITY:
            note = (f"transcrição de '{src_lang}' neste computador sem placa de vídeo erra ~{err:.0%} "
                    f"das palavras; com placa de vídeo cai para ~{MEASURED_ERROR['gpu'][src_lang]:.0%}")
        else:
            note = f"transcrição de '{src_lang}' ainda erra ~{err:.0%} das palavras neste hardware"
    return model, note


# ── Adaptadores de ASR: mesmo .transcribe() do faster_whisper.WhisperModel ──

class _Seg:
    __slots__ = ("text", "no_speech_prob", "avg_logprob")

    def __init__(self, text: str, no_speech_prob: float = 0.0, avg_logprob: float = 0.0) -> None:
        self.text = text
        self.no_speech_prob = no_speech_prob
        self.avg_logprob = avg_logprob


MLX_REPOS = {"tiny": "mlx-community/whisper-tiny-mlx", "base": "mlx-community/whisper-base-mlx",
             "small": "mlx-community/whisper-small-mlx",
             "medium": "mlx-community/whisper-medium-mlx",
             "large-v2": "mlx-community/whisper-large-v2-mlx",
             "large-v3": "mlx-community/whisper-large-v3-mlx",
             "large-v3-turbo": "mlx-community/whisper-large-v3-turbo"}


class MLXWhisper:
    """mlx-whisper (placa de vídeo do Apple Silicon) com a mesma interface do faster-whisper."""
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
            initial_prompt=opts.get("initial_prompt"),
            verbose=None)
        segs = [_Seg(s.get("text", ""), float(s.get("no_speech_prob", 0.0)),
                     float(s.get("avg_logprob", 0.0)))
                for s in r.get("segments", [])]
        return iter(segs), {"language": r.get("language", language)}


class WhisperCpp:
    """whisper.cpp (pywhispercpp) — usa a placa de vídeo pelo backend com que foi compilado."""
    backend = "whispercpp"

    def __init__(self, model_name: str, use_gpu: bool = True) -> None:
        from pywhispercpp.model import Model
        self.model = Model(model_name, redirect_whispercpp_logs_to=None,
                           context_params={"use_gpu": use_gpu},
                           print_progress=False, print_realtime=False,
                           no_context=True, single_segment=False)

    def transcribe(self, audio, language=None, **opts):
        extra = {"initial_prompt": opts["initial_prompt"]} if opts.get("initial_prompt") else {}
        segs = self.model.transcribe(audio, language=language or "auto",
                                     temperature=float(opts.get("temperature", 0) or 0), **extra)
        return iter([_Seg(s.text, 0.0) for s in segs]), {"language": language}


def load_asr(model_name: str, backend: str, log=print):
    """Cria o backend de ASR; se algo falhar, volta para o faster-whisper na CPU."""
    from faster_whisper import WhisperModel
    if backend == "mlx":
        try:
            return MLXWhisper(model_name)
        except Exception as e:
            log(f"mlx-whisper indisponível ({e}); usando a CPU")
    elif backend == "whispercpp":
        try:
            return WhisperCpp(model_name)
        except Exception as e:
            log(f"whisper.cpp indisponível ({e}); usando a CPU")
    elif backend == "cuda":
        try:
            ensure_cuda_libs()
            m = WhisperModel(model_name, device="cuda", compute_type="int8_float16")
            import numpy as np
            list(m.transcribe(np.zeros(1600, dtype=np.float32), language="en")[0])
            m.backend = "cuda"
            return m
        except Exception as e:
            log(f"Whisper com CUDA falhou ({type(e).__name__}: {e}); usando a CPU")
    # Com OMP_NUM_THREADS=1 (modo de compatibilidade da clonagem no Mac) o Whisper
    # ficaria 2× mais lento; o número de threads explícito devolve a velocidade.
    threads = max(1, (os.cpu_count() or 2) // 2) if os.environ.get("OMP_NUM_THREADS") == "1" else 0
    m = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=threads)
    m.backend = "cpu"
    return m


# Calibração da velocidade de fala: algumas vozes do Piper são muito lentas
# (medido: alemão "MLS" 10,8 letras/s contra "Thorsten" 19,9), o que faz a fala
# traduzida durar mais que a original e o motor ficar para trás. Vozes mais
# lentas que a meta ganham uma velocidade padrão maior, nunca além de
# MIN_RATE_SCALE (continua soando natural).
CALIBRATION_TEXT = {
    "pt": "O tempo passa depressa quando conversamos com amigos sobre a vida.",
    "en": "Time goes by quickly when we talk with friends about our lives.",
    "es": "El tiempo pasa rápido cuando hablamos con amigos sobre la vida.",
    "fr": "Le temps passe vite quand on parle avec des amis de la vie.",
    "de": "Die Zeit vergeht schnell, wenn wir mit Freunden über das Leben reden.",
    "it": "Il tempo passa in fretta quando parliamo con gli amici della vita.",
    "nl": "De tijd gaat snel als we met vrienden over het leven praten.",
    "pl": "Czas płynie szybko, gdy rozmawiamy z przyjaciółmi o życiu.",
    "ru": "Время летит быстро, когда мы говорим с друзьями о жизни.",
    "uk": "Час минає швидко, коли ми говоримо з друзями про життя.",
    "tr": "Arkadaşlarla hayat hakkında konuşurken zaman çabuk geçer.",
}
TARGET_LETTERS_PER_S = 15.0
MIN_RATE_SCALE = 0.72


def voice_rate_scale(voice, lang: str) -> float:
    """length_scale que leva uma voz lenta até TARGET_LETTERS_PER_S (1.0 = sem mudança)."""
    text = CALIBRATION_TEXT.get(lang)
    if not text:
        return 1.0                     # escritas sem uma meta comparável de letras/s
    try:
        pcm = b"".join(c.audio_int16_bytes for c in voice.synthesize(text))
        seconds = len(pcm) / 2 / voice.config.sample_rate
    except Exception:
        return 1.0
    letters = sum(ch.isalpha() for ch in text)
    rate = letters / seconds if seconds else TARGET_LETTERS_PER_S
    if rate >= TARGET_LETTERS_PER_S:
        return 1.0
    return max(MIN_RATE_SCALE, round(rate / TARGET_LETTERS_PER_S, 2))


def _voice_lang(path: str) -> str:
    return os.path.basename(str(path)).split("-")[0].split("_")[0].lower()


def load_piper_accelerated(path: str, providers: list[str] | None = None):
    """PiperVoice no melhor provedor do ONNX Runtime (CUDA / DirectML / CoreML),
    com a velocidade de fala calibrada (veja voice_rate_scale)."""
    voice = _load_piper_provider(path, providers)
    voice.praxis_rate_scale = voice_rate_scale(voice, _voice_lang(path))
    return voice


def _load_piper_provider(path: str, providers: list[str] | None = None):
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
            pass   # mantém a sessão na CPU
    return voice
