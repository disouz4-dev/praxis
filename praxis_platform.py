#!/usr/bin/env python3
"""Praxis — platform abstraction layer.

Everything that differs between Linux, macOS and Windows lives here so the
engine (praxis.py) and the UI (praxis_config.py) stay platform-agnostic:

  * per-user config / data / temp directories
  * the interpreter of the installed venv
  * audio device enumeration, capture and playback
  * the "virtual microphone" the call app listens to

Two audio backends are provided:

  PulseBackend        Linux with PulseAudio/PipeWire (pactl/parec/pacat).
                      Creates real virtual devices on demand (null sink +
                      remap source) — no driver install needed.
  SoundDeviceBackend  macOS, Windows, and Linux without pactl. Uses PortAudio
                      via `sounddevice`. The virtual microphone is an
                      already-installed loopback driver:
                        macOS   → BlackHole  (brew install blackhole-2ch)
                        Windows → VB-Audio Virtual Cable
                      Praxis plays into the driver's *output* side and the
                      call app selects its *input* side as the microphone.

Device ids are plain strings in both backends. A ":left" / ":right" suffix
selects one channel of a stereo input (used by audio interfaces where each
channel is a separate mic).
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


# ── Paths ─────────────────────────────────────────────────────────────────────

def config_dir() -> Path:
    """Per-user config directory (config.json lives here)."""
    if IS_WIN:
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "Praxis"
    if IS_MAC:
        return Path.home() / "Library" / "Application Support" / "Praxis"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / APP


def data_dir() -> Path:
    """Per-user install/data directory (venv, installed app copy)."""
    if IS_WIN:
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "Praxis"
    if IS_MAC:
        return Path.home() / "Library" / "Application Support" / "Praxis"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / APP


def venv_python(venv: Path) -> Path:
    """Interpreter path inside a venv for the current OS."""
    if IS_WIN:
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python3"


def installed_python() -> Path | None:
    """Interpreter of the venv created by the installer, if present."""
    p = venv_python(data_dir() / "venv")
    return p if p.exists() else None


_TMP_LOCK = threading.Lock()


def temp_dir() -> Path:
    """Private per-user temp dir (avoids predictable shared /tmp paths)."""
    with _TMP_LOCK:
        uid = os.getuid() if hasattr(os, "getuid") else os.environ.get("USERNAME", "user")
        d = Path(tempfile.gettempdir()) / f"praxis-{uid}"
        d.mkdir(mode=0o700, exist_ok=True)
        return d


def temp_path(name: str) -> str:
    """Stable named file in the private temp dir (e.g. 'ov_ref.wav')."""
    return str(temp_dir() / name)


def new_temp_file(suffix: str = "") -> str:
    """Unique temp file path (closed, so it can be reopened on Windows)."""
    fd, path = tempfile.mkstemp(suffix=suffix, dir=temp_dir())
    os.close(fd)
    return path


def log_path() -> str:
    return temp_path("praxis_engine.log")


def ffmpeg_exe() -> str | None:
    """ffmpeg on PATH, else the binary bundled by imageio-ffmpeg if installed."""
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg  # type: ignore
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def cuda_env(env: dict[str, str]) -> dict[str, str]:
    """Adds known extra CUDA library dirs to the loader path (Linux only).

    Override/extend with PRAXIS_CUDA_LIB (os.pathsep-separated)."""
    env = dict(env)
    extra = [p for p in os.environ.get("PRAXIS_CUDA_LIB", "").split(os.pathsep) if p]
    if IS_LINUX:
        extra.append("/usr/local/lib/ollama/cuda_v12")
    # cuBLAS/cuDNN installed from PyPI (nvidia-cublas-cu12, nvidia-cudnn-cu12)
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
    """(x, y, w, h) of the primary monitor, or zeros if unknown.

    Uses xrandr on X11 Linux (multi-monitor aware); callers fall back to
    Tk's winfo_screenwidth/height elsewhere."""
    if not IS_LINUX or not shutil.which("xrandr"):
        return 0, 0, 0, 0
    try:
        out = subprocess.check_output(["xrandr"], text=True, stderr=subprocess.DEVNULL, timeout=3)
    except Exception:
        return 0, 0, 0, 0
    return parse_xrandr(out)


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


# ── Audio helpers ─────────────────────────────────────────────────────────────

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
    """Linear-interpolation resampler — good enough for speech/meters."""
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
    """Result of setting up the outbound virtual microphone.

    target       device id Praxis plays translated speech into
    mic_label    what the user must select as microphone in the call app
    peer_capture device id to capture the peer's audio from (bilateral) or None
    peer_label   what the user must route the call app's output to, or ""
    """
    target: str | None
    mic_label: str
    peer_capture: str | None = None
    peer_label: str = ""


class CaptureStream:
    """Blocking reader of mono int16 chunks of fixed size."""

    def read(self) -> bytes | None:          # pragma: no cover - interface
        raise NotImplementedError

    def close(self) -> None:                 # pragma: no cover - interface
        raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


class Player:
    """Handle to a WAV/PCM playback started in the background."""

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

    # enumeration -------------------------------------------------------------
    def list_inputs(self) -> list[tuple[str, str]]:
        raise NotImplementedError

    def list_outputs(self) -> list[tuple[str, str]]:
        raise NotImplementedError

    def defaults(self) -> tuple[str, str]:
        return "", ""

    # engine ------------------------------------------------------------------
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
        targets = list(dict.fromkeys(devices))  # dedupe, keep order
        if len(targets) <= 1:
            self.play_pcm(pcm, rate, targets[0] if targets else None)
            return
        ts = [threading.Thread(target=self.play_pcm, args=(pcm, rate, d), daemon=True)
              for d in targets]
        for t in ts:
            t.start()
        for t in ts:
            t.join()

    # UI ----------------------------------------------------------------------
    def play_file(self, path: str, device: str | None = None) -> Player:
        """Plays a WAV file in the background; returns a stoppable handle."""
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
        """Optional system-wide sample rate pin (PipeWire only)."""

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
    """Parses `LANG=C pactl list sources|sinks` → [(name, description, channel_map)]."""
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
            out.append((f"{name}:left",  f"{desc}  —  Input 1 (L)"))
            out.append((f"{name}:right", f"{desc}  —  Input 2 (R)"))
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
        """Turns 'dev:left'/'dev:right' into a mono remap source."""
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


# ── PortAudio (sounddevice) — macOS / Windows / fallback ──────────────────────

# Loopback drivers, in priority order. Each entry: (output-side name fragment
# Praxis plays into, input-side name fragment the call app records from).
LOOPBACK_DRIVERS: list[tuple[str, str]] = [
    ("BlackHole 2ch",   "BlackHole 2ch"),
    ("BlackHole",       "BlackHole"),
    ("CABLE Input",     "CABLE Output"),
    ("VoiceMeeter Input", "VoiceMeeter Output"),
    ("Loopback Audio",  "Loopback Audio"),
    ("Soundflower (2ch)", "Soundflower (2ch)"),
]
# Second loopback for bilateral mode (call app output → Praxis).
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
    """Returns (output device name, input device name) of the first loopback
    driver in `table` present in `devices` (sounddevice.query_devices())."""
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

        def _cb(indata, frames, time_info, status):  # PortAudio thread
            x = indata[:, self._channel] if self._channel is not None else indata[:, 0]
            x = x.copy()
            if self._dev_rate != self._rate:
                x = resample(x, self._dev_rate, self._rate)
            try:
                self._q.put_nowait(x)
            except queue.Full:
                pass

        # Prefer the engine rate; fall back to the device rate + resampling
        # (WASAPI shared mode and many USB devices refuse 16 kHz).
        last_err: Exception | None = None
        # Native device rate first (CoreAudio/WASAPI reject many rates and
        # PortAudio logs noisy errors); resample to the engine rate in the callback.
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
            raise RuntimeError(f"Cannot open input device: {last_err}")

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
        # On Windows the same device appears once per host API (MME, DirectSound,
        # WASAPI, WDM-KS). Keep only the default host API to avoid duplicates.
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
                out.append((f"{n}:left",  f"{n}  —  Input 1 (L)"))
                out.append((f"{n}:right", f"{n}  —  Input 2 (R)"))
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
                "No virtual audio cable found. " + self.setup_hint())
        vm = VirtualMic(target=lb[0], mic_label=lb[1])
        if bilateral:
            peer = find_loopback(devs, PEER_LOOPBACK_DRIVERS, avoid=lb)
            if not peer:
                raise RuntimeError(
                    "Bilateral mode needs a second virtual cable. " + self.setup_hint(bilateral=True))
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
            return ("Install BlackHole: `brew install blackhole-2ch`"
                    + (" and `brew install blackhole-16ch`" if bilateral else "")
                    + ", then select 'BlackHole 2ch' as the microphone in your call app.")
        if IS_WIN:
            return ("Install VB-Audio Virtual Cable (https://vb-audio.com/Cable/)"
                    + (" and VB-Cable A+B for bilateral mode" if bilateral else "")
                    + ", then select 'CABLE Output' as the microphone in your call app.")
        return ("Install pulseaudio-utils (pactl/parec/pacat) so Praxis can create "
                "its virtual microphone, or load snd-aloop and select it.")


# ── Factory ───────────────────────────────────────────────────────────────────

_backend: AudioBackend | None = None
_backend_lock = threading.Lock()


def get_backend(force: str | None = None) -> AudioBackend:
    """Picks the audio backend. Override with PRAXIS_AUDIO=pulse|sounddevice."""
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
