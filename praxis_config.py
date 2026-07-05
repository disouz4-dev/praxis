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
    "pt": "Olá! Este é um teste da voz selecionada.",
    "en": "Hello! This is a test of the selected voice.",
    "es": "¡Hola! Esta es una prueba de la voz seleccionada.",
    "fr": "Bonjour ! Ceci est un test de la voix sélectionnée.",
    "de": "Hallo! Dies ist ein Test der ausgewählten Stimme.",
    "it": "Ciao! Questo è un test della voce selezionata.",
    "ja": "こんにちは！これは選択された音声のテストです。",
    "zh": "你好！这是所选语音的测试。",
    "ko": "안녕하세요! 이것은 선택된 음성의 테스트입니다.",
    "ru": "Привет! Это тест выбранного голоса.",
}


def _voice_lang_code(path: str) -> str:
    """Extrai código de idioma do arquivo de voz (ex: it_IT-paola-medium.onnx → 'it')."""
    stem = Path(path).stem          # it_IT-paola-medium
    locale = stem.split("-")[0]     # it_IT
    return locale[:2].lower()       # it


def _voices_for_lang(voices: list[tuple[str, str]], lang_code: str) -> list[tuple[str, str]]:
    """Filtra vozes disponíveis pelo código de idioma."""
    return [(p, lbl) for p, lbl in voices if _voice_lang_code(p) == lang_code]


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
        super().__init__()
        ctk.set_default_color_theme("blue")

        self.cfg = load_cfg()

        # Aplica tema salvo antes de construir qualquer widget
        theme_name = self.cfg.get("theme", "light")
        theme = THEME_DARK if theme_name == "dark" else THEME_LIGHT
        for k, v in theme.items():
            setattr(ConfigWindow, k, v)
        ctk.set_appearance_mode("Dark" if theme_name == "dark" else "Light")

        self._monitor: bool = self.cfg.get("monitor", False)
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
        self.resizable(False, False)
        self.configure(fg_color=self.BG)

        # Centraliza na tela do monitor primário
        ox, oy, sw, sh = _get_primary_monitor()
        if sw == 0:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            ox = oy = 0
        x = ox + (sw - 560) // 2
        y = oy + max(0, (sh - 720) // 2)
        self.geometry(f"560x720+{x}+{y}")

        self.withdraw()  # oculta enquanto splash está aberta

        self._build()
        self._refresh_devices(startup=True)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._set_window_icon()
        self._show_splash()
        self.after(1800, self.deiconify)  # exibe janela principal enquanto splash ainda está visível

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
        self.destroy()

    # ── Ícone e splash ────────────────────────────────────────────────────────

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
        # Contêiner principal: esquerda (config) + direita (monitoramento, oculta)
        self._main = ctk.CTkFrame(self, fg_color="transparent")
        self._main.pack(fill="both", expand=True)

        # PAINEL ESQUERDO — sempre visível, 560px
        self._left = ctk.CTkFrame(self._main, fg_color=self.BG, width=560)
        self._left.pack(side="left", fill="y")
        self._left.pack_propagate(False)

        hdr = ctk.CTkFrame(self._left, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 10))
        # 3 colunas: [spacer, minsize=34] [logo] [botão 34px]
        # minsize=34 espelha largura do botão → logo fica geometricamente centrada
        hdr.grid_columnconfigure(0, weight=1, minsize=34)
        hdr.grid_columnconfigure(1, weight=0)
        hdr.grid_columnconfigure(2, weight=1, minsize=34)

        _is_dark = ctk.get_appearance_mode().lower() == "dark"

        # Botão de tema — canto superior direito, alinhado ao topo
        self._theme_btn = ctk.CTkButton(
            hdr, text="☀" if _is_dark else "☾",
            width=34, height=34,
            fg_color=self.ACCENT, hover_color=self.HOVER,
            text_color="#FFFFFF", border_width=0,
            corner_radius=17, font=ctk.CTkFont(size=15),
            command=self._toggle_theme,
        )
        self._theme_btn.grid(row=0, column=2, sticky="ne")

        # Logo centralizada (col 1, entre os dois spacers de peso igual)
        try:
            from PIL import Image
            _logo_file = "praxis_logo_white.png" if _is_dark else "praxis_logo_black.png"
            _logo_path = ASSETS_DIR / _logo_file
            if not _logo_path.exists():
                _logo_path = ASSETS_DIR / "praxis_logo.png"
            _logo_pil = Image.open(_logo_path).convert("RGBA")
            self._logo_img = ctk.CTkImage(
                light_image=_logo_pil, dark_image=_logo_pil, size=(110, 110))
            ctk.CTkLabel(hdr, image=self._logo_img, text="").grid(row=0, column=1)
        except Exception:
            pass

        # Slogan — abaixo da logo, span nas 3 colunas (centralizado automaticamente)
        ctk.CTkLabel(
            hdr,
            text="Uma mensagem. Todas as línguas.",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.MUTED,
        ).grid(row=1, column=0, columnspan=3, pady=(6, 0))

        self._card = ctk.CTkScrollableFrame(
            self._left, fg_color=self.CARD, corner_radius=14,
            border_width=1, border_color=self.BORDER,
            scrollbar_button_color=self.SEG_BG,
            scrollbar_button_hover_color=self.IBORDER,
        )
        self._card.pack(fill="both", expand=True, padx=24, pady=(12, 8))
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

        # PAINEL DIREITO — monitoramento, oculto até Iniciar
        self._right = ctk.CTkFrame(self._main, fg_color=self.BG,
                                    border_width=1, border_color=self.BORDER,
                                    width=560)
        self._right.pack_propagate(False)
        self._build_monitoring_ui()

    def _idiomas(self, r: int) -> int:
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
        self._optmenu(card, r, 0, LANG_LABELS, self.src_var, pr=8)
        self._optmenu(card, r, 1, _tgt_labels, self.tgt_var, pl=8)
        return r + 1

    def _whisper(self, r: int) -> int:
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
                      command=self._refresh_voices, **btn_kw).pack(side="left")
        return frame

    def _open_download_dialog(self) -> None:
        VoiceDownloadDialog(self, on_downloaded=self._refresh_voices)

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

    # ── Monitor toggle ────────────────────────────────────────────────────────

    def _toggle_monitor(self) -> None:
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

    # ── Coleta / salva / lança ────────────────────────────────────────────────

    def _collect(self) -> dict:
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
            "voice_in":       "",
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
        save_cfg(self._collect())
        messagebox.showinfo("Praxis", "Configurações salvas.")

    def _launch(self) -> None:
        cfg = self._collect()
        voice_out = cfg["voice_out"]
        if not voice_out:
            messagebox.showerror("Praxis",
                                 "Selecione a voz de saída (.onnx) antes de iniciar.")
            return
        if not Path(voice_out).exists():
            messagebox.showerror("Praxis",
                                 f"Arquivo de voz não encontrado:\n{voice_out}\n\n"
                                 "Baixe uma voz Piper e selecione o arquivo .onnx.")
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
            stdout=subprocess.PIPE,
            stderr=self._engine_log,
            text=True,
            bufsize=1,
            env=_env,
        )
        threading.Thread(target=self._engine_reader, daemon=True).start()

        # Expande janela para a direita e exibe painel de monitoramento
        self._right.pack(side="left", fill="both", expand=True)
        self.geometry("1120x720")
        self._iniciar_btn.configure(state="disabled", text="Rodando…")
        if hasattr(self, "_theme_btn"):
            self._theme_btn.configure(state="disabled")

    def _stop_engine(self, collapse: bool = True) -> None:
        proc = getattr(self, "_engine_proc", None)
        if proc and proc.poll() is None:
            proc.terminate()
        self._engine_proc = None

        if collapse:
            self._right.pack_forget()
            self.geometry("560x720")
            self._iniciar_btn.configure(state="normal", text="✦  Iniciar")
            self._mon_set_status("Parado", "#EF4444")
        if hasattr(self, "_theme_btn"):
            self._theme_btn.configure(state="normal")

    def _engine_reader(self) -> None:
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
