"""praxis_platform: leitura de saídas de comandos, caminhos, reamostragem e detecção de dispositivos de loopback (áudio virtual)."""
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


def test_leitura_pactl_list_exclui_monitores_e_praxis():
    devs = plat.parse_pactl_list(PACTL_SOURCES, (".monitor", "Praxis"))
    assert [d[0] for d in devs] == ["alsa_input.usb-Focusrite_Scarlett-00.analog-stereo",
                                    "alsa_input.pci.analog-mono"]
    assert devs[0][2] == "front-left,front-right"


def test_expandir_entradas_estereo_separa_canais():
    out = plat.expand_stereo_inputs(plat.parse_pactl_list(PACTL_SOURCES, (".monitor", "Praxis")))
    ids = [i for i, _ in out]
    assert ids[0].endswith(":left") and ids[1].endswith(":right")
    assert ids[2] == "alsa_input.pci.analog-mono"
    assert "Entrada 1 (esquerda)" in out[0][1]


def test_leitura_pactl_info():
    raw = "Server Name: PulseAudio (on PipeWire 1.0)\nDefault Sink: spk\nDefault Source: mic\n"
    assert plat.parse_pactl_info(raw) == ("mic", "spk")
    assert plat.parse_pactl_info("") == ("", "")


@pytest.mark.parametrize("dev,expected", [
    (None, (None, None)), ("", (None, None)), ("hw", ("hw", None)),
    ("hw:left", ("hw", 0)), ("hw:right", ("hw", 1)),
    ("alsa:card:left", ("alsa:card", 0)),
])
def test_separa_canal(dev, expected):
    assert plat.split_channel(dev) == expected


def test_reamostragem_tamanhos_e_tipo():
    x = (np.sin(np.linspace(0, 20, 48000)) * 10000).astype(np.int16)
    y = plat.resample(x, 48000, 16000)
    assert y.dtype == np.int16 and abs(len(y) - 16000) <= 1
    f = np.linspace(-1, 1, 441).astype(np.float32)
    g = plat.resample(f, 44100, 16000)
    assert g.dtype == np.float32 and abs(len(g) - 160) <= 1
    assert plat.resample(x, 16000, 16000) is x
    assert len(plat.resample(np.zeros(0, np.int16), 8000, 16000)) == 0


def test_reamostragem_preserva_frequencia_do_tom():
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


def test_encontra_loopback_macos_blackhole():
    assert plat.find_loopback(DEVICES, plat.LOOPBACK_DRIVERS) == ("BlackHole 2ch", "BlackHole 2ch")
    peer = plat.find_loopback(DEVICES, plat.PEER_LOOPBACK_DRIVERS, avoid=("BlackHole 2ch",))
    assert peer == ("BlackHole 16ch", "BlackHole 16ch")


def test_encontra_loopback_windows_vbcable():
    assert plat.find_loopback(WIN_DEVICES, plat.LOOPBACK_DRIVERS) == (
        "CABLE Input (VB-Audio Virtual Cable)", "CABLE Output (VB-Audio Virtual Cable)")


def test_encontra_loopback_nenhum():
    assert plat.find_loopback(DEVICES[:2], plat.LOOPBACK_DRIVERS) is None


def test_loopbacks_ocultos_das_listas_de_dispositivos():
    assert plat._is_loopback("BlackHole 2ch")
    assert plat._is_loopback("CABLE Output (VB-Audio Virtual Cable)")
    assert not plat._is_loopback("MacBook Pro Microphone")


def test_caminhos_dependem_do_sistema():
    assert plat.config_dir().name.lower() == "praxis"
    vp = plat.venv_python(Path("/x/venv"))
    assert vp.name in ("python3", "python.exe")
    assert ("Scripts" in vp.parts) == plat.IS_WIN


def test_caminhos_temporarios_privados_e_unicos():
    d = plat.temp_dir()
    assert d.is_dir()
    if hasattr(os, "getuid"):
        assert (d.stat().st_mode & 0o077) == 0
    a, b = plat.new_temp_file(".wav"), plat.new_temp_file(".wav")
    assert a != b and Path(a).exists()
    Path(a).unlink(); Path(b).unlink()
    assert Path(plat.temp_path("x.wav")).parent == d


def test_ambiente_cuda_adiciona_so_pastas_existentes(tmp_path, monkeypatch):
    monkeypatch.setenv("PRAXIS_CUDA_LIB", os.pathsep.join([str(tmp_path), "/does/not/exist"]))
    env = plat.cuda_env({"PATH": "p", "LD_LIBRARY_PATH": "l"})
    var = "PATH" if plat.IS_WIN else "LD_LIBRARY_PATH"
    assert env[var].startswith(str(tmp_path))
    assert "/does/not/exist" not in env[var]


def test_leitura_xrandr_prefere_monitor_principal():
    out = ("Screen 0: minimum 8 x 8\n"
           "HDMI-1 connected 1920x1080+0+0 (normal) 600mm x 340mm\n"
           "eDP-1 connected primary 2560x1600+1920+0 (normal) 300mm x 190mm\n"
           "DP-2 disconnected (normal)\n")
    assert plat.parse_xrandr(out) == (1920, 0, 2560, 1600)
    assert plat.parse_xrandr("HDMI-1 connected 1280x720+0+0\n") == (0, 0, 1280, 720)
    assert plat.parse_xrandr("") == (0, 0, 0, 0)


def test_backend_escolhido_por_variavel_de_ambiente(monkeypatch):
    pytest.importorskip("sounddevice")
    plat.reset_backend()
    monkeypatch.setenv("PRAXIS_AUDIO", "sounddevice")
    try:
        assert plat.get_backend().name == "sounddevice"
    except OSError:
        pytest.skip("biblioteca PortAudio não disponível")
    finally:
        plat.reset_backend()


def test_dica_do_backend_sounddevice_cita_o_driver():
    b = plat.SoundDeviceBackend.__new__(plat.SoundDeviceBackend)
    hint = b.setup_hint()
    if plat.IS_MAC:
        assert "BlackHole" in hint
    elif plat.IS_WIN:
        assert "VB-Audio" in hint


def test_player_parar_e_esperar():
    p = plat.Player()
    assert not p.done
    p.stop()
    assert p.wait(0.1) and p.done


# ── janelas nunca podem sair da área útil da tela ─────────────────────────────

MAC_WORK = (0, 30, 1792, 1004)       # MacBook 16": barra de menus 30 px, Dock 86 px
SMALL = (0, 0, 1366, 728)            # notebook 1366×768 com barra de tarefas de 40 px
SECOND = (1920, 0, 1280, 984)        # monitor secundário à direita


def _inside(work, w, h, x, y, titlebar):
    wx, wy, ww, wh = work
    return wx <= x and x + w <= wx + ww and wy <= y and y + h + titlebar <= wy + wh


@pytest.mark.parametrize("work", [MAC_WORK, SMALL, SECOND, (0, 0, 800, 600)])
@pytest.mark.parametrize("want", [(560, 900), (1120, 1040), (480, 540), (3000, 3000)])
def test_ajusta_janela_sempre_dentro(work, want):
    w, h, x, y = plat.fit_window(work, *want, titlebar=32)
    assert _inside(work, w, h, x, y, 32), (work, want, (w, h, x, y))
    assert w <= want[0] and h <= want[1]


def test_ajusta_janela_regressao_v010_estouro():
    """A v0.1.0 pedia screen_h - 80 = 1040 px (+ barra de título) numa tela de Mac
    de 1120 px cuja altura útil é 1004 px → a parte de baixo ficava sob o Dock."""
    w, h, x, y = plat.fit_window(MAC_WORK, 560, 1040, titlebar=28)
    assert y + h + 28 <= 30 + 1004


@pytest.mark.parametrize("prefer", [(-500, -500), (5000, 5000), (100, 100)])
def test_ajusta_janela_limita_posicao_preferida(prefer):
    w, h, x, y = plat.fit_window(SMALL, 1120, 700, titlebar=32, prefer=prefer)
    assert _inside(SMALL, w, h, x, y, 32)


def test_area_de_trabalho_retorna_retangulo_util():
    x, y, w, h = plat.work_area()
    if w == 0:
        pytest.skip("sem tela / sem API de área de trabalho nesta máquina de testes")
    assert w > 0 and h > 0



def test_normalizacao_do_benchmark_mantem_sinais_combinados():
    """Sinais de vogal do hindi e letras árabes não podem ser quebrados em pedaços
    (isso inflava/escondia erros no benchmark com fala real)."""
    import sys
    from conftest import ROOT
    sys.path.insert(0, str(ROOT / "benchmarks"))
    from run_benchmarks import normalize
    assert normalize("कुछ अणुओं में अस्थिर केंद्रक") == "कुछ अणुओं में अस्थिर केंद्रक"
    assert normalize("عاصفة مُسماة لموسم الأعاصير") == "عاصفة مسماة لموسم الاعاصير"
    assert normalize("Elle appela sa sœur, l’aînée!") == "elle appela sa soeur l aînée"


def test_area_de_trabalho_linux_sem_gerenciador_de_janelas(monkeypatch):
    """Na integração contínua (CI) / em desktops Linux mínimos não há gerenciador de
    janelas: wm_maxsize() voltava 560 × 1048575 e a janela era 'ajustada' a um absurdo."""
    import types
    monkeypatch.setattr(plat, "IS_LINUX", True)
    monkeypatch.setattr(plat, "IS_MAC", False)
    monkeypatch.setattr(plat, "IS_WIN", False)
    monkeypatch.setattr(plat, "primary_monitor_geometry", lambda: (0, 0, 0, 0))
    monkeypatch.setattr(plat, "_net_workarea", lambda: None)
    root = types.SimpleNamespace(winfo_screenwidth=lambda: 1920, winfo_screenheight=lambda: 1080,
                                 wm_maxsize=lambda: (560, 1048575))
    assert plat.work_area(root) == (0, 0, 1920, 1080)



# ── idioma do sistema ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("tag,code", [("pt-BR", "pt"), ("pt_BR.UTF-8", "pt"), ("zh-Hans-CN", "zh"),
                                      ("en_US@euro", "en"), ("C", ""), ("POSIX", ""), ("", "")])
def test_codigo_de_idioma(tag, code):
    assert plat._lang_code(tag) == code


def test_idioma_do_sistema_no_linux_pelas_variaveis(monkeypatch):
    monkeypatch.setattr(plat, "IS_MAC", False)
    monkeypatch.setattr(plat, "IS_WIN", False)
    for v in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("LANG", "de_DE.UTF-8")
    assert plat.system_language() == "de"
    monkeypatch.setenv("LANGUAGE", "fr_FR:en_US")      # LANGUAGE tem prioridade
    assert plat.system_language() == "fr"


@pytest.mark.parametrize("sistema,esperado", [
    ("pt", {"ui_lang": "pt", "src": "pt", "tgt": "en"}),
    ("en", {"ui_lang": "en", "src": "en", "tgt": "es"}),
    ("ja", {"ui_lang": "en", "src": "ja", "tgt": "en"}),     # interface sem japonês → inglês
    ("sv", {"ui_lang": "en", "src": "en", "tgt": "es"}),     # idioma que o Praxis não tem
    ("", {"ui_lang": "en", "src": "en", "tgt": "es"}),       # não deu para saber
])
def test_escolhas_iniciais_herdam_o_idioma_do_sistema(monkeypatch, sistema, esperado):
    monkeypatch.setattr(plat, "system_language", lambda: sistema)
    ui = ["pt", "en", "es", "fr", "de", "it", "ru", "zh", "nl", "pl", "uk", "tr", "ar", "hi"]
    assert plat.default_languages(ui, ui + ["ja", "ko"]) == esperado


def test_idioma_do_sistema_neste_computador():
    """Só confere que a detecção roda e devolve um código de 2 letras ou vazio."""
    code = plat.system_language()
    assert code == "" or (len(code) in (2, 3) and code.isalpha())
