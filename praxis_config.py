#!/usr/bin/env python3
"""Praxis — Janela de Configuração."""

import json
import os
import queue
import re
import select
import subprocess
import sys
import threading
import tkinter as tk
import urllib.request
from pathlib import Path
from tkinter import messagebox

import numpy as np
import customtkinter as ctk

CONFIG_FILE = Path.home() / ".config" / "praxis" / "config.json"
VOICES_DIR  = Path(__file__).parent / "voices"
PRAXIS_PY   = Path(__file__).parent / "praxis.py"
ASSETS_DIR  = Path(__file__).parent / "assets"

# Idiomas que o Whisper reconhece como fonte (transcrição)
SRC_LANGS = [
    ("pt", "Português"),
    ("en", "English"),
    ("es", "Español"),
    ("fr", "Français"),
    ("de", "Deutsch"),
    ("it", "Italiano"),
    ("ja", "日本語"),
    ("zh", "中文"),
    ("ko", "한국어"),
    ("ru", "Русский"),
    ("ar", "العربية"),
    ("hi", "हिन्दी"),
    ("nl", "Nederlands"),
    ("pl", "Polski"),
    ("uk", "Українська"),
    ("tr", "Türkçe"),
]

_HF_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

# Vozes verificadas em rhasspy/piper-voices voices.json (todas com HTTP 200)
VOICE_CATALOG: list[dict] = [
    {"lang": "pt", "locale": "pt_BR", "speaker": "faber",    "quality": "medium", "gender": "M", "name": "Faber (BR)"},
    {"lang": "pt", "locale": "pt_BR", "speaker": "cadu",     "quality": "medium", "gender": "M", "name": "Cadu (BR)"},
    {"lang": "pt", "locale": "pt_PT", "speaker": "tugão",    "quality": "medium", "gender": "M", "name": "Tugão (PT)"},
    {"lang": "en", "locale": "en_US", "speaker": "lessac",   "quality": "medium", "gender": "F", "name": "Lessac (US)"},
    {"lang": "en", "locale": "en_US", "speaker": "ryan",     "quality": "medium", "gender": "M", "name": "Ryan (US)"},
    {"lang": "en", "locale": "en_GB", "speaker": "alan",     "quality": "medium", "gender": "M", "name": "Alan (GB)"},
    {"lang": "en", "locale": "en_GB", "speaker": "alba",     "quality": "medium", "gender": "F", "name": "Alba (GB)"},
    {"lang": "es", "locale": "es_ES", "speaker": "sharvard", "quality": "medium", "gender": "M", "name": "Sharvard (ES)"},
    {"lang": "es", "locale": "es_MX", "speaker": "ald",      "quality": "medium", "gender": "M", "name": "ALD (MX)"},
    {"lang": "fr", "locale": "fr_FR", "speaker": "siwis",    "quality": "medium", "gender": "F", "name": "Siwis"},
    {"lang": "fr", "locale": "fr_FR", "speaker": "gilles",   "quality": "low",    "gender": "M", "name": "Gilles"},
    {"lang": "de", "locale": "de_DE", "speaker": "thorsten", "quality": "high",   "gender": "M", "name": "Thorsten"},
    {"lang": "de", "locale": "de_DE", "speaker": "karlsson", "quality": "low",    "gender": "M", "name": "Karlsson"},
    {"lang": "de", "locale": "de_DE", "speaker": "mls",      "quality": "medium", "gender": "?", "name": "MLS"},
    {"lang": "it", "locale": "it_IT", "speaker": "paola",    "quality": "medium", "gender": "F", "name": "Paola"},
    {"lang": "it", "locale": "it_IT", "speaker": "riccardo", "quality": "x_low",  "gender": "M", "name": "Riccardo"},
    {"lang": "ru", "locale": "ru_RU", "speaker": "dmitri",   "quality": "medium", "gender": "M", "name": "Dmitri"},
    {"lang": "ru", "locale": "ru_RU", "speaker": "irina",    "quality": "medium", "gender": "F", "name": "Irina"},
    {"lang": "zh", "locale": "zh_CN", "speaker": "huayan",   "quality": "medium", "gender": "F", "name": "Huayan"},
    {"lang": "nl", "locale": "nl_NL", "speaker": "mls",      "quality": "medium", "gender": "?", "name": "MLS"},
    {"lang": "pl", "locale": "pl_PL", "speaker": "gosia",    "quality": "medium", "gender": "F", "name": "Gosia"},
    {"lang": "uk", "locale": "uk_UA", "speaker": "lada",     "quality": "x_low",  "gender": "F", "name": "Lada"},
    {"lang": "tr", "locale": "tr_TR", "speaker": "dfki",     "quality": "medium", "gender": "?", "name": "DFKI"},
    {"lang": "ar", "locale": "ar_JO", "speaker": "kareem",   "quality": "medium", "gender": "M", "name": "Kareem"},
    {"lang": "hi", "locale": "hi_IN", "speaker": "rohan",    "quality": "medium", "gender": "M", "name": "Rohan"},
]

# Idiomas de destino: apenas os que têm voz no catálogo ou já instalada
def _tgt_langs_with_voices() -> list[tuple[str, str]]:
    _names = {
        "pt": "Português", "en": "English",  "es": "Español",
        "fr": "Français",  "de": "Deutsch",  "it": "Italiano",
        "ru": "Русский",   "zh": "中文",      "nl": "Nederlands",
        "pl": "Polski",    "uk": "Українська","tr": "Türkçe",
        "ar": "العربية",   "hi": "हिन्दी",
    }
    catalog_langs = {v["lang"] for v in VOICE_CATALOG}
    installed_langs = {p.stem[:2] for p in VOICES_DIR.glob("*.onnx")} if VOICES_DIR.exists() else set()
    available = catalog_langs | installed_langs
    return [(c, n) for c, n in _names.items() if c in available]

# LANGS unificado (compatibilidade com código existente) = união
LANGS = SRC_LANGS
LANG_CODES  = [c for c, _ in LANGS]
LANG_LABELS = [f"{n}  ({c})" for c, n in LANGS]
MODELS      = ["tiny", "base", "small", "medium", "large-v2"]


def _catalog_filename(v: dict) -> str:
    return f"{v['locale']}-{v['speaker']}-{v['quality']}.onnx"


def _catalog_url(v: dict, ext: str = "") -> str:
    l, lo, sp, q = v["lang"], v["locale"], v["speaker"], v["quality"]
    return f"{_HF_BASE}/{l}/{lo}/{sp}/{q}/{lo}-{sp}-{q}.onnx{ext}"


DEFAULT_CFG: dict = {
    "src":            "pt",
    "tgt":            "en",
    "voice_out":      str(VOICES_DIR / "en_US-lessac-medium.onnx"),
    "voice_in":       "",
    "model":          "small",
    "mic":            "",
    "output":         "",
    "monitor":        False,
    "mode":           "vad",
    "gate_threshold": 0.10,
    "ptt_key":        "",
    "theme":          "light",
}

THEME_LIGHT: dict = {
    "BG":     "#F5F7FA", "CARD":    "#FFFFFF", "BORDER": "#E2E5EB",
    "TEXT":   "#111827", "MUTED":   "#6B7280", "ACCENT": "#18181B",
    "HOVER":  "#3F3F46", "INPUT":   "#FAFAFA", "IBORDER": "#D1D5DB",
    "SEG_BG": "#F0F1F3", "MON_ON":  "#18181B", "MON_OFF": "#F0F1F3",
}
THEME_DARK: dict = {
    "BG":     "#0F1117", "CARD":    "#1A1D24", "BORDER": "#272B36",
    "TEXT":   "#F3F4F6", "MUTED":   "#9CA3AF", "ACCENT": "#60A5FA",
    "HOVER":  "#93C5FD", "INPUT":   "#161920", "IBORDER": "#374151",
    "SEG_BG": "#1A1E28", "MON_ON":  "#3B82F6", "MON_OFF": "#1A1E28",
}


def _get_primary_monitor() -> tuple[int, int, int, int]:
    """Retorna (x_offset, y_offset, largura, altura) do monitor primário via xrandr.
    Returns (0, 0, 0, 0) se não conseguir determinar."""
    try:
        out = subprocess.check_output(
            ["xrandr"], text=True, stderr=subprocess.DEVNULL)
        # Prefere o monitor marcado como "primary"
        for line in out.splitlines():
            if " connected primary" in line:
                m = re.search(r'(\d+)x(\d+)\+(\d+)\+(\d+)', line)
                if m:
                    return (int(m.group(3)), int(m.group(4)),
                            int(m.group(1)), int(m.group(2)))
        # Fallback: primeiro monitor conectado
        for line in out.splitlines():
            if " connected" in line and "disconnected" not in line:
                m = re.search(r'(\d+)x(\d+)\+(\d+)\+(\d+)', line)
                if m:
                    return (int(m.group(3)), int(m.group(4)),
                            int(m.group(1)), int(m.group(2)))
    except Exception:
        pass
    return 0, 0, 0, 0


# ── Voz / catálogo ────────────────────────────────────────────────────────────

TEST_PHRASES: dict[str, str] = {
    "pt": (
        "Olá! Estou testando a clonagem de voz no Praxis. "
        "É incrível poder falar em português e ser ouvido em inglês, "
        "mantendo o meu próprio timbre e entonação."
    ),
    "en": (
        "Hello! I'm testing voice cloning in Praxis. "
        "It's incredible to speak in English and be heard in Portuguese, "
        "while keeping my own voice and tone."
    ),
    "es": (
        "¡Hola! Estoy probando la clonación de voz en Praxis. "
        "Es increíble poder hablar en español y ser escuchado en otro idioma, "
        "manteniendo mi propio timbre y entonación."
    ),
    "fr": (
        "Bonjour ! Je teste le clonage vocal dans Praxis. "
        "C'est incroyable de pouvoir parler en français et être entendu dans une autre langue, "
        "tout en conservant ma propre voix."
    ),
    "de": (
        "Hallo! Ich teste das Voice-Cloning in Praxis. "
        "Es ist unglaublich, auf Deutsch zu sprechen und in einer anderen Sprache gehört zu werden, "
        "während ich meine eigene Stimme behalte."
    ),
    "it": (
        "Ciao! Sto testando la clonazione vocale in Praxis. "
        "È incredibile poter parlare in italiano ed essere ascoltato in un'altra lingua, "
        "mantenendo la mia voce e la mia intonazione."
    ),
    "ru": (
        "Привет! Я тестирую клонирование голоса в Praxis. "
        "Невероятно говорить по-русски и быть услышанным на другом языке, "
        "сохраняя свой собственный голос."
    ),
    "zh": "你好！我正在测试Praxis中的语音克隆功能。保持我自己的声音和语调，同时用另一种语言被听到，这真是令人难以置信。",
}


def _voice_lang_code(path: str) -> str:
    """Extrai código de idioma do arquivo de voz (ex: it_IT-paola-medium.onnx → 'it')."""
    stem = Path(path).stem          # it_IT-paola-medium
    locale = stem.split("-")[0]     # it_IT
    return locale[:2].lower()       # it


def _voices_for_lang(voices: list[tuple[str, str]], lang_code: str) -> list[tuple[str, str]]:
    """Filtra vozes Piper por idioma; clones (🎙) aparecem em todos os idiomas.
    Filters Piper voices by language; clones (🎙) always appear regardless of language."""
    return [(p, lbl) for p, lbl in voices
            if lbl.startswith("🎙 ") or _voice_lang_code(p) == lang_code]


def _best_catalog_voice(lang_code: str) -> dict | None:
    """Retorna a melhor voz do catálogo para o idioma (prefere qualidade média)."""
    candidates = [v for v in VOICE_CATALOG if v["lang"] == lang_code]
    if not candidates:
        return None
    medium = [v for v in candidates if v["quality"] == "medium"]
    return medium[0] if medium else candidates[0]


# ── Áudio ─────────────────────────────────────────────────────────────────────

def _pa_devices(pa_type: str, exclude: list[str]) -> list[tuple[str, str, str]]:
    """Retorna [(name, description, channel_map)] via `pactl list <pa_type>`."""
    try:
        raw = subprocess.check_output(
            ["pactl", "list", pa_type], text=True, stderr=subprocess.DEVNULL,
            env={**__import__("os").environ, "LANG": "C", "LC_ALL": "C"},
        )
    except Exception:
        return []

    result: list[tuple[str, str, str]] = []
    name = desc = chmap = ""
    for line in raw.splitlines():
        s = line.strip()
        if s.startswith("Name:"):
            name = s.split(":", 1)[1].strip()
            desc = chmap = ""
        elif s.startswith("Description:"):
            desc = s.split(":", 1)[1].strip()
        elif s.startswith("Channel Map:"):
            chmap = s.split(":", 1)[1].strip()
            if name and desc and not any(ex in name for ex in exclude):
                result.append((name, desc, chmap))
            name = desc = chmap = ""
    return result


def get_audio_inputs() -> list[tuple[str, str]]:
    """Fontes de áudio — expande dispositivos estéreo em Input 1 / Input 2."""
    raw = _pa_devices("sources", exclude=[".monitor", "Praxis", "Atos2"])
    result: list[tuple[str, str]] = []
    for name, desc, chmap in raw:
        channels = chmap.split(",")
        if len(channels) == 2:
            result.append((f"{name}:left",  f"{desc}  —  Input 1 (L)"))
            result.append((f"{name}:right", f"{desc}  —  Input 2 (R)"))
        else:
            result.append((name, desc))
    return result


def get_audio_outputs() -> list[tuple[str, str]]:
    """Sinks de áudio (saídas) — exclui dispositivos virtuais do Praxis."""
    return [(n, d) for n, d, _ in _pa_devices("sinks", exclude=["Praxis", "Atos2"])]


def get_voices() -> list[tuple[str, str]]:
    """Retorna [(path, label)] de todos os .onnx encontrados em VOICES_DIR."""
    if not VOICES_DIR.exists():
        return []

    # Carrega metadados de gênero se disponível
    meta: dict = {}
    meta_file = VOICES_DIR / "voices_meta.json"
    if meta_file.exists():
        try:
            meta = json.loads(meta_file.read_text())
        except Exception:
            pass

    GENDER = {"M": "♂", "F": "♀", "?": ""}
    LANG_SHORT = {
        "en_US": "EN-US", "en_GB": "EN-GB",
        "pt_BR": "PT-BR", "pt_PT": "PT-PT",
    }

    result = []
    for p in sorted(VOICES_DIR.glob("*.onnx")):
        key = p.stem
        m = meta.get(key, {})
        gender  = GENDER.get(m.get("gender", "?"), "")
        lang    = LANG_SHORT.get(m.get("lang", ""), m.get("lang", ""))
        name    = m.get("name", key).capitalize()
        quality = m.get("quality", "")
        quality_label = {"low": "baixa", "medium": "média", "high": "alta"}.get(quality, quality)

        if m:
            label = f"{gender} {name}  [{lang} · {quality_label}]".strip()
        else:
            label = key
        result.append((str(p), label))

    # Adiciona clones gravados (VOICES_DIR/clones/*.json) / add recorded clones
    clones_dir = VOICES_DIR / "clones"
    if clones_dir.exists():
        for jp in sorted(clones_dir.glob("*.json")):
            try:
                cm = json.loads(jp.read_text())
                wav = clones_dir / cm.get("wav", jp.stem + ".wav")
                if wav.exists():
                    result.append((str(wav), f"🎙 {cm.get('name', jp.stem)}"))
            except Exception:
                pass

    return result


def _pa_defaults() -> tuple[str, str]:
    """Retorna (default_source_name, default_sink_name) via `pactl info`."""
    try:
        raw = subprocess.check_output(
            ["pactl", "info"], text=True, stderr=subprocess.DEVNULL,
            env={**__import__("os").environ, "LANG": "C", "LC_ALL": "C"},
        )
    except Exception:
        return "", ""
    src = sink = ""
    for line in raw.splitlines():
        if line.startswith("Default Source:"):
            src = line.split(":", 1)[1].strip()
        elif line.startswith("Default Sink:"):
            sink = line.split(":", 1)[1].strip()
    return src, sink


# ── Config ────────────────────────────────────────────────────────────────────

def load_cfg() -> dict:
    cfg = dict(DEFAULT_CFG)
    if CONFIG_FILE.exists():
        try:
            cfg.update(json.loads(CONFIG_FILE.read_text()))
        except Exception:
            pass
    # Migra voice_out para a pasta local do programa se ainda aponta para o path antigo
    old_base = str(Path.home() / ".local" / "share" / "praxis" / "voices")
    vo = cfg.get("voice_out", "")
    if vo.startswith(old_base):
        new_vo = str(VOICES_DIR / Path(vo).name)
        cfg["voice_out"] = new_vo if Path(new_vo).exists() else ""
    return cfg


def save_cfg(cfg: dict) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))


def lang_label(code: str) -> str:
    for c, n in LANGS:
        if c == code:
            return f"{n}  ({c})"
    return code


# ── Diálogo de download de vozes ──────────────────────────────────────────────

class VoiceDownloadDialog(ctk.CTkToplevel):
    """Lista vozes do catálogo e baixa as selecionadas do HuggingFace."""

    BG      = "#F5F7FA"
    CARD    = "#FFFFFF"
    TEXT    = "#111827"
    MUTED   = "#6B7280"
    IBORDER = "#D1D5DB"
    SEG_BG  = "#F0F1F3"
    ACCENT  = "#18181B"
    AMBER   = "#F59E0B"
    GREEN   = "#22C55E"

    _LANG_NAMES = {
        "it": "Italiano", "de": "Deutsch", "fr": "Français",
        "es": "Español",  "ru": "Русский", "zh": "中文",
        "ja": "日本語",   "ko": "한국어",
    }
    _GENDER = {"M": "♂", "F": "♀", "?": ""}
    _QUALITY = {"x_low": "muito baixa", "low": "baixa", "medium": "média", "high": "alta"}

    def __init__(self, parent: ctk.CTk, on_downloaded=None) -> None:
        super().__init__(parent)
        self.title("Baixar Vozes Piper")
        self.geometry("480x540")
        self.resizable(False, False)
        ctk.set_appearance_mode("light")
        self.configure(fg_color=self.BG)
        self._on_downloaded = on_downloaded
        self._checks: dict[str, ctk.BooleanVar] = {}
        self._build_ui()
        self.lift()
        self.focus_force()
        self.grab_set()

    def _build_ui(self) -> None:
        ctk.CTkLabel(self, text="Baixar Vozes Piper",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=self.TEXT).pack(anchor="w", padx=20, pady=(18, 2))
        ctk.CTkLabel(self, text="Selecione as vozes para baixar do HuggingFace:",
                     font=ctk.CTkFont(size=12), text_color=self.MUTED).pack(anchor="w", padx=20, pady=(0, 10))

        scroll = ctk.CTkScrollableFrame(self, fg_color=self.CARD,
                                        border_width=1, border_color=self.IBORDER,
                                        corner_radius=8)
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        installed = {_catalog_filename(v) for v in VOICE_CATALOG
                     if (VOICES_DIR / _catalog_filename(v)).exists()}

        groups: dict[str, list] = {}
        for v in VOICE_CATALOG:
            groups.setdefault(v["lang"], []).append(v)

        for lang, voices in groups.items():
            ctk.CTkLabel(scroll,
                         text=self._LANG_NAMES.get(lang, lang).upper(),
                         font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=self.MUTED).pack(anchor="w", padx=12, pady=(12, 4))
            for v in voices:
                fname = _catalog_filename(v)
                is_inst = fname in installed
                row = ctk.CTkFrame(scroll, fg_color="transparent")
                row.pack(fill="x", padx=8, pady=2)
                var = ctk.BooleanVar(value=False)
                self._checks[fname] = var
                gender  = self._GENDER.get(v["gender"], "")
                quality = self._QUALITY.get(v["quality"], v["quality"])
                lbl = f"{gender} {v['name']}  [{v['locale']} · {quality}]".strip()
                ctk.CTkCheckBox(row, text=lbl, variable=var,
                                font=ctk.CTkFont(size=12), text_color=self.TEXT,
                                checkbox_width=16, checkbox_height=16,
                                state="disabled" if is_inst else "normal"
                                ).pack(side="left", padx=(4, 0))
                if is_inst:
                    ctk.CTkLabel(row, text="✓ instalada",
                                 font=ctk.CTkFont(size=10),
                                 text_color=self.GREEN).pack(side="right", padx=8)

        self._prog_frame = ctk.CTkFrame(self, fg_color="transparent", height=14)
        self._prog_frame.pack(fill="x", padx=20, pady=(0, 2))
        self._prog_bar = ctk.CTkProgressBar(self._prog_frame, height=6, corner_radius=3,
                                             progress_color=self.AMBER, fg_color=self.IBORDER)
        self._prog_bar.pack(fill="x")
        self._prog_bar.set(0)
        self._prog_frame.pack_forget()

        self._status_lbl = ctk.CTkLabel(self, text="",
                                         font=ctk.CTkFont(size=11), text_color=self.MUTED)
        self._status_lbl.pack(anchor="w", padx=20, pady=(0, 4))

        self._dl_btn = ctk.CTkButton(
            self, text="Baixar Selecionadas", height=38,
            fg_color=self.ACCENT, hover_color="#374151",
            text_color="#FFFFFF", corner_radius=10,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._start_download,
        )
        self._dl_btn.pack(fill="x", padx=20, pady=(0, 20))

    def _start_download(self) -> None:
        selected = [v for v in VOICE_CATALOG
                    if self._checks.get(_catalog_filename(v), ctk.BooleanVar()).get()]
        if not selected:
            messagebox.showinfo("Praxis", "Selecione ao menos uma voz.")
            return
        self._dl_btn.configure(state="disabled", text="Baixando…")
        self._prog_frame.pack(fill="x", padx=20, pady=(0, 2))
        threading.Thread(target=self._worker, args=(selected,), daemon=True).start()

    def _worker(self, voices: list[dict]) -> None:
        import urllib.request
        VOICES_DIR.mkdir(parents=True, exist_ok=True)
        total = len(voices)
        for i, v in enumerate(voices):
            fname = _catalog_filename(v)
            msg = f"({i + 1}/{total}) Baixando {v['name']}…"
            self.after(0, lambda m=msg: self._status_lbl.configure(text=m))
            self.after(0, lambda p=i / total: self._prog_bar.set(p))
            for ext in ("", ".json"):
                try:
                    urllib.request.urlretrieve(
                        _catalog_url(v, ext), str(VOICES_DIR / f"{fname}{ext}"))
                except Exception as e:
                    err = f"Erro {v['name']}{ext}: {e}"
                    self.after(0, lambda m=err: self._status_lbl.configure(text=m))
        self.after(0, self._done)

    def _done(self) -> None:
        self._prog_bar.set(1.0)
        self._prog_bar.configure(progress_color=self.GREEN)
        self._status_lbl.configure(text="Concluído! Clique em Atualizar na janela principal.")
        self._dl_btn.configure(state="normal", text="Baixar Selecionadas")
        if self._on_downloaded:
            self._on_downloaded()


# ── Janela ────────────────────────────────────────────────────────────────────

class ConfigWindow(ctk.CTk):

    BG      = "#F5F7FA"
    CARD    = "#FFFFFF"
    BORDER  = "#E2E5EB"
    TEXT    = "#111827"
    MUTED   = "#6B7280"
    ACCENT  = "#18181B"
    HOVER   = "#3F3F46"
    INPUT   = "#FAFAFA"
    IBORDER = "#D1D5DB"
    SEG_BG  = "#F0F1F3"
    MON_ON  = "#18181B"
    MON_OFF = "#F0F1F3"

    def __init__(self) -> None:
        """Inicializa a janela principal de configuração do Praxis.
        Initializes the main Praxis configuration window."""
        super().__init__()
        ctk.set_default_color_theme("blue")

        self.cfg = load_cfg()

        # Aplica tema salvo antes de construir qualquer widget
        theme_name = self.cfg.get("theme", "light")
        theme = THEME_DARK if theme_name == "dark" else THEME_LIGHT
        for k, v in theme.items():
            setattr(ConfigWindow, k, v)
        ctk.set_appearance_mode("Dark" if theme_name == "dark" else "Light")

        self._monitor: bool  = self.cfg.get("monitor", False)
        self._bilateral: bool = bool(self.cfg.get("voice_in", ""))
        self._mode_var      = ctk.StringVar(value=self.cfg.get("mode", "vad"))
        self._gate_frac     = min(1.0, self.cfg.get("gate_threshold", 0.10) / 0.28)
        self._ptt_key: str  = self.cfg.get("ptt_key", "")
        self._gate_dragging = False
        self._engine_proc   = None
        self._meter_active  = True
        self._meter_poll_id = None

        # listas de áudio (name, desc)
        self._inputs:  list[tuple[str, str]] = []
        self._outputs: list[tuple[str, str]] = []

        self.title("Praxis — Configuração")
        self.resizable(True, True)
        self.configure(fg_color=self.BG)

        # Centraliza na tela do monitor primário
        ox, oy, sw, sh = _get_primary_monitor()
        if sw == 0:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            ox = oy = 0
        win_h = max(680, min(sh - 80, sh))   # usa quase toda a tela, mínimo 680
        self.minsize(560, 640)
        x = ox + (sw - 560) // 2
        y = oy + max(0, (sh - win_h) // 2)
        self.geometry(f"560x{win_h}+{x}+{y}")

        self.withdraw()  # oculta a janela principal durante o carregamento / hide main window during load

        # Força PipeWire a 44100 Hz em todo o sistema ao iniciar
        # Force PipeWire to 44100 Hz system-wide on startup
        subprocess.run(
            ["pw-metadata", "-n", "settings", "0", "clock.force-rate", "44100"],
            capture_output=True, timeout=3
        )

        # Splash de carregamento aparece ANTES de _build() para dar feedback imediato
        # Loading splash appears BEFORE _build() to give immediate visual feedback
        splash, _sp_prog, _sp_lbl = self._create_loading_splash()
        self.update()  # força a splash a renderizar antes do build pesado / force splash to render

        # Thread daemon que anima a barra de progresso enquanto _build() bloqueia o main thread
        # Daemon thread animates the progress bar while _build() blocks the main thread
        import time as _time
        _sp_stop = threading.Event()
        _sp_phase: list[float] = [0.05, 0.82]  # [valor_atual, limite_fase]

        def _sp_anim() -> None:
            while not _sp_stop.is_set():
                _time.sleep(0.12)
                v, hi = _sp_phase
                nxt = min(hi, v + 0.008)
                _sp_phase[0] = nxt
                try:
                    splash.after(0, _sp_prog.set, nxt)
                except Exception:
                    break

        _sp_thread = threading.Thread(target=_sp_anim, daemon=True)
        _sp_thread.start()

        _sp_lbl.configure(text="Construindo interface…")
        self.update()
        self._build()

        _sp_phase[1] = 0.96   # nova fase: dispositivos de áudio / new phase: audio devices
        _sp_lbl.configure(text="Conectando áudio…")
        self.update()
        self._refresh_devices(startup=True)

        # Finaliza animação / finish animation
        _sp_stop.set()
        _sp_prog.set(1.0)
        _sp_lbl.configure(text="Pronto!")
        self.update()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._set_window_icon()

        # Fecha splash e exibe janela principal após breve pausa
        # Close splash and show main window after brief pause
        def _open_main() -> None:
            try:
                splash.destroy()
            except Exception:
                pass
            self._show_splash()
            self.after(1800, self.deiconify)

        self.after(350, _open_main)

    def _toggle_theme(self) -> None:
        """Alterna entre light/dark mode: salva preferência e reconstrói a UI."""
        try:
            self._toggle_theme_impl()
        except Exception as _te:
            import traceback
            with open("/tmp/praxis_theme_err.log", "a") as _f:
                traceback.print_exc(file=_f)

    def _toggle_theme_impl(self) -> None:
        is_dark = ctk.get_appearance_mode().lower() == "dark"
        new_name = "light" if is_dark else "dark"
        new_theme = THEME_DARK if new_name == "dark" else THEME_LIGHT
        for k, v in new_theme.items():
            setattr(ConfigWindow, k, v)
        ctk.set_appearance_mode("Dark" if new_name == "dark" else "Light")

        self.cfg["theme"] = new_name
        save_cfg(self.cfg)

        # Para o polling do meter para não criar duas correntes após o rebuild
        if self._meter_poll_id:
            try: self.after_cancel(self._meter_poll_id)
            except Exception: pass
        self._meter_poll_id = None

        # Para o thread do meter
        self._meter_stop.set()
        if self._meter_proc:
            try: self._meter_proc.terminate()
            except Exception: pass
        self._meter_proc = None

        self._stop_ptt_config_listener()
        self._stop_engine(collapse=False)

        # Reconstrói a UI com as novas cores
        self.configure(fg_color=self.BG)
        self._main.destroy()

        # Limpa referências stale — widgets destruídos junto com _main
        self._meter_ids = {}
        self._meter_W   = 0
        self._meter_H   = 0
        for _attr in ("_gate_info_row", "_gate_info_row_kw", "_gate_pct_lbl",
                       "_meter_canvas", "_btn_vad", "_btn_gate", "_btn_ptt",
                       "_mode_cond", "_mode_cond_kw", "_ptt_info",
                       "_voice_menu", "_test_btn", "_theme_btn",
                       "_tab_seg", "_config_frame_outer", "_clone_frame_outer",
                       "_dl_card", "_dl_card_kw", "_dl_inner",
                       "_dl_progress", "_dl_pct_lbl", "_dl_status"):
            try: delattr(self, _attr)
            except AttributeError: pass

        self._build()
        self._refresh_devices(startup=True)

    def _on_close(self) -> None:
        self._stop_engine(collapse=False)
        self._meter_stop.set()
        if self._meter_proc:
            try:
                self._meter_proc.terminate()
            except Exception:
                pass
        if hasattr(self, "_stop_meter"):
            self._stop_meter()
        # Restaura PipeWire para rate automático ao fechar
        # Restore PipeWire to automatic rate on close
        subprocess.run(
            ["pw-metadata", "-n", "settings", "0", "clock.force-rate", "0"],
            capture_output=True, timeout=3
        )
        self.destroy()

    # ── Ícone e splash ────────────────────────────────────────────────────────

    def _create_loading_splash(self) -> "tuple[tk.Toplevel, ctk.CTkProgressBar, ctk.CTkLabel]":
        """Cria e exibe a splash de carregamento com logo + barra de progresso.
        Creates and shows the loading splash with logo + progress bar."""
        from PIL import Image, ImageTk  # lazy import / importação tardia

        WIDTH, LOGO_H = 420, 280
        BAR_H = 6

        ox, oy, sw, sh = _get_primary_monitor()
        if sw == 0:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            ox = oy = 0

        total_h = LOGO_H + 64  # logo + padding + label + barra
        x = ox + (sw - WIDTH) // 2
        y = oy + max(0, (sh - total_h) // 2)

        sp = tk.Toplevel(self)
        sp.overrideredirect(True)
        sp.configure(bg="#0D1117")
        sp.geometry(f"{WIDTH}x{total_h}+{x}+{y}")
        sp.lift()
        sp.attributes("-topmost", True)

        # Logo / imagem de topo
        splash_path = ASSETS_DIR / "praxis.png"
        if splash_path.exists():
            img = Image.open(splash_path).resize((WIDTH, LOGO_H), Image.LANCZOS)
            self._loading_photo = ImageTk.PhotoImage(img)
            tk.Label(sp, image=self._loading_photo, bg="#0D1117", bd=0).pack()
        else:
            tk.Label(sp, text="Praxis", font=("Segoe UI", 28, "bold"),
                     fg="white", bg="#0D1117").pack(pady=(LOGO_H // 2 - 20, 0))

        # Label de status / status label
        status_lbl = ctk.CTkLabel(
            sp, text="Iniciando…",
            font=ctk.CTkFont(size=12), text_color="#A1A1AA",
            fg_color="#0D1117"
        )
        status_lbl.pack(pady=(8, 4))

        # Barra de progresso / progress bar
        prog = ctk.CTkProgressBar(
            sp, width=WIDTH - 48, height=BAR_H,
            progress_color="#7C3AED", fg_color="#27272A",
            corner_radius=3
        )
        prog.set(0.05)
        prog.pack(padx=24, pady=(0, 16))

        sp.update_idletasks()
        return sp, prog, status_lbl

    def _set_window_icon(self) -> None:
        """Define o ícone da janela/barra de tarefas a partir de praxis.png."""
        try:
            from PIL import Image, ImageTk
            img = Image.open(ASSETS_DIR / "praxis.png").resize((64, 64), Image.LANCZOS)
            self._taskbar_icon = ImageTk.PhotoImage(img)
            self.wm_iconphoto(True, self._taskbar_icon)
        except Exception:
            pass

    def _show_splash(self) -> None:
        """Exibe splash screen centralizada com praxis.png, fecha após 2.4s."""
        try:
            from PIL import Image, ImageTk
        except ImportError:
            return

        splash_path = ASSETS_DIR / "praxis.png"
        if not splash_path.exists():
            return

        SIZE = 380
        ox, oy, sw, sh = _get_primary_monitor()
        if sw == 0:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            ox = oy = 0
        x = ox + (sw - SIZE) // 2
        y = oy + max(0, (sh - SIZE) // 2)

        splash = tk.Toplevel(self)
        splash.overrideredirect(True)           # sem borda/barra de título
        splash.configure(bg="#0D1117")
        splash.geometry(f"{SIZE}x{SIZE}+{x}+{y}")
        splash.lift()
        splash.attributes("-topmost", True)

        img = Image.open(splash_path).resize((SIZE, SIZE), Image.LANCZOS)
        self._splash_photo = ImageTk.PhotoImage(img)
        tk.Label(splash, image=self._splash_photo, bg="#0D1117", bd=0).pack()

        # Fade leve: reduz opacidade antes de fechar
        def _fade(alpha: float = 1.0) -> None:
            if alpha <= 0.0:
                splash.destroy()
                return
            try:
                splash.attributes("-alpha", alpha)
                splash.after(30, _fade, round(alpha - 0.08, 2))
            except Exception:
                pass

        splash.after(1900, _fade)   # começa o fade em 1.9s, fecha ~2.4s

    # ── Construção da UI ──────────────────────────────────────────────────────

    def _build(self) -> None:
        """Constrói toda a UI: painel esquerdo (config) + painel direito (monitoramento).
        Builds the full UI: left config panel + right monitoring panel."""
        # Contêiner principal: esquerda (config) + direita (monitoramento, oculta)
        self._main = ctk.CTkFrame(self, fg_color="transparent")
        self._main.pack(fill="both", expand=True)

        # PAINEL ESQUERDO — expande com a janela quando o painel de monitoramento está oculto
        # Left panel — expands with the window when the monitoring panel is hidden
        self._left = ctk.CTkFrame(self._main, fg_color=self.BG)
        self._left.pack(side="left", fill="both", expand=True)

        hdr = ctk.CTkFrame(self._left, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 10))

        _is_dark = ctk.get_appearance_mode().lower() == "dark"

        # Estrutura: [spacer 34px] [centro expand] [botão 34px]
        # O spacer espelha a largura do botão → centro fica geometricamente centrado
        _hdr_spacer = ctk.CTkFrame(hdr, fg_color="transparent", width=34, height=34)
        _hdr_spacer.pack(side="left")
        _hdr_spacer.pack_propagate(False)

        _hdr_right = ctk.CTkFrame(hdr, fg_color="transparent", width=34)
        _hdr_right.pack(side="right", anchor="n")
        _hdr_right.pack_propagate(False)

        self._theme_btn = ctk.CTkButton(
            _hdr_right, text="☀" if _is_dark else "☾",
            width=34, height=34,
            fg_color=self.ACCENT, hover_color=self.HOVER,
            text_color="#FFFFFF", border_width=0,
            corner_radius=17, font=ctk.CTkFont(size=15),
            command=self._toggle_theme,
        )
        self._theme_btn.pack()

        _hdr_center = ctk.CTkFrame(hdr, fg_color="transparent")
        _hdr_center.pack(side="left", fill="both", expand=True)

        # Logo centrada horizontalmente dentro do centro
        try:
            from PIL import Image
            _logo_file = "praxis_logo_white.png" if _is_dark else "praxis_logo_black.png"
            _logo_path = ASSETS_DIR / _logo_file
            if not _logo_path.exists():
                _logo_path = ASSETS_DIR / "praxis_logo.png"
            _logo_pil = Image.open(_logo_path).convert("RGBA")
            self._logo_img = ctk.CTkImage(
                light_image=_logo_pil, dark_image=_logo_pil, size=(110, 110))
            ctk.CTkLabel(_hdr_center, image=self._logo_img, text="").pack()
        except Exception:
            pass

        ctk.CTkLabel(
            _hdr_center,
            text="Uma mensagem. Todas as línguas.",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.MUTED,
        ).pack(pady=(6, 0))

        # ── Seletor de abas (sem CTkTabview — evita janela separada no Linux) ──
        # Tab selector using SegmentedButton (avoids CTkTabview opening a new window on Linux)
        self._tab_seg = ctk.CTkSegmentedButton(
            self._left,
            values=["⚙  Config", "🎙  Clonar minha voz"],
            fg_color=self.SEG_BG,
            selected_color=self.ACCENT,
            selected_hover_color=self.HOVER,
            unselected_color=self.SEG_BG,
            unselected_hover_color=self.IBORDER,
            text_color=self.TEXT,
            font=ctk.CTkFont(size=13),
            command=self._on_tab_change,
        )
        self._tab_seg.set("⚙  Config")
        self._tab_seg.pack(fill="x", padx=24, pady=(8, 0))

        # ── Frame container das abas (só um visível por vez) ─────────────────
        # Container for tab content — only one frame is visible at a time
        self._config_frame_outer = ctk.CTkFrame(self._left, fg_color="transparent")
        self._config_frame_outer.pack(fill="both", expand=True)

        self._clone_frame_outer = ctk.CTkFrame(self._left, fg_color="transparent")
        # Não empacotado ainda — aparece ao selecionar a aba / not packed yet

        # ── Aba Config ────────────────────────────────────────────────────────
        self._card = ctk.CTkScrollableFrame(
            self._config_frame_outer,
            fg_color="transparent",
            scrollbar_button_color=self.SEG_BG,
            scrollbar_button_hover_color=self.IBORDER,
        )
        self._card.pack(fill="both", expand=True)
        self._card.grid_columnconfigure((0, 1), weight=1)

        r = 0
        r = self._section(r, "Áudio", right_widget=self._make_refresh_btn())
        r = self._audio_section(r)
        r = self._sep(r)

        r = self._section(r, "Idiomas")
        r = self._idiomas(r)
        r = self._sep(r)

        r = self._section(r, "Modelo Whisper")
        r = self._whisper(r)
        r = self._sep(r)

        r = self._section(r, "Voz de saída",
                          right_widget=self._make_voice_header_btns())
        r = self._voice_field(r)
        r = self._sep(r)
        r = self._bilateral_section(r)

        # ── Aba Clonar minha voz ──────────────────────────────────────────────
        self._build_clone_tab(self._clone_frame_outer)

        # Detecta treino em andamento 500ms após a UI estar pronta
        # Detect in-progress training 500ms after UI is ready
        self.after(500, self._detect_existing_training)

        footer = ctk.CTkFrame(self._left, fg_color="transparent")
        footer.pack(fill="x", padx=24, pady=(4, 20))
        ctk.CTkButton(
            footer, text="Salvar", width=100, height=38,
            fg_color=self.SEG_BG, hover_color=self.IBORDER,
            text_color=self.TEXT, border_width=1, border_color=self.IBORDER,
            corner_radius=10, font=ctk.CTkFont(size=13),
            command=self._save,
        ).pack(side="left")
        self._iniciar_btn = ctk.CTkButton(
            footer, text="✦  Iniciar", height=38,
            fg_color=self.ACCENT, hover_color=self.HOVER,
            text_color="#FFFFFF", corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._launch,
        )
        self._iniciar_btn.pack(side="right")

        # PAINEL DIREITO — monitoramento, oculto até Iniciar, largura fixa 560px
        # Right panel — monitoring, hidden until Start, fixed 560px width
        self._right = ctk.CTkFrame(self._main, fg_color=self.BG,
                                    border_width=1, border_color=self.BORDER,
                                    width=560)
        self._right.pack_propagate(False)
        self._build_monitoring_ui()

    def _on_tab_change(self, value: str) -> None:
        """Alterna a aba visível entre Config e Clonar, mostrando/ocultando os frames.
        Switches the visible tab between Config and Clone by showing/hiding frames."""
        if "Config" in value:
            self._clone_frame_outer.pack_forget()
            self._config_frame_outer.pack(fill="both", expand=True)
        else:
            self._config_frame_outer.pack_forget()
            self._clone_frame_outer.pack(fill="both", expand=True)

    # ── Helpers do dashboard de treino ───────────────────────────────────────

    def _set_train_phase(self, phase: int, done: bool = False) -> None:
        """Atualiza os pills de fase (0=pré-proc, 1=extração, 2=treino).
        Updates phase pills (0=preproc, 1=extract, 2=train)."""
        names = ["Pré-proc", "Extração", "Treino"]
        for i, lbl in enumerate(self._dash_phases):
            if i < phase:
                lbl.configure(text=f"✓  {names[i]}", text_color="#22C55E")
            elif i == phase:
                icon, color = ("✓", "#22C55E") if done else ("●", "#F59E0B")
                lbl.configure(text=f"{icon}  {names[i]}", text_color=color)
            else:
                lbl.configure(text=f"○  {names[i]}", text_color=self.MUTED)

    @staticmethod
    def _parse_train_line(line: str, total: int = 300) -> dict | None:
        """Extrai métricas estruturadas de uma linha do train.py.
        Extracts structured metrics from a train.py stdout line.
        Retorna None se a linha não for uma linha de época / Returns None if not an epoch line."""
        import re
        if "epoch=" not in line:
            return None
        data: dict = {"total": total}
        for key, pat in [
            ("epoch",      r"epoch=(\d+)"),
            ("loss_gen",   r"smoothed_loss_gen=([\d.]+)"),
            ("loss_disc",  r"smoothed_loss_disc=([\d.]+)"),
            ("best_loss",  r"lowest_value=([\d.]+)"),
            ("best_epoch", r"lowest_value=[\d.]+\s*\(epoch\s+(\d+)"),
        ]:
            m = re.search(pat, line)
            if m:
                data[key] = float(m.group(1))
        # training_speed=0:00:21 → segundos / → seconds
        m = re.search(r"training_speed=(?:(\d+):)?(\d+):(\d+)", line)
        if m:
            h, mn, s = (int(x or 0) for x in m.groups())
            data["speed_s"] = h * 3600 + mn * 60 + s
        return data if "epoch" in data else None

    def _update_train_dashboard(self, data: dict) -> None:
        """Atualiza widgets do dashboard com métricas parseadas da linha de treino.
        Updates dashboard widgets with metrics parsed from a training line."""
        epoch = data.get("epoch")
        total = int(data.get("total", 300))

        if epoch is not None:
            epoch = int(epoch)
            self._dash_epoch_lbl.configure(text=f"{epoch} / {total}")
            pct = int(epoch / total * 100)
            self._dash_pct_lbl.configure(text=f"{pct}%")
            # Faixa de treino: 0.33 → 0.99 / Training range: 0.33 → 0.99
            self._train_prog.set(min(0.33 + 0.66 * epoch / total, 0.99))

        if "loss_gen" in data:
            self._dash_loss_gen.configure(text=f"{data['loss_gen']:.2f}")
        if "loss_disc" in data:
            self._dash_loss_disc.configure(text=f"{data['loss_disc']:.2f}")

        if "speed_s" in data and epoch is not None:
            spd = int(data["speed_s"])
            rem = (total - epoch) * spd
            self._dash_speed.configure(text=f"~{spd}s")
            if rem >= 3600:
                h, m = divmod(rem, 3600)
                self._dash_eta.configure(text=f"{h}h{m//60:02d}m")
            else:
                self._dash_eta.configure(text=f"{rem // 60}min")

        if "best_loss" in data and "best_epoch" in data:
            self._train_status.configure(
                text=f"✦ Melhor: época {int(data['best_epoch'])} · loss {data['best_loss']:.3f}",
                text_color=self.MUTED)

    def _detect_existing_training(self) -> None:
        """Escaneia /proc buscando train.py em execução; se achar, faz tail do log.
        Scans /proc for a running train.py; if found, tails its log into the UI."""
        import glob, os, re

        train_pid   = None
        model_name  = None
        total_epochs = 300

        # Percorre todos os cmdline de processos Python / scan all Python process cmdlines
        for cmdline_path in glob.glob("/proc/[0-9]*/cmdline"):
            try:
                raw = open(cmdline_path, "rb").read().replace(b"\x00", b" ").decode(errors="replace")
                if "train.py" not in raw:
                    continue
                # Primeiro argumento após train.py é o nome do modelo / first arg after train.py is model name
                m = re.search(r"train\.py\s+(\S+)", raw)
                if m:
                    model_name   = m.group(1)
                    train_pid    = int(cmdline_path.split("/")[2])
                    # Tenta extrair total_epoch da linha de comando / try to extract total_epoch from cmdline
                    ep_m = re.search(r"train\.py\s+\S+\s+\d+\s+(\d+)", raw)
                    if ep_m:
                        total_epochs = int(ep_m.group(1))
                    break
            except Exception:
                continue

        if not train_pid or not model_name:
            return  # Nenhum treino em andamento / no training in progress

        log_path = f"/tmp/rvc_train_{model_name}.log"
        if not os.path.exists(log_path):
            return

        # Treino detectado — atualiza UI e muda para aba Clonar
        # Training detected — update UI and switch to Clone tab
        self._training = True
        self._train_btn.configure(state="disabled", text="Treinando…")
        self._set_train_phase(2)  # Já está na fase de treino / already in training phase
        self._tab_seg.set("🎙  Clonar minha voz")
        self._on_tab_change("🎙  Clonar minha voz")

        import threading
        t = threading.Thread(
            target=self._tail_log_worker,
            args=(log_path, train_pid, total_epochs),
            daemon=True,
        )
        t.start()

    def _tail_log_worker(self, log_path: str, pid: int, total_epochs: int) -> None:
        """Thread que faz tail do arquivo de log existente e alimenta o dashboard visual.
        Thread that tails an existing log file and feeds the visual training dashboard."""
        import os, time

        # Fase de treino já em andamento ao detectar processo externo
        # Training phase already in progress when external process detected
        self.after(0, self._set_train_phase, 2)

        # Carrega última linha de época do histórico para popular o dashboard imediatamente
        # Load last epoch line from history to populate dashboard immediately
        def _load_from_history():
            try:
                with open(log_path, "r", errors="replace") as f:
                    lines = f.readlines()
                for ln in reversed(lines):
                    parsed = self._parse_train_line(ln, total=total_epochs)
                    if parsed:
                        self._update_train_dashboard(parsed)
                        break
            except Exception:
                pass
        self.after(0, _load_from_history)

        # Tail em tempo real / real-time tail
        with open(log_path, "r", errors="replace") as f:
            f.seek(0, 2)
            while True:
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    break
                line = f.readline()
                if not line:
                    time.sleep(0.5)
                    continue
                parsed = self._parse_train_line(line, total=total_epochs)
                if parsed:
                    self.after(0, self._update_train_dashboard, parsed)

        # Processo terminou / process ended
        self._training = False
        self.after(0, self._set_train_phase, 2, True)
        self.after(0, self._train_prog.set, 1.0)
        self.after(0, self._train_status.configure,
                   {"text": "✅ Treino concluído!", "text_color": "#22C55E"})
        self.after(0, self._train_btn.configure,
                   {"state": "normal", "text": "🎙 Treinar Voz"})

    def _idiomas(self, r: int) -> int:
        """Seção de seleção de idiomas (fala → traduz para). Returns next grid row.
        Language selection section (speaks → translates to). Returns next grid row."""
        card = self._card
        ctk.CTkLabel(card, text="Você fala",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self.MUTED).grid(row=r, column=0, sticky="w",
                                                  padx=20, pady=(0, 4))
        ctk.CTkLabel(card, text="Traduz para",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self.MUTED).grid(row=r, column=1, sticky="w",
                                                  padx=20, pady=(0, 4))
        r += 1
        self.src_var = ctk.StringVar(value=lang_label(self.cfg["src"]))
        # destino: apenas idiomas com voz disponível no catálogo ou instalada
        _tgt_pairs  = _tgt_langs_with_voices()
        _tgt_labels = [f"{n}  ({c})" for c, n in _tgt_pairs]
        self._tgt_pairs = _tgt_pairs
        saved_tgt = lang_label(self.cfg["tgt"])
        if saved_tgt not in _tgt_labels:
            saved_tgt = _tgt_labels[0]
        self.tgt_var = ctk.StringVar(value=saved_tgt)
        self.tgt_var.trace_add("write", lambda *_: self.after(0, self._on_tgt_change))
        self.src_var.trace_add("write", lambda *_: self.after(0, self._on_src_change))
        self._optmenu(card, r, 0, LANG_LABELS, self.src_var, pr=8)
        self._optmenu(card, r, 1, _tgt_labels, self.tgt_var, pl=8)
        return r + 1

    def _whisper(self, r: int) -> int:
        """Seção de seleção do modelo Whisper (tiny/base/small/medium/large-v2).
        Whisper model selection section."""
        self.model_var = ctk.StringVar(value=self.cfg["model"])
        ctk.CTkSegmentedButton(
            self._card, values=MODELS, variable=self.model_var,
            fg_color=self.SEG_BG,
            selected_color=self.ACCENT, selected_hover_color=self.HOVER,
            unselected_color=self.SEG_BG, unselected_hover_color=self.IBORDER,
            text_color=self.MUTED, font=ctk.CTkFont(size=12),
        ).grid(row=r, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 16))
        return r + 1

    def _audio_section(self, r: int) -> int:
        """Seção de áudio: modo, microfone, VU meter, saída e monitor.
        Audio section: mode, microphone, VU meter, output and monitor."""
        card = self._card

        # 1. Modos de funcionamento (primeiro, antes dos dispositivos)
        r = self._mode_section(r)

        # 2. Entrada (microfone)
        ctk.CTkLabel(card, text="Entrada  (microfone)",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self.MUTED).grid(row=r, column=0, columnspan=2,
                                                  sticky="w", padx=20, pady=(0, 4))
        r += 1
        self.mic_var   = ctk.StringVar(value="(padrão do sistema)")
        self._mic_menu = ctk.CTkOptionMenu(
            card, values=["(padrão do sistema)"], variable=self.mic_var,
            fg_color=self.INPUT, button_color=self.IBORDER,
            button_hover_color=self.SEG_BG, text_color=self.TEXT,
            dropdown_fg_color=self.CARD, dropdown_text_color=self.TEXT,
            dropdown_hover_color=self.SEG_BG, font=ctk.CTkFont(size=13),
        )
        self._mic_menu.configure(command=self._on_mic_change)
        self._mic_menu.grid(row=r, column=0, columnspan=2, sticky="ew",
                            padx=20, pady=(0, 8))
        r += 1

        # 3. VU Meter
        r = self._build_meter(r)

        # 4. Barra de gate (abaixo do meter, visível só no modo gate)
        r = self._build_gate_bar(r)

        # 5. Saída (fones / caixas)
        ctk.CTkLabel(card, text="Saída  (fones / caixas)",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self.MUTED).grid(row=r, column=0, columnspan=2,
                                                  sticky="w", padx=20, pady=(0, 4))
        r += 1
        self.out_var   = ctk.StringVar(value="(padrão do sistema)")
        self._out_menu = ctk.CTkOptionMenu(
            card, values=["(padrão do sistema)"], variable=self.out_var,
            fg_color=self.INPUT, button_color=self.IBORDER,
            button_hover_color=self.SEG_BG, text_color=self.TEXT,
            dropdown_fg_color=self.CARD, dropdown_text_color=self.TEXT,
            dropdown_hover_color=self.SEG_BG, font=ctk.CTkFont(size=13),
        )
        self._out_menu.grid(row=r, column=0, columnspan=2, sticky="ew",
                            padx=20, pady=(0, 16))
        r += 1

        # 6. Monitor toggle
        self._mon_btn = ctk.CTkButton(
            card,
            text="● Monitor ativo" if self._monitor else "○ Monitor desligado",
            height=38, corner_radius=10,
            fg_color=self.MON_ON if self._monitor else self.MON_OFF,
            hover_color=self.HOVER if self._monitor else self.IBORDER,
            text_color="#FFFFFF" if self._monitor else self.MUTED,
            border_width=1, border_color=self.IBORDER,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._toggle_monitor,
        )
        self._mon_btn.grid(row=r, column=0, columnspan=2, sticky="ew",
                           padx=20, pady=(0, 4))
        r += 1
        ctk.CTkLabel(
            card, text="Ouvir a tradução na saída selecionada acima",
            font=ctk.CTkFont(size=11), text_color=self.MUTED,
        ).grid(row=r, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 18))
        r += 1

        return r

    def _build_gate_bar(self, r: int) -> int:
        """Gate threshold agora está integrado dentro do VU meter — não consome linha."""
        self._gate_bar_W  = 0
        self._gate_bar_H  = 0
        self._gate_bar_ids: dict = {}
        return r  # sem widget separado; threshold fica no meter canvas

        # ── código da barra separada desativado ──────────────────────────────
        self._gate_bar_frame = ctk.CTkFrame(
            self._card, fg_color=self.CARD,
            border_width=1, border_color=self.IBORDER, corner_radius=6,
        )
        self._gate_bar_frame.grid(row=r, column=0, columnspan=2,
                                   sticky="ew", padx=20, pady=(0, 8))

        top = ctk.CTkFrame(self._gate_bar_frame, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(7, 2))
        ctk.CTkLabel(top, text="SENSIBILIDADE DE ENTRADA",
                     font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=self.MUTED).pack(side="left")
        self._gate_pct_lbl = ctk.CTkLabel(top, text=f"{int(self._gate_frac*100)}%",
                                            font=ctk.CTkFont(size=9, weight="bold"),
                                            text_color=self.ACCENT)
        self._gate_pct_lbl.pack(side="right")

        # Canvas com fundo do card; os itens desenhados definem a aparência
        self._gate_canvas = tk.Canvas(
            self._gate_bar_frame, height=30, bg=self.CARD,
            highlightthickness=0, bd=0, cursor="sb_h_double_arrow",
        )
        self._gate_canvas.pack(fill="x", expand=True, padx=10, pady=(0, 10))
        self._gate_canvas.bind("<Configure>",       self._gate_bar_configure)
        self._gate_canvas.bind("<ButtonPress-1>",   self._gate_press)
        self._gate_canvas.bind("<B1-Motion>",       self._gate_drag)
        self._gate_canvas.bind("<ButtonRelease-1>", self._gate_release)

        self._gate_bar_frame.grid_remove()
        return r + 1

    def _gate_bar_configure(self, event: tk.Event) -> None:
        W, H = event.width, event.height
        if W < 2:
            return
        self._gate_bar_W = W
        self._gate_bar_H = H
        self._gate_bar_init()

    def _gate_bar_init(self) -> None:
        """Cria os itens do canvas uma única vez; atualizações apenas movem coords."""
        W, H = self._gate_bar_W, self._gate_bar_H
        c = self._gate_canvas
        c.delete("all")
        pad = 9  # margem vertical da trilha
        r   = 4  # raio do arredondamento da trilha (simulado com oval+rect)

        # Trilha cinza de fundo
        c.create_rectangle(0, pad, W, H - pad, fill="#E5E7EB", outline="", tags="track")

        # Preenchimento verde (nível de áudio) — largura inicial 0
        c.create_rectangle(0, pad, 0, H - pad, fill="#22C55E", outline="", tags="fill")

        # Sombra do handle (mais larga, cor escura)
        tx = int(self._gate_frac * W)
        c.create_line(tx, pad - 4, tx, H - pad + 4,
                      fill="#6B7280", width=5, tags="handle_shadow")
        # Handle branco
        c.create_line(tx, pad - 4, tx, H - pad + 4,
                      fill="#FFFFFF", width=3, tags="handle")
        # Círculo central no handle
        c.create_oval(tx - 5, H // 2 - 5, tx + 5, H // 2 + 5,
                      fill="#FFFFFF", outline="#D1D5DB", width=1, tags="knob")

        self._gate_bar_ids = {"ready": True}

    def _gate_bar_update_level(self, level: float) -> None:
        """Atualiza o preenchimento verde com o nível de áudio atual."""
        W, H = self._gate_bar_W, self._gate_bar_H
        if not W or not self._gate_bar_ids.get("ready"):
            return
        pad = 9
        level_x = int(min(level / 0.28, 1.0) * W)
        self._gate_canvas.coords("fill", 0, pad, level_x, H - pad)

    # ── VU Meter ──────────────────────────────────────────────────────────────

    def _build_meter(self, r: int) -> int:
        """Constrói o canvas do VU meter na aba de configuração. Returns next grid row.
        Builds the VU meter canvas in the config tab. Returns next grid row."""
        self._meter_level  = 0.0
        self._meter_peak   = 0.0
        self._meter_q: "queue.Queue[float]" = queue.Queue(maxsize=20)
        self._meter_proc   = None
        self._meter_stop   = threading.Event()
        self._meter_ids: dict = {}
        self._meter_W      = 0
        self._meter_H      = 0
        self._meter_poll_id = None

        meter_frame = ctk.CTkFrame(
            self._card, fg_color=self.CARD,
            border_width=1, border_color=self.IBORDER, corner_radius=6,
        )
        meter_frame.grid(row=r, column=0, columnspan=2,
                         sticky="ew", padx=20, pady=(0, 8))

        self._meter_canvas = tk.Canvas(
            meter_frame, height=14, bg=self.CARD,
            highlightthickness=0, bd=0,
        )
        self._meter_canvas.pack(fill="x", expand=True, padx=2, pady=2)
        self._meter_canvas.bind("<Configure>", self._meter_configure)

        # Linha de info do gate — FORA da caixa do meter, na row seguinte do card
        # Visível apenas quando modo Gate está ativo
        self._gate_info_row = ctk.CTkFrame(self._card, fg_color="transparent")
        ctk.CTkLabel(self._gate_info_row, text="GATE THRESHOLD",
                     font=ctk.CTkFont(size=9, weight="bold"),
                     text_color=self.MUTED).pack(side="left")
        self._gate_pct_lbl = ctk.CTkLabel(self._gate_info_row,
                                            text=f"{int(self._gate_frac*100)}%",
                                            font=ctk.CTkFont(size=9, weight="bold"),
                                            text_color=self.ACCENT)
        self._gate_pct_lbl.pack(side="right")
        _gi_kw = dict(row=r + 1, column=0, columnspan=2,
                      sticky="ew", padx=20, pady=(2, 8))
        self._gate_info_row_kw = _gi_kw
        self._gate_info_row.grid(**_gi_kw)
        self._gate_info_row.grid_remove()  # oculta por padrão

        self._start_meter_thread()
        self._meter_poll()
        return r + 2  # consome 2 linhas: meter + gate_info

    def _meter_configure(self, event: tk.Event) -> None:
        """Renderiza gradiente uma vez; cria máscara e pico."""
        W, H = event.width, event.height
        if W < 2:
            return
        self._meter_W = W
        self._meter_H = H
        c = self._meter_canvas
        c.delete("all")

        GREEN  = (34,  197,  94)
        YELLOW = (234, 179,   8)
        RED    = (239,  68,  68)

        for i in range(W):
            frac = i / W
            if frac < 0.65:
                t  = frac / 0.65
                r2 = int(GREEN[0]  + (YELLOW[0] - GREEN[0])  * t)
                g2 = int(GREEN[1]  + (YELLOW[1] - GREEN[1])  * t)
                b2 = int(GREEN[2]  + (YELLOW[2] - GREEN[2])  * t)
            else:
                t  = (frac - 0.65) / 0.35
                r2 = int(YELLOW[0] + (RED[0] - YELLOW[0]) * t)
                g2 = int(YELLOW[1] + (RED[1] - YELLOW[1]) * t)
                b2 = int(YELLOW[2] + (RED[2] - YELLOW[2]) * t)
            c.create_line(i, 0, i, H, fill=f"#{r2:02x}{g2:02x}{b2:02x}")

        # Máscara cobre a parte não preenchida (cor do card para funcionar em dark/light)
        self._meter_ids["mask"] = c.create_rectangle(
            0, 0, W, H, fill=self.CARD, outline=""
        )
        # Linha de pico
        self._meter_ids["peak"] = c.create_line(
            0, 0, 0, H, fill=self.CARD, width=2
        )
        # Marcador de gate threshold — criado sobre a máscara para ser sempre visível
        tx = int(getattr(self, "_gate_frac", 0.0) * W)
        is_gate = getattr(self, "_mode_var", None) and self._mode_var.get() == "gate"
        _gs = "normal" if is_gate else "hidden"
        self._meter_ids["gate_shadow"] = c.create_line(
            tx, 0, tx, H, fill="#1F2937", width=5, state=_gs)
        self._meter_ids["gate_line"] = c.create_line(
            tx, 0, tx, H, fill="#FFFFFF", width=2, state=_gs)

    def _get_meter_device(self) -> str | None:
        """Devolve o nome PA da fonte selecionada, sem sufixo :left/:right."""
        label = self.mic_var.get()
        if label.startswith("("):
            return None
        name = self._label_to_name(label, self._inputs)
        if not name:
            return None
        return name.split(":")[0]   # remove :left / :right

    def _start_meter_thread(self) -> None:
        self._meter_stop.clear()
        if self._meter_proc:
            try:
                self._meter_proc.terminate()
            except Exception:
                pass
            self._meter_proc = None

        device = self._get_meter_device()
        cmd = ["parec", "--format=s16le", "--rate=48000", "--channels=2",
               "--latency-msec=5"]
        if device:
            cmd.append(f"--device={device}")

        try:
            self._meter_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        except Exception:
            return

        def _reader():
            frames     = 128                 # ~2.7 ms por chunk a 48 kHz
            chunk_sz   = frames * 2 * 2      # stereo s16le = 4 bytes/frame
            proc       = self._meter_proc
            stop       = self._meter_stop
            q          = self._meter_q
            fd         = proc.stdout.fileno()
            env        = 0.0
            rate       = 48000
            att  = 1.0 - np.exp(-1.0 / (0.003 * rate / frames))
            rel  = 1.0 - np.exp(-1.0 / (0.120 * rate / frames))

            while not stop.is_set():
                data = proc.stdout.read(chunk_sz)
                if not data:
                    break

                # Drena buffer acumulado → usa só o chunk mais recente
                while True:
                    ready, _, _ = select.select([fd], [], [], 0)
                    if not ready:
                        break
                    extra = os.read(fd, chunk_sz)
                    if not extra:
                        break
                    data = extra

                arr = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                if len(arr) >= 2:
                    mono = np.maximum(np.abs(arr[0::2]), np.abs(arr[1::2]))
                    rms  = float(np.sqrt(np.mean(mono ** 2)))
                else:
                    rms = 0.0

                if rms > env:
                    env += att * (rms - env)
                else:
                    env += rel * (rms - env)

                if q.full():
                    try: q.get_nowait()
                    except queue.Empty: pass
                try: q.put_nowait(env)
                except queue.Full: pass

        threading.Thread(target=_reader, daemon=True).start()

    def _on_mic_change(self, _=None) -> None:
        self._start_meter_thread()

    def _meter_poll(self) -> None:
        # Pega o valor mais recente da fila (o envelope já vem suavizado)
        latest = None
        try:
            while True:
                latest = self._meter_q.get_nowait()
        except queue.Empty:
            pass

        if latest is not None:
            self._meter_level = latest

        self._meter_peak = max(self._meter_peak * 0.992, self._meter_level)

        self._meter_draw()
        self._meter_poll_id = self.after(16, self._meter_poll)

    def _meter_draw(self) -> None:
        if not self._meter_ids or not self._meter_W:
            return
        W = self._meter_W
        H = self._meter_H

        level_x = int(min(self._meter_level / 0.28, 1.0) * W)
        peak_x  = int(min(self._meter_peak  / 0.28, 1.0) * W)

        c = self._meter_canvas
        c.coords(self._meter_ids["mask"], level_x, 0, W, H)
        c.coords(self._meter_ids["peak"], peak_x, 0, peak_x, H)

        # Mantém posição do marcador de gate atualizada (visível só quando gate ativo)
        if "gate_line" in self._meter_ids:
            tx = int(self._gate_frac * W)
            c.coords(self._meter_ids["gate_shadow"], tx, 0, tx, H)
            c.coords(self._meter_ids["gate_line"],   tx, 0, tx, H)

    # ── Gate drag handlers ────────────────────────────────────────────────────

    def _gate_press(self, event) -> None:
        self._gate_dragging = True

    def _gate_drag(self, event) -> None:
        if not self._gate_dragging or not self._meter_W:
            return
        self._gate_frac = max(0.0, min(1.0, event.x / self._meter_W))
        # A posição do marcador é atualizada por _meter_draw a cada frame
        if hasattr(self, "_gate_pct_lbl"):
            self._gate_pct_lbl.configure(text=f"{int(self._gate_frac*100)}%")

    def _gate_release(self, event) -> None:
        self._gate_dragging = False

    # ── Modo de ativação (VAD / Gate / PTT) ───────────────────────────────────

    def _mode_section(self, row: int) -> int:
        """Seção de seleção de modo de operação (VAD / Gate / PTT).
        Operation mode selection section (VAD / Gate / PTT)."""
        # Três botões de modo no topo
        btn_frame = ctk.CTkFrame(self._card, fg_color="transparent")
        btn_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(4, 6))
        btn_frame.grid_columnconfigure((0, 1, 2), weight=1)
        row += 1

        kw_idle   = dict(height=28, fg_color=self.SEG_BG, hover_color=self.IBORDER,
                         text_color=self.MUTED, border_width=1, border_color=self.IBORDER,
                         corner_radius=8, font=ctk.CTkFont(size=11))
        kw_active = dict(height=28, fg_color=self.ACCENT, hover_color=self.HOVER,
                         text_color="#FFFFFF", border_width=0, border_color=self.ACCENT,
                         corner_radius=8, font=ctk.CTkFont(size=11))

        def _make_btn(label, value):
            btn = ctk.CTkButton(btn_frame, text=label,
                                command=lambda v=value: self._set_mode(v),
                                **(kw_active if self._mode_var.get() == value else kw_idle))
            return btn

        self._btn_vad  = _make_btn("VAD automático",  "vad")
        self._btn_gate = _make_btn("Gate threshold",   "gate")
        self._btn_ptt  = _make_btn("Push-to-talk",     "ptt")
        self._btn_vad .grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self._btn_gate.grid(row=0, column=1, sticky="ew", padx=(0, 4))
        self._btn_ptt .grid(row=0, column=2, sticky="ew")

        # Frame condicional — PTT config (gate usa barra própria abaixo do meter)
        self._mode_cond = ctk.CTkFrame(self._card, fg_color="transparent")
        _mc_kw = dict(row=row, column=0, columnspan=2, sticky="ew", padx=20)
        self._mode_cond_kw = _mc_kw
        self._mode_cond.grid(**_mc_kw)
        row += 1

        # Sub-frame PTT
        self._ptt_info = ctk.CTkFrame(self._mode_cond, fg_color="transparent")
        ptt_row = ctk.CTkFrame(self._ptt_info, fg_color="transparent")
        ptt_row.pack(fill="x", pady=(2, 6))
        self._ptt_key_lbl = ctk.CTkLabel(
            ptt_row,
            text=self._ptt_key if self._ptt_key else "(nenhum configurado)",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.TEXT,
        )
        self._ptt_key_lbl.pack(side="left", padx=(0, 12))
        ctk.CTkButton(
            ptt_row, text="Configurar botão", width=140, height=28,
            fg_color=self.SEG_BG, hover_color=self.IBORDER,
            text_color=self.MUTED, border_width=1, border_color=self.IBORDER,
            corner_radius=8, font=ctk.CTkFont(size=11),
            command=self._capture_ptt_key,
        ).pack(side="left")

        self._update_mode_ui()
        # Inicia listener PTT se já há tecla configurada ao abrir a janela
        if self._mode_var.get() == "ptt" and self._ptt_key:
            self._start_ptt_config_listener(self._ptt_key)
        return row

    def _set_mode(self, mode: str) -> None:
        """Altera o modo de operação do motor (vad/gate/ptt) e atualiza a UI.
        Changes the engine operation mode (vad/gate/ptt) and updates the UI."""
        self._mode_var.set(mode)
        if mode == "ptt" and self._ptt_key:
            self._start_ptt_config_listener(self._ptt_key)
        else:
            self._stop_ptt_config_listener()
        self._update_mode_ui()

    # ── Meter ativo/cinza (PTT feedback na config) ────────────────────────────

    def _meter_set_active(self, active: bool) -> None:
        """Redesenha o gradiente do meter: colorido (ativo) ou cinza (PTT inativo)."""
        self._meter_active = active
        if hasattr(self, "_meter_canvas") and self._meter_W > 0:
            c = self._meter_canvas
            W, H = self._meter_W, self._meter_H
            c.delete("all")
            if active:
                GREEN  = (34,  197,  94)
                YELLOW = (234, 179,   8)
                RED    = (239,  68,  68)
            else:
                GREEN  = (180, 180, 180)
                YELLOW = (150, 150, 150)
                RED    = (120, 120, 120)
            for i in range(W):
                frac = i / W
                if frac < 0.65:
                    t = frac / 0.65
                    r2 = int(GREEN[0] + (YELLOW[0]-GREEN[0])*t)
                    g2 = int(GREEN[1] + (YELLOW[1]-GREEN[1])*t)
                    b2 = int(GREEN[2] + (YELLOW[2]-GREEN[2])*t)
                else:
                    t = (frac-0.65)/0.35
                    r2 = int(YELLOW[0] + (RED[0]-YELLOW[0])*t)
                    g2 = int(YELLOW[1] + (RED[1]-YELLOW[1])*t)
                    b2 = int(YELLOW[2] + (RED[2]-YELLOW[2])*t)
                c.create_line(i, 0, i, H, fill=f"#{r2:02x}{g2:02x}{b2:02x}")
            mask_color = self.CARD
            self._meter_ids["mask"] = c.create_rectangle(0, 0, W, H,
                                                           fill=mask_color, outline="")
            self._meter_ids["peak"] = c.create_line(0, 0, 0, H,
                                                     fill=mask_color, width=2)
            # Recria marcador de gate (perdido ao deletar o canvas)
            tx = int(self._gate_frac * W)
            is_gate = self._mode_var.get() == "gate"
            _gs = "normal" if is_gate else "hidden"
            self._meter_ids["gate_shadow"] = c.create_line(
                tx, 0, tx, H, fill="#1F2937", width=5, state=_gs)
            self._meter_ids["gate_line"] = c.create_line(
                tx, 0, tx, H, fill="#FFFFFF", width=2, state=_gs)

    def _start_ptt_config_listener(self, key_str: str) -> None:
        """Listener na janela de config: detecta PTT pressionado e coloriza meter."""
        self._stop_ptt_config_listener()
        if not key_str:
            return
        from pynput import keyboard as _kb, mouse as _ms
        kind, name = key_str.split(":", 1) if ":" in key_str else ("keyboard", key_str)
        if kind == "mouse":
            ptt_btn = getattr(_ms.Button, name, None)
            if not ptt_btn:
                return
            def _on_click(x, y, button, pressed):
                if button == ptt_btn:
                    self.after(0, self._meter_set_active, pressed)
            self._ptt_cfg_listener = _ms.Listener(on_click=_on_click, daemon=True)
        else:
            ptt_key = getattr(_kb.Key, name, None) or _kb.KeyCode.from_char(name)
            def _on_press(key):
                if key == ptt_key:
                    self.after(0, self._meter_set_active, True)
            def _on_release(key):
                if key == ptt_key:
                    self.after(0, self._meter_set_active, False)
            self._ptt_cfg_listener = _kb.Listener(
                on_press=_on_press, on_release=_on_release, daemon=True)
        self._ptt_cfg_listener.start()

    def _stop_ptt_config_listener(self) -> None:
        lst = getattr(self, "_ptt_cfg_listener", None)
        if lst:
            try: lst.stop()
            except Exception: pass
        self._ptt_cfg_listener = None

    # ── UI de monitoramento (painel direito) ──────────────────────────────────

    def _build_monitoring_ui(self) -> None:
        """Constrói o painel direito de monitoramento (transcrição, tradução, logs).
        Builds the right monitoring panel (transcript, translation, logs)."""
        GREEN = "#22C55E"
        AMBER = "#F59E0B"
        RED   = "#EF4444"

        # Status bar
        top = ctk.CTkFrame(self._right, fg_color=self.CARD,
                           border_width=1, border_color=self.BORDER,
                           corner_radius=10)
        top.pack(fill="x", padx=16, pady=(16, 10))

        row1 = ctk.CTkFrame(top, fg_color="transparent", height=42)
        row1.pack(fill="x")
        row1.pack_propagate(False)

        self._mon_dot = ctk.CTkLabel(row1, text="●", font=ctk.CTkFont(size=16),
                                      text_color=AMBER)
        self._mon_dot.pack(side="left", padx=(14, 6))

        self._mon_status = ctk.CTkLabel(row1, text="Iniciando…",
                                         font=ctk.CTkFont(size=13),
                                         text_color="#374151")
        self._mon_status.pack(side="left")

        ctk.CTkButton(row1, text="Parar", width=80, height=30,
                      fg_color=RED, hover_color="#DC2626",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._stop_engine).pack(side="right", padx=12)

        # Barra de progresso
        self._mon_prog_frame = ctk.CTkFrame(top, fg_color="transparent", height=18)
        self._mon_prog_frame.pack(fill="x", padx=14, pady=(0, 10))
        self._mon_prog_bar = ctk.CTkProgressBar(self._mon_prog_frame, height=6,
                                                  corner_radius=3,
                                                  progress_color=AMBER,
                                                  fg_color=self.BORDER)
        self._mon_prog_bar.pack(fill="x")
        self._mon_prog_bar.set(0)

        # Painéis de transcrição
        body = ctk.CTkFrame(self._right, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(0, 4))
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._orig_box  = self._make_mon_panel(body, 0, "Você está dizendo")
        self._trans_box = self._make_mon_panel(body, 1, "Sendo enviado")

        # Log
        log_card = ctk.CTkFrame(self._right, fg_color=self.CARD,
                                 border_width=1, border_color=self.BORDER,
                                 corner_radius=10, height=90)
        log_card.pack(fill="x", padx=16, pady=(0, 12))
        log_card.pack_propagate(False)
        ctk.CTkLabel(log_card, text="Log", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self.MUTED).pack(anchor="w", padx=12, pady=(6, 2))
        self._log_box = ctk.CTkTextbox(log_card, fg_color=self.CARD,
                                        font=ctk.CTkFont(size=10, family="Monospace"),
                                        border_width=0, wrap="none",
                                        state="disabled", height=60)
        self._log_box.pack(fill="both", expand=True, padx=8, pady=(0, 6))

    def _make_mon_panel(self, parent, col: int, title: str) -> ctk.CTkTextbox:
        pad = (0, 8) if col == 0 else (8, 0)
        card = ctk.CTkFrame(parent, fg_color=self.CARD,
                             border_width=1, border_color=self.BORDER,
                             corner_radius=12)
        card.grid(row=0, column=col, sticky="nsew", padx=pad)
        ctk.CTkLabel(card, text=title,
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=self.MUTED).pack(anchor="w", padx=16, pady=(14, 4))
        ctk.CTkFrame(card, fg_color=self.BORDER, height=1).pack(fill="x", padx=16)
        box = ctk.CTkTextbox(card, fg_color=self.CARD,
                              font=ctk.CTkFont(size=15), border_width=0,
                              wrap="word", state="disabled")
        box.pack(fill="both", expand=True, padx=12, pady=(8, 12))
        return box

    def _update_mode_ui(self) -> None:
        mode = self._mode_var.get()
        kw_idle   = dict(fg_color=self.SEG_BG,  text_color=self.MUTED, hover_color=self.IBORDER,
                         border_width=1, border_color=self.IBORDER)
        kw_active = dict(fg_color=self.ACCENT,  text_color="#FFFFFF",  hover_color=self.HOVER,
                         border_width=0, border_color=self.ACCENT)
        for btn, val in [(self._btn_vad,"vad"),(self._btn_gate,"gate"),(self._btn_ptt,"ptt")]:
            btn.configure(**(kw_active if mode == val else kw_idle))

        # Mostra/oculta sub-frame PTT (e o container inteiro para não deixar vão)
        for w in self._mode_cond.winfo_children():
            w.pack_forget()
        if mode == "ptt":
            self._ptt_info.pack(fill="x")
            self._mode_cond.grid(**self._mode_cond_kw)
        else:
            self._mode_cond.grid_remove()

        # Gate: mostra marcador dentro do meter + info row + bind drag
        is_gate = (mode == "gate")
        if hasattr(self, "_meter_ids"):
            for tag in ("gate_shadow", "gate_line"):
                if tag in self._meter_ids:
                    self._meter_canvas.itemconfigure(
                        self._meter_ids[tag], state="normal" if is_gate else "hidden")
        _gi = getattr(self, "_gate_info_row", None)
        if _gi is not None:
            if is_gate:
                _gi.grid(**self._gate_info_row_kw)
            else:
                _gi.grid_remove()
        if hasattr(self, "_meter_canvas"):
            if is_gate:
                self._meter_canvas.configure(cursor="sb_h_double_arrow")
                self._meter_canvas.bind("<ButtonPress-1>",   self._gate_press)
                self._meter_canvas.bind("<B1-Motion>",       self._gate_drag)
                self._meter_canvas.bind("<ButtonRelease-1>", self._gate_release)
            else:
                self._meter_canvas.configure(cursor="")
                self._meter_canvas.unbind("<ButtonPress-1>")
                self._meter_canvas.unbind("<B1-Motion>")
                self._meter_canvas.unbind("<ButtonRelease-1>")

        # PTT: meter fica cinza quando botão não está pressionado
        self._meter_set_active(mode != "ptt")

    def _capture_ptt_key(self) -> None:
        """Aguarda próxima tecla ou botão do mouse e salva como PTT."""
        self._ptt_key_lbl.configure(text="Pressione qualquer tecla ou botão do mouse…")
        captured = []

        def _done(key_str: str) -> None:
            if captured:
                return
            captured.append(key_str)
            self._ptt_key = key_str
            self.after(0, lambda: self._ptt_key_lbl.configure(text=key_str))
            # Inicia listener de feedback imediatamente após configurar a tecla
            self.after(0, lambda: self._start_ptt_config_listener(key_str))
            try: kl.stop()
            except Exception: pass
            try: ml.stop()
            except Exception: pass

        from pynput import keyboard as _kb, mouse as _ms

        def _on_key(key):
            try:
                _done(f"keyboard:{key.name}")
            except AttributeError:
                pass
            return False

        def _on_click(x, y, button, pressed):
            if pressed:
                _done(f"mouse:{button.name}")
                return False

        kl = _kb.Listener(on_press=_on_key, daemon=True)
        ml = _ms.Listener(on_click=_on_click, daemon=True)
        kl.start()
        ml.start()

    # ── Helpers de layout ─────────────────────────────────────────────────────

    def _section(self, row: int, title: str,
                 right_widget: ctk.CTkBaseClass | None = None) -> int:
        frame = ctk.CTkFrame(self._card, fg_color="transparent")
        frame.grid(row=row, column=0, columnspan=2, sticky="ew",
                   padx=20, pady=(18, 8))
        frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(frame, text=title.upper(),
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=self.MUTED).grid(row=0, column=0, sticky="w")
        if right_widget:
            right_widget.grid(row=0, column=1, sticky="e", in_=frame)
            frame.grid_columnconfigure(1, weight=0)
        return row + 1

    def _sep(self, row: int) -> int:
        ctk.CTkFrame(self._card, height=1, fg_color="#EAECF0").grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=16, pady=4)
        return row + 1

    def _optmenu(self, parent, row: int, col: int,
                 values: list[str], var: ctk.StringVar,
                 pl: int = 20, pr: int = 20) -> None:
        ctk.CTkOptionMenu(
            parent, values=values, variable=var,
            fg_color=self.INPUT, button_color=self.IBORDER,
            button_hover_color=self.SEG_BG, text_color=self.TEXT,
            dropdown_fg_color=self.CARD, dropdown_text_color=self.TEXT,
            dropdown_hover_color=self.SEG_BG, font=ctk.CTkFont(size=13),
        ).grid(row=row, column=col, sticky="ew", padx=(pl, pr), pady=(0, 12))

    def _voice_field(self, row: int) -> int:
        self._voices: list[tuple[str, str]] = get_voices()
        tgt_code = self._tgt_code()
        filtered = _voices_for_lang(self._voices, tgt_code)
        labels = [lbl for _, lbl in filtered] or ["(nenhuma voz)"]

        saved_path = self.cfg.get("voice_out", "")
        saved_label = next((lbl for p, lbl in filtered if p == saved_path), labels[0])

        self.voice_var = ctk.StringVar(value=saved_label)
        self._voice_menu = ctk.CTkOptionMenu(
            self._card, values=labels, variable=self.voice_var,
            fg_color=self.INPUT, button_color=self.IBORDER,
            button_hover_color=self.SEG_BG, text_color=self.TEXT,
            dropdown_fg_color=self.CARD, dropdown_text_color=self.TEXT,
            dropdown_hover_color=self.SEG_BG, font=ctk.CTkFont(size=13),
        )
        self._voice_menu.grid(row=row, column=0, columnspan=2, sticky="ew",
                              padx=20, pady=(0, 6))
        row += 1

        # Linha: caminho das vozes + botão testar
        info_row = ctk.CTkFrame(self._card, fg_color="transparent")
        info_row.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 8))
        info_row.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(info_row, text=f"Vozes em: {VOICES_DIR}",
                     font=ctk.CTkFont(size=10), text_color=self.MUTED).grid(
                         row=0, column=0, sticky="w")
        self._test_btn = ctk.CTkButton(
            info_row, text="▶  Testar", width=90, height=26,
            fg_color=self.SEG_BG, hover_color=self.IBORDER,
            text_color=self.MUTED, border_width=1, border_color=self.IBORDER,
            corner_radius=8, font=ctk.CTkFont(size=11),
            command=self._test_voice,
        )
        self._test_btn.grid(row=0, column=1, sticky="e")
        row += 1

        # Card de download — conteúdo gerado dinamicamente em _show_dl_card
        self._dl_card = ctk.CTkFrame(
            self._card, fg_color=self.CARD,
            border_width=1, border_color=self.IBORDER, corner_radius=8,
        )
        self._dl_card_kw = dict(row=row, column=0, columnspan=2,
                                 sticky="ew", padx=20, pady=(0, 12))
        self._dl_card.grid(**self._dl_card_kw)
        self._dl_card.grid_remove()

        # Frame interno que é limpo e repopulado ao mudar de idioma
        self._dl_inner = ctk.CTkFrame(self._dl_card, fg_color="transparent")
        self._dl_inner.pack(fill="x", padx=12, pady=10)

        row += 1

        # Verifica estado inicial para o idioma corrente
        self._on_tgt_change()
        return row

    def _refresh_voices(self) -> None:
        self._voices = get_voices()
        self._on_tgt_change()

    # ── Voz: idioma / filtro / download / teste ───────────────────────────────

    def _tgt_code(self) -> str:
        """Retorna o código de idioma do destino atual."""
        label = getattr(self, "tgt_var", None)
        if label is None:
            return self.cfg.get("tgt", "en")
        lbl = label.get()
        # Tenta _tgt_pairs primeiro (lista filtrada de destino)
        pairs = getattr(self, "_tgt_pairs", None) or []
        for code, name in pairs:
            if f"{name}  ({code})" == lbl:
                return code
        # Fallback: lista global
        try:
            return LANG_CODES[LANG_LABELS.index(lbl)]
        except (ValueError, IndexError):
            return self.cfg.get("tgt", "en")

    def _on_src_change(self) -> None:
        """Atualiza o seletor de voz bilateral quando o idioma de origem muda."""
        if not hasattr(self, "_voice_in_menu"):
            return
        try:
            src_code = LANG_CODES[LANG_LABELS.index(self.src_var.get())]
        except ValueError:
            return
        in_voices = _voices_for_lang(self._voices, src_code)
        in_labels = [lbl for _, lbl in in_voices] or [f"(nenhuma voz {src_code})"]
        self._voice_in_menu.configure(values=in_labels)
        if self.voice_in_var.get() not in in_labels:
            self.voice_in_var.set(in_labels[0])

    def _on_tgt_change(self) -> None:
        """Chamado quando o idioma de destino muda: filtra vozes e mostra download se vazio."""
        if not hasattr(self, "_voice_menu"):
            return
        tgt_code = self._tgt_code()
        filtered = _voices_for_lang(self._voices, tgt_code)
        labels = [lbl for _, lbl in filtered]
        if labels:
            self._voice_menu.configure(values=labels)
            if self.voice_var.get() not in labels:
                self.voice_var.set(labels[0])
        else:
            self._voice_menu.configure(values=["(nenhuma voz)"])
            self.voice_var.set("(nenhuma voz)")

        # Mostra card de download se houver vozes do catálogo ainda não baixadas
        remaining = [v for v in VOICE_CATALOG
                     if v["lang"] == tgt_code
                     and not (VOICES_DIR / _catalog_filename(v)).exists()]
        if remaining:
            self._show_dl_card(tgt_code)
        elif hasattr(self, "_dl_card"):
            self._dl_card.grid_remove()

    def _show_dl_card(self, lang_code: str) -> None:
        """Reconstrói o card de download listando TODAS as vozes do catálogo para o idioma."""
        if not hasattr(self, "_dl_inner"):
            return
        self._dl_current_lang = lang_code
        lang_name  = dict(LANGS).get(lang_code, lang_code.upper())
        candidates = [v for v in VOICE_CATALOG if v["lang"] == lang_code]

        # Limpa conteúdo anterior
        for w in self._dl_inner.winfo_children():
            w.destroy()

        if not candidates:
            ctk.CTkLabel(self._dl_inner,
                         text=f"Sem voz para {lang_name} no catálogo.",
                         font=ctk.CTkFont(size=11), text_color=self.MUTED,
                         anchor="w").pack(fill="x")
            self._dl_card.grid(**self._dl_card_kw)
            return

        # Cabeçalho — texto muda conforme há vozes instaladas ou não
        installed_any = any(
            (VOICES_DIR / _catalog_filename(v)).exists()
            for v in VOICE_CATALOG if v["lang"] == lang_code
        )
        hdr_text = (f"Mais vozes para {lang_name}:" if installed_any
                    else f"Sem voz para {lang_name}. Baixar do catálogo:")
        ctk.CTkLabel(self._dl_inner,
                     text=hdr_text,
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self.MUTED, anchor="w",
                     ).pack(fill="x", pady=(0, 6))

        # Barra de progresso + label (ocultos até iniciar download)
        self._dl_progress = ctk.CTkProgressBar(
            self._dl_inner, height=6, corner_radius=3,
            progress_color=self.ACCENT, fg_color=self.BORDER)
        self._dl_pct_lbl = ctk.CTkLabel(
            self._dl_inner, text="",
            font=ctk.CTkFont(size=10), text_color=self.MUTED)
        self._dl_status = ctk.CTkLabel(
            self._dl_inner, text="",
            font=ctk.CTkFont(size=11), text_color=self.MUTED, anchor="w")

        # Um botão por voz não baixada
        _GENDER  = {"M": "♂", "F": "♀", "?": ""}
        _QUALITY = {"x_low": "mín.", "low": "baixa", "medium": "média", "high": "alta"}
        _btn_kw  = dict(height=30, fg_color=self.ACCENT, hover_color=self.HOVER,
                        text_color="#FFFFFF", corner_radius=8,
                        font=ctk.CTkFont(size=12, weight="bold"))
        any_shown = False
        for v in candidates:
            fname = _catalog_filename(v)
            if (VOICES_DIR / fname).exists():
                continue  # já baixada
            g  = _GENDER.get(v["gender"], "")
            ql = _QUALITY.get(v["quality"], v["quality"])
            lbl = f"⬇  {g} {v['name']}  ·  {ql}".strip()
            btn = ctk.CTkButton(self._dl_inner, text=lbl, **_btn_kw)
            btn.configure(command=lambda vv=v, bb=btn: self._download_voice(vv, bb))
            btn.pack(fill="x", pady=(0, 4))
            any_shown = True

        if not any_shown:
            # Todas já baixadas (não deveria aparecer, mas garante)
            self._dl_card.grid_remove()
            return

        self._dl_card.grid(**self._dl_card_kw)

    def _download_voice(self, voice_entry: dict, btn: ctk.CTkButton) -> None:
        """Inicia download de uma voz específica do catálogo."""
        lang_code = voice_entry["lang"]
        fname     = _catalog_filename(voice_entry)
        dest      = VOICES_DIR / fname
        if dest.exists():
            self._dl_complete_for(lang_code)
            return

        lang_name = dict(LANGS).get(lang_code, lang_code.upper())

        # Oculta todos os botões de voz, mostra progresso
        for w in self._dl_inner.winfo_children():
            if isinstance(w, ctk.CTkButton):
                w.pack_forget()

        self._dl_status.configure(text=f"⬇  Baixando {voice_entry['name']} ({lang_name})…")
        self._dl_status.pack(fill="x", pady=(0, 4))
        self._dl_progress.set(0)
        self._dl_progress.pack(fill="x", pady=(0, 2))
        self._dl_pct_lbl.configure(text="")
        self._dl_pct_lbl.pack()

        def _download():
            try:
                VOICES_DIR.mkdir(parents=True, exist_ok=True)
                json_url  = _catalog_url(voice_entry, ".json")
                json_dest = VOICES_DIR / (fname + ".json")
                try:
                    with urllib.request.urlopen(json_url, timeout=30) as rj:
                        json_dest.write_bytes(rj.read())
                except Exception:
                    pass
                url = _catalog_url(voice_entry)
                with urllib.request.urlopen(url, timeout=120) as r:
                    total = int(r.headers.get("Content-Length", 0))
                    done  = 0
                    with open(dest, "wb") as f:
                        while True:
                            chunk = r.read(65536)
                            if not chunk:
                                break
                            f.write(chunk)
                            done += len(chunk)
                            if total:
                                self.after(0, self._dl_update_progress,
                                           done / total, voice_entry["name"])
                self.after(0, self._dl_complete_for, lang_code)
            except Exception as e:
                self.after(0, self._dl_failed_msg, str(e))

        threading.Thread(target=_download, daemon=True).start()

    def _dl_update_progress(self, pct: float, name: str) -> None:
        if hasattr(self, "_dl_progress"):
            self._dl_progress.set(pct)
        if hasattr(self, "_dl_pct_lbl"):
            self._dl_pct_lbl.configure(text=f"{name}  —  {int(pct * 100)}%")

    def _dl_complete_for(self, lang_code: str) -> None:
        """Download concluído: atualiza menu de voz e mostra vozes restantes ou esconde card."""
        self._voices = get_voices()
        filtered = _voices_for_lang(self._voices, lang_code)
        if filtered and hasattr(self, "_voice_menu"):
            labels = [lbl for _, lbl in filtered]
            self._voice_menu.configure(values=labels)
            self.voice_var.set(labels[0])
        # Reexibe card com vozes ainda não baixadas (ou oculta se todas baixadas)
        remaining = [v for v in VOICE_CATALOG
                     if v["lang"] == lang_code
                     and not (VOICES_DIR / _catalog_filename(v)).exists()]
        if remaining and hasattr(self, "_dl_card"):
            self._show_dl_card(lang_code)
        elif hasattr(self, "_dl_card"):
            self._dl_card.grid_remove()

    def _dl_failed_msg(self, error: str) -> None:
        if hasattr(self, "_dl_status"):
            self._dl_status.configure(text=f"Erro: {error[:80]}", text_color="#EF4444")
        try: self._dl_progress.pack_forget()
        except Exception: pass
        try: self._dl_pct_lbl.pack_forget()
        except Exception: pass
        # Restaura botões após 3 s para que o erro seja legível
        lang_code = getattr(self, "_dl_current_lang", None)
        if lang_code:
            self.after(3000, lambda: self._show_dl_card(lang_code))

    def _test_voice(self) -> None:
        """Testa a voz selecionada com uma frase no idioma de destino."""
        selected = self.voice_var.get()
        if selected.startswith("("):
            return
        voice_path = next((p for p, lbl in self._voices if lbl == selected), "")
        if not voice_path or not Path(voice_path).exists():
            return

        tgt_code = self._tgt_code()
        phrase   = TEST_PHRASES.get(tgt_code, "Uma mensagem. Todas as línguas.")

        def _run():
            try:
                self.after(0, lambda: self._test_btn.configure(
                    state="disabled", text="▶  …"))
                from piper import PiperVoice
                import wave, io
                voice = PiperVoice.load(voice_path)
                tmp_wav = "/tmp/praxis_voice_test.wav"
                with wave.open(tmp_wav, "wb") as wf:
                    voice.synthesize_wav(phrase, wf)
                subprocess.run(["aplay", tmp_wav],
                               stderr=subprocess.DEVNULL, timeout=30)
            except Exception:
                pass
            finally:
                self.after(0, lambda: self._test_btn.configure(
                    state="normal", text="▶  Testar"))

        threading.Thread(target=_run, daemon=True).start()

    def _make_voice_header_btns(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self._card, fg_color="transparent")
        btn_kw = dict(height=26, fg_color=self.SEG_BG, hover_color=self.IBORDER,
                      text_color=self.MUTED, border_width=1, border_color=self.IBORDER,
                      corner_radius=8, font=ctk.CTkFont(size=11))
        ctk.CTkButton(frame, text="⬇  Baixar", width=80,
                      command=self._open_download_dialog, **btn_kw).pack(side="left", padx=(0, 4))
        ctk.CTkButton(frame, text="↺  Atualizar", width=100,
                      command=self._refresh_voices, **btn_kw).pack(side="left", padx=(0, 4))
        self._apply_voice_btn = ctk.CTkButton(
            frame, text="⟳  Aplicar", width=90,
            command=self._apply_voice, state="disabled", **btn_kw)
        self._apply_voice_btn.pack(side="left")
        return frame

    def _open_download_dialog(self) -> None:
        VoiceDownloadDialog(self, on_downloaded=self._refresh_voices)

    def _apply_voice(self) -> None:
        proc = getattr(self, "_engine_proc", None)
        if not proc or proc.poll() is not None or proc.stdin is None:
            return
        selected = self.voice_var.get()
        voice_path = next((p for p, lbl in self._voices if lbl == selected), "")
        if not voice_path or not Path(voice_path).exists():
            return
        cmd = json.dumps({"cmd": "reload_voice", "path": voice_path}) + "\n"
        try:
            proc.stdin.write(cmd)
            proc.stdin.flush()
            self._apply_voice_btn.configure(state="disabled", text="Aplicando…")
        except Exception:
            pass

    def _make_voices_refresh_btn(self) -> ctk.CTkButton:
        return ctk.CTkButton(
            self._card, text="↺  Atualizar", width=100, height=26,
            fg_color=self.SEG_BG, hover_color=self.IBORDER,
            text_color=self.MUTED, border_width=1, border_color=self.IBORDER,
            corner_radius=8, font=ctk.CTkFont(size=11),
            command=self._refresh_voices,
        )

    def _make_refresh_btn(self) -> ctk.CTkButton:
        return ctk.CTkButton(
            self._card, text="↺  Atualizar", width=100, height=26,
            fg_color=self.SEG_BG, hover_color=self.IBORDER,
            text_color=self.MUTED, border_width=1, border_color=self.IBORDER,
            corner_radius=8, font=ctk.CTkFont(size=11),
            command=self._refresh_devices,
        )

    # ── Lógica de dispositivos ────────────────────────────────────────────────

    def _refresh_devices(self, startup: bool = False) -> None:
        self._inputs  = get_audio_inputs()
        self._outputs = get_audio_outputs()

        in_labels  = ["(padrão do sistema)"] + [d for _, d in self._inputs]
        out_labels = ["(padrão do sistema)"] + [d for _, d in self._outputs]

        self._mic_menu.configure(values=in_labels)
        self._out_menu.configure(values=out_labels)

        if startup:
            saved_mic = self.cfg.get("mic", "")
            saved_out = self.cfg.get("output", "")

            # Se não há dispositivo salvo, pré-seleciona o padrão do sistema
            if not saved_mic and not saved_out:
                def_src, def_sink = _pa_defaults()
                # Fonte estéreo: usa canal 1 (L) como padrão
                if def_src and not saved_mic:
                    names = [n for n, _ in self._inputs]
                    if f"{def_src}:left" in names:
                        saved_mic = f"{def_src}:left"
                    else:
                        saved_mic = def_src
                saved_out = saved_out or def_sink

            self.mic_var.set(self._name_to_label(saved_mic, self._inputs))
            self.out_var.set(self._name_to_label(saved_out, self._outputs))

    def _name_to_label(self, name: str, devs: list[tuple[str, str]]) -> str:
        if not name:
            return "(padrão do sistema)"
        for n, d in devs:
            if n == name:
                return d
        return "(padrão do sistema)"

    def _label_to_name(self, label: str, devs: list[tuple[str, str]]) -> str:
        if label.startswith("("):
            return ""
        for n, d in devs:
            if d == label:
                return n
        return ""

    # ── Aba Minha Voz — clonagem de voz ──────────────────────────────────────

    # Texto de ~1000 palavras dividido em 4 páginas para leitura paginada.
    # ~1000-word text split into 4 pages for paginated reading.
    CLONE_PAGES = [
        # Página 1 / Page 1
        (
            "Olá! Vamos começar a gravação. Fale de forma natural, como se estivesse "
            "conversando com alguém. Não precisa ser perfeito — o importante é manter um "
            "ritmo constante e uma voz clara. Às vezes mais rápido, às vezes mais pausado. "
            "Às vezes com mais ênfase, outras vezes de forma mais suave.\n\n"
            "A comunicação humana é muito mais do que palavras. Carregamos no tom da voz "
            "emoções, intenções e personalidade. Quando falamos com alguém, transmitimos "
            "muito além do conteúdo — transmitimos presença.\n\n"
            "O idioma conecta pessoas. Ele constrói amizades, abre portas profissionais e "
            "permite que ideias cruzem fronteiras. Mas a barreira linguística ainda separa "
            "bilhões de pessoas que poderiam se entender se falassem a mesma língua.\n\n"
            "Respire fundo. Continue lendo com calma. Toda boa conversa começa com "
            "atenção e presença. Agora vamos para o próximo trecho."
        ),
        # Página 2 / Page 2
        (
            "Nos últimos anos, a inteligência artificial avançou de forma impressionante. "
            "Modelos de linguagem, síntese de voz, visão computacional, tradução automática — "
            "tudo evoluiu numa velocidade surpreendente.\n\n"
            "Uma ferramenta só tem valor real quando resolve um problema verdadeiro. "
            "O reconhecimento de voz existe há décadas, mas por muito tempo era impreciso. "
            "Hoje, a transcrição em tempo real funciona tão bem que mal percebemos o "
            "processamento acontecendo.\n\n"
            "A síntese de voz passou pelo mesmo caminho. Vozes sintetizadas costumavam soar "
            "mecânicas e sem emoção. Hoje um bom modelo captura timbre, entonação e "
            "naturalidade com qualidade impressionante.\n\n"
            "Vamos variar um pouco. Um, dois, três, quatro, cinco. Dez, vinte, cinquenta, "
            "cem, mil. Terça-feira, doze de agosto. Oito horas da manhã. Trinta graus. "
            "Cento e vinte quilômetros por hora. Seiscentos reais."
        ),
        # Página 3 / Page 3
        (
            "Imagine viajar para um país sem falar o idioma local. Entrar num restaurante, "
            "pedir comida apenas com gestos e sorrisos — é uma experiência rica, mas "
            "também frustrante. Muitas informações importantes se perdem na barreira do idioma.\n\n"
            "Em situações profissionais, a diferença é ainda maior. Reuniões, negociações, "
            "apresentações — cada palavra importa. Perder nuances pode significar perder "
            "oportunidades.\n\n"
            "Pense em tudo que ficou do outro lado de uma barreira linguística. Conhecimentos "
            "que não foram acessados, conexões que não aconteceram, negócios que não avançaram. "
            "A tecnologia pode mudar isso.\n\n"
            "A ideia é simples: qualquer pessoa pode falar em qualquer idioma mantendo "
            "sua própria voz, seu sotaque, seu jeito único de se expressar. "
            "Isso transforma a comunicação global de forma profunda."
        ),
        # Página 4 / Page 4
        (
            "Chegamos à última parte. Vamos variar a entonação. "
            "Uma pergunta: você já imaginou falar cinco idiomas com a mesma naturalidade "
            "que fala a sua língua nativa? Uma afirmação firme: isso é possível.\n\n"
            "A voz humana carrega muito além das palavras. O tom revela emoção. "
            "O ritmo revela confiança. A respiração revela tensão ou calma. "
            "Quando ouvimos alguém falar, não estamos apenas decodificando palavras — "
            "estamos reconhecendo uma pessoa.\n\n"
            "Capturar isso é o grande desafio da clonagem de voz. Não basta replicar "
            "fonemas corretos. É preciso capturar cadência, ritmo e personalidade. "
            "O que torna uma voz única entre todas as outras.\n\n"
            "Obrigado por gravar. Cada segundo de áudio ajuda o modelo a ser mais "
            "fiel e preciso. Quanto mais você falar de forma natural, melhor o resultado."
        ),
    ]

    # Texto completo concatenado — usado como ref_text no JSON do perfil.
    # Full concatenated text — used as ref_text in profile JSON.
    CLONE_TEXT = " ".join(CLONE_PAGES)
    CLONES_DIR = VOICES_DIR / "clones"

    def _build_clone_tab(self, parent: ctk.CTkFrame) -> None:
        """Constrói a aba de clonagem de voz: texto paginado, gravação, treino RVC.
        Builds the voice cloning tab: paginated text, recording, RVC training."""
        self.CLONES_DIR.mkdir(parents=True, exist_ok=True)
        self._rec_thread   = None
        self._rec_stop_evt = None
        self._rec_frames   = []
        self._xtts_model   = None   # cache — carrega só uma vez por sessão / loaded once per session
        self._xtts_latents = {}     # cache de latents por wav_path / latents cache by wav path
        self._meter_stream = None   # sounddevice stream do VU meter / VU meter audio stream
        self._testing      = False  # trava para evitar testes simultâneos / lock to prevent concurrent tests
        self._training     = False  # trava para evitar treinos simultâneos / lock to prevent concurrent training
        self._clone_page   = 0      # página atual do texto de clonagem / current clone text page

        scroll = ctk.CTkScrollableFrame(
            parent, fg_color="transparent",
            scrollbar_button_color=self.SEG_BG,
            scrollbar_button_hover_color=self.IBORDER,
        )
        scroll.pack(fill="both", expand=True, padx=4, pady=4)

        # ── Seletor de modo de clonagem ─────────────────────────────────────
        # Clone mode selector: RVC (training) vs OmniVoice (zero-shot)
        self._clone_mode_var = ctk.StringVar(value="rvc")
        ctk.CTkSegmentedButton(
            scroll,
            values=["🎙 RVC — Treino", "🤖 OmniVoice"],
            variable=self._clone_mode_var,
            command=self._switch_clone_mode,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=self.SEG_BG, selected_color=self.ACCENT,
            selected_hover_color=self.HOVER, unselected_color=self.SEG_BG,
            text_color=self.TEXT,
        ).pack(fill="x", padx=16, pady=(12, 4))

        # Frames por modo — criados mas ainda não empacotados / created but not yet packed
        # (pack acontece após o VU meter para garantir a ordem correta de layout)
        # (pack happens after the VU meter to ensure correct layout order)
        self._rvc_section = ctk.CTkFrame(scroll, fg_color="transparent")
        self._ov_section  = ctk.CTkFrame(scroll, fg_color="transparent")

        # Alias local para construção da seção RVC / local alias for RVC section build
        _s = self._rvc_section

        # ── Instruções ─────────────────────────────────────────────────────
        info = ctk.CTkFrame(_s, fg_color=self.SEG_BG,
                            corner_radius=10, border_width=1,
                            border_color=self.IBORDER)
        info.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(info, text="Como funciona",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=self.TEXT).pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(info,
                     text=(
                         "1. Dê um nome e grave lendo o texto abaixo (pode gravar várias vezes — o áudio acumula)\n"
                         "2. Meta: 3 minutos no total — quanto mais, melhor a qualidade\n"
                         "3. Com 3min+ gravados, clique em Treinar Voz (leva 10-30 min)\n"
                         "4. Após o treino, use Testar para ouvir e Usar para ativar"
                     ),
                     font=ctk.CTkFont(size=11), text_color=self.MUTED,
                     justify="left", anchor="w").pack(anchor="w", padx=12, pady=(0, 10))

        # ── Nome do perfil ──────────────────────────────────────────────────
        name_row = ctk.CTkFrame(_s, fg_color="transparent")
        name_row.pack(fill="x", padx=16, pady=(4, 0))
        name_row.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(name_row, text="Nome do perfil:",
                     font=ctk.CTkFont(size=12), text_color=self.TEXT).grid(
            row=0, column=0, sticky="w", padx=(0, 8))
        self._clone_name_var = ctk.StringVar(value="minha_voz")
        ctk.CTkEntry(name_row, textvariable=self._clone_name_var,
                     fg_color=self.INPUT, border_color=self.IBORDER,
                     text_color=self.TEXT, font=ctk.CTkFont(size=13)).grid(
            row=0, column=1, sticky="ew")

        # ── Texto de referência paginado ────────────────────────────────────
        # Paginated reference text — no scroll, navigate with buttons
        _total_pages = len(self.CLONE_PAGES)

        # Cabeçalho: título + indicador de página / header: title + page indicator
        ref_header = ctk.CTkFrame(_s, fg_color="transparent")
        ref_header.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(ref_header, text="Leia este texto em voz alta:",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self.MUTED).pack(side="left")
        self._page_lbl = ctk.CTkLabel(
            ref_header,
            text=f"Página 1 de {_total_pages}",
            font=ctk.CTkFont(size=11), text_color=self.MUTED)
        self._page_lbl.pack(side="right")

        # Card com o texto da página atual / card showing current page text
        ref_card = ctk.CTkFrame(_s, fg_color=self.INPUT,
                                border_color=self.IBORDER, border_width=1,
                                corner_radius=8)
        ref_card.pack(fill="x", padx=16)
        self._ref_lbl = ctk.CTkLabel(
            ref_card, text=self.CLONE_PAGES[0],
            font=ctk.CTkFont(size=12), text_color=self.TEXT,
            wraplength=400, justify="left", anchor="nw")
        self._ref_lbl.pack(fill="x", padx=12, pady=10)

        # Ajusta wraplength ao redimensionar (bind no card evita loop infinito)
        # Adjust wraplength on resize (bind on card to avoid infinite loop)
        _last_w = [0]
        def _on_card_resize(e):
            new_w = max(100, e.width - 28)
            if abs(new_w - _last_w[0]) > 2:
                _last_w[0] = new_w
                self._ref_lbl.configure(wraplength=new_w)
        ref_card.bind("<Configure>", _on_card_resize)

        # Botões de navegação de página / page navigation buttons
        nav_row = ctk.CTkFrame(_s, fg_color="transparent")
        nav_row.pack(fill="x", padx=16, pady=(6, 2))

        def _go_page(delta: int):
            # Navega entre páginas, atualizando texto e indicador
            # Navigate between pages, updating text and indicator
            self._clone_page = max(0, min(_total_pages - 1, self._clone_page + delta))
            self._ref_lbl.configure(text=self.CLONE_PAGES[self._clone_page])
            self._page_lbl.configure(
                text=f"Página {self._clone_page + 1} de {_total_pages}")
            _prev_btn.configure(state="normal" if self._clone_page > 0 else "disabled")
            _next_btn.configure(state="normal" if self._clone_page < _total_pages - 1 else "disabled")

        _prev_btn = ctk.CTkButton(
            nav_row, text="← Anterior", width=100, height=28,
            fg_color=self.SEG_BG, hover_color=self.IBORDER,
            text_color=self.MUTED, border_width=1,
            border_color=self.IBORDER, corner_radius=6,
            font=ctk.CTkFont(size=11),
            state="disabled",
            command=lambda: _go_page(-1),
        )
        _prev_btn.pack(side="left")

        _next_btn = ctk.CTkButton(
            nav_row, text="Próximo →", width=100, height=28,
            fg_color=self.SEG_BG, hover_color=self.IBORDER,
            text_color=self.MUTED, border_width=1,
            border_color=self.IBORDER, corner_radius=6,
            font=ctk.CTkFont(size=11),
            command=lambda: _go_page(1),
        )
        _next_btn.pack(side="right")

        # Dispositivo herdado da aba Config — sem seletor próprio na aba de clonagem
        # Device inherited from Config tab — no separate selector in clone tab

        # ── VU Meter compartilhado (visível em ambos os modos) ─────────────
        # Shared VU meter — visible in both RVC and OmniVoice modes
        meter_frame = ctk.CTkFrame(scroll, fg_color=self.INPUT,
                                   border_color=self.IBORDER, border_width=1,
                                   corner_radius=8)
        meter_frame.pack(fill="x", padx=16, pady=(8, 4))

        meter_top = ctk.CTkFrame(meter_frame, fg_color="transparent")
        meter_top.pack(fill="x", padx=10, pady=(8, 2))
        ctk.CTkLabel(meter_top, text="Nível do microfone",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self.MUTED).pack(side="left")
        self._meter_db_lbl = ctk.CTkLabel(meter_top, text="— dB",
                                           font=ctk.CTkFont(size=11),
                                           text_color=self.MUTED)
        self._meter_db_lbl.pack(side="right")
        # Botão monitor: roteia mic → caixa em tempo real / Monitor: routes mic → speakers live
        # ⚠ Use fones de ouvido para evitar eco / use headphones to avoid echo feedback
        self._monitor_var = ctk.BooleanVar(value=False)
        self._monitor_lbl = ctk.CTkLabel(
            meter_top, text="🎧 Monitor",
            font=ctk.CTkFont(size=10), text_color=self.MUTED,
            cursor="hand2")
        self._monitor_lbl.pack(side="right", padx=(0, 4))
        ctk.CTkSwitch(
            meter_top, text="", width=36,
            variable=self._monitor_var, onvalue=True, offvalue=False,
            progress_color=self.ACCENT,
            command=self._toggle_monitor,
        ).pack(side="right", padx=(0, 6))

        # Inicializa estado ANTES de criar o canvas — <Configure> pode disparar no pack()
        # Init state BEFORE creating canvas — <Configure> may fire during pack()
        self._clone_meter_W    = 0
        self._clone_meter_H    = 0
        self._clone_meter_peak = 0.0
        self._clone_meter_ids: dict = {}

        # Canvas com gradiente verde→amarelo→vermelho (igual ao VU meter do Config)
        # Canvas with green→yellow→red gradient (same as Config VU meter)
        self._clone_meter_canvas = tk.Canvas(
            meter_frame, height=14, bg=self.INPUT,
            highlightthickness=0, bd=0,
        )
        self._clone_meter_canvas.pack(fill="x", padx=10, pady=(2, 4))
        self._clone_meter_canvas.bind("<Configure>", self._clone_meter_configure)

        # marcas de referência: -40  -20  -12  -6  0 dB
        marks_row = ctk.CTkFrame(meter_frame, fg_color="transparent")
        marks_row.pack(fill="x", padx=10, pady=(0, 6))
        for label, pos in [("-40", 0.0), ("-20", 0.33), ("-12", 0.55),
                            ("-6", 0.73), ("0", 1.0)]:
            ctk.CTkLabel(marks_row, text=label,
                         font=ctk.CTkFont(size=9), text_color=self.MUTED,
                         ).place(relx=pos, anchor="n" if pos < 1.0 else "ne")
        marks_row.configure(height=14)
        marks_row.pack_propagate(False)

        # Delay de 300ms para o mainloop estar pronto antes de abrir o stream
        # 300ms delay so mainloop is ready before opening the audio stream
        self.after(300, self._start_meter)

        # Empacota as seções APÓS o VU meter para que apareçam abaixo dele
        # Pack sections AFTER the VU meter so they appear below it in layout
        self._rvc_section.pack(fill="x")

        # ── Botão + barra de progresso da gravação ─────────────────────────
        rec_row = ctk.CTkFrame(_s, fg_color="transparent")
        rec_row.pack(fill="x", padx=16, pady=(10, 2))
        self._rec_btn = ctk.CTkButton(
            rec_row, text="● Gravar", width=130, height=36,
            fg_color="#DC2626", hover_color="#B91C1C",
            text_color="#FFFFFF", corner_radius=10,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._toggle_recording,
        )
        self._rec_btn.pack(side="left", padx=(0, 10))
        self._rec_status = ctk.CTkLabel(
            rec_row, text="Pronto para gravar",
            font=ctk.CTkFont(size=11), text_color=self.MUTED)
        self._rec_status.pack(side="left")

        self._rec_prog = ctk.CTkProgressBar(_s, height=6,
                                             fg_color=self.SEG_BG,
                                             progress_color="#DC2626")
        self._rec_prog.set(0)
        self._rec_prog.pack(fill="x", padx=16, pady=(2, 4))

        # ── Card de efeitos de áudio: Denoise + Compressor ─────────────────
        # Audio FX card: applied after recording before saving
        fx_card = ctk.CTkFrame(_s, fg_color=self.INPUT,
                               border_color=self.IBORDER, border_width=1,
                               corner_radius=8)
        fx_card.pack(fill="x", padx=16, pady=(6, 4))

        # Linha Denoise / Denoise row
        dn_row = ctk.CTkFrame(fx_card, fg_color="transparent")
        dn_row.pack(fill="x", padx=12, pady=(8, 2))
        ctk.CTkLabel(dn_row, text="Denoise",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self.TEXT).pack(side="left")
        self._denoise_pct_lbl = ctk.CTkLabel(
            dn_row, text="0%", width=36,
            font=ctk.CTkFont(size=11), text_color=self.MUTED)
        self._denoise_pct_lbl.pack(side="right")
        self._denoise_var = ctk.DoubleVar(value=0.0)

        def _on_denoise_slide(v):
            self._denoise_pct_lbl.configure(text=f"{int(float(v)*100)}%")
        ctk.CTkSlider(
            fx_card, from_=0.0, to=1.0, variable=self._denoise_var,
            fg_color=self.SEG_BG, progress_color=self.ACCENT,
            button_color=self.ACCENT, button_hover_color=self.HOVER,
            command=_on_denoise_slide,
        ).pack(fill="x", padx=12, pady=(0, 6))

        # ── Compressor — parâmetros individuais / individual parameters ────
        cmp_header = ctk.CTkFrame(fx_card, fg_color="transparent")
        cmp_header.pack(fill="x", padx=12, pady=(2, 4))
        ctk.CTkLabel(cmp_header, text="Compressor",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self.TEXT).pack(side="left")
        # Switch para ligar/desligar sem perder os valores / toggle without losing values
        self._cmp_on_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(
            cmp_header, text="", width=40,
            variable=self._cmp_on_var, onvalue=True, offvalue=False,
            progress_color=self.ACCENT,
        ).pack(side="right")

        # Grid de 4 parâmetros: Threshold / Ratio / Attack / Release
        # 4-parameter grid: Threshold / Ratio / Attack / Release
        cmp_grid = ctk.CTkFrame(fx_card, fg_color="transparent")
        cmp_grid.pack(fill="x", padx=12, pady=(0, 8))
        cmp_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

        def _cmp_param(col: int, label: str, unit: str,
                       from_: float, to: float, init: float,
                       fmt: str = ".0f") -> ctk.DoubleVar:
            """Cria célula de parâmetro com label, valor numérico e slider.
            Creates a parameter cell with label, numeric value and slider."""
            cell = ctk.CTkFrame(cmp_grid, fg_color=self.SEG_BG, corner_radius=8)
            cell.grid(row=0, column=col, sticky="ew", padx=4, pady=4)
            ctk.CTkLabel(cell, text=label,
                         font=ctk.CTkFont(size=9), text_color=self.MUTED).pack(pady=(6, 0))
            var = ctk.DoubleVar(value=init)
            val_lbl = ctk.CTkLabel(cell, text=f"{init:{fmt}}{unit}",
                                   font=ctk.CTkFont(size=13, weight="bold"),
                                   text_color=self.TEXT)
            val_lbl.pack()

            def _on_slide(v):
                val_lbl.configure(text=f"{float(v):{fmt}}{unit}")

            ctk.CTkSlider(
                cell, from_=from_, to=to, variable=var,
                orientation="horizontal", height=12,
                fg_color=self.BORDER, progress_color=self.ACCENT,
                button_color=self.ACCENT, button_hover_color=self.HOVER,
                command=_on_slide,
            ).pack(fill="x", padx=8, pady=(2, 8))
            return var

        self._cmp_threshold = _cmp_param(0, "Threshold", " dB", -40, 0,  -18)
        self._cmp_ratio     = _cmp_param(1, "Ratio",     ":1",   1, 20,   4, ".1f")
        self._cmp_attack    = _cmp_param(2, "Attack",    " ms",  1, 100,  5)
        self._cmp_release   = _cmp_param(3, "Release",   " ms", 10, 500, 80)

        # ── Duração acumulada + botão Treinar ──────────────────────────────
        # Accumulated duration + Train button
        dur_row = ctk.CTkFrame(_s, fg_color="transparent")
        dur_row.pack(fill="x", padx=16, pady=(0, 4))
        self._dur_lbl = ctk.CTkLabel(
            dur_row, text="0s gravados — mínimo 180s para treinar",
            font=ctk.CTkFont(size=11), text_color=self.MUTED)
        self._dur_lbl.pack(side="left")

        # Botão Treinar — habilitado somente quando há áudio suficiente
        # Train button — enabled only when enough audio is recorded
        self._train_btn = ctk.CTkButton(
            dur_row, text="🎙 Treinar Voz", width=120, height=30,
            fg_color=self.SEG_BG, hover_color=self.IBORDER,
            text_color=self.MUTED, border_width=1,
            border_color=self.IBORDER, corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            state="disabled",
            command=self._start_train_rvc,
        )
        self._train_btn.pack(side="right")

        # ── Dashboard visual de treino RVC ─────────────────────────────────
        # Visual training dashboard — phases, epoch counter, metric cards, ETA
        _dash = ctk.CTkFrame(_s, fg_color=self.INPUT,
                             border_color=self.IBORDER, border_width=1,
                             corner_radius=10)
        _dash.pack(fill="x", padx=16, pady=(0, 8))

        # Pills de fase / Phase indicator pills
        phase_row = ctk.CTkFrame(_dash, fg_color="transparent")
        phase_row.pack(fill="x", padx=12, pady=(10, 4))
        self._dash_phases = []
        for _ph_label in ["Pré-proc", "Extração", "Treino"]:
            _pill = ctk.CTkFrame(phase_row, fg_color=self.SEG_BG, corner_radius=20)
            _pill.pack(side="left", padx=(0, 6))
            _ph_lbl = ctk.CTkLabel(_pill, text=f"○  {_ph_label}",
                                   font=ctk.CTkFont(size=10), text_color=self.MUTED)
            _ph_lbl.pack(padx=10, pady=4)
            self._dash_phases.append(_ph_lbl)

        ctk.CTkFrame(_dash, height=1, fg_color=self.BORDER).pack(
            fill="x", padx=12, pady=(4, 0))

        # Contador de épocas / Epoch counter row
        _ep_row = ctk.CTkFrame(_dash, fg_color="transparent")
        _ep_row.pack(fill="x", padx=14, pady=(8, 2))
        ctk.CTkLabel(_ep_row, text="Época",
                     font=ctk.CTkFont(size=10), text_color=self.MUTED).pack(side="left")
        self._dash_epoch_lbl = ctk.CTkLabel(
            _ep_row, text="—",
            font=ctk.CTkFont(size=20, weight="bold"), text_color=self.TEXT)
        self._dash_epoch_lbl.pack(side="left", padx=(8, 0))
        self._dash_pct_lbl = ctk.CTkLabel(
            _ep_row, text="",
            font=ctk.CTkFont(size=12), text_color=self.MUTED)
        self._dash_pct_lbl.pack(side="right")

        # Barra de progresso do treino / Training progress bar
        self._train_prog = ctk.CTkProgressBar(
            _dash, height=10, corner_radius=5,
            fg_color=self.SEG_BG, progress_color="#8B5CF6")
        self._train_prog.set(0)
        self._train_prog.pack(fill="x", padx=14, pady=(0, 8))

        ctk.CTkFrame(_dash, height=1, fg_color=self.BORDER).pack(
            fill="x", padx=12)

        # Cards de métricas (Loss Gen / Loss Disc / Velocidade / ETA)
        # Metric cards
        _metrics_row = ctk.CTkFrame(_dash, fg_color="transparent")
        _metrics_row.pack(fill="x", padx=10, pady=(8, 4))
        _metrics_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        def _metric_card(col: int, title: str) -> ctk.CTkLabel:
            card = ctk.CTkFrame(_metrics_row, fg_color=self.SEG_BG, corner_radius=8)
            card.grid(row=0, column=col, sticky="ew", padx=4)
            ctk.CTkLabel(card, text=title,
                         font=ctk.CTkFont(size=9), text_color=self.MUTED).pack(pady=(6, 0))
            val = ctk.CTkLabel(card, text="—",
                               font=ctk.CTkFont(size=14, weight="bold"),
                               text_color=self.TEXT)
            val.pack(pady=(0, 6))
            return val

        self._dash_loss_gen  = _metric_card(0, "Loss Gen")
        self._dash_loss_disc = _metric_card(1, "Loss Disc")
        self._dash_speed     = _metric_card(2, "Vel./época")
        self._dash_eta       = _metric_card(3, "ETA")

        # Linha de melhor época + status / Best epoch + status line
        self._train_status = ctk.CTkLabel(
            _dash, text="",
            font=ctk.CTkFont(size=10), text_color=self.MUTED)
        self._train_status.pack(anchor="w", padx=14, pady=(0, 10))

        # Atualiza label de duração se já existe arquivo wav salvo
        # Update duration label if wav file already exists
        self._refresh_dur_label()

        # ── Card de texto para teste de voz clonada ────────────────────────
        # Test text card — mesma UX do OmniVoice; texto alimenta os botões ▶ Testar
        # Test text card — same UX as OmniVoice; text feeds into all ▶ Testar buttons
        _test_lang_options = [
            "pt — Português", "en — English", "es — Español",
            "fr — Français", "de — Deutsch", "it — Italiano",
            "ru — Русский", "zh — 中文",
        ]
        self._test_lang_var = ctk.StringVar(value="pt — Português")

        _rvc_tcard = ctk.CTkFrame(_s, fg_color=self.INPUT,
                                   border_color=self.IBORDER, border_width=1,
                                   corner_radius=10)
        _rvc_tcard.pack(fill="x", padx=16, pady=(0, 8))

        _rvc_trow = ctk.CTkFrame(_rvc_tcard, fg_color="transparent")
        _rvc_trow.pack(fill="x", padx=12, pady=(10, 4))

        ctk.CTkLabel(_rvc_trow, text="Texto para teste:",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self.TEXT).pack(side="left")

        ctk.CTkOptionMenu(
            _rvc_trow, values=_test_lang_options, variable=self._test_lang_var,
            fg_color=self.SEG_BG, button_color=self.IBORDER,
            button_hover_color=self.SEG_BG, text_color=self.TEXT,
            dropdown_fg_color=self.CARD, dropdown_text_color=self.TEXT,
            dropdown_hover_color=self.SEG_BG, font=ctk.CTkFont(size=12),
            width=160,
        ).pack(side="left", padx=(8, 8))

        def _rvc_fill_phrase() -> None:
            """Preenche a caixa com a frase padrão do idioma selecionado.
            Fills the box with the default phrase for the selected language."""
            lang = self._test_lang_var.get().split(" ")[0]
            self._rvc_test_text.delete("1.0", "end")
            self._rvc_test_text.insert("1.0", TEST_PHRASES.get(lang, TEST_PHRASES["pt"]))

        ctk.CTkButton(
            _rvc_trow, text="↺ Frase", width=72, height=28,
            fg_color=self.SEG_BG, hover_color=self.HOVER,
            text_color=self.TEXT, corner_radius=8,
            font=ctk.CTkFont(size=12),
            command=_rvc_fill_phrase,
        ).pack(side="left")

        self._rvc_test_text = ctk.CTkTextbox(
            _rvc_tcard, height=72, wrap="word",
            fg_color=self.SEG_BG, border_color=self.IBORDER, border_width=1,
            text_color=self.TEXT, font=ctk.CTkFont(size=12),
        )
        self._rvc_test_text.pack(fill="x", padx=12, pady=(0, 10))
        self._rvc_test_text.insert("1.0", TEST_PHRASES["pt"])

        # ── Separador + lista de vozes clonadas ────────────────────────────
        ctk.CTkFrame(_s, height=1, fg_color=self.BORDER).pack(
            fill="x", padx=16, pady=(6, 0))
        ctk.CTkLabel(_s, text="VOZES SALVAS",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=self.MUTED).pack(anchor="w", padx=16, pady=(10, 6))
        self._clone_list_frame = ctk.CTkFrame(_s, fg_color="transparent")
        self._clone_list_frame.pack(fill="x", padx=16)
        self._refresh_clone_list()

        # ── Seção OmniVoice (zero-shot) ─────────────────────────────────────
        # OmniVoice section — shown only when mode="ov"
        _ov = self._ov_section
        self._ov_rec_frames: list = []
        self._ov_rec_active = False
        self._ov_ref_path   = ctk.StringVar(value="")
        _OV_REF_MAX_S = 15   # max seconds for reference recording / máx seg para referência

        # Card de explicação / Explanation card
        _ov_info = ctk.CTkFrame(_ov, fg_color=self.SEG_BG,
                                corner_radius=10, border_width=1,
                                border_color=self.IBORDER)
        _ov_info.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(_ov_info, text="OmniVoice — Clonagem zero-shot",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=self.TEXT).pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(
            _ov_info,
            text=(
                "Grave ~10s da sua voz lendo o texto abaixo, depois clique em Gerar.\n"
                "O Whisper transcreve automaticamente — sem treino necessário."
            ),
            font=ctk.CTkFont(size=11), text_color=self.MUTED,
            justify="left", anchor="w",
        ).pack(anchor="w", padx=12, pady=(0, 10))

        # ── Card de gravação de referência ─────────────────────────────────
        # Reference recording card — record ~10s of natural speech
        _ov_rec_card = ctk.CTkFrame(_ov, fg_color=self.INPUT,
                                    border_color=self.IBORDER, border_width=1,
                                    corner_radius=8)
        _ov_rec_card.pack(fill="x", padx=16, pady=(0, 6))

        # Texto de exemplo para leitura / sample text to read aloud
        ctk.CTkLabel(_ov_rec_card, text="Leia este trecho em voz alta:",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self.MUTED).pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(
            _ov_rec_card,
            text=(
                "Olá! Estou gravando uma amostra de voz para o sistema de clonagem. "
                "A tecnologia aprende com poucos segundos de áudio e reproduz qualquer texto "
                "mantendo o timbre e a entonação natural da voz gravada."
            ),
            font=ctk.CTkFont(size=12), text_color=self.TEXT,
            wraplength=380, justify="left", anchor="nw",
        ).pack(fill="x", padx=12, pady=(0, 8))

        # Controles de gravação / Recording controls
        _ov_ctl = ctk.CTkFrame(_ov_rec_card, fg_color="transparent")
        _ov_ctl.pack(fill="x", padx=12, pady=(0, 4))

        self._ov_rec_btn = ctk.CTkButton(
            _ov_ctl, text="● Gravar referência", width=150, height=32,
            fg_color="#DC2626", hover_color="#B91C1C",
            text_color="#FFFFFF", corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._ov_toggle_recording,
        )
        self._ov_rec_btn.pack(side="left", padx=(0, 10))

        self._ov_rec_status = ctk.CTkLabel(
            _ov_ctl, text="Pronto — grave ~10s",
            font=ctk.CTkFont(size=11), text_color=self.MUTED)
        self._ov_rec_status.pack(side="left")

        def _ov_import_audio(src_path: str) -> None:
            """Importa qualquer formato de áudio como referência OmniVoice,
            convertendo para WAV 24 kHz mono via ffmpeg interno se necessário.
            Imports any audio format as OmniVoice reference, converting to
            WAV 24 kHz mono via internal ffmpeg when needed."""
            import os, subprocess
            src_path = src_path.strip()
            if not src_path or not os.path.exists(src_path):
                self._ov_rec_status.configure(
                    text="❌ Arquivo não encontrado", text_color="#EF4444")
                return
            ext = os.path.splitext(src_path)[1].lower()
            if ext == ".wav":
                # Apara WAV para ≤15s sem recodificar / trim WAV to ≤15s without re-encoding
                wav_path = self._trim_ref_wav(src_path, max_s=15.0)
            else:
                # Converte + apara para ≤15s em uma passagem ffmpeg
                # Convert + trim to ≤15s in a single ffmpeg pass
                self._ov_rec_status.configure(
                    text="Convertendo áudio…", text_color="#F59E0B")
                self.update_idletasks()
                wav_path = "/tmp/ov_ref_import.wav"
                r = subprocess.run(
                    ["ffmpeg", "-y", "-i", src_path, "-t", "15",
                     "-ar", "24000", "-ac", "1", "-sample_fmt", "s16", wav_path],
                    capture_output=True, timeout=60,
                )
                if r.returncode != 0:
                    self._ov_rec_status.configure(
                        text="❌ Conversão falhou", text_color="#EF4444")
                    return
            self._ov_ref_path.set(wav_path)
            # Atualiza entry com nome original / update entry with original filename
            self._ov_import_entry.delete(0, "end")
            self._ov_import_entry.insert(0, os.path.basename(src_path))
            try:
                self._ov_play_ref_btn.configure(state="normal")
            except Exception:
                pass
            self._ov_rec_status.configure(
                text=f"✓ {os.path.basename(src_path)}", text_color="#22C55E")
            self._ov_transcribe()

        def _ov_browse() -> None:
            """Abre diálogo de arquivo com todos os formatos de áudio suportados.
            Opens file dialog with all supported audio formats."""
            import tkinter.filedialog as fd
            path = fd.askopenfilename(
                title="Selecionar áudio de referência",
                filetypes=[
                    ("Áudio", "*.wav *.mp3 *.ogg *.opus *.m4a *.flac *.aac *.mp4 *.webm *.3gp"),
                    ("WAV", "*.wav"),
                    ("MP3", "*.mp3"),
                    ("OGG / Opus  (WhatsApp)", "*.ogg *.opus"),
                    ("M4A / AAC", "*.m4a *.aac"),
                    ("FLAC", "*.flac"),
                    ("Todos", "*.*"),
                ],
            )
            if path:
                _ov_import_audio(path)

        self._ov_rec_prog = ctk.CTkProgressBar(_ov_rec_card, height=5,
                                                fg_color=self.SEG_BG,
                                                progress_color="#DC2626")
        self._ov_rec_prog.set(0)
        self._ov_rec_prog.pack(fill="x", padx=12, pady=(4, 6))

        # ── Importar áudio externo ──────────────────────────────────────────
        # External audio import — any format, converted internally via ffmpeg
        ctk.CTkLabel(_ov_rec_card,
                     text="— ou importe um áudio gravado —",
                     font=ctk.CTkFont(size=10), text_color=self.MUTED,
                     ).pack(pady=(0, 4))

        _ov_import_row = ctk.CTkFrame(_ov_rec_card, fg_color="transparent")
        _ov_import_row.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkButton(
            _ov_import_row, text="📂 Importar", width=100, height=28,
            fg_color=self.SEG_BG, hover_color=self.IBORDER,
            text_color=self.TEXT, border_width=1, border_color=self.IBORDER,
            corner_radius=8, font=ctk.CTkFont(size=12),
            command=_ov_browse,
        ).pack(side="left", padx=(0, 8))

        self._ov_import_entry = ctk.CTkEntry(
            _ov_import_row,
            placeholder_text="WAV · MP3 · OGG · OPUS (WhatsApp) · M4A · FLAC…",
            fg_color=self.SEG_BG, border_color=self.IBORDER,
            text_color=self.TEXT, font=ctk.CTkFont(size=11),
        )
        self._ov_import_entry.pack(side="left", fill="x", expand=True)
        # Enter em campo de caminho importa diretamente / Enter in path field imports directly
        self._ov_import_entry.bind(
            "<Return>",
            lambda e: _ov_import_audio(self._ov_import_entry.get()),
        )

        # Transcrição (preenchida automaticamente após gravação / auto-filled after recording)
        _ref_txt_row = ctk.CTkFrame(_ov_rec_card, fg_color="transparent")
        _ref_txt_row.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkLabel(_ref_txt_row, text="Transcrição:",
                     font=ctk.CTkFont(size=11), text_color=self.MUTED).pack(
            side="left", padx=(0, 8))
        self._ov_ref_text = ctk.CTkEntry(
            _ref_txt_row,
            placeholder_text="Preenchido automaticamente após gravar…",
            fg_color=self.SEG_BG, border_color=self.IBORDER,
            text_color=self.TEXT, font=ctk.CTkFont(size=11),
        )
        self._ov_ref_text.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self._ov_transcribe_btn = ctk.CTkButton(
            _ref_txt_row, text="🔄", width=32, height=28,
            fg_color=self.SEG_BG, hover_color=self.IBORDER,
            text_color=self.MUTED, border_width=1,
            border_color=self.IBORDER, corner_radius=6,
            font=ctk.CTkFont(size=14),
            command=self._ov_transcribe,
        )
        self._ov_transcribe_btn.pack(side="right")

        # Botão para ouvir a gravação de referência / Play button for reference recording
        _ov_play_ref_row = ctk.CTkFrame(_ov_rec_card, fg_color="transparent")
        _ov_play_ref_row.pack(fill="x", padx=12, pady=(0, 4))
        self._ov_play_ref_btn = ctk.CTkButton(
            _ov_play_ref_row, text="▶ Ouvir referência", width=140, height=26,
            fg_color=self.SEG_BG, hover_color=self.IBORDER,
            text_color=self.MUTED, border_width=1,
            border_color=self.IBORDER, corner_radius=6,
            font=ctk.CTkFont(size=11), state="disabled",
            command=self._ov_play_ref,
        )
        self._ov_play_ref_btn.pack(side="left")

        # Campo de nome + botão salvar referência como clone OmniVoice
        # Name field + save button for OmniVoice clone reference
        _ov_name_row = ctk.CTkFrame(_ov_rec_card, fg_color="transparent")
        _ov_name_row.pack(fill="x", padx=12, pady=(0, 10))
        ctk.CTkLabel(_ov_name_row, text="Nome do clone:",
                     font=ctk.CTkFont(size=11), text_color=self.MUTED).pack(
            side="left", padx=(0, 8))
        self._ov_clone_name = ctk.CTkEntry(
            _ov_name_row,
            placeholder_text="ex: Voz Apresentadora…",
            fg_color=self.SEG_BG, border_color=self.IBORDER,
            text_color=self.TEXT, font=ctk.CTkFont(size=11),
        )
        self._ov_clone_name.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            _ov_name_row, text="💾 Salvar clone", width=120, height=28,
            fg_color="#7C3AED", hover_color="#6D28D9",
            text_color="#FFFFFF", corner_radius=6,
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._ov_save_ref,
        ).pack(side="right")

        # ── Card de geração / Generation card ──────────────────────────────
        _ov_gen = ctk.CTkFrame(_ov, fg_color=self.INPUT,
                               border_color=self.IBORDER, border_width=1,
                               corner_radius=8)
        _ov_gen.pack(fill="x", padx=16, pady=(0, 6))

        # Frases genéricas por idioma — todos os idiomas suportados pela plataforma
        # Generic phrases per language — all languages supported by the platform
        _OV_LANG_PHRASES: dict[str, tuple[str, str]] = {
            "🇧🇷 Português":   ("pt", "Olá! Esta é uma demonstração de síntese de voz. A tecnologia reproduz qualquer texto mantendo o timbre natural da voz original."),
            "🇺🇸 English":     ("en", "Hello! This is a voice synthesis demonstration. The technology reproduces any text while preserving the natural timbre of the original voice."),
            "🇪🇸 Español":     ("es", "¡Hola! Esta es una demostración de síntesis de voz. La tecnología reproduce cualquier texto manteniendo el timbre natural de la voz original."),
            "🇫🇷 Français":    ("fr", "Bonjour! Ceci est une démonstration de synthèse vocale. La technologie reproduit n'importe quel texte en conservant le timbre naturel de la voix."),
            "🇩🇪 Deutsch":     ("de", "Hallo! Dies ist eine Demonstration der Sprachsynthese. Die Technologie reproduziert jeden Text und bewahrt dabei den natürlichen Klang der Stimme."),
            "🇮🇹 Italiano":    ("it", "Ciao! Questa è una dimostrazione di sintesi vocale. La tecnologia riproduce qualsiasi testo mantenendo il timbro naturale della voce originale."),
            "🇷🇺 Русский":     ("ru", "Привет! Это демонстрация синтеза речи. Технология воспроизводит любой текст, сохраняя естественный тембр оригинального голоса."),
            "🇨🇳 中文":         ("zh", "你好！这是语音合成演示。该技术可以保持原始声音的自然音色，重现任何文本内容。"),
            "🇳🇱 Nederlands":   ("nl", "Hallo! Dit is een demonstratie van spraaksynthese. De technologie reproduceert elke tekst met behoud van het natuurlijke timbre van de stem."),
            "🇵🇱 Polski":      ("pl", "Cześć! To jest demonstracja syntezy mowy. Technologia reprodukuje dowolny tekst, zachowując naturalną barwę oryginalnego głosu."),
            "🇺🇦 Українська":  ("uk", "Привіт! Це демонстрація синтезу мовлення. Технологія відтворює будь-який текст, зберігаючи природний тембр голосу."),
            "🇹🇷 Türkçe":      ("tr", "Merhaba! Bu bir ses sentezi gösterimidir. Teknoloji, orijinal sesin doğal tınısını koruyarak herhangi bir metni yeniden üretebilir."),
            "🇸🇦 العربية":      ("ar", "مرحباً! هذا عرض توضيحي لتوليف الصوت. تستطيع هذه التقنية إعادة إنتاج أي نص مع الحفاظ على الجرس الطبيعي للصوت الأصلي."),
            "🇮🇳 हिन्दी":       ("hi", "नमस्ते! यह एक वाक् संश्लेषण प्रदर्शन है। यह तकनीक मूल आवाज़ की प्राकृतिक ध्वनि को बनाए रखते हुए किसी भी पाठ को पुनः उत्पन्न कर सकती है।"),
        }

        # Linha de seleção de idioma para teste / language selection row for test
        _lang_row = ctk.CTkFrame(_ov_gen, fg_color="transparent")
        _lang_row.pack(fill="x", padx=12, pady=(8, 4))

        ctk.CTkLabel(_lang_row, text="Testar por idioma:",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self.TEXT).pack(side="left")

        self._ov_test_lang_var = ctk.StringVar(value="🇧🇷 Português")
        self._ov_lang_code = "pt"  # código ISO passado ao generate() / ISO code passed to generate()

        def _ov_on_lang_change(label: str) -> None:
            code, _ = _OV_LANG_PHRASES.get(label, ("pt", ""))
            self._ov_lang_code = code

        _ov_lang_menu = ctk.CTkOptionMenu(
            _lang_row, values=list(_OV_LANG_PHRASES.keys()),
            variable=self._ov_test_lang_var,
            fg_color=self.SEG_BG, button_color=self.IBORDER,
            button_hover_color=self.SEG_BG, text_color=self.TEXT,
            dropdown_fg_color=self.CARD, dropdown_text_color=self.TEXT,
            dropdown_hover_color=self.SEG_BG, font=ctk.CTkFont(size=12),
            width=160, command=_ov_on_lang_change,
        )
        _ov_lang_menu.pack(side="left", padx=(8, 8))

        def _ov_fill_test_phrase() -> None:
            """Preenche o campo de texto com a frase genérica do idioma selecionado.
            Fills the text field with the generic phrase for the selected language."""
            lang_label = self._ov_test_lang_var.get()
            _, phrase = _OV_LANG_PHRASES.get(lang_label, ("pt", "Olá! Teste de voz."))
            self._ov_gen_text.delete("1.0", "end")
            self._ov_gen_text.insert("1.0", phrase)

        # Botão para preencher frase do idioma sem sobrescrever texto personalizado
        # Button to fill language phrase without overwriting custom text
        ctk.CTkButton(
            _lang_row, text="↺ Frase", width=72, height=28,
            fg_color=self.SEG_BG, hover_color=self.HOVER,
            text_color=self.TEXT, corner_radius=8,
            font=ctk.CTkFont(size=12),
            command=_ov_fill_test_phrase,
        ).pack(side="left", padx=(0, 6))

        # Testar gera o texto que JÁ ESTÁ no campo — não substitui
        # Test generates with whatever is already in the text field — does not replace
        ctk.CTkButton(
            _lang_row, text="🔊 Testar", width=90, height=28,
            fg_color=self.ACCENT, hover_color=self.HOVER,
            text_color="#FFFFFF", corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._ov_generate,
        ).pack(side="left")

        # Separador / divider
        ctk.CTkLabel(_ov_gen, text="— ou edite o texto manualmente —",
                     font=ctk.CTkFont(size=10), text_color=self.MUTED).pack(pady=(0, 2))

        self._ov_gen_text = ctk.CTkTextbox(
            _ov_gen, height=72, wrap="word",
            fg_color=self.SEG_BG, border_color=self.IBORDER, border_width=1,
            text_color=self.TEXT, font=ctk.CTkFont(size=12),
        )
        self._ov_gen_text.pack(fill="x", padx=12, pady=(0, 8))
        # Pré-preenche com frase PT-BR / pre-fills with PT-BR phrase
        self._ov_gen_text.insert("1.0", _OV_LANG_PHRASES["🇧🇷 Português"][1])

        _gen_row = ctk.CTkFrame(_ov_gen, fg_color="transparent")
        _gen_row.pack(fill="x", padx=12, pady=(0, 10))

        self._ov_status_lbl = ctk.CTkLabel(
            _gen_row, text="",
            font=ctk.CTkFont(size=11), text_color=self.MUTED)
        self._ov_status_lbl.pack(side="left")

        self._ov_play_btn = ctk.CTkButton(
            _gen_row, text="▶ Ouvir", width=70, height=28,
            fg_color=self.SEG_BG, hover_color=self.IBORDER,
            text_color=self.MUTED, border_width=1,
            border_color=self.IBORDER, corner_radius=6,
            font=ctk.CTkFont(size=11), state="disabled",
            command=self._ov_play_result,
        )
        self._ov_play_btn.pack(side="right", padx=(6, 0))

        self._ov_gen_btn = ctk.CTkButton(
            _gen_row, text="🤖 Gerar voz", width=120, height=30,
            fg_color=self.ACCENT, hover_color=self.HOVER,
            text_color="#FFFFFF", corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._ov_generate,
        )
        self._ov_gen_btn.pack(side="right")

        # Ativa o modo padrão (RVC) / activate default mode (RVC)
        self._switch_clone_mode("🎙 RVC — Treino")

    def _switch_clone_mode(self, mode: str) -> None:
        """Alterna entre seção RVC e OmniVoice na aba Clone.
        Switches between RVC and OmniVoice sections in the Clone tab."""
        if "OmniVoice" in mode:
            self._rvc_section.pack_forget()
            self._ov_section.pack(fill="x")
        else:
            self._ov_section.pack_forget()
            self._rvc_section.pack(fill="x")

    # ── OmniVoice: gravação de referência ────────────────────────────────────

    _OV_REF_MAX_S = 15   # duração máxima da gravação de referência / max reference recording seconds

    def _ov_toggle_recording(self) -> None:
        """Alterna gravação de referência OmniVoice. Toggles OmniVoice reference recording."""
        if getattr(self, "_ov_rec_active", False):
            self._ov_stop_recording()
        else:
            self._ov_start_recording()

    def _ov_start_recording(self) -> None:
        """Inicia gravação de referência OmniVoice via stream compartilhado.
        Starts OmniVoice reference recording using the shared audio stream."""
        if not self._meter_stream:
            self._ov_rec_status.configure(
                text="❌ Sem microfone — verifique o dispositivo na Config",
                text_color="#EF4444")
            return
        self._ov_rec_frames = []
        self._ov_rec_active = True
        self._ov_rec_btn.configure(text="■ Parar", fg_color="#7C3AED",
                                    hover_color="#6D28D9")
        self._ov_rec_status.configure(text="● Gravando — leia o texto acima",
                                       text_color="#DC2626")
        self._ov_rec_prog.set(0)
        self._ov_rec_timer = 0
        self._ov_rec_tick()

    def _ov_rec_tick(self) -> None:
        """Tick a cada segundo durante a gravação de referência OmniVoice.
        Fires every second during OmniVoice reference recording."""
        if not getattr(self, "_ov_rec_active", False):
            return
        self._ov_rec_timer += 1
        self._ov_rec_prog.set(self._ov_rec_timer / self._OV_REF_MAX_S)
        self._ov_rec_status.configure(
            text=f"● Gravando — {self._ov_rec_timer}s / {self._OV_REF_MAX_S}s",
            text_color="#DC2626")
        if self._ov_rec_timer >= self._OV_REF_MAX_S:
            self._ov_stop_recording()
            return
        self.after(1000, self._ov_rec_tick)

    def _ov_stop_recording(self) -> None:
        """Para gravação de referência, salva WAV e transcreve com Whisper.
        Stops reference recording, saves WAV, and transcribes with Whisper."""
        self._ov_rec_active = False
        self._ov_rec_btn.configure(text="● Gravar referência",
                                    fg_color="#DC2626", hover_color="#B91C1C")
        frames = list(self._ov_rec_frames)
        if not frames:
            self._ov_rec_status.configure(text="Sem áudio capturado",
                                           text_color="#EF4444")
            return

        self._ov_rec_status.configure(text="Salvando…", text_color=self.MUTED)

        def _save_and_transcribe():
            import numpy as np, soundfile as sf
            # O stream usa dtype=int16 → normalizar para [-1, 1] antes de sf.write
            # Stream uses dtype=int16 → normalize to [-1, 1] before sf.write (PCM_16 expects float in [-1,1])
            pcm = np.concatenate(frames, axis=0).flatten().astype(np.float32) / 32768.0
            out = "/tmp/ov_ref.wav"
            sr  = getattr(self, "_audio_sr", 44100)
            sf.write(out, pcm, sr, subtype="PCM_16")
            self.after(0, lambda: self._ov_ref_path.set(out))
            self.after(0, lambda: self._ov_rec_status.configure(
                text="Gravado — transcrevendo…", text_color=self.MUTED))
            # Habilita botão de play após gravar / enable play button after recording
            self.after(0, lambda: self._ov_play_ref_btn.configure(state="normal"))
            # Transcrever automaticamente / auto-transcribe
            self.after(0, self._ov_transcribe)

        threading.Thread(target=_save_and_transcribe, daemon=True).start()

    def _ov_play_ref(self) -> None:
        """Toggle play/pause do WAV de referência. Toggle play/pause of reference WAV."""
        # Se já está tocando, mata o processo e volta ao estado inicial
        # If already playing, kill the process and return to idle state
        proc: subprocess.Popen | None = getattr(self, "_ov_play_proc", None)
        if proc and proc.poll() is None:
            proc.kill()
            self._ov_play_proc = None
            self._ov_play_ref_btn.configure(text="▶ Ouvir referência")
            return

        path = self._ov_ref_path.get()
        if not path or not __import__("os").path.exists(path):
            return

        self._ov_play_ref_btn.configure(text="■ Parar")

        def _play():
            self._ov_play_proc = subprocess.Popen(
                ["aplay", path], stderr=subprocess.DEVNULL)
            self._ov_play_proc.wait()
            # Quando terminar naturalmente, restaura o botão
            # When playback finishes naturally, restore button
            self.after(0, lambda: self._ov_play_ref_btn.configure(
                text="▶ Ouvir referência"))
            self._ov_play_proc = None

        threading.Thread(target=_play, daemon=True).start()

    def _ov_transcribe(self) -> None:
        """Transcreve o WAV de referência com Whisper. Transcribes ref WAV with Whisper."""
        path = self._ov_ref_path.get()
        if not path:
            return
        self._ov_transcribe_btn.configure(state="disabled")
        self._ov_rec_status.configure(text="Transcrevendo…", text_color=self.MUTED)

        def _worker():
            try:
                # Usa faster_whisper (mesmo backend do Praxis) / uses faster_whisper (same as Praxis)
                from faster_whisper import WhisperModel
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
                ctype  = "int8_float16" if device == "cuda" else "int8"
                _m = WhisperModel("base", device=device, compute_type=ctype)
                segments, _ = _m.transcribe(path, task="transcribe")
                text = " ".join(s.text.strip() for s in segments).strip()
                self.after(0, lambda: self._ov_ref_text.delete(0, "end"))
                self.after(0, lambda: self._ov_ref_text.insert(0, text))
                self.after(0, lambda: self._ov_rec_status.configure(
                    text="Pronto — revise a transcrição e gere", text_color="#22C55E"))
            except Exception:
                import traceback; traceback.print_exc()
                self.after(0, lambda: self._ov_rec_status.configure(
                    text="Erro na transcrição — edite manualmente", text_color="#F59E0B"))
            finally:
                self.after(0, lambda: self._ov_transcribe_btn.configure(state="normal"))

        threading.Thread(target=_worker, daemon=True).start()

    def _ov_save_ref(self) -> None:
        """Salva WAV de referência + JSON de metadados na pasta de clones OmniVoice.
        Saves reference WAV + metadata JSON to the clones folder as an OmniVoice clone."""
        import re as _re, shutil, wave as _wave

        name = self._ov_clone_name.get().strip()
        if not name:
            self._ov_rec_status.configure(
                text="❌ Digite um nome para o clone", text_color="#EF4444")
            return

        ref_path = self._ov_ref_path.get()
        if not ref_path or not Path(ref_path).exists():
            self._ov_rec_status.configure(
                text="❌ Grave uma referência antes de salvar", text_color="#EF4444")
            return

        ref_text = self._ov_ref_text.get().strip()
        safe = _re.sub(r"[^\w\-]", "_", name)

        wav_p  = self.CLONES_DIR / f"{safe}.wav"
        json_p = self.CLONES_DIR / f"{safe}.json"

        try:
            shutil.copy2(ref_path, wav_p)
            with _wave.open(str(wav_p), "rb") as wf:
                dur = round(wf.getnframes() / wf.getframerate(), 1)

            meta = {
                "name":       name,
                "wav":        f"{safe}.wav",
                "ref_text":   ref_text,
                "duration_s": dur,
                "type":       "omnivoice",
                "lang":       "pt",
            }
            json_p.write_text(json.dumps(meta, ensure_ascii=False, indent=2))

            self._ov_rec_status.configure(
                text=f"✅ Clone «{name}» salvo", text_color="#22C55E")
            self._ov_clone_name.delete(0, "end")
            self.after(200, self._refresh_clone_list)

        except Exception as e:
            self._ov_rec_status.configure(
                text=f"❌ Erro ao salvar: {e}", text_color="#EF4444")

    def _ov_generate(self) -> None:
        """Dispara geração OmniVoice em thread separada.
        Fires OmniVoice generation in a background thread."""
        ref_path = self._ov_ref_path.get()
        ref_text = self._ov_ref_text.get().strip()
        gen_text = self._ov_gen_text.get("1.0", "end").strip()

        if not ref_path:
            self._ov_status_lbl.configure(
                text="❌ Selecione um áudio de referência", text_color="#EF4444")
            return
        if not gen_text:
            self._ov_status_lbl.configure(
                text="❌ Digite o texto a gerar", text_color="#EF4444")
            return

        lang_code = getattr(self, "_ov_lang_code", "pt")
        self._ov_gen_btn.configure(state="disabled", text="Gerando…")
        self._ov_play_btn.configure(state="disabled")
        self._ov_status_lbl.configure(text="Carregando modelo…", text_color=self.MUTED)
        threading.Thread(
            target=self._ov_generate_worker,
            args=(ref_path, ref_text, gen_text, lang_code),
            daemon=True,
        ).start()

    @staticmethod
    def _transcribe_wav(wav_path: str) -> str:
        """Transcreve WAV com faster-whisper 'small' (mais preciso que 'base').
        Transcribes WAV with faster-whisper 'small' (more accurate than 'base').
        Evita TorchCodec do OmniVoice. Avoids OmniVoice's TorchCodec."""
        try:
            from faster_whisper import WhisperModel
            import torch as _t
            _dev   = "cuda" if _t.cuda.is_available() else "cpu"
            _ctype = "int8_float16" if _dev == "cuda" else "int8"
            _wm    = WhisperModel("small", device=_dev, compute_type=_ctype)
            segs, _ = _wm.transcribe(wav_path, task="transcribe")
            return " ".join(s.text.strip() for s in segs).strip()
        except Exception:
            return ""

    @staticmethod
    def _patch_ov_transcribe(model):
        """Monkey-patch do método ASR interno do OmniVoice para usar faster-whisper.
        Monkey-patches OmniVoice's internal ASR to use faster-whisper.

        TorchCodec 0.14 é incompatível com PyTorch 2.6.0+cu124 (undefined symbol:
        aoti_torch_abi_version). O OmniVoice usa TorchCodec internamente para decodificar
        áudio antes do ASR. Substituindo o callable _asr_pipe (ou transcribe) por uma
        implementação faster-whisper, podemos usar ref_text=None e deixar o OmniVoice
        transcrever o ref_audio com alinhamento perfeito — eliminando alucinações por mismatch.

        TorchCodec 0.14 is incompatible with PyTorch 2.6.0+cu124 (undefined symbol:
        aoti_torch_abi_version). OmniVoice uses TorchCodec internally to decode audio
        before ASR. By replacing the _asr_pipe callable (or transcribe) with a
        faster-whisper implementation, we can pass ref_text=None and let OmniVoice
        transcribe ref_audio with perfect alignment — eliminating hallucinations from mismatch.
        """
        import tempfile, soundfile as _sf, numpy as _np

        def _fw_asr(audio_input):
            # audio_input pode ser (array, sr) ou path str
            # audio_input may be (array, sr) tuple or a path str
            if isinstance(audio_input, (list, tuple)) and len(audio_input) == 2:
                arr, sr = audio_input
                arr = _np.asarray(arr)
                if arr.dtype != _np.float32:
                    arr = arr.astype(_np.float32)
                if arr.ndim > 1:
                    arr = arr.mean(axis=-1)  # mono
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    _sf.write(f.name, arr, int(sr), subtype="PCM_16")
                    _path = f.name
            else:
                _path = str(audio_input)

            try:
                from faster_whisper import WhisperModel
                import torch as _t
                _dev   = "cuda" if _t.cuda.is_available() else "cpu"
                _ctype = "int8_float16" if _dev == "cuda" else "int8"
                _wm    = WhisperModel("small", device=_dev, compute_type=_ctype)
                segs, _ = _wm.transcribe(_path, task="transcribe")
                return " ".join(s.text.strip() for s in segs).strip()
            except Exception:
                return ""

        # Tenta patching via atributo _asr_pipe (OmniVoice >= 0.2)
        # Try patching via _asr_pipe attribute (OmniVoice >= 0.2)
        if hasattr(model, "_asr_pipe"):
            model._asr_pipe = _fw_asr
        # Fallback: patch direto no método transcribe (versões mais antigas)
        # Fallback: patch transcribe method directly (older versions)
        if hasattr(model, "transcribe"):
            model.transcribe = _fw_asr
        return model

    @staticmethod
    def _ov_warmup(model, torch_mod) -> None:
        """Aquece kernels CUDA com inferência muda (num_step=4, texto mínimo).
        Warms up CUDA kernels with a dummy inference so the first real test is accurate.

        Sem warm-up: primeira inferência usa kernels não compilados → pitch extractor
        (RMVPE) produz estimativas erradas → timbre distorcido no primeiro teste.
        Without warm-up: first inference uses uncompiled kernels → RMVPE pitch estimates
        are inaccurate → distorted timbre on the first test.
        """
        import tempfile, soundfile as _sf, numpy as _np
        try:
            # Cria WAV de silêncio curto como referência para o warm-up.
            # Creates a short silent WAV as reference for the warm-up.
            _dummy = _np.zeros(int(0.5 * 24000), dtype=_np.float32)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as _f:
                _sf.write(_f.name, _dummy, 24000, subtype="PCM_16")
                _dp = _f.name
            # Usa ref_text explícito — silêncio não tem transcrição útil
            # Use explicit ref_text — silence has no useful transcription
            _p = model.create_voice_clone_prompt(ref_audio=_dp, ref_text="ok")
            model.generate(
                text="ok",
                language="pt",
                voice_clone_prompt=_p,
                audio_chunk_duration=1.0,
                audio_chunk_threshold=0.5,
                guidance_scale=1.0,
                num_step=4,          # mínimo de passos para compilar kernels rapidamente
                postprocess_output=False,
            )
        except Exception:
            pass  # falha no warm-up não é fatal / warm-up failure is non-fatal
        finally:
            if torch_mod.cuda.is_available():
                torch_mod.cuda.empty_cache()

    @staticmethod
    def _trim_ref_wav(wav_path: str, max_s: float = 15.0) -> str:
        """Apara WAV de referência para max_s segundos para evitar OOM em gravações longas.
        Trims reference WAV to max_s seconds to prevent OOM on long recordings."""
        import wave as _wave
        with _wave.open(wav_path, "rb") as wf:
            sr, nch, sw = wf.getframerate(), wf.getnchannels(), wf.getsampwidth()
            dur = wf.getnframes() / sr
            if dur <= max_s:
                return wav_path  # já curto o suficiente / already short enough
            raw = wf.readframes(int(sr * max_s))
        out = "/tmp/ov_ref_trim.wav"
        with _wave.open(out, "wb") as wf:
            wf.setnchannels(nch); wf.setsampwidth(sw); wf.setframerate(sr)
            wf.writeframes(raw)
        return out

    def _ov_generate_worker(self, ref_path: str, ref_text: str, gen_text: str, lang_code: str = "pt") -> None:
        """Worker: roda OmniVoice e salva resultado em /tmp/ov_result.wav.
        Worker: runs OmniVoice and saves result to /tmp/ov_result.wav.
        Usa create_voice_clone_prompt(ref_text=None) para auto-transcrição —
        evita ruído por mismatch entre ref_text e ref_audio.
        Uses create_voice_clone_prompt(ref_text=None) for auto-transcription —
        prevents noise from ref_text/ref_audio mismatch."""
        def _st(msg, color=None):
            self.after(0, lambda: self._ov_status_lbl.configure(
                text=msg, **({"text_color": color} if color else {})))

        try:
            _st("Carregando OmniVoice…")
            from omnivoice import OmniVoice
            import torch, soundfile as sf

            if not hasattr(self, "_ov_model") or self._ov_model is None:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                dtype  = torch.float16 if device == "cuda" else torch.float32
                _st(f"Baixando modelo ({device})… pode demorar na 1ª vez")
                self._ov_model = OmniVoice.from_pretrained(
                    "k2-fsa/OmniVoice", device_map=device, dtype=dtype)
                # Patch: substitui _asr_pipe do OmniVoice por faster-whisper local.
                # TorchCodec 0.14 é incompatível com PyTorch 2.6 (undefined symbol aoti_torch_abi_version).
                # Patch: replace OmniVoice's internal _asr_pipe with local faster-whisper.
                self._ov_model = self._patch_ov_transcribe(self._ov_model)
                # Aquece GPU: compila kernels CUDA para o primeiro teste ser preciso
                # Warm up GPU: compiles CUDA kernels so the first test is accurate
                _st("Aquecendo GPU…")
                self._ov_warmup(self._ov_model, torch)

            # Apara para ≤5s — fronteira ref/target mais limpa
            # Trim to ≤5s — cleaner ref/target boundary
            ref_path = self._trim_ref_wav(ref_path, max_s=5.0)

            # Libera cache CUDA antes da inferência / free CUDA cache before inference
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            # ref_text=None → OmniVoice transcreve internamente via nosso patch Whisper
            # ref_text=None → OmniVoice transcribes internally via our Whisper patch
            _st("Transcrevendo referência…")
            prompt = self._ov_model.create_voice_clone_prompt(
                ref_audio=ref_path, ref_text=None)

            _st("Gerando voz…")
            audio = self._ov_model.generate(
                text=gen_text,
                language=lang_code,
                voice_clone_prompt=prompt,
                speed=0.9,
                guidance_scale=3.5,
                audio_chunk_duration=60.0,
                audio_chunk_threshold=5.0,
                postprocess_output=False,
                num_step=64,
            )

            # Normaliza e salva como PCM_16 para evitar distorção / volume estourado
            # Normalize and save as PCM_16 to avoid distortion / clipped volume
            import numpy as _np
            _audio = _np.array(audio[0], dtype=_np.float32)
            _peak = float(_np.max(_np.abs(_audio)))
            if _peak > 1e-6:
                _audio = _audio / max(_peak, 1.0)
            out_path = "/tmp/ov_result.wav"
            sf.write(out_path, _audio, 24000, subtype="PCM_16")
            self._ov_result_path = out_path
            _st("✓ Pronto — clique em Ouvir", "#22C55E")
            self.after(0, lambda: self._ov_play_btn.configure(state="normal"))
        except Exception:
            import traceback; traceback.print_exc()
            _st("❌ Erro na geração — veja o terminal", "#EF4444")
        finally:
            self.after(0, lambda: self._ov_gen_btn.configure(
                state="normal", text="🤖 Gerar voz"))

    def _ov_play_result(self) -> None:
        """Reproduz /tmp/ov_result.wav. Plays the OmniVoice result WAV."""
        path = getattr(self, "_ov_result_path", "/tmp/ov_result.wav")
        if not __import__("os").path.exists(path):
            return
        def _play():
            import sounddevice as sd, soundfile as sf
            data, sr = sf.read(path, dtype="float32")
            sd.play(data, sr)
            sd.wait()
        threading.Thread(target=_play, daemon=True).start()

    def _refresh_clone_list(self) -> None:
        """Atualiza a lista de clones existentes na aba de clonagem.
        Refreshes the list of existing voice clones in the cloning tab."""
        for w in self._clone_list_frame.winfo_children():
            w.destroy()
        profiles = sorted(self.CLONES_DIR.glob("*.json"))
        if not profiles:
            ctk.CTkLabel(self._clone_list_frame,
                         text="Nenhuma voz clonada ainda.",
                         font=ctk.CTkFont(size=11), text_color=self.MUTED).pack(
                             anchor="w", pady=4)
            return
        for jp in profiles:
            try:
                meta = json.loads(jp.read_text())
            except Exception:
                continue
            name       = meta.get("name", jp.stem)
            dur        = meta.get("duration_s", 0)
            clone_type = meta.get("type", "xtts")
            # Rótulo e cor do motor de clonagem / engine badge label and color
            if clone_type == "omnivoice":
                _engine_lbl, _engine_color = "OmniVoice", "#7C3AED"
            else:
                _engine_lbl, _engine_color = "RVC", "#0EA5E9"

            row  = ctk.CTkFrame(self._clone_list_frame, fg_color=self.SEG_BG,
                                corner_radius=8, border_width=1,
                                border_color=self.IBORDER)
            row.pack(fill="x", pady=(0, 6))
            row.grid_columnconfigure(0, weight=1)

            # Linha de nome: nome + badge de motor / name row: name + engine badge
            name_row = ctk.CTkFrame(row, fg_color="transparent")
            name_row.grid(row=0, column=0, sticky="w", padx=10, pady=6)
            ctk.CTkLabel(name_row, text=name,
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=self.TEXT).pack(side="left")
            ctk.CTkLabel(name_row, text=f"  {dur:.0f}s",
                         font=ctk.CTkFont(size=11),
                         text_color=self.MUTED).pack(side="left")
            ctk.CTkLabel(name_row, text=f" {_engine_lbl}",
                         font=ctk.CTkFont(size=10),
                         text_color=_engine_color).pack(side="left", padx=(6, 0))
            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.grid(row=0, column=1, padx=6)
            wav_path = str(self.CLONES_DIR / meta.get("wav", f"{jp.stem}.wav"))
            _tbtn = ctk.CTkButton(
                btn_frame, text="▶ Testar", width=80, height=26,
                fg_color=self.SEG_BG, hover_color=self.IBORDER,
                text_color=self.MUTED, border_width=1,
                border_color=self.IBORDER, corner_radius=6,
                font=ctk.CTkFont(size=11),
            )
            _tbtn.pack(side="left", padx=(0, 4))
            ctk.CTkButton(
                btn_frame, text="Usar", width=60, height=26,
                fg_color=self.ACCENT, hover_color=self.HOVER,
                text_color="#FFFFFF", corner_radius=6,
                font=ctk.CTkFont(size=11),
                command=lambda p=wav_path, n=name: self._use_clone(p, n),
            ).pack(side="left", padx=(0, 4))
            ctk.CTkButton(
                btn_frame, text="✕", width=26, height=26,
                fg_color=self.SEG_BG, hover_color="#FEE2E2",
                text_color=self.MUTED, border_width=1,
                border_color=self.IBORDER, corner_radius=6,
                font=ctk.CTkFont(size=11),
                command=lambda jp=jp: self._delete_clone(jp),
            ).pack(side="left")

            # Progress bar + status label dentro do card para feedback visual do teste
            # Per-card progress bar + status for visual test feedback
            _card_prog_row = ctk.CTkFrame(row, fg_color="transparent")
            _card_prog_row.grid(row=1, column=0, columnspan=2, sticky="ew",
                                padx=10, pady=(0, 6))
            _card_prog_row.grid_columnconfigure(1, weight=1)
            _card_status = ctk.CTkLabel(_card_prog_row, text="",
                                        font=ctk.CTkFont(size=10),
                                        text_color=self.MUTED, anchor="w", width=160)
            _card_status.grid(row=0, column=0, sticky="w")
            _card_prog = ctk.CTkProgressBar(_card_prog_row, height=4,
                                            progress_color=self.ACCENT,
                                            corner_radius=2)
            _card_prog.set(0)
            _card_prog.grid(row=0, column=1, sticky="ew", padx=(8, 0))
            _card_prog.grid_remove()   # oculta até o teste iniciar / hidden until test starts

            _tbtn.configure(
                command=lambda p=wav_path, rt=meta.get("ref_text", ""), b=_tbtn,
                              pg=_card_prog, st=_card_status:
                    self._test_clone(p, rt, b, pg, st))

    _REC_MAX_S    = 300   # máximo por sessão de gravação / max seconds per recording session
    _REC_MIN_TRAIN = 180  # mínimo para habilitar treino / minimum seconds to enable training

    def _toggle_recording(self) -> None:
        """Alterna entre iniciar e parar a gravação. Toggle recording on/off."""
        if getattr(self, "_rec_active", False):
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self) -> None:
        """Inicia gravação: ativa coleta de frames no stream full-duplex compartilhado.
        Starts recording: activates frame collection in the shared full-duplex stream."""
        if not self._meter_stream:
            self._rec_status.configure(
                text="❌ Sem microfone — verifique o dispositivo de áudio")
            return
        self._rec_frames = []
        self._rec_active = True
        self._rec_btn.configure(text="■ Parar", fg_color="#7C3AED",
                                hover_color="#6D28D9")
        self._rec_status.configure(text="● Gravando — fale agora", text_color="#DC2626")
        self._rec_prog.configure(progress_color="#DC2626")
        self._rec_prog.set(0)
        self._rec_timer = 0
        self._rec_tick()

    def _rec_tick(self) -> None:
        """Tick a cada segundo durante a gravação: atualiza barra de progresso e timer.
        Fires every second during recording: updates progress bar and timer."""
        if getattr(self, "_rec_active", False):
            self._rec_timer += 1
            pct = min(self._rec_timer / self._REC_MAX_S, 1.0)
            self._rec_prog.set(pct)
            self._rec_status.configure(
                text=f"● Gravando — {self._rec_timer}s / {self._REC_MAX_S}s")
            if self._rec_timer >= self._REC_MAX_S:
                self._stop_recording()
                return
            self.after(1000, self._rec_tick)

    def _stop_recording(self) -> None:
        """Para a gravação e inicia o worker de salvamento do áudio.
        Stops recording and starts the audio save worker."""
        self._rec_active = False
        self._rec_btn.configure(text="● Gravar", fg_color="#DC2626",
                                hover_color="#B91C1C", state="disabled")
        self._rec_status.configure(text="Salvando áudio…", text_color=self.MUTED)
        self._rec_prog.configure(progress_color="#60A5FA")
        self._rec_prog.set(0.1)
        threading.Thread(target=self._save_clone_worker, daemon=True).start()

    def _restart_audio_stream(self) -> None:
        """Reinicia o stream quando o dispositivo da Config muda.
        Restarts the stream when the Config device changes."""
        self._stop_meter()
        import time; time.sleep(0.2)
        self._start_meter()

    def _clone_meter_configure(self, event: tk.Event) -> None:
        """Desenha gradiente verde→amarelo→vermelho no canvas do VU meter da clonagem.
        Draws green→yellow→red gradient on the Clone tab VU meter canvas."""
        W, H = event.width, event.height
        if W < 2:
            return
        self._clone_meter_W = W
        self._clone_meter_H = H
        c = self._clone_meter_canvas
        c.delete("all")

        GREEN  = (34,  197,  94)
        YELLOW = (234, 179,   8)
        RED    = (239,  68,  68)

        for i in range(W):
            frac = i / W
            if frac < 0.65:
                t  = frac / 0.65
                r2 = int(GREEN[0]  + (YELLOW[0] - GREEN[0])  * t)
                g2 = int(GREEN[1]  + (YELLOW[1] - GREEN[1])  * t)
                b2 = int(GREEN[2]  + (YELLOW[2] - GREEN[2])  * t)
            else:
                t  = (frac - 0.65) / 0.35
                r2 = int(YELLOW[0] + (RED[0] - YELLOW[0]) * t)
                g2 = int(YELLOW[1] + (RED[1] - YELLOW[1]) * t)
                b2 = int(YELLOW[2] + (RED[2] - YELLOW[2]) * t)
            c.create_line(i, 0, i, H, fill=f"#{r2:02x}{g2:02x}{b2:02x}")

        # Máscara cobre parte não preenchida / mask covers the unfilled region
        self._clone_meter_ids["mask"] = c.create_rectangle(
            0, 0, W, H, fill=self.INPUT, outline="")
        # Linha de pico / peak line
        self._clone_meter_ids["peak"] = c.create_line(
            0, 0, 0, H, fill=self.INPUT, width=2)

    def _clone_meter_update(self, level: float, db: float) -> None:
        """Atualiza máscara e pico do VU meter da clonagem a partir do nível de áudio.
        Updates Clone tab VU meter mask and peak from the current audio level."""
        W = self._clone_meter_W
        H = self._clone_meter_H
        if W < 2 or not self._clone_meter_ids:
            return
        c  = self._clone_meter_canvas
        mx = int(W * level)

        # Move máscara para revelar o gradiente até o nível atual
        # Move mask to reveal gradient up to current level
        c.coords(self._clone_meter_ids["mask"], mx, 0, W, H)

        # Pico: avança rápido, cai devagar (hold + decay)
        # Peak: rises fast, falls slowly (hold + decay)
        if level >= self._clone_meter_peak:
            self._clone_meter_peak = level
        else:
            self._clone_meter_peak = max(0.0, self._clone_meter_peak - 0.008)
        px = int(W * self._clone_meter_peak)
        peak_color = "#EF4444" if db > -6 else "#F59E0B" if db > -18 else "#22C55E"
        c.coords(self._clone_meter_ids["peak"], px, 0, px, H)
        c.itemconfigure(self._clone_meter_ids["peak"], fill=peak_color)

        # Atualiza label dB / update dB label
        self._meter_db_lbl.configure(text=f"{db:.0f} dB")

    def _start_meter(self) -> None:
        """Stream full-duplex compartilhado: VU meter + monitor + gravação.
        Shared full-duplex stream: VU meter + monitor + recording.
        Herda o dispositivo selecionado na aba Config via self.mic_var.
        Inherits the device selected in the Config tab via self.mic_var."""
        # Obter nome PA do dispositivo configurado (sem sufixo :left/:right)
        # Get PA name from configured device (strip :left/:right channel suffix)
        mic_label = getattr(self, "mic_var", None)
        mic_name  = self._label_to_name(mic_label.get(), self._inputs) if mic_label else ""
        pa_in     = mic_name.split(":")[0] if mic_name else ""

        out_label = getattr(self, "out_var", None)
        out_name  = self._label_to_name(out_label.get(), self._outputs) if out_label else ""
        pa_out    = out_name.split(":")[0] if out_name else ""

        def _run():
            try:
                import sounddevice as sd, numpy as np

                # Definir dispositivos padrão no PipeWire para que 'default' aponte para a seleção
                # Set PipeWire defaults so 'default' routes to the selected devices
                if pa_in:
                    subprocess.run(["pactl", "set-default-source", pa_in],
                                   capture_output=True, timeout=3)
                if pa_out:
                    subprocess.run(["pactl", "set-default-sink", pa_out],
                                   capture_output=True, timeout=3)

                SR = 44100  # fixo; PipeWire faz resampling se necessário / fixed; PipeWire resamples if needed

                self._audio_sr = SR

                def _cb(indata, outdata, frames, time_info, status):
                    # VU meter com gradiente (canvas igual ao Config)
                    # Gradient VU meter (canvas identical to Config tab)
                    rms = float(np.sqrt(np.mean(indata.astype(np.float32) ** 2)))
                    db = 20 * np.log10(rms / 32768.0) if rms > 0 else -60.0
                    db = max(-60.0, min(0.0, db))
                    level = (db + 60.0) / 60.0
                    self.after(0, self._clone_meter_update, level, db)

                    # Monitor / loopback
                    if getattr(self, "_monitor_on", False):
                        outdata[:] = indata
                    else:
                        outdata.fill(0)

                    # Gravação RVC / RVC recording
                    if getattr(self, "_rec_active", False):
                        self._rec_frames.append(indata.copy())

                    # Gravação de referência OmniVoice / OmniVoice reference recording
                    if getattr(self, "_ov_rec_active", False):
                        self._ov_rec_frames.append(indata.copy())

                # Abre para dispositivo 'default' que agora aponta para a seleção pactl
                # Opens to 'default' device which now routes to the pactl selection
                with sd.Stream(
                    device=None,
                    samplerate=SR, channels=1, dtype="int16",
                    blocksize=128, latency="low", callback=_cb,
                ) as stream:
                    self._meter_stream = stream
                    while self._meter_stream is not None:
                        import time; time.sleep(0.05)
            except Exception:
                import traceback; traceback.print_exc()

        threading.Thread(target=_run, daemon=True).start()

    def _toggle_monitor(self) -> None:
        """Liga/desliga o monitor de áudio (loopback mic → caixas).
        Toggles audio monitor (mic → speakers loopback). Warns about echo if speakers."""
        on = self._monitor_var.get()
        setattr(self, "_monitor_on", on)
        if on:
            # Aviso de eco quando monitor ligado / echo warning when monitor enabled
            self._monitor_lbl.configure(
                text="🎧 Monitor  ⚠ use fones", text_color="#F59E0B")
        else:
            self._monitor_lbl.configure(text="🎧 Monitor", text_color=self.MUTED)

    def _stop_meter(self) -> None:
        self._meter_stream = None

    def _refresh_dur_label(self) -> None:
        """Atualiza o label de duração acumulada e habilita/desabilita botão de treino.
        Updates accumulated duration label and enables/disables train button."""
        import wave as _wave
        name = self._clone_name_var.get().strip() or "minha_voz"
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        wav_p = self.CLONES_DIR / f"{safe}.wav"
        dur = 0.0
        if wav_p.exists():
            try:
                with _wave.open(str(wav_p), "rb") as wf:
                    dur = wf.getnframes() / wf.getframerate()
            except Exception:
                pass
        mins = int(dur) // 60
        secs = int(dur) % 60
        meta = self._REC_MIN_TRAIN
        if dur >= meta:
            # Áudio suficiente — habilita treino / enough audio — enable training
            self._dur_lbl.configure(
                text=f"✅ {mins}m{secs:02d}s gravados — pronto para treinar!",
                text_color="#22C55E")
            self._train_btn.configure(
                state="normal", fg_color=self.ACCENT,
                hover_color=self.HOVER, text_color="#FFFFFF",
                border_color=self.ACCENT)
        else:
            falta = meta - int(dur)
            self._dur_lbl.configure(
                text=f"{mins}m{secs:02d}s gravados — faltam {falta}s para treinar",
                text_color=self.MUTED)
            self._train_btn.configure(
                state="disabled", fg_color=self.SEG_BG,
                text_color=self.MUTED, border_color=self.IBORDER)

    def _start_train_rvc(self) -> None:
        """Inicia o pipeline de treino RVC em thread separada.
        Starts the RVC training pipeline in a separate thread."""
        if self._training:
            return
        name = self._clone_name_var.get().strip() or "minha_voz"
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        wav_p = self.CLONES_DIR / f"{safe}.wav"
        if not wav_p.exists():
            return
        self._training = True
        self._train_btn.configure(state="disabled", text="Treinando…")
        self._train_prog.set(0)
        self._train_status.configure(text="Iniciando pipeline de treino…", text_color=self.MUTED)
        threading.Thread(
            target=self._train_rvc_worker,
            args=(safe, str(wav_p)),
            daemon=True
        ).start()

    def _train_rvc_worker(self, model_name: str, wav_path: str) -> None:
        """Pipeline completo de treino RVC: pré-processamento → extração → treino.
        Full RVC training pipeline: preprocessing → feature extraction → training.
        Usa Popen para leitura em tempo real e atualiza log + barra de progresso.
        Uses Popen for real-time reading and updates log + progress bar."""
        import subprocess, os, re, shutil, glob

        APPLIO_DIR  = "/home/lab2/Documentos/praxis/applio/src"
        PYTHON      = "/home/lab2/Documentos/praxis/applio/venv/bin/python"
        LOGS_DIR    = os.path.join(APPLIO_DIR, "logs")
        DATASET_DIR = os.path.join(APPLIO_DIR, "assets", "datasets", model_name)
        TOTAL_EPOCHS = 300

        # ── Helpers de UI thread-safe ─────────────────────────────────────
        def _status(msg: str, color: str | None = None) -> None:
            kw: dict = {"text": msg}
            if color:
                kw["text_color"] = color
            self.after(0, self._train_status.configure, kw)

        def _prog(v: float) -> None:
            self.after(0, self._train_prog.set, v)

        def _phase(idx: int, done: bool = False) -> None:
            self.after(0, self._set_train_phase, idx, done)

        def _dash(data: dict) -> None:
            self.after(0, self._update_train_dashboard, data)

        def _run_phase(cmd: list, phase_start: float, phase_end: float,
                       epoch_range: int | None = None) -> bool:
            """Executa subcomando via Popen e alimenta o dashboard em tempo real.
            Runs subprocess via Popen and feeds the dashboard in real time."""
            proc = subprocess.Popen(
                cmd, cwd=APPLIO_DIR,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
            )
            _prog(phase_start)
            for raw in proc.stdout:
                if epoch_range:
                    parsed = self._parse_train_line(raw, total=epoch_range)
                    if parsed:
                        _dash(parsed)
            proc.wait()
            return proc.returncode == 0

        def _done(ok: bool, msg: str) -> None:
            self._training = False
            _status(msg, "#22C55E" if ok else "#DC2626")
            _prog(1.0 if ok else 0.0)
            label = "🎙 Treinar Voz" if ok else "🎙 Tentar de novo"
            self.after(0, self._train_btn.configure, {"state": "normal", "text": label})

        try:
            # Reseta dashboard / reset dashboard to initial state
            self.after(0, self._set_train_phase, 0)

            # ── Fase 1/3: Pré-processamento ───────────────────────────────
            # Phase 1/3: Preprocessing — slice audio into chunks
            _status("Fase 1/3 — Pré-processando áudio…", "#F59E0B")
            _phase(0)
            os.makedirs(DATASET_DIR, exist_ok=True)
            shutil.copy2(wav_path, os.path.join(DATASET_DIR, f"{model_name}.wav"))

            ok = _run_phase([
                PYTHON,
                os.path.join(APPLIO_DIR, "rvc", "train", "preprocess", "preprocess.py"),
                os.path.join(LOGS_DIR, model_name),
                DATASET_DIR,
                "40000", "4", "Automatic", "False", "False",
                "0.7", "3.0", "0.3", "none",
            ], phase_start=0.02, phase_end=0.10)
            if not ok:
                _done(False, "❌ Pré-processamento falhou")
                return
            _phase(0, done=True)
            _prog(0.10)

            # ── Fase 2/3: Extração de features ────────────────────────────
            # Phase 2/3: Feature extraction — HuBERT embeddings + F0 (RMVPE)
            _status("Fase 2/3 — Extraindo features…", "#F59E0B")
            _phase(1)
            ok = _run_phase([
                PYTHON,
                os.path.join(APPLIO_DIR, "rvc", "train", "extract", "extract.py"),
                os.path.join(LOGS_DIR, model_name),
                "rmvpe", "4", "0", "40000", "contentvec", "None", "2",
            ], phase_start=0.10, phase_end=0.33)
            if not ok:
                _done(False, "❌ Extração falhou")
                return
            _phase(1, done=True)
            _prog(0.33)

            # ── Fase 3/3: Treino ──────────────────────────────────────────
            # Phase 3/3: Model training — HiFi-GAN generator + discriminator
            _status("Fase 3/3 — Treinando…", "#8B5CF6")
            _phase(2)

            sys_path_backup = __import__("sys").path[:]
            __import__("sys").path.insert(0, APPLIO_DIR)
            try:
                from rvc.lib.tools.pretrained_selector import pretrained_selector
                pg, pd = pretrained_selector("HiFi-GAN", 40000)
            finally:
                __import__("sys").path[:] = sys_path_backup

            ok = _run_phase([
                PYTHON,
                os.path.join(APPLIO_DIR, "rvc", "train", "train.py"),
                model_name, "10", str(TOTAL_EPOCHS),
                pg, pd, "0", "4", "40000",
                "True", "True", "False",
                "True", "50", "False",
                "HiFi-GAN", "False",
            ], phase_start=0.33, phase_end=0.95, epoch_range=TOTAL_EPOCHS)
            if not ok:
                _done(False, "❌ Treino falhou")
                return
            _phase(2, done=True)

            # ── Copia modelo para a pasta do Praxis ───────────────────────
            # Copy trained model to Praxis voices folder
            _status("Copiando modelo…", "#F59E0B")
            _prog(0.97)

            pth_files = glob.glob(os.path.join(LOGS_DIR, model_name, f"{model_name}*.pth"))
            if not pth_files:
                pth_files = glob.glob(
                    os.path.join(APPLIO_DIR, "assets", "weights", f"{model_name}*.pth"))

            if pth_files:
                pth_files.sort(key=os.path.getmtime)
                shutil.copy2(pth_files[-1], str(self.CLONES_DIR / f"{model_name}.pth"))

                json_p = self.CLONES_DIR / f"{model_name}.json"
                if json_p.exists():
                    meta = json.loads(json_p.read_text())
                    meta["type"] = "rvc"
                    meta["pth"]  = f"{model_name}.pth"
                    json_p.write_text(json.dumps(meta, ensure_ascii=False, indent=2))

                _done(True, f"✅ Modelo {model_name} pronto!")
                self.after(0, self._refresh_clone_list)
            else:
                _done(False, "❌ .pth não encontrado após treino")

        except Exception as e:
            _done(False, f"❌ Erro: {e}")

    def _apply_audio_fx(self, pcm: "np.ndarray", sr: int,
                        status_fn: "callable") -> "np.ndarray":
        """Aplica denoise (DeepFilterNet com resample) e compressor (pedalboard).
        Applies DeepFilterNet denoising (with resampling) and pedalboard compression."""
        import numpy as np

        # Normaliza shape para 1D float32 / normalize to 1D float32
        pcm = np.asarray(pcm, dtype=np.float32).flatten()

        # ── Denoise ────────────────────────────────────────────────────────
        strength = self._denoise_var.get()   # 0.0 → 1.0
        if strength > 0.01:
            try:
                status_fn(f"Reduzindo ruído ({int(strength * 100)}%)…")
                from df import enhance, init_df
                import torch
                from torchaudio.functional import resample as torch_resample

                model, df_state, _ = init_df()
                df_state.set_atten_lim_db(strength * 40.0)   # 0–40 dB de atenuação

                # Resample para o SR do modelo (48 kHz) antes de processar
                # Resample to model SR (48 kHz) before processing
                model_sr = df_state.sr()
                tensor = torch.from_numpy(pcm.reshape(1, -1))
                if sr != model_sr:
                    tensor = torch_resample(tensor, sr, model_sr)

                enhanced = enhance(model, df_state, tensor)

                # Resample de volta ao SR original / resample back to original SR
                if sr != model_sr:
                    enhanced = torch_resample(enhanced, model_sr, sr)

                pcm = enhanced.squeeze(0).numpy()
            except Exception:
                import traceback; traceback.print_exc()

        # ── Compressor ─────────────────────────────────────────────────────
        if getattr(self, "_cmp_on_var", None) and self._cmp_on_var.get():
            try:
                th    = self._cmp_threshold.get()
                ratio = self._cmp_ratio.get()
                atk   = self._cmp_attack.get()
                rel   = self._cmp_release.get()
                status_fn(f"Compressor ({th:.0f}dB  {ratio:.1f}:1  {atk:.0f}/{rel:.0f}ms)…")
                from pedalboard import Pedalboard, Compressor as PBComp
                board = Pedalboard([PBComp(threshold_db=th, ratio=ratio,
                                           attack_ms=atk, release_ms=rel)])
                # pedalboard espera float32 normalizado em (canais, amostras)
                # pedalboard expects normalized float32 in (channels, samples)
                norm = pcm.reshape(1, -1).astype(np.float32) / 32768.0
                pcm = board(norm, sample_rate=float(sr)).reshape(-1) * 32768.0
            except Exception:
                import traceback; traceback.print_exc()

        return pcm

    def _save_clone_worker(self) -> None:
        """Worker: converte frames gravados para WAV e concatena com sessões anteriores.
        Worker: converts recorded frames to WAV and concatenates with previous sessions."""
        def _status(msg, color=None):
            kw = {"text": msg}
            if color:
                kw["text_color"] = color
            self.after(0, self._rec_status.configure, kw)

        def _prog(v, color=None):
            self.after(0, self._rec_prog.set, v)
            if color:
                self.after(0, self._rec_prog.configure, {"progress_color": color})

        try:
            if not self._rec_frames:
                _status("❌ Nenhum áudio capturado — tente gravar novamente.", "#DC2626")
                self.after(0, self._rec_btn.configure, {"state": "normal"})
                _prog(0)
                return

            import numpy as np, wave
            SR = getattr(self, "_audio_sr", 44100)  # SR real do dispositivo / actual device SR

            _status("Concatenando áudio da sessão…")
            _prog(0.3, "#F59E0B")
            # Concatena frames da sessão atual / concatenate frames from current session
            new_pcm = np.concatenate(self._rec_frames, axis=0).astype(np.float32)

            # Aplica denoise + compressor conforme controles da UI
            # Apply denoise + compressor according to UI controls
            new_pcm = self._apply_audio_fx(new_pcm, SR, _status)
            _prog(0.55, "#F59E0B")

            name   = self._clone_name_var.get().strip() or "minha_voz"
            safe   = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
            wav_p  = self.CLONES_DIR / f"{safe}.wav"
            json_p = self.CLONES_DIR / f"{safe}.json"

            # Acumula com gravação anterior se existir / accumulate with previous recording
            if wav_p.exists():
                _status("Acumulando com gravação anterior…")
                _prog(0.45, "#F59E0B")
                with wave.open(str(wav_p), "rb") as wf:
                    existing_raw = wf.readframes(wf.getnframes())
                existing_pcm = np.frombuffer(existing_raw, dtype=np.int16).astype(np.float32)
                # Adiciona 0.3s de silêncio entre sessões / add 0.3s silence between sessions
                silence = np.zeros(int(SR * 0.3), dtype=np.float32)
                combined = np.concatenate([existing_pcm, silence, new_pcm])
            else:
                combined = new_pcm

            dur = len(combined) / SR

            # Normaliza para amplitude 0.88 / normalize to 0.88 amplitude
            _status(f"Normalizando áudio ({dur:.0f}s total)…")
            _prog(0.65, "#F59E0B")
            peak = np.max(np.abs(combined))
            if peak > 0:
                pcm16 = np.clip(combined * (32767 * 0.88 / peak), -32767, 32767).astype(np.int16)
            else:
                pcm16 = combined.astype(np.int16)

            _status(f"Salvando {safe}.wav…")
            _prog(0.8, "#F59E0B")
            with wave.open(str(wav_p), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(SR)
                wf.writeframes(pcm16.tobytes())

            # Tipo depende do modo de clonagem selecionado / type depends on selected clone mode
            _mode = getattr(self, "_clone_mode_var", None)
            _voice_type = "omnivoice" if (_mode and "OmniVoice" in _mode.get()) else "xtts"
            meta = {
                "name":       name,
                "wav":        wav_p.name,
                "ref_text":   self.CLONE_TEXT,
                "duration_s": round(dur, 1),
                "type":       _voice_type,
                "lang":       self.cfg.get("src", "pt"),
            }
            json_p.write_text(json.dumps(meta, ensure_ascii=False, indent=2))

            _prog(1.0, "#22C55E")
            new_s = len(new_pcm) / SR
            _status(f"✅ +{new_s:.0f}s adicionados — total: {dur:.0f}s gravados.", "#22C55E")
            self.after(0, self._rec_btn.configure, {"state": "normal"})
            self.after(0, self._refresh_clone_list)
            self.after(0, self._refresh_dur_label)

        except Exception as e:
            _status(f"❌ Erro ao salvar: {e}", "#DC2626")
            _prog(0)

        finally:
            self.after(0, self._rec_btn.configure, {"state": "normal"})
            self._start_meter()   # reativa VU meter após gravar/salvar

    def _test_clone(self, wav_path: str, ref_text: str,
                    test_btn: ctk.CTkButton | None = None,
                    test_prog: ctk.CTkProgressBar | None = None,
                    test_status: ctk.CTkLabel | None = None) -> None:
        """Testa clone via OmniVoice (zero-shot) ou XTTS v2 dependendo da disponibilidade.
        Tests clone via OmniVoice (zero-shot) or XTTS v2 depending on availability."""
        if self._testing:
            return
        self._testing = True

        lang_code = getattr(self, "_test_lang_var", ctk.StringVar(value="pt")).get()
        lang_code = lang_code.split(" ")[0] if " " in lang_code else lang_code
        # Lê o texto da caixa do RVC se disponível; fallback para frases padrão
        # Read text from RVC text box if available; fall back to default phrases
        _rvc_txt = getattr(self, "_rvc_test_text", None)
        if _rvc_txt:
            try:
                phrase = _rvc_txt.get("1.0", "end").strip() or TEST_PHRASES.get(lang_code, "Teste de voz.")
            except Exception:
                phrase = TEST_PHRASES.get(lang_code, TEST_PHRASES.get("en", "Hello, this is a voice test."))
        else:
            phrase = TEST_PHRASES.get(lang_code, TEST_PHRASES.get("en", "Hello, this is a voice test."))

        if test_btn:
            try:
                test_btn.configure(state="disabled", text="…")
            except Exception:
                pass

        # Decide backend: OmniVoice se tipo omnivoice OU se XTTS não tiver arquivos baixados
        # Decide backend: OmniVoice if clone type is omnivoice OR if XTTS model files are absent
        _XTTS_DIR = Path.home() / ".local/share/tts/tts_models--multilingual--multi-dataset--xtts_v2"
        _json_p = Path(wav_path).with_suffix(".json")
        _clone_type = "xtts"
        if _json_p.exists():
            try:
                _clone_type = json.loads(_json_p.read_text()).get("type", "xtts")
            except Exception:
                pass
        _xtts_ready = any(_XTTS_DIR.glob("*.pth")) if _XTTS_DIR.exists() else False
        _use_ov = (_clone_type == "omnivoice") or (not _xtts_ready)

        _anim_stop = threading.Event()
        _phase_range = [0.05, 0.50]

        def _set_prog(v: float) -> None:
            if test_prog:
                self.after(0, test_prog.set, v)

        def _animate():
            import time
            if test_prog:
                self.after(0, test_prog.grid)   # exibe progress bar no card / show progress bar in card
            while not _anim_stop.is_set():
                lo, hi = _phase_range
                cur = test_prog.get() if test_prog else 0
                nxt = cur + 0.012 if cur < hi - 0.04 else lo
                _set_prog(nxt)
                time.sleep(0.18)

        def _update(msg, color=None, phase=None):
            if test_status:
                kw: dict = {"text": msg}
                if color:
                    kw["text_color"] = color
                self.after(0, test_status.configure, kw)
            if phase:
                _phase_range[0], _phase_range[1] = phase

        def _done():
            _anim_stop.set()
            self._testing = False
            if test_btn:
                try:
                    self.after(0, lambda: test_btn.configure(
                        state="normal", text="▶ Testar"))
                except Exception:
                    pass

        def _worker_ov():
            # Backend OmniVoice: usa create_voice_clone_prompt(ref_text=None) para
            # auto-transcrição interna — elimina ruído por mismatch de texto/áudio.
            # OmniVoice backend: uses create_voice_clone_prompt(ref_text=None) for
            # internal auto-transcription — eliminates noise from text/audio mismatch.
            anim = threading.Thread(target=_animate, daemon=True)
            anim.start()
            try:
                from omnivoice import OmniVoice
                import torch, soundfile as sf

                if not hasattr(self, "_ov_model") or self._ov_model is None:
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                    dtype  = torch.float16 if device == "cuda" else torch.float32
                    _update(f"Carregando OmniVoice ({device})… aguarde",
                            phase=(0.05, 0.45))
                    self._ov_model = OmniVoice.from_pretrained(
                        "k2-fsa/OmniVoice", device_map=device, dtype=dtype)
                    # Patch ASR interno para faster-whisper — TorchCodec 0.14 incompatível.
                    # Patch internal ASR to faster-whisper — TorchCodec 0.14 incompatible.
                    self._ov_model = self._patch_ov_transcribe(self._ov_model)
                    # Aquece GPU para o primeiro teste ser preciso / warm GPU for accurate first test
                    _update("Aquecendo GPU…", phase=(0.45, 0.50))
                    self._ov_warmup(self._ov_model, torch)
                else:
                    _update("OmniVoice em memória…", phase=(0.05, 0.15))

                # Apara para ≤5s — fronteira ref/target mais limpa
                # Trim to ≤5s — cleaner ref/target boundary
                trimmed = self._trim_ref_wav(wav_path, max_s=5.0)

                # Libera cache CUDA antes da inferência / free CUDA cache before inference
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

                # ref_text=None → OmniVoice transcreve internamente via patch Whisper
                # ref_text=None → OmniVoice transcribes internally via Whisper patch
                _update("Transcrevendo referência…", phase=(0.15, 0.45))
                prompt = self._ov_model.create_voice_clone_prompt(
                    ref_audio=trimmed, ref_text=None)

                _update("Gerando voz de teste…", phase=(0.45, 0.88))
                audio = self._ov_model.generate(
                    text=phrase,
                    language=lang_code,
                    voice_clone_prompt=prompt,
                    speed=0.9,
                    guidance_scale=3.5,
                    audio_chunk_duration=60.0,
                    audio_chunk_threshold=5.0,
                    postprocess_output=False,
                    num_step=64,
                )
                _anim_stop.set()
                _set_prog(0.94)
                _update("Reproduzindo…")
                # Normaliza para ±1.0 e salva como PCM_16 — aplay lê header WAV
                # e toca no formato correto sem distorção nem volume estourado.
                # Normalize to ±1.0 and save as PCM_16 — aplay reads the WAV header
                # and plays at the correct level without distortion or clipping.
                import numpy as _np
                _audio = _np.array(audio[0], dtype=_np.float32)
                _peak = float(_np.max(_np.abs(_audio)))
                if _peak > 1e-6:
                    _audio = _audio / max(_peak, 1.0)  # escala se pico > 1; mantém se ≤ 1
                tmp = "/tmp/praxis_clone_test.wav"
                sf.write(tmp, _audio, 24000, subtype="PCM_16")
                subprocess.run(["aplay", tmp], stderr=subprocess.DEVNULL, timeout=60)
                _set_prog(1.0)
                if test_prog:
                    self.after(0, lambda: test_prog.configure(progress_color="#22C55E"))
                _update("✅ Concluído.", "#22C55E")

            except Exception as e:
                import traceback; traceback.print_exc()
                _set_prog(0)
                _update(f"❌ {e}", "#DC2626")
            finally:
                _done()

        def _worker_xtts():
            # Backend XTTS v2: requer modelo baixado em ~/.local/share/tts/
            # XTTS v2 backend: requires model downloaded to ~/.local/share/tts/
            anim = threading.Thread(target=_animate, daemon=True)
            anim.start()
            try:
                import torch, torchaudio
                # Patch ANTES do import TTS para corrigir incompatibilidade de transformers
                # Patch BEFORE importing TTS to fix transformers incompatibility
                import transformers.pytorch_utils as _pu
                if not hasattr(_pu, "isin_mps_friendly"):
                    _pu.isin_mps_friendly = torch.isin
                from TTS.tts.configs.xtts_config import XttsConfig
                from TTS.tts.models.xtts import Xtts

                device = "cuda" if torch.cuda.is_available() else "cpu"

                if self._xtts_model is None:
                    _update(f"1/3  Carregando XTTS v2 ({device}) — ~15s…",
                            phase=(0.05, 0.48))
                    cfg = XttsConfig()
                    cfg.load_json(str(_XTTS_DIR / "config.json"))
                    m = Xtts.init_from_config(cfg)
                    m.load_checkpoint(cfg, checkpoint_dir=str(_XTTS_DIR), use_deepspeed=False)
                    if device == "cuda":
                        m.cuda()
                    self._xtts_model = m
                else:
                    _update(f"1/3  Modelo em memória ({device})…", phase=(0.05, 0.12))

                if wav_path not in self._xtts_latents:
                    _update("2/3  Extraindo embedding de voz…", phase=(0.48, 0.62))
                    gpt_lat, spk_emb = self._xtts_model.get_conditioning_latents(
                        audio_path=[wav_path],
                        gpt_cond_len=self._xtts_model.config.gpt_cond_len,
                        max_ref_length=60,
                        sound_norm_refs=True,
                    )
                    self._xtts_latents[wav_path] = (gpt_lat, spk_emb)
                else:
                    gpt_lat, spk_emb = self._xtts_latents[wav_path]

                _update("2/3  Sintetizando — ~10s…", phase=(0.62, 0.90))
                out = self._xtts_model.inference(
                    text=phrase,
                    language=lang_code,
                    gpt_cond_latent=gpt_lat,
                    speaker_embedding=spk_emb,
                    temperature=0.65,
                    top_p=0.85,
                    repetition_penalty=5.0,
                    enable_text_splitting=True,
                )
                _wav_tensor = torch.tensor(out["wav"])

                _anim_stop.set()
                _set_prog(0.94)
                _update("3/3  Reproduzindo…")
                import sounddevice as _sd
                _sd.play(_wav_tensor.numpy(), 24000, blocking=True)
                _set_prog(1.0)
                if test_prog:
                    self.after(0, lambda: test_prog.configure(progress_color="#22C55E"))
                _update("✅ Concluído.", "#22C55E")

            except Exception as e:
                import traceback; traceback.print_exc()
                _set_prog(0)
                _update(f"❌ {e}", "#DC2626")
            finally:
                _done()

        if test_prog:
            self.after(0, lambda: test_prog.configure(progress_color="#60A5FA"))
        _set_prog(0.05)
        threading.Thread(target=_worker_ov if _use_ov else _worker_xtts, daemon=True).start()

    def _use_clone(self, wav_path: str, name: str) -> None:
        """Define a voz clonada como voz de saída e vai para aba Config."""
        self._clone_voice_path = wav_path
        self._clone_voice_name = name
        # Atualiza o seletor de voz na aba Config (adiciona item se não existe)
        if hasattr(self, "_voice_menu"):
            cur_vals = list(self._voice_menu.cget("values"))
            label = f"🎙 {name}"
            if label not in cur_vals:
                cur_vals.insert(0, label)
                self._voices.insert(0, (wav_path, label))
                self._voice_menu.configure(values=cur_vals)
            self.voice_var.set(label)
        self._tab_seg.set("⚙  Config")
        self._on_tab_change("⚙  Config")

    def _delete_clone(self, json_path: Path) -> None:
        """Remove clone de voz: apaga JSON, WAV e .pth associados.
        Deletes a voice clone: removes JSON, WAV and associated .pth files."""
        try:
            meta = json.loads(json_path.read_text())
            wav  = self.CLONES_DIR / meta.get("wav", "")
            if wav.exists():
                wav.unlink()
            json_path.unlink()
        except Exception:
            pass
        self._refresh_clone_list()

    # ── Monitor toggle ────────────────────────────────────────────────────────

    def _toggle_monitor(self) -> None:
        """Alterna o monitor de áudio (ouvir a tradução na saída) e salva o estado.
        Toggles the audio monitor (hear translation on output) and saves state."""
        self._monitor = not self._monitor
        if self._monitor:
            self._mon_btn.configure(
                text="● Monitor ativo",
                fg_color=self.MON_ON, hover_color=self.HOVER,
                text_color="#FFFFFF",
            )
        else:
            self._mon_btn.configure(
                text="○ Monitor desligado",
                fg_color=self.MON_OFF, hover_color=self.IBORDER,
                text_color=self.MUTED,
            )

    # ── Bilateral ─────────────────────────────────────────────────────────────

    def _bilateral_section(self, row: int) -> int:
        """Seção de tradução bilateral — capta áudio da chamada e traduz de volta."""
        # Cabeçalho
        hdr = ctk.CTkFrame(self._card, fg_color="transparent")
        hdr.grid(row=row, column=0, columnspan=2, sticky="ew", padx=20, pady=(10, 4))
        hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(hdr, text="BILATERAL",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=self.MUTED).grid(row=0, column=0, sticky="w")
        row += 1

        # Botão toggle
        self._bilat_btn = ctk.CTkButton(
            self._card,
            text="● Bilateral ativo" if self._bilateral else "○ Bilateral desligado",
            height=32, corner_radius=8,
            fg_color=self.MON_ON if self._bilateral else self.MON_OFF,
            hover_color=self.HOVER if self._bilateral else self.IBORDER,
            text_color="#FFFFFF" if self._bilateral else self.MUTED,
            border_width=1, border_color=self.IBORDER,
            font=ctk.CTkFont(size=12),
            command=self._toggle_bilateral,
        )
        self._bilat_btn.grid(row=row, column=0, columnspan=2, sticky="ew",
                             padx=20, pady=(0, 6))
        row += 1

        # Seletor de voz para "voz deles" (voice_in) — aparece só quando ativo
        self._bilat_voice_frame = ctk.CTkFrame(self._card, fg_color="transparent")
        self._bilat_voice_frame.grid(row=row, column=0, columnspan=2,
                                     sticky="ew", padx=20, pady=(0, 4))
        self._bilat_voice_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self._bilat_voice_frame,
                     text="Voz deles (você ouve):",
                     font=ctk.CTkFont(size=12), text_color=self.TEXT).grid(
            row=0, column=0, sticky="w", padx=(0, 8))

        src_code = self.cfg.get("src", "pt")
        in_voices = _voices_for_lang(self._voices if hasattr(self, "_voices") else get_voices(), src_code)
        in_labels = [lbl for _, lbl in in_voices] or ["(nenhuma voz pt)"]
        saved_in = self.cfg.get("voice_in", "")
        saved_in_label = next((lbl for p, lbl in in_voices if p == saved_in), in_labels[0])
        self.voice_in_var = ctk.StringVar(value=saved_in_label)
        self._voice_in_menu = ctk.CTkOptionMenu(
            self._bilat_voice_frame, values=in_labels, variable=self.voice_in_var,
            fg_color=self.INPUT, button_color=self.IBORDER,
            button_hover_color=self.SEG_BG, text_color=self.TEXT,
            dropdown_fg_color=self.CARD, dropdown_text_color=self.TEXT,
            dropdown_hover_color=self.SEG_BG, font=ctk.CTkFont(size=13),
        )
        self._voice_in_menu.grid(row=0, column=1, sticky="ew")
        row += 1

        # Card de instrução de roteamento
        self._bilat_info = ctk.CTkFrame(
            self._card, fg_color=self.SEG_BG,
            border_width=1, border_color=self.IBORDER, corner_radius=8,
        )
        self._bilat_info.grid(row=row, column=0, columnspan=2,
                               sticky="ew", padx=20, pady=(0, 8))
        ctk.CTkLabel(
            self._bilat_info,
            text=(
                "Durante a chamada: no pavucontrol (aba Reprodução),\n"
                "altere a saída do app de chamada para  \"Praxis_Entrada\".\n"
                "A fala deles será traduzida e tocada nos seus fones."
            ),
            font=ctk.CTkFont(size=11), text_color=self.MUTED,
            justify="left", anchor="w",
        ).pack(padx=10, pady=8, anchor="w")
        row += 1

        # Esconde frame de voz/info se bilateral estiver desligado
        if not self._bilateral:
            self._bilat_voice_frame.grid_remove()
            self._bilat_info.grid_remove()

        return row

    def _toggle_bilateral(self) -> None:
        self._bilateral = not self._bilateral
        if self._bilateral:
            self._bilat_btn.configure(
                text="● Bilateral ativo",
                fg_color=self.MON_ON, hover_color=self.HOVER,
                text_color="#FFFFFF",
            )
            self._bilat_voice_frame.grid()
            self._bilat_info.grid()
        else:
            self._bilat_btn.configure(
                text="○ Bilateral desligado",
                fg_color=self.MON_OFF, hover_color=self.IBORDER,
                text_color=self.MUTED,
            )
            self._bilat_voice_frame.grid_remove()
            self._bilat_info.grid_remove()

    def _bilateral_voice_path(self) -> str:
        if not hasattr(self, "voice_in_var") or not hasattr(self, "_voices"):
            return ""
        selected = self.voice_in_var.get()
        return next((p for p, lbl in self._voices if lbl == selected), "")

    # ── Coleta / salva / lança ────────────────────────────────────────────────

    def _collect(self) -> dict:
        """Coleta todos os valores atuais da UI e retorna como dict de configuração.
        Collects all current UI values and returns as a config dict."""
        def code_of(label: str) -> str:
            try:
                return LANG_CODES[LANG_LABELS.index(label)]
            except ValueError:
                return label

        selected_label = self.voice_var.get()
        voice_path = next(
            (p for p, lbl in self._voices if lbl == selected_label), ""
        )
        return {
            "src":            code_of(self.src_var.get()),
            "tgt":            code_of(self.tgt_var.get()),
            "voice_out":      voice_path,
            "voice_in":       self._bilateral_voice_path() if self._bilateral else "",
            "model":          self.model_var.get(),
            "mic":            self._label_to_name(self.mic_var.get(), self._inputs),
            "output":         self._label_to_name(self.out_var.get(), self._outputs),
            "monitor":        self._monitor,
            "mode":           self._mode_var.get(),
            "gate_threshold": round(self._gate_frac * 0.28, 4),
            "ptt_key":        self._ptt_key,
            "theme":          self.cfg.get("theme", "light"),
        }

    def _save(self) -> None:
        """Salva as configurações atuais no arquivo de config. Saves current config to file."""
        save_cfg(self._collect())
        messagebox.showinfo("Praxis", "Configurações salvas.")

    def _launch(self) -> None:
        """Valida config e lança o motor Praxis (praxis.py) como subprocesso.
        Validates config and launches the Praxis engine (praxis.py) as subprocess."""
        cfg = self._collect()
        voice_out = cfg["voice_out"]
        if not voice_out:
            messagebox.showerror("Praxis",
                                 "Selecione a voz de saída antes de iniciar.")
            return
        if not Path(voice_out).exists():
            messagebox.showerror("Praxis",
                                 f"Arquivo de voz não encontrado:\n{voice_out}")
            return
        save_cfg(cfg)

        # Para engine anterior se ainda rodando
        self._stop_engine(collapse=False)

        venv_python = Path.home() / ".local/share/praxis/venv/bin/python3"
        python = str(venv_python) if venv_python.exists() else sys.executable

        cmd_parts = [
            python, str(PRAXIS_PY),
            "--src",       cfg["src"],
            "--tgt",       cfg["tgt"],
            "--voice-out", voice_out,
            "--model",     cfg["model"],
            "--json-out",
        ]
        if cfg["voice_in"]:
            cmd_parts += ["--voice-in", cfg["voice_in"]]
        if cfg["mic"]:
            cmd_parts += ["--mic", cfg["mic"]]
        if cfg["output"]:
            cmd_parts += ["--output", cfg["output"]]
        if cfg["monitor"]:
            cmd_parts += ["--monitor"]
        cmd_parts += ["--mode", cfg.get("mode", "vad")]
        if cfg.get("mode") == "gate":
            cmd_parts += ["--gate-threshold", str(cfg.get("gate_threshold", 0.10))]
        if cfg.get("mode") == "ptt" and cfg.get("ptt_key"):
            cmd_parts += ["--ptt-key", cfg["ptt_key"]]

        # Reset UI de monitoramento
        self._mon_set_status("Iniciando…", "#F59E0B")
        self._mon_prog_bar.set(0)
        self._mon_prog_frame.pack(fill="x", padx=14, pady=(0, 10))
        for box in (self._orig_box, self._trans_box, self._log_box):
            box.configure(state="normal")
            box.delete("1.0", "end")
            box.configure(state="disabled")

        # Inicia engine — inclui cuBLAS da Ollama no LD_LIBRARY_PATH para GPU funcionar
        _env = os.environ.copy()
        _cuda12 = "/usr/local/lib/ollama/cuda_v12"
        if Path(_cuda12).exists():
            _env["LD_LIBRARY_PATH"] = (
                f"{_cuda12}:{_env['LD_LIBRARY_PATH']}"
                if _env.get("LD_LIBRARY_PATH") else _cuda12
            )
        self._engine_log = open("/tmp/praxis_engine.log", "w")
        self._engine_proc = subprocess.Popen(
            cmd_parts,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self._engine_log,
            text=True,
            bufsize=1,
            env=_env,
        )
        threading.Thread(target=self._engine_reader, daemon=True).start()

        # Exibe painel de monitoramento à direita — _left encolhe, _right ocupa 560px
        # Show monitoring panel on the right — _left shrinks, _right takes 560px
        self._left.pack_configure(expand=False)
        self._right.pack(side="left", fill="y")
        self._iniciar_btn.configure(state="disabled", text="Rodando…")
        if hasattr(self, "_theme_btn"):
            self._theme_btn.configure(state="disabled")

    def _stop_engine(self, collapse: bool = True) -> None:
        """Para o subprocesso do motor Praxis. Se collapse=True, recolhe o painel de monitoramento.
        Stops the Praxis engine subprocess. If collapse=True, hides the monitoring panel."""
        proc = getattr(self, "_engine_proc", None)
        if proc and proc.poll() is None:
            proc.terminate()
        self._engine_proc = None

        if collapse:
            self._right.pack_forget()
            self._left.pack_configure(expand=True)  # restaura expansão total
            self._iniciar_btn.configure(state="normal", text="✦  Iniciar")
            self._mon_set_status("Parado", "#EF4444")
        if hasattr(self, "_theme_btn"):
            self._theme_btn.configure(state="normal")
        if hasattr(self, "_apply_voice_btn"):
            self._apply_voice_btn.configure(state="disabled", text="⟳  Aplicar")

    def _engine_reader(self) -> None:
        """Thread que lê o stdout do motor (JSON por linha) e atualiza a UI de monitoramento.
        Thread that reads engine stdout (JSON per line) and updates the monitoring UI."""
        proc = self._engine_proc
        if not proc:
            return
        for raw in proc.stdout:
            line = raw.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                self.after(0, self._log_append, line)
                continue
            etype = ev.get("e")
            if etype == "progress":
                pct = ev.get("pct", 0) / 100
                msg = ev.get("msg", "")
                self.after(0, self._set_progress, pct, msg)
            elif etype == "ready":
                self.after(0, self._on_engine_ready)
            elif etype == "transcript":
                self.after(0, self._mon_append, self._orig_box, ev.get("text", ""))
            elif etype == "translation":
                self.after(0, self._mon_append, self._trans_box, ev.get("text", ""))
            elif etype == "voice_reloaded":
                label = next((lbl for p, lbl in self._voices
                              if p == ev.get("path", "")), ev.get("path", ""))
                self.after(0, self._log_append, f"[voz] {label}")
                self.after(0, lambda: self._apply_voice_btn.configure(
                    state="normal", text="⟳  Aplicar") if hasattr(self, "_apply_voice_btn") else None)
            elif etype == "error":
                self.after(0, self._log_append, f"[erro] {ev.get('msg', '')}")
                self.after(0, lambda: self._apply_voice_btn.configure(
                    state="normal", text="⟳  Aplicar") if hasattr(self, "_apply_voice_btn") else None)
        self.after(0, self._mon_set_status, "Encerrado", "#EF4444")

    def _set_progress(self, pct: float, msg: str) -> None:
        self._mon_prog_bar.set(pct)
        self._mon_prog_bar.configure(progress_color="#F59E0B")
        self._mon_status.configure(text=msg or "Iniciando…")
        self._mon_dot.configure(text_color="#F59E0B")

    def _on_engine_ready(self) -> None:
        self._mon_prog_bar.set(1.0)
        self._mon_prog_bar.configure(progress_color="#22C55E")
        self._mon_set_status("Traduzindo", "#22C55E")
        self.after(800, self._hide_mon_progress)
        if hasattr(self, "_apply_voice_btn"):
            self._apply_voice_btn.configure(state="normal", text="⟳  Aplicar")

    def _hide_mon_progress(self) -> None:
        self._mon_prog_frame.pack_forget()

    def _mon_set_status(self, text: str, color: str) -> None:
        self._mon_dot.configure(text_color=color)
        self._mon_status.configure(text=text)

    def _mon_append(self, widget: ctk.CTkTextbox, text: str) -> None:
        widget.configure(state="normal")
        widget.insert("end", text + "\n\n")
        widget.see("end")
        widget.configure(state="disabled")

    def _log_append(self, text: str) -> None:
        self._log_box.configure(state="normal")
        self._log_box.insert("end", text + "\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")


# ── Janela de Monitoramento ───────────────────────────────────────────────────

class MonitorWindow(ctk.CTkToplevel):
    BG     = "#F5F7FA"
    CARD   = "#FFFFFF"
    BORDER = "#E5E7EB"
    MUTED  = "#6B7280"
    GREEN  = "#22C55E"
    AMBER  = "#F59E0B"
    RED    = "#EF4444"

    def __init__(self, parent, cmd_parts: list):
        super().__init__(parent)
        self.title("Praxis — Monitoramento")
        self.geometry("780x520")
        self.resizable(True, True)
        self.configure(fg_color=self.BG)

        self._proc: subprocess.Popen | None = None
        self._cmd  = cmd_parts

        self._build_ui()
        self._start_engine()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        # ── Status bar ────────────────────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color=self.CARD,
                           border_width=1, border_color=self.BORDER,
                           corner_radius=10)
        top.pack(fill="x", padx=16, pady=(16, 10))

        row1 = ctk.CTkFrame(top, fg_color="transparent", height=42)
        row1.pack(fill="x")
        row1.pack_propagate(False)

        self._dot = ctk.CTkLabel(row1, text="●", font=("Inter", 16),
                                  text_color=self.AMBER)
        self._dot.pack(side="left", padx=(14, 6))

        self._status_lbl = ctk.CTkLabel(row1, text="Iniciando…",
                                         font=("Inter", 13),
                                         text_color="#374151")
        self._status_lbl.pack(side="left")

        ctk.CTkButton(row1, text="Parar", width=80, height=30,
                      fg_color=self.RED, hover_color="#DC2626",
                      font=("Inter", 13, "bold"),
                      command=self._stop_engine).pack(side="right", padx=12)

        # ── Barra de progresso (visível apenas durante loading) ───────────────
        self._prog_frame = ctk.CTkFrame(top, fg_color="transparent", height=18)
        self._prog_frame.pack(fill="x", padx=14, pady=(0, 10))
        self._prog_bar = ctk.CTkProgressBar(self._prog_frame, height=6,
                                             corner_radius=3,
                                             progress_color=self.AMBER,
                                             fg_color=self.BORDER)
        self._prog_bar.pack(fill="x")
        self._prog_bar.set(0)

        # ── Dois painéis ──────────────────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(0, 4))
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._orig_box  = self._make_panel(body, 0, "Você está dizendo")
        self._trans_box = self._make_panel(body, 1, "Sendo enviado")

        # ── Log do engine ─────────────────────────────────────────────────────
        log_card = ctk.CTkFrame(self, fg_color=self.CARD,
                                border_width=1, border_color=self.BORDER,
                                corner_radius=10, height=90)
        log_card.pack(fill="x", padx=16, pady=(0, 12))
        log_card.pack_propagate(False)
        ctk.CTkLabel(log_card, text="Log", font=("Inter", 11, "bold"),
                     text_color=self.MUTED).pack(anchor="w", padx=12, pady=(6, 2))
        self._log_box = ctk.CTkTextbox(log_card, fg_color=self.CARD,
                                        font=("Monospace", 10), border_width=0,
                                        wrap="none", state="disabled",
                                        scrollbar_button_color=self.BORDER,
                                        height=60)
        self._log_box.pack(fill="both", expand=True, padx=8, pady=(0, 6))

    def _make_panel(self, parent, col: int, title: str) -> ctk.CTkTextbox:
        pad = (0, 8) if col == 0 else (8, 0)
        card = ctk.CTkFrame(parent, fg_color=self.CARD,
                             border_width=1, border_color=self.BORDER,
                             corner_radius=12)
        card.grid(row=0, column=col, sticky="nsew", padx=pad)

        ctk.CTkLabel(card, text=title, font=("Inter", 12, "bold"),
                     text_color=self.MUTED).pack(anchor="w", padx=16, pady=(14, 4))

        sep = ctk.CTkFrame(card, fg_color=self.BORDER, height=1)
        sep.pack(fill="x", padx=16)

        box = ctk.CTkTextbox(card, fg_color=self.CARD,
                              font=("Inter", 15), border_width=0,
                              wrap="word", state="disabled",
                              scrollbar_button_color=self.BORDER)
        box.pack(fill="both", expand=True, padx=12, pady=(8, 12))
        return box

    # ── Engine ────────────────────────────────────────────────────────────────

    def _start_engine(self) -> None:
        self._log = open("/tmp/praxis_engine.log", "w")
        self._proc = subprocess.Popen(
            self._cmd,
            stdout=subprocess.PIPE,
            stderr=self._log,
            text=True,
            bufsize=1,
        )
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self) -> None:
        for raw in self._proc.stdout:
            line = raw.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            etype = ev.get("e")
            if etype == "progress":
                pct = ev.get("pct", 0) / 100
                msg = ev.get("msg", "")
                self.after(0, self._set_progress, pct, msg)
            elif etype == "ready":
                self.after(0, self._on_ready)
            elif etype == "transcript":
                self.after(0, self._append, self._orig_box, ev.get("text", ""))
            elif etype == "translation":
                self.after(0, self._append, self._trans_box, ev.get("text", ""))

        self.after(0, self._set_status, "Encerrado", self.RED)

    def _set_progress(self, pct: float, msg: str) -> None:
        self._prog_bar.set(pct)
        self._prog_bar.configure(progress_color=self.AMBER)
        self._status_lbl.configure(text=msg or "Iniciando…")
        self._dot.configure(text_color=self.AMBER)

    def _on_ready(self) -> None:
        self._prog_bar.set(1.0)
        self._prog_bar.configure(progress_color=self.GREEN)
        self._set_status("Traduzindo", self.GREEN)
        self.after(800, self._hide_progress)

    def _hide_progress(self) -> None:
        self._prog_frame.pack_forget()

    def _stop_engine(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
        self._set_status("Parado", self.RED)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_status(self, text: str, color: str) -> None:
        self._dot.configure(text_color=color)
        self._status_lbl.configure(text=text)

    def _append(self, widget: ctk.CTkTextbox, text: str) -> None:
        widget.configure(state="normal")
        widget.insert("end", text + "\n\n")
        widget.see("end")
        widget.configure(state="disabled")

    def _on_close(self) -> None:
        self._stop_engine()
        self.destroy()


if __name__ == "__main__":
    app = ConfigWindow()
    app.mainloop()
