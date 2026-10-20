"""praxis_platform: parsers, paths, resampling, loopback detection."""
import os
from pathlib import Path

import numpy as np
import pytest

import praxis_platform as plat

PACTL_SOURCES = """\
Source #1
\tState: SUSPENDED
\tName: alsa_input.usb-Focusrite_Scarlett-00.analog-stereo
\tDescription: Scarlett 2i2 Analog Stereo
\tChannel Map: front-left,front-right
Source #2
\tName: alsa_output.pci.analog-stereo.monitor
\tDescription: Monitor of Built-in Audio
\tChannel Map: front-left,front-right
Source #3
\tName: alsa_input.pci.analog-mono
\tDescription: Built-in Mic
\tChannel Map: mono
Source #4
\tName: Praxis_Mic
\tDescription: Praxis_Microfone
\tChannel Map: mono
"""


def test_parse_pactl_list_excludes_monitors_and_praxis():
    devs = plat.parse_pactl_list(PACTL_SOURCES, (".monitor", "Praxis"))
    assert [d[0] for d in devs] == ["alsa_input.usb-Focusrite_Scarlett-00.analog-stereo",
                                    "alsa_input.pci.analog-mono"]
    assert devs[0][2] == "front-left,front-right"


def test_expand_stereo_inputs_splits_channels():
    out = plat.expand_stereo_inputs(plat.parse_pactl_list(PACTL_SOURCES, (".monitor", "Praxis")))
    ids = [i for i, _ in out]
    assert ids[0].endswith(":left") and ids[1].endswith(":right")
    assert ids[2] == "alsa_input.pci.analog-mono"
    assert "Input 1 (L)" in out[0][1]


def test_parse_pactl_info():
    raw = "Server Name: PulseAudio (on PipeWire 1.0)\nDefault Sink: spk\nDefault Source: mic\n"
    assert plat.parse_pactl_info(raw) == ("mic", "spk")
    assert plat.parse_pactl_info("") == ("", "")


@pytest.mark.parametrize("dev,expected", [
    (None, (None, None)), ("", (None, None)), ("hw", ("hw", None)),
    ("hw:left", ("hw", 0)), ("hw:right", ("hw", 1)),
    ("alsa:card:left", ("alsa:card", 0)),
])
def test_split_channel(dev, expected):
    assert plat.split_channel(dev) == expected


def test_resample_lengths_and_dtype():
    x = (np.sin(np.linspace(0, 20, 48000)) * 10000).astype(np.int16)
    y = plat.resample(x, 48000, 16000)
    assert y.dtype == np.int16 and abs(len(y) - 16000) <= 1
    f = np.linspace(-1, 1, 441).astype(np.float32)
    g = plat.resample(f, 44100, 16000)
    assert g.dtype == np.float32 and abs(len(g) - 160) <= 1
    assert plat.resample(x, 16000, 16000) is x
    assert len(plat.resample(np.zeros(0, np.int16), 8000, 16000)) == 0


def test_resample_preserves_tone_frequency():
    sr_in, sr_out, f0 = 48000, 16000, 440.0
    t = np.arange(sr_in) / sr_in
    y = plat.resample(np.sin(2 * np.pi * f0 * t).astype(np.float32), sr_in, sr_out)
    spec = np.abs(np.fft.rfft(y))
    peak_hz = np.argmax(spec) * sr_out / len(y)
    assert abs(peak_hz - f0) < 2


DEVICES = [
    {"name": "MacBook Pro Microphone", "max_input_channels": 1, "max_output_channels": 0},
    {"name": "MacBook Pro Speakers", "max_input_channels": 0, "max_output_channels": 2},
    {"name": "BlackHole 2ch", "max_input_channels": 2, "max_output_channels": 2},
    {"name": "BlackHole 16ch", "max_input_channels": 16, "max_output_channels": 16},
]
WIN_DEVICES = [
    {"name": "CABLE Input (VB-Audio Virtual Cable)", "max_input_channels": 0, "max_output_channels": 8},
    {"name": "CABLE Output (VB-Audio Virtual Cable)", "max_input_channels": 2, "max_output_channels": 0},
]


def test_find_loopback_macos_blackhole():
    assert plat.find_loopback(DEVICES, plat.LOOPBACK_DRIVERS) == ("BlackHole 2ch", "BlackHole 2ch")
    peer = plat.find_loopback(DEVICES, plat.PEER_LOOPBACK_DRIVERS, avoid=("BlackHole 2ch",))
    assert peer == ("BlackHole 16ch", "BlackHole 16ch")


def test_find_loopback_windows_vbcable():
    assert plat.find_loopback(WIN_DEVICES, plat.LOOPBACK_DRIVERS) == (
        "CABLE Input (VB-Audio Virtual Cable)", "CABLE Output (VB-Audio Virtual Cable)")


def test_find_loopback_none():
    assert plat.find_loopback(DEVICES[:2], plat.LOOPBACK_DRIVERS) is None


def test_loopbacks_hidden_from_device_lists():
    assert plat._is_loopback("BlackHole 2ch")
    assert plat._is_loopback("CABLE Output (VB-Audio Virtual Cable)")
    assert not plat._is_loopback("MacBook Pro Microphone")


def test_paths_are_per_os():
    assert plat.config_dir().name.lower() == "praxis"
    vp = plat.venv_python(Path("/x/venv"))
    assert vp.name in ("python3", "python.exe")
    assert ("Scripts" in vp.parts) == plat.IS_WIN


def test_temp_paths_private_and_unique():
    d = plat.temp_dir()
    assert d.is_dir()
    if hasattr(os, "getuid"):
        assert (d.stat().st_mode & 0o077) == 0
    a, b = plat.new_temp_file(".wav"), plat.new_temp_file(".wav")
    assert a != b and Path(a).exists()
    Path(a).unlink(); Path(b).unlink()
    assert Path(plat.temp_path("x.wav")).parent == d


def test_cuda_env_adds_existing_dirs_only(tmp_path, monkeypatch):
    monkeypatch.setenv("PRAXIS_CUDA_LIB", os.pathsep.join([str(tmp_path), "/does/not/exist"]))
    env = plat.cuda_env({"PATH": "p", "LD_LIBRARY_PATH": "l"})
    var = "PATH" if plat.IS_WIN else "LD_LIBRARY_PATH"
    assert env[var].startswith(str(tmp_path))
    assert "/does/not/exist" not in env[var]


def test_parse_xrandr_prefers_primary():
    out = ("Screen 0: minimum 8 x 8\n"
           "HDMI-1 connected 1920x1080+0+0 (normal) 600mm x 340mm\n"
           "eDP-1 connected primary 2560x1600+1920+0 (normal) 300mm x 190mm\n"
           "DP-2 disconnected (normal)\n")
    assert plat.parse_xrandr(out) == (1920, 0, 2560, 1600)
    assert plat.parse_xrandr("HDMI-1 connected 1280x720+0+0\n") == (0, 0, 1280, 720)
    assert plat.parse_xrandr("") == (0, 0, 0, 0)


def test_get_backend_env_override(monkeypatch):
    pytest.importorskip("sounddevice")
    plat.reset_backend()
    monkeypatch.setenv("PRAXIS_AUDIO", "sounddevice")
    try:
        assert plat.get_backend().name == "sounddevice"
    except OSError:
        pytest.skip("PortAudio library not available")
    finally:
        plat.reset_backend()


def test_sounddevice_backend_hint_mentions_driver():
    b = plat.SoundDeviceBackend.__new__(plat.SoundDeviceBackend)
    hint = b.setup_hint()
    if plat.IS_MAC:
        assert "BlackHole" in hint
    elif plat.IS_WIN:
        assert "VB-Audio" in hint


def test_player_stop_and_wait():
    p = plat.Player()
    assert not p.done
    p.stop()
    assert p.wait(0.1) and p.done
