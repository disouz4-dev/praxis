#!/usr/bin/env python3
"""Praxis — camada que isola as diferenças entre sistemas operacionais.

Tudo o que muda entre Linux, macOS e Windows fica aqui, para que o motor
(praxis.py) e a interface (praxis_config.py) não precisem saber em qual
sistema estão rodando:

  * pastas de configuração / dados / arquivos temporários de cada usuário
  * o interpretador Python do ambiente virtual (venv) instalado
  * listagem, captura e reprodução dos dispositivos de áudio
  * o "microfone virtual" que o app de chamada escuta

Há dois "backends" (implementações) de áudio:

  PulseBackend        Linux com PulseAudio/PipeWire (pactl/parec/pacat).
                      Cria dispositivos virtuais de verdade na hora (uma saída
                      "muda" + uma entrada remapeada) — sem instalar driver.
  SoundDeviceBackend  macOS, Windows e Linux sem pactl. Usa o PortAudio
                      através do `sounddevice`. O microfone virtual é um
                      driver de loopback (cabo de áudio virtual) já instalado:
                        macOS   → BlackHole  (brew install blackhole-2ch)
                        Windows → VB-Audio Virtual Cable
                      O Praxis toca no lado de *saída* do driver e o app de
                      chamada escolhe o lado de *entrada* como microfone.

Os ids de dispositivo são textos simples nos dois backends. O sufixo
":left" / ":right" escolhe um canal de uma entrada estéreo (usado em
interfaces de áudio em que cada canal é um microfone separado).
"""

from __future__ import annotations

import os
import platform
import queue
import shutil
import subprocess
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

SYSTEM  = platform.system()          # "Linux" | "Darwin" | "Windows"
IS_LINUX = SYSTEM == "Linux"
IS_MAC   = SYSTEM == "Darwin"
IS_WIN   = SYSTEM == "Windows"

APP = "praxis"


# ── Caminhos ──────────────────────────────────────────────────────────────────

def config_dir() -> Path:
    """Pasta de configuração do usuário (onde fica o config.json)."""
    if IS_WIN:
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "Praxis"
    if IS_MAC:
        return Path.home() / "Library" / "Application Support" / "Praxis"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / APP


def data_dir() -> Path:
    """Pasta de instalação/dados do usuário (venv e cópia instalada do app)."""
    if IS_WIN:
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "Praxis"
    if IS_MAC:
        return Path.home() / "Library" / "Application Support" / "Praxis"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / APP


def venv_python(venv: Path) -> Path:
    """Caminho do interpretador dentro de um venv, conforme o sistema atual."""
    if IS_WIN:
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python3"


def installed_python() -> Path | None:
    """Interpretador do venv criado pelo instalador, se existir."""
    p = venv_python(data_dir() / "venv")
    return p if p.exists() else None


_TMP_LOCK = threading.Lock()


def temp_dir() -> Path:
    """Pasta temporária privada do usuário (evita caminhos previsíveis e
    compartilhados em /tmp)."""
    with _TMP_LOCK:
        uid = os.getuid() if hasattr(os, "getuid") else os.environ.get("USERNAME", "user")
        d = Path(tempfile.gettempdir()) / f"praxis-{uid}"
        d.mkdir(mode=0o700, exist_ok=True)
        return d


def temp_path(name: str) -> str:
    """Arquivo de nome fixo na pasta temporária privada (ex.: 'ov_ref.wav')."""
    return str(temp_dir() / name)


def new_temp_file(suffix: str = "") -> str:
    """Caminho de arquivo temporário único (já fechado, para poder ser reaberto
    no Windows)."""
    fd, path = tempfile.mkstemp(suffix=suffix, dir=temp_dir())
    os.close(fd)
    return path


def log_path() -> str:
    return temp_path("praxis_engine.log")


def ffmpeg_exe() -> str | None:
    """ffmpeg do PATH; se não houver, o binário que vem com o imageio-ffmpeg
    (se estiver instalado)."""
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg  # type: ignore
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def cuda_env(env: dict[str, str]) -> dict[str, str]:
    """Acrescenta pastas conhecidas de bibliotecas CUDA (placa de vídeo NVIDIA)
    ao caminho de busca de bibliotecas do sistema.

    Para trocar/ampliar, use PRAXIS_CUDA_LIB (pastas separadas por os.pathsep)."""
    env = dict(env)
    extra = [p for p in os.environ.get("PRAXIS_CUDA_LIB", "").split(os.pathsep) if p]
    if IS_LINUX:
        extra.append("/usr/local/lib/ollama/cuda_v12")
    # cuBLAS/cuDNN instalados pelo PyPI (nvidia-cublas-cu12, nvidia-cudnn-cu12)
    import site
    import sys
    for sp in [*site.getsitepackages(), site.getusersitepackages(), *sys.path]:
        for lib in ("cublas", "cudnn"):
            d = Path(sp) / "nvidia" / lib / ("bin" if IS_WIN else "lib")
            if d.is_dir() and str(d) not in extra:
                extra.append(str(d))
    extra = [p for p in extra if Path(p).is_dir()]
    if not extra:
        return env
    var = "PATH" if IS_WIN else "LD_LIBRARY_PATH"
    cur = env.get(var, "")
    env[var] = os.pathsep.join(extra + ([cur] if cur else []))
    return env


def primary_monitor_geometry() -> tuple[int, int, int, int]:
    """(x, y, w, h) do monitor principal, ou zeros se não der para saber.

    Usa o xrandr no Linux com X11 (entende vários monitores); nos outros
    casos quem chama usa o winfo_screenwidth/height do Tk."""
    if not IS_LINUX or not shutil.which("xrandr"):
        return 0, 0, 0, 0
    try:
        out = subprocess.check_output(["xrandr"], text=True, stderr=subprocess.DEVNULL, timeout=3)
    except Exception:
        return 0, 0, 0, 0
    return parse_xrandr(out)


def _contains(rect: tuple[int, int, int, int], px: int, py: int) -> bool:
    x, y, w, h = rect
    return x <= px < x + w and y <= py < y + h


def work_area(tk_root=None, point: tuple[int, int] | None = None) -> tuple[int, int, int, int]:
    """(x, y, w, h) da área útil da tela (o espaço livre para janelas) no
    monitor que contém `point` (padrão: o monitor principal), em coordenadas
    do Tk a partir do canto superior esquerdo — sem contar a barra de menus/
    Dock do macOS, a barra de tarefas do Windows e os painéis do Linux.

    Se não conseguir, usa o wm_maxsize() do Tk (que já desconta as barras do
    sistema no macOS e no Windows) e, por último, zeros (quem chama usa a
    tela inteira)."""
    try:
        if IS_MAC:
            from AppKit import NSScreen  # pyobjc
            screens = list(NSScreen.screens())
            main_h = screens[0].frame().size.height        # no Cocoa, y=0 é a base da tela 0
            areas = []
            for scr in screens:
                f, v = scr.frame(), scr.visibleFrame()
                full = (int(f.origin.x), int(main_h - f.origin.y - f.size.height),
                        int(f.size.width), int(f.size.height))
                vis = (int(v.origin.x), int(main_h - v.origin.y - v.size.height),
                       int(v.size.width), int(v.size.height))
                areas.append((full, vis))
            if point:
                for full, vis in areas:
                    if _contains(full, *point):
                        return vis
            return areas[0][1]
        if IS_WIN:
            import ctypes
            from ctypes import wintypes

            class MONITORINFO(ctypes.Structure):
                _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                            ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]
            px, py = point or (0, 0)
            hmon = ctypes.windll.user32.MonitorFromPoint(wintypes.POINT(px, py), 1)  # monitor mais próximo
            mi = MONITORINFO()
            mi.cbSize = ctypes.sizeof(MONITORINFO)
            if ctypes.windll.user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
                r = mi.rcWork
                return r.left, r.top, r.right - r.left, r.bottom - r.top
        if IS_LINUX:
            mon = monitor_at(point) if point else primary_monitor_geometry()
            wa = _net_workarea()
            if mon[2] and wa:
                x0, y0 = max(wa[0], mon[0]), max(wa[1], mon[1])
                x1 = min(wa[0] + wa[2], mon[0] + mon[2])
                y1 = min(wa[1] + wa[3], mon[1] + mon[3])
                if x1 > x0 and y1 > y0:
                    return x0, y0, x1 - x0, y1 - y0
            if mon[2]:
                return mon
            if wa:
                return wa
    except Exception:
        pass
    if tk_root is not None:
        try:
            if IS_LINUX:
                # Sem gerenciador de janelas (desktops mínimos, CI) o wm_maxsize()
                # não faz sentido (já visto: 560 × 1048575); a tela inteira é segura.
                return 0, 0, int(tk_root.winfo_screenwidth()), int(tk_root.winfo_screenheight())
            mw, mh = tk_root.wm_maxsize()       # já desconta Dock/barra de tarefas no macOS/Windows
            return 0, 0, int(mw), int(mh)
        except Exception:
            pass
    return 0, 0, 0, 0


def _net_workarea() -> tuple[int, int, int, int] | None:
    if not shutil.which("xprop"):
        return None
    try:
        out = subprocess.check_output(["xprop", "-root", "_NET_WORKAREA"], text=True,
                                      timeout=3, stderr=subprocess.DEVNULL)
        nums = [int(n) for n in out.split("=", 1)[1].replace(",", " ").split()[:4]]
        return tuple(nums) if len(nums) == 4 and nums[2] > 0 else None  # type: ignore[return-value]
    except Exception:
        return None


def monitor_at(point: tuple[int, int]) -> tuple[int, int, int, int]:
    """Linux/X11: posição e tamanho do monitor que contém `point` (xrandr)."""
    if not shutil.which("xrandr"):
        return 0, 0, 0, 0
    try:
        out = subprocess.check_output(["xrandr"], text=True, stderr=subprocess.DEVNULL, timeout=3)
    except Exception:
        return 0, 0, 0, 0
    import re
    for line in out.splitlines():
        if " connected" in line:
            m = re.search(r"(\d+)x(\d+)\+(\d+)\+(\d+)", line)
            if m:
                w, h, x, y = map(int, m.groups())
                if _contains((x, y, w, h), *point):
                    return x, y, w, h
    return primary_monitor_geometry()


def fit_window(work: tuple[int, int, int, int], width: int, max_height: int,
               titlebar: int = 32, margin: int = 12,
               prefer: tuple[int, int] | None = None) -> tuple[int, int, int, int]:
    """(w, h, x, y) para uma janela de `width` × até `max_height` (área interna)
    de modo que ela — com a barra de título — caiba inteira dentro de `work`.
    `prefer` mantém a posição atual quando possível (ajustada para dentro de
    `work`)."""
    wx, wy, ww, wh = work
    w = min(width, max(200, ww - 2 * margin))
    h = min(max_height, max(200, wh - titlebar - 2 * margin))
    if prefer is None:
        x = wx + max(0, (ww - w) // 2)
        y = wy + max(0, (wh - h - titlebar) // 2)
    else:
        x = min(max(prefer[0], wx), wx + ww - w)
        y = min(max(prefer[1], wy), wy + wh - h - titlebar)
    return w, h, x, y


def parse_xrandr(out: str) -> tuple[int, int, int, int]:
    import re
    rx = re.compile(r"(\d+)x(\d+)\+(\d+)\+(\d+)")
    for want_primary in (True, False):
        for line in out.splitlines():
            if " connected" not in line:
                continue
            if want_primary and " connected primary" not in line:
                continue
            m = rx.search(line)
            if m:
                w, h, x, y = map(int, m.groups())
                return x, y, w, h
    return 0, 0, 0, 0


# ── Idioma do sistema ────────────────────────────────────────────────────────

def _lang_code(tag: str | None) -> str:
    """'pt-BR', 'pt_BR.UTF-8', 'zh-Hans-CN' → 'pt', 'zh'. Vazio se não for idioma."""
    if not tag:
        return ""
    code = tag.replace("-", "_").split(".")[0].split("@")[0].split("_")[0].strip().lower()
    return "" if code in ("", "c", "posix") else code


def system_language() -> str:
    """Idioma do sistema operacional, em 2 letras ('pt', 'en'…); '' se não der para saber.

    macOS: lista de idiomas preferidos do usuário (aplicativos abertos pelo Dock não
    recebem a variável LANG). Windows: idioma da interface do usuário. Linux: as
    variáveis LANGUAGE, LC_ALL, LC_MESSAGES e LANG, nessa ordem."""
    if IS_MAC:
        try:
            from Foundation import NSLocale          # pyobjc, instalado no macOS
            langs = NSLocale.preferredLanguages()
            if langs and _lang_code(str(langs[0])):
                return _lang_code(str(langs[0]))
        except Exception:
            pass
        try:
            out = subprocess.check_output(["defaults", "read", "-g", "AppleLanguages"],
                                          text=True, timeout=3, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                code = _lang_code(line.strip().strip('(),"'))
                if code:
                    return code
        except Exception:
            pass
    if IS_WIN:
        try:
            import ctypes
            import locale
            lcid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            code = _lang_code(locale.windows_locale.get(lcid, ""))
            if code:
                return code
        except Exception:
            pass
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        for part in os.environ.get(var, "").split(":"):
            code = _lang_code(part)
            if code:
                return code
    try:
        import locale
        return _lang_code(locale.getlocale()[0])
    except Exception:
        return ""


def default_languages(ui_supported, src_supported, fallback: str = "en") -> dict:
    """Escolhas iniciais a partir do idioma do sistema (só na primeira execução):
    interface e "você fala" no idioma do sistema (inglês se a interface não tiver
    esse idioma); "traduzir para" em inglês, ou espanhol se o sistema já for inglês."""
    lang = system_language()
    ui = lang if lang in ui_supported else fallback
    src = lang if lang in src_supported else ui
    tgt = "es" if src == "en" else "en"
    return {"ui_lang": ui, "src": src, "tgt": tgt}


# ── Funções de áudio ──────────────────────────────────────────────────────────

def split_channel(device: str | None) -> tuple[str | None, int | None]:
    """'dev:left' → ('dev', 0), 'dev:right' → ('dev', 1), 'dev' → ('dev', None)."""
    if not device:
        return None, None
    if device.endswith(":left"):
        return device[:-5], 0
    if device.endswith(":right"):
        return device[:-6], 1
    return device, None


def resample(x: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
    """Muda a taxa de amostragem por interpolação linear — suficiente para fala
    e medidores de volume."""
    if src_rate == dst_rate or len(x) == 0:
        return x
    n_out = max(1, int(round(len(x) * dst_rate / src_rate)))
    t_in  = np.arange(len(x), dtype=np.float64)
    t_out = np.linspace(0, len(x) - 1, n_out)
    y = np.interp(t_out, t_in, x.astype(np.float64))
    return y.astype(x.dtype) if np.issubdtype(x.dtype, np.floating) else \
        np.clip(np.round(y), -32768, 32767).astype(x.dtype)


@dataclass
class VirtualMic:
    """Resultado da preparação do microfone virtual de saída.

    target       id do dispositivo onde o Praxis toca a fala traduzida
    mic_label    o que o usuário deve escolher como microfone no app de chamada
    peer_capture id do dispositivo de onde vem o áudio da outra pessoa
                 (modo bilateral) ou None
    peer_label   para onde o usuário deve mandar a saída do app de chamada, ou ""
    """
    target: str | None
    mic_label: str
    peer_capture: str | None = None
    peer_label: str = ""


class CaptureStream:
    """Leitor que espera e entrega blocos mono int16 de tamanho fixo."""

    def read(self) -> bytes | None:          # pragma: no cover - interface
        raise NotImplementedError

    def close(self) -> None:                 # pragma: no cover - interface
        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


class Player:
    """Controle de uma reprodução WAV/PCM iniciada em segundo plano."""

    def __init__(self) -> None:
        self._done = threading.Event()
        self._stop_fn = lambda: None

    def stop(self) -> None:
        try:
            self._stop_fn()
        finally:
            self._done.set()

    def wait(self, timeout: float | None = None) -> bool:
        return self._done.wait(timeout)

    @property
    def done(self) -> bool:
        return self._done.is_set()


class AudioBackend:
    name = "base"
    can_create_virtual_devices = False

    # listagem ----------------------------------------------------------------
    def list_inputs(self) -> list[tuple[str, str]]:
        raise NotImplementedError

    def list_outputs(self) -> list[tuple[str, str]]:
        raise NotImplementedError

    def defaults(self) -> tuple[str, str]:
        return "", ""

    # motor -------------------------------------------------------------------
    def setup_virtual_mic(self, bilateral: bool) -> VirtualMic:
        raise NotImplementedError

    def teardown(self) -> None:
        pass

    def resolve_mic(self, mic: str | None) -> str | None:
        return mic

    def open_capture(self, device: str | None, rate: int, chunk: int) -> CaptureStream:
        raise NotImplementedError

    def play_pcm(self, pcm: bytes, rate: int, device: str | None) -> None:
        raise NotImplementedError

    def play_pcm_multi(self, pcm: bytes, rate: int, devices: Iterable[str | None]) -> None:
        targets = list(dict.fromkeys(devices))  # tira repetidos, mantém a ordem
        if len(targets) <= 1:
            self.play_pcm(pcm, rate, targets[0] if targets else None)
            return
        ts = [threading.Thread(target=self.play_pcm, args=(pcm, rate, d), daemon=True)
              for d in targets]
        for t in ts:
            t.start()
        for t in ts:
            t.join()

    # interface ---------------------------------------------------------------
    def play_file(self, path: str, device: str | None = None) -> Player:
        """Toca um arquivo WAV em segundo plano; devolve um controle que pode parar."""
        import soundfile as sf
        data, rate = sf.read(path, dtype="int16", always_2d=True)
        mono = data.mean(axis=1).astype(np.int16) if data.shape[1] > 1 else data[:, 0]
        player = Player()
        stop = threading.Event()
        player._stop_fn = stop.set

        def _run() -> None:
            try:
                step = int(rate * 0.1)
                for i in range(0, len(mono), step):
                    if stop.is_set():
                        break
                    self.play_pcm(mono[i:i + step].tobytes(), int(rate), device)
            finally:
                player._done.set()

        threading.Thread(target=_run, daemon=True).start()
        return player

    def force_rate(self, rate: int) -> None:
        """Fixa, opcionalmente, a taxa de amostragem do sistema todo (só PipeWire)."""

    def restore_rate(self) -> None:
        pass

    def setup_hint(self) -> str:
        return ""


# ── PulseAudio / PipeWire ─────────────────────────────────────────────────────

SINK_OUT  = "Praxis_Out"
SRC_MIC   = "Praxis_Mic"
SRC_DESC  = "Praxis_Microfone"
SINK_IN   = "Praxis_In"
SINK_IN_DESC = "Praxis_Entrada"


def parse_pactl_list(raw: str, exclude: Iterable[str] = ()) -> list[tuple[str, str, str]]:
    """Lê a saída de `LANG=C pactl list sources|sinks` → [(nome, descrição, mapa_de_canais)]."""
    exclude = list(exclude)
    result: list[tuple[str, str, str]] = []
    name = desc = ""
    for line in raw.splitlines():
        s = line.strip()
        if s.startswith("Name:"):
            name = s.split(":", 1)[1].strip()
            desc = ""
        elif s.startswith("Description:"):
            desc = s.split(":", 1)[1].strip()
        elif s.startswith("Channel Map:"):
            chmap = s.split(":", 1)[1].strip()
            if name and desc and not any(ex in name for ex in exclude):
                result.append((name, desc, chmap))
            name = desc = ""
    return result


def parse_pactl_info(raw: str) -> tuple[str, str]:
    src = sink = ""
    for line in raw.splitlines():
        if line.startswith("Default Source:"):
            src = line.split(":", 1)[1].strip()
        elif line.startswith("Default Sink:"):
            sink = line.split(":", 1)[1].strip()
    return src, sink


def expand_stereo_inputs(devs: list[tuple[str, str, str]]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for name, desc, chmap in devs:
        if len([c for c in chmap.split(",") if c.strip()]) == 2:
            out.append((f"{name}:left",  f"{desc}  —  Entrada 1 (esquerda)"))
            out.append((f"{name}:right", f"{desc}  —  Entrada 2 (direita)"))
        else:
            out.append((name, desc))
    return out


class _PipeCapture(CaptureStream):
    def __init__(self, cmd: list[str], chunk_bytes: int) -> None:
        self._proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self._n = chunk_bytes

    def read(self) -> bytes | None:
        assert self._proc.stdout is not None
        data = self._proc.stdout.read(self._n)
        return data or None

    def close(self) -> None:
        if self._proc.poll() is None:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.wait()


class PulseBackend(AudioBackend):
    name = "pulse"
    can_create_virtual_devices = True
    _EXCLUDE = (".monitor", "Praxis", "Atos2")

    def __init__(self) -> None:
        self._mods: list[int] = []
        self._lock = threading.Lock()

    @staticmethod
    def available() -> bool:
        return IS_LINUX and bool(shutil.which("pactl")) and bool(shutil.which("parec")) \
            and bool(shutil.which("pacat"))

    def _pactl(self, *args: str) -> str:
        r = subprocess.run(["pactl", *args], capture_output=True, text=True, check=True,
                           env={**os.environ, "LANG": "C", "LC_ALL": "C"}, timeout=10)
        return r.stdout.strip()

    def _load(self, *args: str) -> int:
        mod = int(self._pactl("load-module", *args))
        with self._lock:
            self._mods.append(mod)
        return mod

    def list_inputs(self) -> list[tuple[str, str]]:
        try:
            raw = self._pactl("list", "sources")
        except Exception:
            return []
        return expand_stereo_inputs(parse_pactl_list(raw, self._EXCLUDE))

    def list_outputs(self) -> list[tuple[str, str]]:
        try:
            raw = self._pactl("list", "sinks")
        except Exception:
            return []
        return [(n, d) for n, d, _ in parse_pactl_list(raw, ("Praxis", "Atos2"))]

    def defaults(self) -> tuple[str, str]:
        try:
            return parse_pactl_info(self._pactl("info"))
        except Exception:
            return "", ""

    def setup_virtual_mic(self, bilateral: bool) -> VirtualMic:
        self._load("module-null-sink", f"sink_name={SINK_OUT}",
                   f"sink_properties=device.description={SINK_OUT}")
        self._load("module-remap-source", f"source_name={SRC_MIC}",
                   f"master={SINK_OUT}.monitor",
                   f"source_properties=device.description={SRC_DESC}")
        vm = VirtualMic(target=SINK_OUT, mic_label=SRC_DESC)
        if bilateral:
            self._load("module-null-sink", f"sink_name={SINK_IN}",
                       f"sink_properties=device.description={SINK_IN_DESC}")
            vm.peer_capture = f"{SINK_IN}.monitor"
            vm.peer_label = SINK_IN_DESC
        return vm

    def teardown(self) -> None:
        with self._lock:
            mods, self._mods = list(reversed(self._mods)), []
        for mod in mods:
            try:
                self._pactl("unload-module", str(mod))
            except Exception:
                pass

    def resolve_mic(self, mic: str | None) -> str | None:
        """Transforma 'dev:left'/'dev:right' numa entrada mono remapeada."""
        master, ch = split_channel(mic)
        if ch is None:
            return master
        side = "left" if ch == 0 else "right"
        src_name = f"Praxis_Src_{side.capitalize()}"
        self._load("module-remap-source", f"source_name={src_name}", f"master={master}",
                   "channels=1", f"master_channel_map=front-{side}", "channel_map=mono",
                   f"source_properties=device.description=Praxis_{side.capitalize()}_Mono")
        return src_name

    def open_capture(self, device: str | None, rate: int, chunk: int) -> CaptureStream:
        master, _ch = split_channel(device)
        cmd = ["parec", "--format=s16le", f"--rate={rate}", "--channels=1",
               "--latency-msec=100"]
        if master:
            cmd.append(f"--device={master}")
        return _PipeCapture(cmd, chunk * 2)

    def play_pcm(self, pcm: bytes, rate: int, device: str | None) -> None:
        cmd = ["pacat", "--playback", "--format=s16le", f"--rate={rate}", "--channels=1"]
        if device:
            cmd.append(f"--device={device}")
        subprocess.run(cmd, input=pcm, check=False, stderr=subprocess.DEVNULL)

    def force_rate(self, rate: int) -> None:
        if shutil.which("pw-metadata"):
            try:
                subprocess.run(["pw-metadata", "-n", "settings", "0", "clock.force-rate",
                                str(rate)], capture_output=True, timeout=3)
            except Exception:
                pass

    def restore_rate(self) -> None:
        self.force_rate(0)


# ── PortAudio (sounddevice) — macOS / Windows / alternativa ─────────────────────

# Drivers de loopback (cabos de áudio virtuais), em ordem de prioridade. Cada
# item: (trecho do nome do lado de saída, onde o Praxis toca; trecho do nome do
# lado de entrada, que o app de chamada grava).
LOOPBACK_DRIVERS: list[tuple[str, str]] = [
    ("BlackHole 2ch",   "BlackHole 2ch"),
    ("BlackHole",       "BlackHole"),
    ("CABLE Input",     "CABLE Output"),
    ("VoiceMeeter Input", "VoiceMeeter Output"),
    ("Loopback Audio",  "Loopback Audio"),
    ("Soundflower (2ch)", "Soundflower (2ch)"),
]
# Segundo loopback para o modo bilateral (saída do app de chamada → Praxis).
PEER_LOOPBACK_DRIVERS: list[tuple[str, str]] = [
    ("BlackHole 16ch",  "BlackHole 16ch"),
    ("CABLE-A Input",   "CABLE-A Output"),
    ("VoiceMeeter Aux Input", "VoiceMeeter Aux Output"),
]


def _is_loopback(name: str) -> bool:
    return any(o in name or i in name
               for o, i in LOOPBACK_DRIVERS + PEER_LOOPBACK_DRIVERS)


def find_loopback(devices: list[dict], table: list[tuple[str, str]],
                  avoid: Iterable[str] = ()) -> tuple[str, str] | None:
    """Devolve (nome do dispositivo de saída, nome do dispositivo de entrada) do
    primeiro driver de loopback de `table` presente em `devices`
    (sounddevice.query_devices())."""
    avoid = set(avoid)
    outs = [d["name"] for d in devices if d.get("max_output_channels", 0) > 0]
    ins  = [d["name"] for d in devices if d.get("max_input_channels", 0) > 0]
    for out_frag, in_frag in table:
        o = next((n for n in outs if out_frag in n and n not in avoid), None)
        i = next((n for n in ins if in_frag in n and n not in avoid), None)
        if o:
            return o, (i or o)
    return None


class _SDCapture(CaptureStream):
    def __init__(self, sd, device_index: int | None, channel: int | None,
                 rate: int, chunk: int) -> None:
        self._q: "queue.Queue[np.ndarray | None]" = queue.Queue(maxsize=400)
        self._chunk = chunk
        self._rate = rate
        self._buf = np.zeros(0, dtype=np.int16)
        self._closed = False
        info = sd.query_devices(device_index if device_index is not None else sd.default.device[0],
                                "input")
        channels = 2 if (channel is not None and info["max_input_channels"] >= 2) else 1
        self._channel = channel if channels == 2 else None

        def _cb(indata, frames, time_info, status):  # roda na thread do PortAudio
            x = indata[:, self._channel] if self._channel is not None else indata[:, 0]
            x = x.copy()
            if self._dev_rate != self._rate:
                x = resample(x, self._dev_rate, self._rate)
            try:
                self._q.put_nowait(x)
            except queue.Full:
                pass

        # Prefere a taxa do motor; se falhar, usa a taxa do dispositivo e converte
        # (o modo compartilhado do WASAPI e muitos dispositivos USB recusam 16 kHz).
        last_err: Exception | None = None
        # Primeiro a taxa nativa do dispositivo (CoreAudio/WASAPI recusam muitas
        # taxas e o PortAudio enche o log de erros); a conversão para a taxa do
        # motor é feita no callback.
        for r in dict.fromkeys((int(info["default_samplerate"]), rate)):
            try:
                self._dev_rate = r
                self._stream = sd.InputStream(device=device_index, channels=channels,
                                              samplerate=r, dtype="int16",
                                              blocksize=0, callback=_cb)
                self._stream.start()
                break
            except Exception as e:  # noqa: PERF203
                last_err = e
        else:
            raise RuntimeError(f"Não foi possível abrir o dispositivo de entrada: {last_err}")

    def read(self) -> bytes | None:
        while len(self._buf) < self._chunk:
            if self._closed:
                return None
            try:
                x = self._q.get(timeout=0.5)
            except queue.Empty:
                continue
            if x is None:
                return None
            self._buf = np.concatenate([self._buf, x])
        out, self._buf = self._buf[:self._chunk], self._buf[self._chunk:]
        return out.tobytes()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._stream.stop()
            self._stream.close()
        except Exception:
            pass
        try:
            self._q.put_nowait(None)
        except queue.Full:
            pass


class SoundDeviceBackend(AudioBackend):
    name = "sounddevice"

    def __init__(self) -> None:
        import sounddevice as sd
        self.sd = sd

    def _devices(self) -> list[dict]:
        try:
            return [dict(d, index=i) for i, d in enumerate(self.sd.query_devices())]
        except Exception:
            return []

    def _hostapi_ok(self, d: dict) -> bool:
        # No Windows o mesmo dispositivo aparece uma vez para cada "host API"
        # (MME, DirectSound, WASAPI, WDM-KS — as interfaces de áudio do sistema).
        # Mantém só a padrão para não repetir dispositivos.
        if not IS_WIN:
            return True
        try:
            return d.get("hostapi") == self.sd.default.hostapi
        except Exception:
            return True

    def device_index(self, name: str | None, kind: str) -> int | None:
        if not name:
            return None
        key = "max_input_channels" if kind == "input" else "max_output_channels"
        devs = [d for d in self._devices() if d.get(key, 0) > 0]
        for pred in (lambda d: d["name"] == name, lambda d: name in d["name"]):
            for d in devs:
                if pred(d) and self._hostapi_ok(d):
                    return d["index"]
            for d in devs:
                if pred(d):
                    return d["index"]
        return None

    def list_inputs(self) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        for d in self._devices():
            if d.get("max_input_channels", 0) <= 0 or not self._hostapi_ok(d):
                continue
            if _is_loopback(d["name"]) or "Praxis" in d["name"]:
                continue
            n = d["name"]
            if d["max_input_channels"] == 2:
                out.append((f"{n}:left",  f"{n}  —  Entrada 1 (esquerda)"))
                out.append((f"{n}:right", f"{n}  —  Entrada 2 (direita)"))
            else:
                out.append((n, n))
        return out

    def list_outputs(self) -> list[tuple[str, str]]:
        return [(d["name"], d["name"]) for d in self._devices()
                if d.get("max_output_channels", 0) > 0 and self._hostapi_ok(d)
                and not _is_loopback(d["name"])]

    def defaults(self) -> tuple[str, str]:
        try:
            i, o = self.sd.default.device
            devs = self.sd.query_devices()
            return (devs[i]["name"] if i is not None and i >= 0 else "",
                    devs[o]["name"] if o is not None and o >= 0 else "")
        except Exception:
            return "", ""

    def setup_virtual_mic(self, bilateral: bool) -> VirtualMic:
        devs = self._devices()
        lb = find_loopback(devs, LOOPBACK_DRIVERS)
        if not lb:
            raise RuntimeError(
                "Nenhum cabo de áudio virtual encontrado. " + self.setup_hint())
        vm = VirtualMic(target=lb[0], mic_label=lb[1])
        if bilateral:
            peer = find_loopback(devs, PEER_LOOPBACK_DRIVERS, avoid=lb)
            if not peer:
                raise RuntimeError(
                    "O modo bilateral precisa de um segundo cabo virtual. " + self.setup_hint(bilateral=True))
            vm.peer_capture, vm.peer_label = peer[1], peer[0]
        return vm

    def open_capture(self, device: str | None, rate: int, chunk: int) -> CaptureStream:
        name, ch = split_channel(device)
        idx = self.device_index(name, "input")
        return _SDCapture(self.sd, idx, ch, rate, chunk)

    def play_pcm(self, pcm: bytes, rate: int, device: str | None) -> None:
        if not pcm:
            return
        x = np.frombuffer(pcm, dtype=np.int16)
        idx = self.device_index(device, "output") if device else None
        info = self.sd.query_devices(idx if idx is not None else self.sd.default.device[1],
                                     "output")
        channels = 2 if info["max_output_channels"] >= 2 else 1
        for r in (rate, int(info["default_samplerate"])):
            try:
                y = resample(x, rate, r)
                data = np.repeat(y[:, None], channels, axis=1) if channels == 2 else y[:, None]
                with self.sd.OutputStream(device=idx, samplerate=r, channels=channels,
                                          dtype="int16") as s:
                    s.write(np.ascontiguousarray(data))
                return
            except Exception:
                continue

    def setup_hint(self, bilateral: bool = False) -> str:
        if IS_MAC:
            return ("Instale o BlackHole: `brew install blackhole-2ch`"
                    + (" e `brew install blackhole-16ch`" if bilateral else "")
                    + "; depois escolha 'BlackHole 2ch' como microfone no seu app de chamada.")
        if IS_WIN:
            return ("Instale o VB-Audio Virtual Cable (https://vb-audio.com/Cable/)"
                    + (" e o VB-Cable A+B para o modo bilateral" if bilateral else "")
                    + "; depois escolha 'CABLE Output' como microfone no seu app de chamada.")
        return ("Instale o pulseaudio-utils (pactl/parec/pacat) para o Praxis poder criar "
                "o microfone virtual, ou carregue o snd-aloop e escolha esse dispositivo.")


# ── Fábrica ───────────────────────────────────────────────────────────────────

_backend: AudioBackend | None = None
_backend_lock = threading.Lock()


def get_backend(force: str | None = None) -> AudioBackend:
    """Escolhe o backend de áudio. Para forçar, use PRAXIS_AUDIO=pulse|sounddevice."""
    global _backend
    with _backend_lock:
        choice = force or os.environ.get("PRAXIS_AUDIO", "")
        if _backend is not None and not force:
            return _backend
        if choice == "pulse" or (not choice and PulseBackend.available()):
            b: AudioBackend = PulseBackend()
        else:
            b = SoundDeviceBackend()
        if not force:
            _backend = b
        return b


def reset_backend() -> None:
    global _backend
    with _backend_lock:
        _backend = None
