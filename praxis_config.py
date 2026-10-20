#!/usr/bin/env python3
"""Praxis — Janela de Configuração."""

import json
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
import urllib.request
from pathlib import Path
from tkinter import messagebox

import numpy as np
import customtkinter as ctk

import praxis_platform as plat

CONFIG_FILE = plat.config_dir() / "config.json"
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

# Fontes disponíveis em cada sistema
_MONO_FONT = "Menlo" if plat.IS_MAC else "Consolas" if plat.IS_WIN else "Monospace"
_UI_FONT   = "Helvetica Neue" if plat.IS_MAC else "Segoe UI" if plat.IS_WIN else "DejaVu Sans"

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
    {"lang": "de", "locale": "de_DE", "speaker": "thorsten", "quality": "high",   "gender": "M", "name": "Thorsten", "default": True},
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
MODELS      = ["auto", "tiny", "base", "small", "medium", "large-v2", "large-v3", "large-v3-turbo"]


def _catalog_filename(v: dict) -> str:
    return f"{v['locale']}-{v['speaker']}-{v['quality']}.onnx"


def _catalog_url(v: dict, ext: str = "") -> str:
    l, lo, sp, q = v["lang"], v["locale"], v["speaker"], v["quality"]
    from urllib.parse import quote
    return f"{_HF_BASE}/" + quote(f"{l}/{lo}/{sp}/{q}/{lo}-{sp}-{q}.onnx{ext}")


# ── Tradução da interface ─────────────────────────────────────────────────────

# Nomes de cada idioma, traduzidos para cada um dos 14 idiomas da interface
# Usados para preencher as listas de idioma de origem/destino no idioma da interface
LANG_NAMES_BY_UI: dict[str, dict[str, str]] = {
    "pt": {"pt":"Português","en":"Inglês","es":"Espanhol","fr":"Francês","de":"Alemão","it":"Italiano","ru":"Russo","zh":"Chinês","nl":"Holandês","pl":"Polonês","uk":"Ucraniano","tr":"Turco","ar":"Árabe","hi":"Hindi"},
    "en": {"pt":"Portuguese","en":"English","es":"Spanish","fr":"French","de":"German","it":"Italian","ru":"Russian","zh":"Chinese","nl":"Dutch","pl":"Polish","uk":"Ukrainian","tr":"Turkish","ar":"Arabic","hi":"Hindi"},
    "es": {"pt":"Portugués","en":"Inglés","es":"Español","fr":"Francés","de":"Alemán","it":"Italiano","ru":"Ruso","zh":"Chino","nl":"Holandés","pl":"Polaco","uk":"Ucraniano","tr":"Turco","ar":"Árabe","hi":"Hindi"},
    "fr": {"pt":"Portugais","en":"Anglais","es":"Espagnol","fr":"Français","de":"Allemand","it":"Italien","ru":"Russe","zh":"Chinois","nl":"Néerlandais","pl":"Polonais","uk":"Ukrainien","tr":"Turc","ar":"Arabe","hi":"Hindi"},
    "de": {"pt":"Portugiesisch","en":"Englisch","es":"Spanisch","fr":"Französisch","de":"Deutsch","it":"Italienisch","ru":"Russisch","zh":"Chinesisch","nl":"Niederländisch","pl":"Polnisch","uk":"Ukrainisch","tr":"Türkisch","ar":"Arabisch","hi":"Hindi"},
    "it": {"pt":"Portoghese","en":"Inglese","es":"Spagnolo","fr":"Francese","de":"Tedesco","it":"Italiano","ru":"Russo","zh":"Cinese","nl":"Olandese","pl":"Polacco","uk":"Ucraino","tr":"Turco","ar":"Arabo","hi":"Hindi"},
    "ru": {"pt":"Португальский","en":"Английский","es":"Испанский","fr":"Французский","de":"Немецкий","it":"Итальянский","ru":"Русский","zh":"Китайский","nl":"Нидерландский","pl":"Польский","uk":"Украинский","tr":"Турецкий","ar":"Арабский","hi":"Хинди"},
    "zh": {"pt":"葡萄牙语","en":"英语","es":"西班牙语","fr":"法语","de":"德语","it":"意大利语","ru":"俄语","zh":"中文","nl":"荷兰语","pl":"波兰语","uk":"乌克兰语","tr":"土耳其语","ar":"阿拉伯语","hi":"印地语"},
    "nl": {"pt":"Portugees","en":"Engels","es":"Spaans","fr":"Frans","de":"Duits","it":"Italiaans","ru":"Russisch","zh":"Chinees","nl":"Nederlands","pl":"Pools","uk":"Oekraïens","tr":"Turks","ar":"Arabisch","hi":"Hindi"},
    "pl": {"pt":"Portugalski","en":"Angielski","es":"Hiszpański","fr":"Francuski","de":"Niemiecki","it":"Włoski","ru":"Rosyjski","zh":"Chiński","nl":"Niderlandzki","pl":"Polski","uk":"Ukraiński","tr":"Turecki","ar":"Arabski","hi":"Hindi"},
    "uk": {"pt":"Португальська","en":"Англійська","es":"Іспанська","fr":"Французька","de":"Німецька","it":"Італійська","ru":"Російська","zh":"Китайська","nl":"Нідерландська","pl":"Польська","uk":"Українська","tr":"Турецька","ar":"Арабська","hi":"Гінді"},
    "tr": {"pt":"Portekizce","en":"İngilizce","es":"İspanyolca","fr":"Fransızca","de":"Almanca","it":"İtalyanca","ru":"Rusça","zh":"Çince","nl":"Hollandaca","pl":"Lehçe","uk":"Ukraynaca","tr":"Türkçe","ar":"Arapça","hi":"Hintçe"},
    "ar": {"pt":"البرتغالية","en":"الإنجليزية","es":"الإسبانية","fr":"الفرنسية","de":"الألمانية","it":"الإيطالية","ru":"الروسية","zh":"الصينية","nl":"الهولندية","pl":"البولندية","uk":"الأوكرانية","tr":"التركية","ar":"العربية","hi":"الهندية"},
    "hi": {"pt":"पुर्तगाली","en":"अंग्रेज़ी","es":"स्पेनी","fr":"फ़्रांसीसी","de":"जर्मन","it":"इतालवी","ru":"रूसी","zh":"चीनी","nl":"डच","pl":"पोलिश","uk":"यूक्रेनी","tr":"तुर्की","ar":"अरबी","hi":"हिन्दी"},
}

_UI_LANG_FLAGS: dict[str, str] = {
    "pt":"🇧🇷", "en":"🇺🇸", "es":"🇪🇸", "fr":"🇫🇷", "de":"🇩🇪",
    "it":"🇮🇹", "ru":"🇷🇺", "zh":"🇨🇳", "nl":"🇳🇱", "pl":"🇵🇱",
    "uk":"🇺🇦", "tr":"🇹🇷", "ar":"🇸🇦", "hi":"🇮🇳",
}

UI_STRINGS: dict[str, dict[str, str]] = {
    "pt": {
        "tagline":        "Uma mensagem. Todas as línguas.",
        "tab_config":     "⚙  Config",
        "tab_clone":      "🎙  Clonar minha voz",
        "btn_save":       "Salvar",
        "btn_start":      "✦  Iniciar",
        "btn_stop":       "✦  Parar",
        "sec_audio":      "Áudio",
        "sec_langs":      "Idiomas",
        "sec_whisper":    "Modelo Whisper",
        "sec_voice_out":  "Voz de saída",
        "lbl_input":      "Entrada  (microfone)",
        "lbl_output":     "Saída  (fones / caixas)",
        "lbl_sys_default":"(padrão do sistema)",
        "mon_on":         "● Monitor ativo",
        "mon_off":        "○ Monitor desligado",
        "mon_hint":       "Ouvir a tradução na saída selecionada acima",
        "bilat_on":       "● Bilateral ativo",
        "bilat_off":      "○ Bilateral desligado",
        "bilat_label":    "BILATERAL",
        "bilat_voice":    "Voz deles (você ouve):",
        "mode_vad":       "VAD automático",
        "mode_gate":      "Gate threshold",
        "mode_ptt":       "Push-to-talk",
        "ptt_none":       "(nenhum configurado)",
        "btn_configure":  "Configurar botão",
        "lbl_src_lang":   "Você fala",
        "lbl_tgt_lang":   "Traduzir para",
        "ov_title":       "OmniVoice — Clonagem zero-shot",
        "ov_desc":        "Grave ~10s da sua voz lendo o texto abaixo, depois clique em Gerar.\nO Whisper transcreve automaticamente — sem treino necessário.",
        "ov_read_aloud":  "Leia este trecho em voz alta:",
        "ov_ref_text":    "Olá! Estou gravando uma amostra de voz para o sistema de clonagem. A tecnologia aprende com poucos segundos de áudio e reproduz qualquer texto mantendo o timbre e a entonação natural da voz gravada.",
        "btn_rec_ref":    "● Gravar referência",
        "btn_stop_rec":   "■ Parar gravação",
        "lbl_ready":      "Pronto — grave ~10s",
        "btn_import":     "📁  Importar áudio",
        "lbl_import_hint":"WAV · MP3 · OGG · OPUS · M4A · FLAC · WhatsApp",
        "lbl_profile_name":"Nome do perfil",
        "btn_test":       "▶  Testar",
        "btn_use":        "✓  Usar",
        "btn_generate":   "Gerar Clone",
        "lbl_no_clones":  "Nenhum clone salvo",
        "lbl_test_phrase":"Frase de teste",
        "lbl_their_voice_hint": "Nenhuma voz {lang} instalada",
        "btn_refresh":    "↺",
        "btn_download":   "⬇  Baixar vozes",
        "lbl_cloned_models": "Modelos clonados",
    },
    "en": {
        "tagline":        "One message. Every language.",
        "tab_config":     "⚙  Config",
        "tab_clone":      "🎙  Clone my voice",
        "btn_save":       "Save",
        "btn_start":      "✦  Start",
        "btn_stop":       "✦  Stop",
        "sec_audio":      "Audio",
        "sec_langs":      "Languages",
        "sec_whisper":    "Whisper Model",
        "sec_voice_out":  "Output voice",
        "lbl_input":      "Input  (microphone)",
        "lbl_output":     "Output  (speakers)",
        "lbl_sys_default":"(system default)",
        "mon_on":         "● Monitor active",
        "mon_off":        "○ Monitor off",
        "mon_hint":       "Hear the translation on the selected output above",
        "bilat_on":       "● Bilateral active",
        "bilat_off":      "○ Bilateral off",
        "bilat_label":    "BILATERAL",
        "bilat_voice":    "Their voice (you hear):",
        "mode_vad":       "Auto VAD",
        "mode_gate":      "Gate threshold",
        "mode_ptt":       "Push-to-talk",
        "ptt_none":       "(none configured)",
        "btn_configure":  "Configure button",
        "lbl_src_lang":   "You speak",
        "lbl_tgt_lang":   "Translate to",
        "ov_title":       "OmniVoice — Zero-shot cloning",
        "ov_desc":        "Record ~10s of your voice reading the text below, then click Generate.\nWhisper transcribes automatically — no training needed.",
        "ov_read_aloud":  "Read this text aloud:",
        "ov_ref_text":    "Hello! I am recording a voice sample for the cloning system. The technology learns from just a few seconds of audio and reproduces any text while keeping the natural timbre and intonation of the recorded voice.",
        "btn_rec_ref":    "● Record reference",
        "btn_stop_rec":   "■ Stop recording",
        "lbl_ready":      "Ready — record ~10s",
        "btn_import":     "📁  Import audio",
        "lbl_import_hint":"WAV · MP3 · OGG · OPUS · M4A · FLAC · WhatsApp",
        "lbl_profile_name":"Profile name",
        "btn_test":       "▶  Test",
        "btn_use":        "✓  Use",
        "btn_generate":   "Generate Clone",
        "lbl_no_clones":  "No saved clones",
        "lbl_test_phrase":"Test phrase",
        "lbl_their_voice_hint": "No {lang} voice installed",
        "btn_refresh":    "↺",
        "btn_download":   "⬇  Download voices",
        "lbl_cloned_models": "Cloned voices",
    },
    "es": {
        "tagline":        "Un mensaje. Todos los idiomas.",
        "tab_config":     "⚙  Config",
        "tab_clone":      "🎙  Clonar mi voz",
        "btn_save":       "Guardar",
        "btn_start":      "✦  Iniciar",
        "btn_stop":       "✦  Detener",
        "sec_audio":      "Audio",
        "sec_langs":      "Idiomas",
        "sec_whisper":    "Modelo Whisper",
        "sec_voice_out":  "Voz de salida",
        "lbl_input":      "Entrada  (micrófono)",
        "lbl_output":     "Salida  (auriculares / altavoces)",
        "lbl_sys_default":"(predeterminado del sistema)",
        "mon_on":         "● Monitor activo",
        "mon_off":        "○ Monitor apagado",
        "mon_hint":       "Escuchar la traducción en la salida seleccionada",
        "bilat_on":       "● Bilateral activo",
        "bilat_off":      "○ Bilateral apagado",
        "bilat_label":    "BILATERAL",
        "bilat_voice":    "Su voz (usted escucha):",
        "mode_vad":       "VAD automático",
        "mode_gate":      "Gate threshold",
        "mode_ptt":       "Push-to-talk",
        "ptt_none":       "(ninguno configurado)",
        "btn_configure":  "Configurar botón",
        "lbl_src_lang":   "Usted habla",
        "lbl_tgt_lang":   "Traducir a",
        "ov_title":       "OmniVoice — Clonación zero-shot",
        "ov_desc":        "Grabe ~10s de su voz leyendo el texto abajo, luego haga clic en Generar.\nWhisper transcribe automáticamente — sin entrenamiento.",
        "ov_read_aloud":  "Lea este texto en voz alta:",
        "ov_ref_text":    "¡Hola! Estoy grabando una muestra de voz para el sistema de clonación. La tecnología aprende con pocos segundos de audio y reproduce cualquier texto manteniendo el timbre y la entonación natural de la voz grabada.",
        "btn_rec_ref":    "● Grabar referencia",
        "btn_stop_rec":   "■ Parar grabación",
        "lbl_ready":      "Listo — grabe ~10s",
        "btn_import":     "📁  Importar audio",
        "lbl_import_hint":"WAV · MP3 · OGG · OPUS · M4A · FLAC · WhatsApp",
        "lbl_profile_name":"Nombre del perfil",
        "btn_test":       "▶  Probar",
        "btn_use":        "✓  Usar",
        "btn_generate":   "Generar Clone",
        "lbl_no_clones":  "Sin clones guardados",
        "lbl_test_phrase":"Frase de prueba",
        "lbl_their_voice_hint": "Sin voz {lang} instalada",
        "btn_refresh":    "↺",
        "btn_download":   "⬇  Descargar voces",
        "lbl_cloned_models": "Voces clonadas",
    },
    "fr": {
        "tagline":        "Un message. Toutes les langues.",
        "tab_config":     "⚙  Config",
        "tab_clone":      "🎙  Cloner ma voix",
        "btn_save":       "Enregistrer",
        "btn_start":      "✦  Démarrer",
        "btn_stop":       "✦  Arrêter",
        "sec_audio":      "Audio",
        "sec_langs":      "Langues",
        "sec_whisper":    "Modèle Whisper",
        "sec_voice_out":  "Voix de sortie",
        "lbl_input":      "Entrée  (microphone)",
        "lbl_output":     "Sortie  (casque / haut-parleurs)",
        "lbl_sys_default":"(défaut système)",
        "mon_on":         "● Moniteur actif",
        "mon_off":        "○ Moniteur éteint",
        "mon_hint":       "Écouter la traduction sur la sortie sélectionnée ci-dessus",
        "bilat_on":       "● Bilatéral actif",
        "bilat_off":      "○ Bilatéral éteint",
        "bilat_label":    "BILATÉRAL",
        "bilat_voice":    "Leur voix (vous entendez) :",
        "mode_vad":       "VAD automatique",
        "mode_gate":      "Gate threshold",
        "mode_ptt":       "Push-to-talk",
        "ptt_none":       "(aucun configuré)",
        "btn_configure":  "Configurer bouton",
        "lbl_src_lang":   "Vous parlez",
        "lbl_tgt_lang":   "Traduire en",
        "ov_title":       "OmniVoice — Clonage zero-shot",
        "ov_desc":        "Enregistrez ~10s de votre voix en lisant le texte ci-dessous, puis cliquez sur Générer.\nWhisper transcrit automatiquement — sans entraînement.",
        "ov_read_aloud":  "Lisez ce texte à voix haute :",
        "ov_ref_text":    "Bonjour ! J'enregistre un échantillon vocal pour le système de clonage. La technologie apprend avec quelques secondes d'audio et reproduit n'importe quel texte en conservant le timbre et l'intonation naturels de la voix enregistrée.",
        "btn_rec_ref":    "● Enregistrer référence",
        "btn_stop_rec":   "■ Arrêter enregistrement",
        "lbl_ready":      "Prêt — enregistrez ~10s",
        "btn_import":     "📁  Importer audio",
        "lbl_import_hint":"WAV · MP3 · OGG · OPUS · M4A · FLAC · WhatsApp",
        "lbl_profile_name":"Nom du profil",
        "btn_test":       "▶  Tester",
        "btn_use":        "✓  Utiliser",
        "btn_generate":   "Générer Clone",
        "lbl_no_clones":  "Aucun clone sauvegardé",
        "lbl_test_phrase":"Phrase de test",
        "lbl_their_voice_hint": "Aucune voix {lang} installée",
        "btn_refresh":    "↺",
        "btn_download":   "⬇  Télécharger voix",
        "lbl_cloned_models": "Voix clonées",
    },
    "de": {
        "tagline":        "Eine Nachricht. Alle Sprachen.",
        "tab_config":     "⚙  Einstellungen",
        "tab_clone":      "🎙  Stimme klonen",
        "btn_save":       "Speichern",
        "btn_start":      "✦  Starten",
        "btn_stop":       "✦  Stoppen",
        "sec_audio":      "Audio",
        "sec_langs":      "Sprachen",
        "sec_whisper":    "Whisper-Modell",
        "sec_voice_out":  "Ausgabestimme",
        "lbl_input":      "Eingabe  (Mikrofon)",
        "lbl_output":     "Ausgabe  (Kopfhörer / Lautsprecher)",
        "lbl_sys_default":"(Systemstandard)",
        "mon_on":         "● Monitor aktiv",
        "mon_off":        "○ Monitor aus",
        "mon_hint":       "Übersetzung am ausgewählten Ausgang hören",
        "bilat_on":       "● Bilateral aktiv",
        "bilat_off":      "○ Bilateral aus",
        "bilat_label":    "BILATERAL",
        "bilat_voice":    "Ihre Stimme (Sie hören):",
        "mode_vad":       "Auto VAD",
        "mode_gate":      "Gate threshold",
        "mode_ptt":       "Push-to-talk",
        "ptt_none":       "(keine konfiguriert)",
        "btn_configure":  "Taste konfigurieren",
        "lbl_src_lang":   "Sie sprechen",
        "lbl_tgt_lang":   "Übersetzen in",
        "ov_title":       "OmniVoice — Zero-Shot-Klonierung",
        "ov_desc":        "Nehmen Sie ~10s Ihrer Stimme beim Vorlesen des Textes auf, dann klicken Sie auf Generieren.\nWhisper transkribiert automatisch — kein Training nötig.",
        "ov_read_aloud":  "Lesen Sie diesen Text laut vor:",
        "ov_ref_text":    "Hallo! Ich nehme eine Sprachprobe für das Klonierungs-System auf. Die Technologie lernt aus wenigen Sekunden Audio und reproduziert beliebigen Text, dabei wird der natürliche Klang und die Intonation der aufgezeichneten Stimme beibehalten.",
        "btn_rec_ref":    "● Referenz aufnehmen",
        "btn_stop_rec":   "■ Aufnahme stoppen",
        "lbl_ready":      "Bereit — nehmen Sie ~10s auf",
        "btn_import":     "📁  Audio importieren",
        "lbl_import_hint":"WAV · MP3 · OGG · OPUS · M4A · FLAC · WhatsApp",
        "lbl_profile_name":"Profilname",
        "btn_test":       "▶  Testen",
        "btn_use":        "✓  Verwenden",
        "btn_generate":   "Klon generieren",
        "lbl_no_clones":  "Keine gespeicherten Klone",
        "lbl_test_phrase":"Testsatz",
        "lbl_their_voice_hint": "Keine {lang}-Stimme installiert",
        "btn_refresh":    "↺",
        "btn_download":   "⬇  Stimmen herunterladen",
        "lbl_cloned_models": "Geklonte Stimmen",
    },
    "it": {
        "tagline":        "Un messaggio. Tutte le lingue.",
        "tab_config":     "⚙  Config",
        "tab_clone":      "🎙  Clona la mia voce",
        "btn_save":       "Salva",
        "btn_start":      "✦  Avvia",
        "btn_stop":       "✦  Ferma",
        "sec_audio":      "Audio",
        "sec_langs":      "Lingue",
        "sec_whisper":    "Modello Whisper",
        "sec_voice_out":  "Voce di uscita",
        "lbl_input":      "Ingresso  (microfono)",
        "lbl_output":     "Uscita  (cuffie / altoparlanti)",
        "lbl_sys_default":"(predefinito di sistema)",
        "mon_on":         "● Monitor attivo",
        "mon_off":        "○ Monitor spento",
        "mon_hint":       "Ascoltare la traduzione sull'uscita selezionata sopra",
        "bilat_on":       "● Bilaterale attivo",
        "bilat_off":      "○ Bilaterale spento",
        "bilat_label":    "BILATERALE",
        "bilat_voice":    "La loro voce (senti tu):",
        "mode_vad":       "VAD automatico",
        "mode_gate":      "Gate threshold",
        "mode_ptt":       "Push-to-talk",
        "ptt_none":       "(nessuno configurato)",
        "btn_configure":  "Configura pulsante",
        "lbl_src_lang":   "Parli",
        "lbl_tgt_lang":   "Traduci in",
        "ov_title":       "OmniVoice — Clonazione zero-shot",
        "ov_desc":        "Registra ~10s della tua voce leggendo il testo qui sotto, poi clicca Genera.\nWhisper trascrive automaticamente — senza addestramento.",
        "ov_read_aloud":  "Leggi questo testo ad alta voce:",
        "ov_ref_text":    "Ciao! Sto registrando un campione vocale per il sistema di clonazione. La tecnologia impara da pochi secondi di audio e riproduce qualsiasi testo mantenendo il timbro e l'intonazione naturale della voce registrata.",
        "btn_rec_ref":    "● Registra riferimento",
        "btn_stop_rec":   "■ Stop registrazione",
        "lbl_ready":      "Pronto — registra ~10s",
        "btn_import":     "📁  Importa audio",
        "lbl_import_hint":"WAV · MP3 · OGG · OPUS · M4A · FLAC · WhatsApp",
        "lbl_profile_name":"Nome profilo",
        "btn_test":       "▶  Test",
        "btn_use":        "✓  Usa",
        "btn_generate":   "Genera Clone",
        "lbl_no_clones":  "Nessun clone salvato",
        "lbl_test_phrase":"Frase di test",
        "lbl_their_voice_hint": "Nessuna voce {lang} installata",
        "btn_refresh":    "↺",
        "btn_download":   "⬇  Scarica voci",
        "lbl_cloned_models": "Voci clonate",
    },
    "ru": {
        "tagline":        "Одно сообщение. Все языки.",
        "tab_config":     "⚙  Настройки",
        "tab_clone":      "🎙  Клонировать голос",
        "btn_save":       "Сохранить",
        "btn_start":      "✦  Запустить",
        "btn_stop":       "✦  Остановить",
        "sec_audio":      "Аудио",
        "sec_langs":      "Языки",
        "sec_whisper":    "Модель Whisper",
        "sec_voice_out":  "Выходной голос",
        "lbl_input":      "Вход  (микрофон)",
        "lbl_output":     "Выход  (наушники / динамики)",
        "lbl_sys_default":"(системный по умолчанию)",
        "mon_on":         "● Монитор активен",
        "mon_off":        "○ Монитор выключен",
        "mon_hint":       "Слышать перевод на выбранном выходе выше",
        "bilat_on":       "● Двусторонний активен",
        "bilat_off":      "○ Двусторонний выключен",
        "bilat_label":    "ДВУСТОРОННЕЕ",
        "bilat_voice":    "Их голос (вы слышите):",
        "mode_vad":       "Авто VAD",
        "mode_gate":      "Gate threshold",
        "mode_ptt":       "Push-to-talk",
        "ptt_none":       "(не настроено)",
        "btn_configure":  "Настроить кнопку",
        "lbl_src_lang":   "Вы говорите",
        "lbl_tgt_lang":   "Перевести на",
        "ov_title":       "OmniVoice — Zero-shot клонирование",
        "ov_desc":        "Запишите ~10с вашего голоса, читая текст ниже, затем нажмите Генерировать.\nWhisper транскрибирует автоматически — обучение не требуется.",
        "ov_read_aloud":  "Прочтите этот текст вслух:",
        "ov_ref_text":    "Привет! Я записываю образец голоса для системы клонирования. Технология обучается на нескольких секундах аудио и воспроизводит любой текст, сохраняя тембр и естественную интонацию записанного голоса.",
        "btn_rec_ref":    "● Записать референс",
        "btn_stop_rec":   "■ Стоп запись",
        "lbl_ready":      "Готово — запишите ~10с",
        "btn_import":     "📁  Импортировать аудио",
        "lbl_import_hint":"WAV · MP3 · OGG · OPUS · M4A · FLAC · WhatsApp",
        "lbl_profile_name":"Имя профиля",
        "btn_test":       "▶  Тест",
        "btn_use":        "✓  Использовать",
        "btn_generate":   "Генерировать клон",
        "lbl_no_clones":  "Нет сохранённых клонов",
        "lbl_test_phrase":"Тестовая фраза",
        "lbl_their_voice_hint": "Нет голоса {lang}",
        "btn_refresh":    "↺",
        "btn_download":   "⬇  Загрузить голоса",
        "lbl_cloned_models": "Клонированные голоса",
    },
    "zh": {
        "tagline":        "一条消息。所有语言。",
        "tab_config":     "⚙  设置",
        "tab_clone":      "🎙  克隆我的声音",
        "btn_save":       "保存",
        "btn_start":      "✦  开始",
        "btn_stop":       "✦  停止",
        "sec_audio":      "音频",
        "sec_langs":      "语言",
        "sec_whisper":    "Whisper 模型",
        "sec_voice_out":  "输出语音",
        "lbl_input":      "输入（麦克风）",
        "lbl_output":     "输出（耳机/扬声器）",
        "lbl_sys_default":"（系统默认）",
        "mon_on":         "● 监听已激活",
        "mon_off":        "○ 监听已关闭",
        "mon_hint":       "在上方选择的输出上听取翻译",
        "bilat_on":       "● 双向已激活",
        "bilat_off":      "○ 双向已关闭",
        "bilat_label":    "双向模式",
        "bilat_voice":    "他们的声音（您听到）：",
        "mode_vad":       "自动 VAD",
        "mode_gate":      "Gate threshold",
        "mode_ptt":       "Push-to-talk",
        "ptt_none":       "（未配置）",
        "btn_configure":  "配置按钮",
        "lbl_src_lang":   "您说",
        "lbl_tgt_lang":   "翻译为",
        "ov_title":       "OmniVoice — 零样本克隆",
        "ov_desc":        "录制 ~10s 朗读下方文本的声音，然后点击生成。\nWhisper 自动转录 — 无需训练。",
        "ov_read_aloud":  "大声朗读此文本：",
        "ov_ref_text":    "你好！我正在为克隆系统录制声音样本。该技术只需几秒钟的音频即可学习，并在保留所录声音的自然音色和语调的同时再现任何文本。",
        "btn_rec_ref":    "● 录制参考",
        "btn_stop_rec":   "■ 停止录制",
        "lbl_ready":      "就绪 — 录制 ~10s",
        "btn_import":     "📁  导入音频",
        "lbl_import_hint":"WAV · MP3 · OGG · OPUS · M4A · FLAC · WhatsApp",
        "lbl_profile_name":"配置文件名称",
        "btn_test":       "▶  测试",
        "btn_use":        "✓  使用",
        "btn_generate":   "生成克隆",
        "lbl_no_clones":  "无已保存的克隆",
        "lbl_test_phrase":"测试短语",
        "lbl_their_voice_hint": "未安装 {lang} 语音",
        "btn_refresh":    "↺",
        "btn_download":   "⬇  下载语音",
        "lbl_cloned_models": "克隆语音",
    },
    "nl": {
        "tagline":        "Één bericht. Elke taal.",
        "tab_config":     "⚙  Config",
        "tab_clone":      "🎙  Mijn stem klonen",
        "btn_save":       "Opslaan",
        "btn_start":      "✦  Starten",
        "btn_stop":       "✦  Stoppen",
        "sec_audio":      "Audio",
        "sec_langs":      "Talen",
        "sec_whisper":    "Whisper-model",
        "sec_voice_out":  "Uitgangsstem",
        "lbl_input":      "Ingang  (microfoon)",
        "lbl_output":     "Uitgang  (koptelefoon / luidsprekers)",
        "lbl_sys_default":"(systeemstandaard)",
        "mon_on":         "● Monitor actief",
        "mon_off":        "○ Monitor uit",
        "mon_hint":       "Vertaling horen op de bovenstaande geselecteerde uitgang",
        "bilat_on":       "● Bidirectioneel actief",
        "bilat_off":      "○ Bidirectioneel uit",
        "bilat_label":    "BIDIRECTIONEEL",
        "bilat_voice":    "Hun stem (u hoort):",
        "mode_vad":       "Auto VAD",
        "mode_gate":      "Gate drempel",
        "mode_ptt":       "Push-to-talk",
        "ptt_none":       "(geen geconfigureerd)",
        "btn_configure":  "Knop configureren",
        "lbl_src_lang":   "U spreekt",
        "lbl_tgt_lang":   "Vertaal naar",
        "ov_title":       "OmniVoice — Zero-shot klonen",
        "ov_desc":        "Neem ~10s op terwijl u de tekst hieronder leest, klik dan op Genereer.\nWhisper transcribeert automatisch — geen training vereist.",
        "ov_read_aloud":  "Lees deze tekst hardop:",
        "ov_ref_text":    "Hallo! Ik neem een stemsample op voor het kloonsysteem. De technologie leert van slechts een paar seconden audio en reproduceert elke tekst met behoud van het natuurlijke timbre en de intonatie van de opgenomen stem.",
        "btn_rec_ref":    "● Referentie opnemen",
        "btn_stop_rec":   "■ Stop opname",
        "lbl_ready":      "Klaar — neem ~10s op",
        "btn_import":     "📁  Audio importeren",
        "lbl_import_hint":"WAV · MP3 · OGG · OPUS · M4A · FLAC · WhatsApp",
        "lbl_profile_name":"Profielnaam",
        "btn_test":       "▶  Testen",
        "btn_use":        "✓  Gebruiken",
        "btn_generate":   "Kloon genereren",
        "lbl_no_clones":  "Geen opgeslagen klonen",
        "lbl_test_phrase":"Testzin",
        "lbl_their_voice_hint": "Geen {lang} stem geïnstalleerd",
        "btn_refresh":    "↺",
        "btn_download":   "⬇  Stemmen downloaden",
        "lbl_cloned_models": "Gekloonde stemmen",
    },
    "pl": {
        "tagline":        "Jedna wiadomość. Każdy język.",
        "tab_config":     "⚙  Ustawienia",
        "tab_clone":      "🎙  Sklonuj głos",
        "btn_save":       "Zapisz",
        "btn_start":      "✦  Uruchom",
        "btn_stop":       "✦  Zatrzymaj",
        "sec_audio":      "Audio",
        "sec_langs":      "Języki",
        "sec_whisper":    "Model Whisper",
        "sec_voice_out":  "Głos wyjściowy",
        "lbl_input":      "Wejście  (mikrofon)",
        "lbl_output":     "Wyjście  (słuchawki / głośniki)",
        "lbl_sys_default":"(domyślny systemu)",
        "mon_on":         "● Monitor aktywny",
        "mon_off":        "○ Monitor wyłączony",
        "mon_hint":       "Słuchać tłumaczenia na wybranym wyjściu powyżej",
        "bilat_on":       "● Dwukierunkowe aktywne",
        "bilat_off":      "○ Dwukierunkowe wyłączone",
        "bilat_label":    "DWUKIERUNKOWE",
        "bilat_voice":    "Ich głos (słyszysz):",
        "mode_vad":       "Auto VAD",
        "mode_gate":      "Gate threshold",
        "mode_ptt":       "Push-to-talk",
        "ptt_none":       "(nie skonfigurowano)",
        "btn_configure":  "Skonfiguruj przycisk",
        "lbl_src_lang":   "Mówisz",
        "lbl_tgt_lang":   "Tłumacz na",
        "ov_title":       "OmniVoice — Klonowanie zero-shot",
        "ov_desc":        "Nagraj ~10s swojego głosu czytając tekst poniżej, potem kliknij Generuj.\nWhisper transkrybuje automatycznie — bez treningu.",
        "ov_read_aloud":  "Przeczytaj ten tekst na głos:",
        "ov_ref_text":    "Hej! Nagrywam próbkę głosu dla systemu klonowania. Technologia uczy się z zaledwie kilku sekund audio i odtwarza dowolny tekst, zachowując naturalne brzmienie i intonację nagranego głosu.",
        "btn_rec_ref":    "● Nagraj referencję",
        "btn_stop_rec":   "■ Zatrzymaj nagranie",
        "lbl_ready":      "Gotowe — nagraj ~10s",
        "btn_import":     "📁  Importuj audio",
        "lbl_import_hint":"WAV · MP3 · OGG · OPUS · M4A · FLAC · WhatsApp",
        "lbl_profile_name":"Nazwa profilu",
        "btn_test":       "▶  Test",
        "btn_use":        "✓  Użyj",
        "btn_generate":   "Generuj klon",
        "lbl_no_clones":  "Brak zapisanych klonów",
        "lbl_test_phrase":"Fraza testowa",
        "lbl_their_voice_hint": "Brak głosu {lang}",
        "btn_refresh":    "↺",
        "btn_download":   "⬇  Pobierz głosy",
        "lbl_cloned_models": "Sklonowane głosy",
    },
    "uk": {
        "tagline":        "Одне повідомлення. Всі мови.",
        "tab_config":     "⚙  Налаштування",
        "tab_clone":      "🎙  Клонувати голос",
        "btn_save":       "Зберегти",
        "btn_start":      "✦  Запустити",
        "btn_stop":       "✦  Зупинити",
        "sec_audio":      "Аудіо",
        "sec_langs":      "Мови",
        "sec_whisper":    "Модель Whisper",
        "sec_voice_out":  "Вихідний голос",
        "lbl_input":      "Вхід  (мікрофон)",
        "lbl_output":     "Вихід  (навушники / динаміки)",
        "lbl_sys_default":"(системний за замовчуванням)",
        "mon_on":         "● Монітор активний",
        "mon_off":        "○ Монітор вимкнено",
        "mon_hint":       "Чути переклад на вибраному виходи вище",
        "bilat_on":       "● Двосторонній активний",
        "bilat_off":      "○ Двосторонній вимкнено",
        "bilat_label":    "ДВОСТОРОННЄ",
        "bilat_voice":    "Їх голос (ви чуєте):",
        "mode_vad":       "Авто VAD",
        "mode_gate":      "Gate threshold",
        "mode_ptt":       "Push-to-talk",
        "ptt_none":       "(не налаштовано)",
        "btn_configure":  "Налаштувати кнопку",
        "lbl_src_lang":   "Ви говорите",
        "lbl_tgt_lang":   "Перекласти на",
        "ov_title":       "OmniVoice — Zero-shot клонування",
        "ov_desc":        "Запишіть ~10с вашого голосу, читаючи текст нижче, потім натисніть Генерувати.\nWhisper транскрибує автоматично — навчання не потрібно.",
        "ov_read_aloud":  "Прочитайте цей текст вголос:",
        "ov_ref_text":    "Привіт! Я записую зразок голосу для системи клонування. Технологія навчається на кількох секундах аудіо і відтворює будь-який текст, зберігаючи тембр і природну інтонацію записаного голосу.",
        "btn_rec_ref":    "● Записати референс",
        "btn_stop_rec":   "■ Зупинити запис",
        "lbl_ready":      "Готово — запишіть ~10с",
        "btn_import":     "📁  Імпортувати аудіо",
        "lbl_import_hint":"WAV · MP3 · OGG · OPUS · M4A · FLAC · WhatsApp",
        "lbl_profile_name":"Назва профілю",
        "btn_test":       "▶  Тест",
        "btn_use":        "✓  Використати",
        "btn_generate":   "Генерувати клон",
        "lbl_no_clones":  "Немає збережених клонів",
        "lbl_test_phrase":"Тестова фраза",
        "lbl_their_voice_hint": "Немає голосу {lang}",
        "btn_refresh":    "↺",
        "btn_download":   "⬇  Завантажити голоси",
        "lbl_cloned_models": "Клоновані голоси",
    },
    "tr": {
        "tagline":        "Bir mesaj. Her dil.",
        "tab_config":     "⚙  Ayarlar",
        "tab_clone":      "🎙  Sesimi klonla",
        "btn_save":       "Kaydet",
        "btn_start":      "✦  Başlat",
        "btn_stop":       "✦  Durdur",
        "sec_audio":      "Ses",
        "sec_langs":      "Diller",
        "sec_whisper":    "Whisper Modeli",
        "sec_voice_out":  "Çıkış sesi",
        "lbl_input":      "Giriş  (mikrofon)",
        "lbl_output":     "Çıkış  (kulaklık / hoparlörler)",
        "lbl_sys_default":"(sistem varsayılanı)",
        "mon_on":         "● Monitör aktif",
        "mon_off":        "○ Monitör kapalı",
        "mon_hint":       "Yukarıda seçilen çıkışta çeviriyi duyun",
        "bilat_on":       "● Çift yönlü aktif",
        "bilat_off":      "○ Çift yönlü kapalı",
        "bilat_label":    "ÇİFT YÖNLÜ",
        "bilat_voice":    "Onların sesi (siz duyuyorsunuz):",
        "mode_vad":       "Otomatik VAD",
        "mode_gate":      "Gate threshold",
        "mode_ptt":       "Push-to-talk",
        "ptt_none":       "(hiçbiri yapılandırılmadı)",
        "btn_configure":  "Düğme yapılandır",
        "lbl_src_lang":   "Siz konuşuyorsunuz",
        "lbl_tgt_lang":   "Çeviri dili",
        "ov_title":       "OmniVoice — Zero-shot klonlama",
        "ov_desc":        "Aşağıdaki metni okurken ~10s ses kaydı yapın, ardından Oluştur'a tıklayın.\nWhisper otomatik transkribe eder — eğitim gerekmez.",
        "ov_read_aloud":  "Bu metni sesli okuyun:",
        "ov_ref_text":    "Merhaba! Klonlama sistemi için ses örneği kaydediyorum. Teknoloji, yalnızca birkaç saniyelik sesle öğrenir ve kaydedilen sesin doğal tını ve tonlamasını koruyarak herhangi bir metni yeniden üretir.",
        "btn_rec_ref":    "● Referans kaydet",
        "btn_stop_rec":   "■ Kaydı durdur",
        "lbl_ready":      "Hazır — ~10s kaydedin",
        "btn_import":     "📁  Ses içe aktar",
        "lbl_import_hint":"WAV · MP3 · OGG · OPUS · M4A · FLAC · WhatsApp",
        "lbl_profile_name":"Profil adı",
        "btn_test":       "▶  Test",
        "btn_use":        "✓  Kullan",
        "btn_generate":   "Klon oluştur",
        "lbl_no_clones":  "Kayıtlı klon yok",
        "lbl_test_phrase":"Test cümlesi",
        "lbl_their_voice_hint": "{lang} sesi kurulu değil",
        "btn_refresh":    "↺",
        "btn_download":   "⬇  Ses indir",
        "lbl_cloned_models": "Klonlanmış sesler",
    },
    "ar": {
        "tagline":        "رسالة واحدة. كل اللغات.",
        "tab_config":     "⚙  الإعدادات",
        "tab_clone":      "🎙  استنسخ صوتي",
        "btn_save":       "حفظ",
        "btn_start":      "✦  ابدأ",
        "btn_stop":       "✦  أوقف",
        "sec_audio":      "الصوت",
        "sec_langs":      "اللغات",
        "sec_whisper":    "نموذج Whisper",
        "sec_voice_out":  "صوت الإخراج",
        "lbl_input":      "الإدخال  (الميكروفون)",
        "lbl_output":     "الإخراج  (السماعات)",
        "lbl_sys_default":"(افتراضي النظام)",
        "mon_on":         "● المراقب نشط",
        "mon_off":        "○ المراقب معطل",
        "mon_hint":       "سماع الترجمة على الإخراج المحدد أعلاه",
        "bilat_on":       "● ثنائي الاتجاه نشط",
        "bilat_off":      "○ ثنائي الاتجاه معطل",
        "bilat_label":    "ثنائي الاتجاه",
        "bilat_voice":    "صوتهم (تسمع أنت):",
        "mode_vad":       "VAD تلقائي",
        "mode_gate":      "Gate threshold",
        "mode_ptt":       "Push-to-talk",
        "ptt_none":       "(لم يُضبط)",
        "btn_configure":  "ضبط الزر",
        "lbl_src_lang":   "أنت تتحدث",
        "lbl_tgt_lang":   "ترجمة إلى",
        "ov_title":       "OmniVoice — استنساخ zero-shot",
        "ov_desc":        "سجّل ~10s من صوتك وأنت تقرأ النص أدناه، ثم انقر توليد.\nيُفرَّغ الصوت تلقائياً — لا يلزم تدريب.",
        "ov_read_aloud":  "اقرأ هذا النص بصوت عالٍ:",
        "ov_ref_text":    "مرحباً! أسجّل عيّنة صوتية لنظام الاستنساخ. تتعلم التقنية من ثوانٍ قليلة من الصوت وتُعيد إنتاج أي نص مع الحفاظ على الجرس والنبرة الطبيعية للصوت المُسجَّل.",
        "btn_rec_ref":    "● تسجيل مرجع",
        "btn_stop_rec":   "■ إيقاف التسجيل",
        "lbl_ready":      "جاهز — سجّل ~10s",
        "btn_import":     "📁  استيراد صوت",
        "lbl_import_hint":"WAV · MP3 · OGG · OPUS · M4A · FLAC · WhatsApp",
        "lbl_profile_name":"اسم الملف الشخصي",
        "btn_test":       "▶  اختبار",
        "btn_use":        "✓  استخدام",
        "btn_generate":   "توليد كلون",
        "lbl_no_clones":  "لا توجد كلونات محفوظة",
        "lbl_test_phrase":"جملة اختبار",
        "lbl_their_voice_hint": "لا يوجد صوت {lang} مثبّت",
        "btn_refresh":    "↺",
        "btn_download":   "⬇  تحميل الأصوات",
        "lbl_cloned_models": "الأصوات المستنسخة",
    },
    "hi": {
        "tagline":        "एक संदेश। हर भाषा।",
        "tab_config":     "⚙  सेटिंग्स",
        "tab_clone":      "🎙  मेरी आवाज़ क्लोन करें",
        "btn_save":       "सहेजें",
        "btn_start":      "✦  शुरू करें",
        "btn_stop":       "✦  रोकें",
        "sec_audio":      "ऑडियो",
        "sec_langs":      "भाषाएं",
        "sec_whisper":    "Whisper मॉडल",
        "sec_voice_out":  "आउटपुट आवाज़",
        "lbl_input":      "इनपुट  (माइक्रोफोन)",
        "lbl_output":     "आउटपुट  (हेडफोन / स्पीकर)",
        "lbl_sys_default":"(सिस्टम डिफ़ॉल्ट)",
        "mon_on":         "● मॉनिटर सक्रिय",
        "mon_off":        "○ मॉनिटर बंद",
        "mon_hint":       "ऊपर चुने गए आउटपुट पर अनुवाद सुनें",
        "bilat_on":       "● द्विपक्षीय सक्रिय",
        "bilat_off":      "○ द्विपक्षीय बंद",
        "bilat_label":    "द्विपक्षीय",
        "bilat_voice":    "उनकी आवाज़ (आप सुनते हैं):",
        "mode_vad":       "ऑटो VAD",
        "mode_gate":      "Gate threshold",
        "mode_ptt":       "Push-to-talk",
        "ptt_none":       "(कोई नहीं कॉन्फ़िगर किया)",
        "btn_configure":  "बटन कॉन्फ़िगर करें",
        "lbl_src_lang":   "आप बोलते हैं",
        "lbl_tgt_lang":   "अनुवाद करें",
        "ov_title":       "OmniVoice — Zero-shot क्लोनिंग",
        "ov_desc":        "नीचे का टेक्स्ट पढ़ते हुए ~10s रिकॉर्ड करें, फिर जेनरेट पर क्लिक करें।\nWhisper स्वचालित रूप से ट्रांसक्राइब करता है — कोई ट्रेनिंग नहीं।",
        "ov_read_aloud":  "यह टेक्स्ट ज़ोर से पढ़ें:",
        "ov_ref_text":    "नमस्ते! मैं क्लोनिंग सिस्टम के लिए आवाज़ का नमूना रिकॉर्ड कर रहा हूं। तकनीक कुछ सेकंड के ऑडियो से सीखती है और रिकॉर्ड की गई आवाज़ के प्राकृतिक स्वर और लय को बनाए रखते हुए किसी भी टेक्स्ट को पुन: प्रस्तुत करती है।",
        "btn_rec_ref":    "● रेफरेंस रिकॉर्ड करें",
        "btn_stop_rec":   "■ रिकॉर्डिंग रोकें",
        "lbl_ready":      "तैयार — ~10s रिकॉर्ड करें",
        "btn_import":     "📁  ऑडियो आयात करें",
        "lbl_import_hint":"WAV · MP3 · OGG · OPUS · M4A · FLAC · WhatsApp",
        "lbl_profile_name":"प्रोफ़ाइल नाम",
        "btn_test":       "▶  टेस्ट",
        "btn_use":        "✓  उपयोग करें",
        "btn_generate":   "क्लोन जेनरेट करें",
        "lbl_no_clones":  "कोई सहेजा गया क्लोन नहीं",
        "lbl_test_phrase":"टेस्ट वाक्यांश",
        "lbl_their_voice_hint": "कोई {lang} आवाज़ नहीं",
        "btn_refresh":    "↺",
        "btn_download":   "⬇  आवाज़ें डाउनलोड करें",
        "lbl_cloned_models": "क्लोन आवाज़ें",
    },
}


DEFAULT_CFG: dict = {
    "src":            "pt",
    "tgt":            "en",
    "voice_out":      str(VOICES_DIR / "en_US-lessac-medium.onnx"),
    "voice_in":       "",
    "model":          "auto",       # melhor modelo medido para o hardware
    "mic":            "",
    "output":         "",
    "monitor":        False,
    "mode":           "vad",
    "gate_threshold": 0.10,
    "ptt_key":        "",
    "theme":          "light",
    "ui_lang":        "pt",
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
    """(x, y, w, h) do monitor primário; (0, 0, 0, 0) se desconhecido
    (quem chama usa então o valor do Tk como reserva)."""
    return plat.primary_monitor_geometry()


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


def _window_scaling(win) -> float:
    try:
        return float(ctk.ScalingTracker.get_window_scaling(win)) or 1.0
    except Exception:
        return 1.0


def place_window(win, want_w: int, want_h: int, *, over=None, keep_position: bool = False) -> None:
    """Dimensiona e posiciona uma janela para que ela NUNCA saia da área útil do
    monitor em que está (ou do monitor de `over`), em qualquer sistema e escala de tela.

    want_w/want_h são tamanhos lógicos (sem escala); janelas CTk multiplicam
    largura e altura pela escala da tela, mas não x/y, então as contas são
    feitas em pixels reais e convertidas de volta."""
    win.update_idletasks()
    scale = _window_scaling(win) if isinstance(win, (ctk.CTk, ctk.CTkToplevel)) else 1.0
    ref = over if over is not None else win
    try:
        cx = ref.winfo_rootx() + ref.winfo_width() // 2
        cy = ref.winfo_rooty() + ref.winfo_height() // 2
        point = (cx, cy) if ref.winfo_ismapped() else None
    except Exception:
        point = None
    work = plat.work_area(win, point=point)
    if not work[2]:
        work = (0, 0, win.winfo_screenwidth(), win.winfo_screenheight() - 80)
    prefer = None
    if keep_position and win.winfo_ismapped():
        # posição externa (com a barra de título) — a mesma que geometry("+x+y") define
        try:
            _, ox, oy = win.wm_geometry().split("+")[:3] if win.wm_geometry().count("+") >= 2 \
                else (None, win.winfo_x(), win.winfo_y())
            prefer = (int(ox), int(oy))
        except Exception:
            prefer = (win.winfo_x(), win.winfo_y())
    elif over is not None and point is not None:
        prefer = (point[0] - int(want_w * scale) // 2, point[1] - int(want_h * scale) // 2)
    w, h, x, y = plat.fit_window(work, int(want_w * scale), int(want_h * scale),
                                 titlebar=int(32 * scale), prefer=prefer)
    win.geometry(f"{round(w / scale)}x{round(h / scale)}+{x}+{y}")


def _voice_lang_code(path: str) -> str:
    """Extrai código de idioma do arquivo de voz (ex: it_IT-paola-medium.onnx → 'it')."""
    stem = Path(path).stem          # it_IT-paola-medium
    locale = stem.split("-")[0]     # it_IT
    return locale[:2].lower()       # it


def _voices_for_lang(voices: list[tuple[str, str]], lang_code: str) -> list[tuple[str, str]]:
    """Filtra vozes Piper por idioma; clones (🎙) aparecem em todos os idiomas."""
    return [(p, lbl) for p, lbl in voices
            if lbl.startswith("🎙 ") or _voice_lang_code(p) == lang_code]


def _best_catalog_voice(lang_code: str) -> dict | None:
    """Melhor voz do catálogo para o idioma: a marcada como padrão (escolhida por
    medição — a alemã "MLS" fala a metade da velocidade da "Thorsten"), senão a
    de qualidade média."""
    candidates = [v for v in VOICE_CATALOG if v["lang"] == lang_code]
    if not candidates:
        return None
    default = [v for v in candidates if v.get("default")]
    if default:
        return default[0]
    medium = [v for v in candidates if v["quality"] == "medium"]
    return medium[0] if medium else candidates[0]


# ── Áudio ─────────────────────────────────────────────────────────────────────

def get_audio_inputs() -> list[tuple[str, str]]:
    """Entradas de áudio (id, rótulo) pelo backend da plataforma — dispositivos
    estéreo viram Input 1 / Input 2 (esquerdo/direito)."""
    try:
        return plat.get_backend().list_inputs()
    except Exception:
        return []


def get_audio_outputs() -> list[tuple[str, str]]:
    """Saídas de áudio — exclui os dispositivos virtuais do Praxis e drivers de retorno (loopback)."""
    try:
        return plat.get_backend().list_outputs()
    except Exception:
        return []


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

    # Adiciona clones gravados (VOICES_DIR/clones/*.json)
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
    """(default_input, default_output) do sistema via backend de áudio."""
    try:
        return plat.get_backend().defaults()
    except Exception:
        return "", ""


# ── Config ────────────────────────────────────────────────────────────────────

def load_cfg() -> dict:
    cfg = dict(DEFAULT_CFG)
    if CONFIG_FILE.exists():
        try:
            loaded = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                cfg.update(loaded)
        except Exception:
            pass
    # Corrige tipos: um arquivo editado à mão ou corrompido nunca pode derrubar a interface
    for k, v in DEFAULT_CFG.items():
        if v is not None and not isinstance(cfg.get(k), type(v)):
            if isinstance(v, float) and isinstance(cfg.get(k), int) and not isinstance(cfg.get(k), bool):
                cfg[k] = float(cfg[k])
            else:
                cfg[k] = v
    # Migra voice_out para a pasta local do programa se ainda aponta para o path antigo
    old_base = str(Path.home() / ".local" / "share" / "praxis" / "voices")
    vo = cfg.get("voice_out", "")
    if vo.startswith(old_base):
        new_vo = str(VOICES_DIR / Path(vo).name)
        cfg["voice_out"] = new_vo if Path(new_vo).exists() else ""
    return cfg


def save_cfg(cfg: dict) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    # Gravação atômica: uma falha no meio da gravação não pode corromper a configuração
    tmp = CONFIG_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, CONFIG_FILE)


def _download_voice_files(v: dict, timeout: float = 60.0) -> None:
    """Baixa o .onnx + .onnx.json de uma voz do catálogo de forma atômica.

    Cada arquivo vai para `<nome>.part` e só é renomeado quando completo, então
    um download interrompido nunca parece uma voz instalada."""
    import shutil as _sh
    VOICES_DIR.mkdir(parents=True, exist_ok=True)
    fname = _catalog_filename(v)
    done: list[Path] = []
    try:
        for ext in (".json", ""):   # json pequeno primeiro: falha logo se der 404
            dest = VOICES_DIR / f"{fname}{ext}"
            part = dest.with_name(dest.name + ".part")
            with urllib.request.urlopen(_catalog_url(v, ext), timeout=timeout) as r, \
                    open(part, "wb") as f:
                _sh.copyfileobj(r, f, 1 << 16)
            os.replace(part, dest)
            done.append(dest)
    except Exception:
        for d in done:
            d.unlink(missing_ok=True)
        for ext in (".json", ""):
            (VOICES_DIR / f"{fname}{ext}.part").unlink(missing_ok=True)
        raise


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
        place_window(self, 480, 540, over=parent)
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
        VOICES_DIR.mkdir(parents=True, exist_ok=True)
        total = len(voices)
        for i, v in enumerate(voices):
            msg = f"({i + 1}/{total}) Baixando {v['name']}…"
            self.after(0, lambda m=msg: self._status_lbl.configure(text=m))
            self.after(0, lambda p=i / total: self._prog_bar.set(p))
            try:
                _download_voice_files(v)
            except Exception as e:
                err = f"Erro {v['name']}: {e}"
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

    WIN_W, WIN_H = 560, 720    # tamanho padrão da janela (pixels lógicos)

    def __init__(self) -> None:
        """Inicializa a janela principal de configuração do Praxis."""
        super().__init__()
        self._set_window_icon()   # antes da tela de abertura, para o Dock nunca mostrar o ícone do Python
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

        # App de meio de tela: tamanho médio fixo, centralizado — nunca esticado até
        # a altura da tela. Só encolhe se não couber na área útil (Dock, menu,
        # barra de tarefas), nunca vaza na vertical. O conteúdo rola por dentro.
        self.minsize(420, 480)
        place_window(self, self.WIN_W, self.WIN_H)

        self.withdraw()  # oculta a janela principal durante o carregamento

        # Força o PipeWire a 44100 Hz em todo o sistema ao iniciar
        try:
            plat.get_backend().force_rate(44100)   # só PipeWire; nos outros sistemas não faz nada
        except Exception:
            pass

        # Tela de carregamento aparece ANTES de _build() para dar retorno visual imediato
        splash, _sp_prog, _sp_lbl = self._create_loading_splash()
        self.update()  # força a tela de abertura a aparecer antes da construção pesada

        # O progresso avança na thread principal entre as fases (o Tk não é seguro
        # entre threads; _build() bloqueia o laço de eventos de todo jeito, então
        # uma thread não conseguiria animá-lo).
        _sp_prog.set(0.10)
        _sp_lbl.configure(text="Construindo interface…")
        self.update()
        self._build()

        _sp_prog.set(0.82)
        _sp_lbl.configure(text="Conectando áudio…")
        self.update()
        self._refresh_devices(startup=True)

        _sp_prog.set(1.0)
        _sp_lbl.configure(text="Pronto!")
        self.update()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Fecha a tela de abertura e exibe a janela principal após breve pausa.
        # Uma única janela de abertura: a tela de carregamento esmaece e a
        # janela principal aparece. (Uma 2ª tela era desenhada como caixa cinza vazia no macOS.)
        self.after(600, lambda: self._fade_out(splash, then=self.deiconify))

    def _fade_out(self, win, then=None, alpha: float = 1.0) -> None:
        """Esmaece uma janela (onde o gerenciador de janelas suporta -alpha), a destrói e executa `then`."""
        if alpha <= 0.0:
            try:
                win.destroy()
            finally:
                if then:
                    then()
            return
        try:
            win.attributes("-alpha", alpha)
        except Exception:
            alpha = 0.0
        self.after(25, self._fade_out, win, then, round(alpha - 0.1, 2))

    def _toggle_theme(self) -> None:
        """Alterna entre tema claro/escuro: salva a preferência e reconstrói a interface."""
        try:
            self._toggle_theme_impl()
        except Exception as _te:
            import traceback
            with open(plat.temp_path("praxis_theme_err.log"), "a") as _f:
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

        # Para a consulta periódica do medidor para não criar dois ciclos após a reconstrução
        if self._meter_poll_id:
            try: self.after_cancel(self._meter_poll_id)
            except Exception: pass
        self._meter_poll_id = None

        # Para a thread do medidor
        self._meter_stop.set()
        self._close_meter_capture()

        self._stop_ptt_config_listener()
        self._stop_engine(collapse=False)

        # Reconstrói a UI com as novas cores
        self.configure(fg_color=self.BG)
        self._main.destroy()

        # Limpa referências antigas — widgets destruídos junto com _main
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
        self._close_meter_capture()
        self._stop_meter()
        self._stop_ov_playback()
        # Restaura a taxa automática do PipeWire ao fechar
        try:
            plat.get_backend().restore_rate()
        except Exception:
            pass
        self._restore_default_devices()
        self.destroy()

    # ── Auxiliares de tradução e cores ────────────────────────────────────────

    def _t(self, key: str) -> str:
        """Retorna o texto da interface no idioma atual, recorrendo ao PT-BR se faltar."""
        lang = self.cfg.get("ui_lang", "pt")
        return UI_STRINGS.get(lang, UI_STRINGS["pt"]).get(key, UI_STRINGS["pt"].get(key, key))

    def _lang_name(self, code: str) -> str:
        """Retorna o nome do idioma `code` no idioma atual da interface."""
        ui_lang = self.cfg.get("ui_lang", "pt")
        return LANG_NAMES_BY_UI.get(ui_lang, LANG_NAMES_BY_UI["pt"]).get(code, code)

    def _fix_seg_colors(self, seg, sel_tc: str = "#FFFFFF", unsel_tc: str | None = None) -> None:
        """Corrige as cores do texto selecionado/não selecionado no CTkSegmentedButton.
        O CustomTkinter aplica um único text_color a todos os estados, então
        ajustamos _buttons_dict diretamente."""
        if unsel_tc is None:
            unsel_tc = self.TEXT
        try:
            selected = seg.get()
            for key, btn in seg._buttons_dict.items():
                btn.configure(text_color=sel_tc if key == selected else unsel_tc)
        except Exception:
            pass

    def _change_ui_lang(self, lang_label: str) -> None:
        """Muda o idioma da interface e a reconstrói inteira."""
        code = lang_label.strip().split()[-1].lower()
        if code == self.cfg.get("ui_lang", "pt"):
            return
        self.cfg["ui_lang"] = code

        # Para processos ativos antes de reconstruir (mesmo padrão de _toggle_theme_impl)
        if self._meter_poll_id:
            try: self.after_cancel(self._meter_poll_id)
            except Exception: pass
        self._meter_poll_id = None
        self._meter_stop.set()
        if self._meter_proc:
            try: self._meter_proc.terminate()
            except Exception: pass
        self._meter_proc = None
        self._stop_ptt_config_listener()
        self._stop_engine(collapse=False)

        self.configure(fg_color=self.BG)
        self._main.destroy()

        # Limpa referências antigas
        self._meter_ids = {}
        self._meter_W   = 0
        self._meter_H   = 0
        for _attr in ("_gate_info_row", "_gate_info_row_kw", "_gate_pct_lbl",
                       "_meter_canvas", "_btn_vad", "_btn_gate", "_btn_ptt",
                       "_mode_cond", "_mode_cond_kw", "_ptt_info",
                       "_voice_menu", "_test_btn", "_theme_btn", "_lang_menu",
                       "_tab_seg", "_config_frame_outer", "_clone_frame_outer",
                       "_dl_card", "_dl_card_kw", "_dl_inner",
                       "_dl_progress", "_dl_pct_lbl", "_dl_status",
                       "_show_clones"):
            try: delattr(self, _attr)
            except AttributeError: pass

        self._build()
        self._refresh_devices(startup=True)

    def _filter_voices(self, lang_code: str, clones_only: bool = False) -> list[tuple[str, str]]:
        """Filtra a lista de vozes: clones_only=True → só clones 🎙; False → só vozes Piper do idioma."""
        if clones_only:
            return [(p, lbl) for p, lbl in self._voices if lbl.startswith("🎙 ")]
        return [(p, lbl) for p, lbl in self._voices
                if not lbl.startswith("🎙 ") and _voice_lang_code(p) == lang_code]

    def _on_clone_filter_toggle(self) -> None:
        """Alterna entre vozes Piper e clones OmniVoice na lista da voz de saída."""
        tgt_code = self._tgt_code()
        clones_only = getattr(self, "_show_clones", None)
        clones_only = clones_only.get() if clones_only else False
        filtered = self._filter_voices(tgt_code, clones_only=clones_only)
        labels = [lbl for _, lbl in filtered]
        if not labels:
            labels = [self._t("lbl_no_clones") if clones_only else "(nenhuma voz)"]
        self._voice_menu.configure(values=labels)
        if self.voice_var.get() not in labels:
            self.voice_var.set(labels[0])

    # ── Ícone e splash ────────────────────────────────────────────────────────

    SPLASH_BG = "#01030F"   # igual ao fundo escuro de assets/praxis.png

    def _load_logo(self, max_side: int) -> "tk.PhotoImage | None":
        """Logo reduzida para caber em max_side × max_side SEM mudar a proporção
        (Pillow se disponível; senão, PNG nativo do Tk + redução por fator inteiro)."""
        path = ASSETS_DIR / "praxis.png"
        if not path.exists():
            return None
        try:
            from PIL import Image, ImageTk
            img = Image.open(path)
            img.thumbnail((max_side, max_side), Image.LANCZOS)   # mantém a proporção
            return ImageTk.PhotoImage(img)
        except Exception:
            pass
        try:
            photo = tk.PhotoImage(file=str(path))
            factor = max(1, -(-max(photo.width(), photo.height()) // max_side))  # arredonda para cima
            return photo.subsample(factor, factor) if factor > 1 else photo
        except Exception:
            return None

    def _logical_height(self) -> int:
        try:
            return int(self.winfo_height() / _window_scaling(self))
        except Exception:
            return 900

    def _ui_scaling(self) -> float:
        """Escala de tela que o CustomTkinter aplica (Windows 125/150%, Linux em alta resolução)."""
        try:
            return float(ctk.ScalingTracker.get_window_scaling(self)) or 1.0
        except Exception:
            return 1.0

    def _create_loading_splash(self) -> "tuple[tk.Toplevel, ctk.CTkProgressBar, ctk.CTkLabel]":
        """Cria e exibe a tela de carregamento com logo + barra de progresso.

        Regra (todos os sistemas): a logo nunca é distorcida — ela é reduzida
        mantendo a proporção e a JANELA é dimensionada pelo conteúdo, nunca o
        contrário. Nada tem tamanho fixo em pixels, então a escala de tela do
        Windows/Linux (125%, 150%, alta resolução) não corta nem estica nada."""
        BAR_H = 6
        ox, oy, sw, sh = plat.work_area(self)
        if sw == 0:
            ox, oy, sw, sh = 0, 0, self.winfo_screenwidth(), self.winfo_screenheight()
        side = min(int(380 * self._ui_scaling()), sw - 48, sh - 140)   # nunca maior que a tela
        logo = self._load_logo(max(120, side))
        self._loading_photo = logo

        sp = tk.Toplevel(self)
        sp.withdraw()                       # constrói primeiro, mede e depois mostra centralizada
        sp.overrideredirect(True)
        sp.configure(bg=self.SPLASH_BG)

        # Logo na proporção original; a janela é que se ajusta a ela
        if logo:
            tk.Label(sp, image=logo, bg=self.SPLASH_BG, bd=0,
                     highlightthickness=0).pack()
        else:
            tk.Label(sp, text="Praxis", font=(_UI_FONT, 28, "bold"),
                     fg="white", bg=self.SPLASH_BG).pack(padx=80, pady=60)

        status_lbl = ctk.CTkLabel(
            sp, text="Iniciando…",
            font=ctk.CTkFont(size=12), text_color="#A1A1AA",
            fg_color=self.SPLASH_BG
        )
        status_lbl.pack(pady=(8, 4))

        # Barra estica até a largura da logo (fill), não define a largura da janela
        prog = ctk.CTkProgressBar(
            sp, width=40, height=BAR_H,
            progress_color="#7C3AED", fg_color="#27272A",
            corner_radius=3
        )
        prog.set(0.05)
        prog.pack(fill="x", padx=24, pady=(0, 16))

        # Mede o conteúdo e centraliza no monitor principal
        sp.update_idletasks()
        w, h = sp.winfo_reqwidth(), sp.winfo_reqheight()
        sp.geometry(f"+{ox + max(0, (sw - w) // 2)}+{oy + max(0, (sh - h) // 2)}")
        sp.deiconify()
        sp.lift()
        sp.attributes("-topmost", True)
        sp.update_idletasks()
        return sp, prog, status_lbl

    def _set_window_icon(self) -> None:
        """Define o ícone da janela / barra de tarefas / Dock do macOS (sem depender do
        Pillow; o Tk 8.6+ lê PNG nativamente)."""
        try:
            if plat.IS_WIN and (ASSETS_DIR / "icon.ico").exists():
                self.iconbitmap(default=str(ASSETS_DIR / "icon.ico"))
            png = ASSETS_DIR / ("icon.png" if plat.IS_MAC else "icon_256.png")
            if not png.exists():
                png = ASSETS_DIR / "praxis.png"
            self._taskbar_icon = tk.PhotoImage(file=str(png))
            self.wm_iconphoto(True, self._taskbar_icon)
        except Exception:
            pass

    # ── Construção da UI ──────────────────────────────────────────────────────

    def _build(self) -> None:
        """Constrói toda a interface: painel esquerdo (configuração) + painel direito (monitoramento)."""
        # Contêiner principal: esquerda (config) + direita (monitoramento, oculta)
        self._main = ctk.CTkFrame(self, fg_color="transparent")
        self._main.pack(fill="both", expand=True)

        # PAINEL ESQUERDO — expande com a janela quando o painel de monitoramento está oculto
        self._left = ctk.CTkFrame(self._main, fg_color=self.BG)
        self._left.pack(side="left", fill="both", expand=True)

        hdr = ctk.CTkFrame(self._left, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(20, 10))

        _is_dark = ctk.get_appearance_mode().lower() == "dark"

        # Estrutura: [espaçador 120px] [centro expansível] [seletor de idioma 80px + botão 34px]
        # Lado direito: [seletor de idioma] + [botão de tema] — largura igual à do espaçador
        # esquerdo, para centralizar a logo
        _hdr_right = ctk.CTkFrame(hdr, fg_color="transparent")
        _hdr_right.pack(side="right", anchor="n")

        _cur_lang = self.cfg.get("ui_lang", "pt")
        _lang_options = [f"{_UI_LANG_FLAGS[c]} {c.upper()}" for c in _UI_LANG_FLAGS]
        _lang_cur_label = f"{_UI_LANG_FLAGS.get(_cur_lang, '🌐')} {_cur_lang.upper()}"
        self._lang_menu = ctk.CTkOptionMenu(
            _hdr_right,
            values=_lang_options,
            width=80, height=34,
            fg_color=self.SEG_BG, button_color=self.IBORDER,
            button_hover_color=self.HOVER,
            text_color=self.TEXT,
            dropdown_fg_color=self.CARD,
            dropdown_text_color=self.TEXT,
            dropdown_hover_color=self.SEG_BG,
            font=ctk.CTkFont(size=11),
            command=self._change_ui_lang,
        )
        self._lang_menu.set(_lang_cur_label)
        self._lang_menu.pack(side="left", padx=(0, 6))

        self._theme_btn = ctk.CTkButton(
            _hdr_right, text="☀" if _is_dark else "☾",
            width=34, height=34,
            fg_color=self.ACCENT, hover_color=self.HOVER,
            text_color="#FFFFFF", border_width=0,
            corner_radius=17, font=ctk.CTkFont(size=15),
            command=self._toggle_theme,
        )
        self._theme_btn.pack(side="left")

        # Espaçador esquerdo espelha a largura do lado direito para centralizar a logo (80+6+34 = 120px)
        _hdr_spacer = ctk.CTkFrame(hdr, fg_color="transparent", width=120, height=34)
        _hdr_spacer.pack(side="left")
        _hdr_spacer.pack_propagate(False)

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
            _lw, _lh = _logo_pil.size          # mantém a proporção
            _scale = 110 / max(_lw, _lh)
            self._logo_img = ctk.CTkImage(
                light_image=_logo_pil, dark_image=_logo_pil,
                size=(round(_lw * _scale), round(_lh * _scale)))
            ctk.CTkLabel(_hdr_center, image=self._logo_img, text="").pack()
        except Exception:
            pass

        ctk.CTkLabel(
            _hdr_center,
            text=self._t("tagline"),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.MUTED,
        ).pack(pady=(6, 0))

        # ── Seletor de abas (sem CTkTabview — evita janela separada no Linux) ──
        self._tab_seg = ctk.CTkSegmentedButton(
            self._left,
            values=[self._t("tab_config"), self._t("tab_clone")],
            fg_color=self.SEG_BG,
            selected_color=self.ACCENT,
            selected_hover_color=self.HOVER,
            unselected_color=self.SEG_BG,
            unselected_hover_color=self.IBORDER,
            text_color=self.TEXT,
            font=ctk.CTkFont(size=13),
            command=self._on_tab_change,
        )
        self._tab_seg.set(self._t("tab_config"))
        self._fix_seg_colors(self._tab_seg)
        self._tab_seg.pack(fill="x", padx=24, pady=(8, 0))

        # ── Contêiner das abas (só uma visível por vez) ──────────────────────
        self._config_frame_outer = ctk.CTkFrame(self._left, fg_color="transparent")
        self._config_frame_outer.pack(fill="both", expand=True)

        self._clone_frame_outer = ctk.CTkFrame(self._left, fg_color="transparent")
        # Não empacotado ainda — aparece ao selecionar a aba

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
        r = self._section(r, self._t("sec_audio"), right_widget=self._make_refresh_btn())
        r = self._audio_section(r)
        r = self._sep(r)

        r = self._section(r, self._t("sec_langs"))
        r = self._idiomas(r)
        r = self._sep(r)

        r = self._section(r, self._t("sec_whisper"))
        r = self._whisper(r)
        r = self._sep(r)

        r = self._section(r, self._t("sec_voice_out"),
                          right_widget=self._make_voice_header_btns())
        r = self._voice_field(r)
        r = self._sep(r)
        r = self._bilateral_section(r)

        # ── Aba Clonar minha voz ──────────────────────────────────────────────
        self._build_clone_tab(self._clone_frame_outer)

        footer = ctk.CTkFrame(self._left, fg_color="transparent")
        footer.pack(fill="x", padx=24, pady=(4, 20))
        ctk.CTkButton(
            footer, text=self._t("btn_save"), width=100, height=38,
            fg_color=self.SEG_BG, hover_color=self.IBORDER,
            text_color=self.TEXT, border_width=1, border_color=self.IBORDER,
            corner_radius=10, font=ctk.CTkFont(size=13),
            command=self._save,
        ).pack(side="left")
        self._iniciar_btn = ctk.CTkButton(
            footer, text=self._t("btn_start"), height=38,
            fg_color=self.ACCENT, hover_color=self.HOVER,
            text_color="#FFFFFF", corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._launch,
        )
        self._iniciar_btn.pack(side="right")

        # PAINEL DIREITO — monitoramento, oculto até Iniciar, largura fixa de 560px
        self._right = ctk.CTkFrame(self._main, fg_color=self.BG,
                                    border_width=1, border_color=self.BORDER,
                                    width=560)
        self._right.pack_propagate(False)
        self._build_monitoring_ui()

    def _on_tab_change(self, value: str) -> None:
        """Alterna a aba visível entre Config e Clonar, mostrando/ocultando os quadros."""
        self._fix_seg_colors(self._tab_seg)
        if value == self._t("tab_config"):
            self._clone_frame_outer.pack_forget()
            self._config_frame_outer.pack(fill="both", expand=True)
        else:
            self._config_frame_outer.pack_forget()
            self._clone_frame_outer.pack(fill="both", expand=True)


    def _idiomas(self, r: int) -> int:
        """Seção de seleção de idiomas (fala → traduz para). Retorna a próxima linha da grade."""
        card = self._card
        ctk.CTkLabel(card, text=self._t("lbl_src_lang"),
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self.MUTED).grid(row=r, column=0, sticky="w",
                                                  padx=20, pady=(0, 4))
        ctk.CTkLabel(card, text=self._t("lbl_tgt_lang"),
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self.MUTED).grid(row=r, column=1, sticky="w",
                                                  padx=20, pady=(0, 4))
        r += 1
        # rótulos traduzidos para o idioma atual da interface
        _src_labels = [f"{self._lang_name(c)}  ({c})" for c, _ in LANGS]
        self.src_var = ctk.StringVar(
            value=f"{self._lang_name(self.cfg['src'])}  ({self.cfg['src']})")
        # destino: apenas idiomas com voz disponível no catálogo ou instalada
        _tgt_pairs  = _tgt_langs_with_voices()
        _tgt_labels = [f"{self._lang_name(c)}  ({c})" for c, _ in _tgt_pairs]
        self._tgt_pairs = _tgt_pairs
        saved_tgt = f"{self._lang_name(self.cfg['tgt'])}  ({self.cfg['tgt']})"
        if saved_tgt not in _tgt_labels:
            saved_tgt = _tgt_labels[0]
        self.tgt_var = ctk.StringVar(value=saved_tgt)
        self.tgt_var.trace_add("write", lambda *_: self.after(0, self._on_tgt_change))
        self.src_var.trace_add("write", lambda *_: self.after(0, self._on_src_change))
        self._optmenu(card, r, 0, _src_labels, self.src_var, pr=8)
        self._optmenu(card, r, 1, _tgt_labels, self.tgt_var, pl=8)
        return r + 1

    def _whisper(self, r: int) -> int:
        """Seção de seleção do modelo Whisper (menu: cabe em qualquer largura, nunca transborda)."""
        model = self.cfg.get("model", "small")
        if model not in MODELS:          # valor salvo por uma versão antiga/diferente
            model = "auto"
        self.model_var = ctk.StringVar(value=model)
        _whisper_menu = ctk.CTkOptionMenu(
            self._card, values=MODELS, variable=self.model_var,
            fg_color=self.INPUT, button_color=self.SEG_BG,
            button_hover_color=self.IBORDER, text_color=self.TEXT,
            dropdown_fg_color=self.CARD, dropdown_text_color=self.TEXT,
            font=ctk.CTkFont(size=12), dynamic_resizing=False,
        )
        _whisper_menu.grid(row=r, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 16))
        return r + 1

    def _audio_section(self, r: int) -> int:
        """Seção de áudio: modo, microfone, medidor de volume, saída e monitor."""
        card = self._card

        # 1. Modos de funcionamento (primeiro, antes dos dispositivos)
        r = self._mode_section(r)

        # 2. Entrada (microfone)
        ctk.CTkLabel(card, text=self._t("lbl_input"),
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self.MUTED).grid(row=r, column=0, columnspan=2,
                                                  sticky="w", padx=20, pady=(0, 4))
        r += 1
        self.mic_var   = ctk.StringVar(value=self._t("lbl_sys_default"))
        self._mic_menu = ctk.CTkOptionMenu(
            card, values=[self._t("lbl_sys_default")], variable=self.mic_var,
            fg_color=self.INPUT, button_color=self.IBORDER,
            button_hover_color=self.SEG_BG, text_color=self.TEXT,
            dropdown_fg_color=self.CARD, dropdown_text_color=self.TEXT,
            dropdown_hover_color=self.SEG_BG, font=ctk.CTkFont(size=13),
        )
        self._mic_menu.configure(command=self._on_mic_change)
        self._mic_menu.grid(row=r, column=0, columnspan=2, sticky="ew",
                            padx=20, pady=(0, 8))
        r += 1

        # 3. Medidor de volume
        r = self._build_meter(r)

        # 4. Barra de gate (abaixo do medidor, visível só no modo gate)
        r = self._build_gate_bar(r)

        # 5. Saída (fones / caixas)
        ctk.CTkLabel(card, text=self._t("lbl_output"),
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self.MUTED).grid(row=r, column=0, columnspan=2,
                                                  sticky="w", padx=20, pady=(0, 4))
        r += 1
        self.out_var   = ctk.StringVar(value=self._t("lbl_sys_default"))
        self._out_menu = ctk.CTkOptionMenu(
            card, values=[self._t("lbl_sys_default")], variable=self.out_var,
            fg_color=self.INPUT, button_color=self.IBORDER,
            button_hover_color=self.SEG_BG, text_color=self.TEXT,
            dropdown_fg_color=self.CARD, dropdown_text_color=self.TEXT,
            dropdown_hover_color=self.SEG_BG, font=ctk.CTkFont(size=13),
        )
        self._out_menu.grid(row=r, column=0, columnspan=2, sticky="ew",
                            padx=20, pady=(0, 16))
        r += 1

        # 6. Botão liga/desliga do monitor
        self._mon_btn = ctk.CTkButton(
            card,
            text=self._t("mon_on") if self._monitor else self._t("mon_off"),
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
            card, text=self._t("mon_hint"),
            font=ctk.CTkFont(size=11), text_color=self.MUTED,
        ).grid(row=r, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 18))
        r += 1

        return r

    def _build_gate_bar(self, r: int) -> int:
        """O limiar do gate agora fica dentro do medidor de volume — não ocupa linha."""
        self._gate_bar_W  = 0
        self._gate_bar_H  = 0
        self._gate_bar_ids: dict = {}
        return r  # sem widget separado; o limiar fica no canvas do medidor

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

        # Trilha cinza de fundo
        c.create_rectangle(0, pad, W, H - pad, fill="#E5E7EB", outline="", tags="track")

        # Preenchimento verde (nível de áudio) — largura inicial 0
        c.create_rectangle(0, pad, 0, H - pad, fill="#22C55E", outline="", tags="fill")

        # Sombra do marcador arrastável (mais larga, cor escura)
        tx = int(self._gate_frac * W)
        c.create_line(tx, pad - 4, tx, H - pad + 4,
                      fill="#6B7280", width=5, tags="handle_shadow")
        # Marcador branco
        c.create_line(tx, pad - 4, tx, H - pad + 4,
                      fill="#FFFFFF", width=3, tags="handle")
        # Círculo central no marcador
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

    # ── Medidor de volume ─────────────────────────────────────────────────────

    def _build_meter(self, r: int) -> int:
        """Constrói o canvas do medidor de volume na aba de configuração. Retorna a próxima linha da grade."""
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

        # Linha de info do gate — FORA da caixa do medidor, na linha seguinte do cartão
        # Visível apenas quando modo Gate está ativo
        self._gate_info_row = ctk.CTkFrame(self._card, fg_color="transparent")
        ctk.CTkLabel(self._gate_info_row, text="LIMIAR DO GATE",
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
        return r + 2  # ocupa 2 linhas: medidor + gate_info

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

        # Máscara cobre a parte não preenchida (cor do cartão, para funcionar no tema claro e escuro)
        self._meter_ids["mask"] = c.create_rectangle(
            0, 0, W, H, fill=self.CARD, outline=""
        )
        # Linha de pico
        self._meter_ids["peak"] = c.create_line(
            0, 0, 0, H, fill=self.CARD, width=2
        )
        # Marcador do limiar do gate — criado sobre a máscara para ser sempre visível
        tx = int(getattr(self, "_gate_frac", 0.0) * W)
        is_gate = getattr(self, "_mode_var", None) and self._mode_var.get() == "gate"
        _gs = "normal" if is_gate else "hidden"
        self._meter_ids["gate_shadow"] = c.create_line(
            tx, 0, tx, H, fill="#1F2937", width=5, state=_gs)
        self._meter_ids["gate_line"] = c.create_line(
            tx, 0, tx, H, fill="#FFFFFF", width=2, state=_gs)

    def _get_meter_device(self) -> str | None:
        """Devolve o nome PulseAudio da fonte selecionada, sem o sufixo :left/:right."""
        label = self.mic_var.get()
        if label.startswith("("):
            return None
        name = self._label_to_name(label, self._inputs)
        if not name:
            return None
        return name.split(":")[0]   # remove :left / :right

    def _close_meter_capture(self) -> None:
        cap = getattr(self, "_meter_proc", None)
        self._meter_proc = None
        if cap is not None:
            try:
                cap.close()
            except Exception:
                pass

    def _start_meter_thread(self) -> None:
        self._close_meter_capture()
        self._meter_stop = threading.Event()   # evento novo: o leitor antigo termina sozinho

        mic_label = getattr(self, "mic_var", None)
        device = self._label_to_name(mic_label.get(), self._inputs) if mic_label else None
        rate, frames = 16000, 256              # 16 ms por bloco

        try:
            cap = plat.get_backend().open_capture(device or None, rate, frames)
        except Exception:
            return
        self._meter_proc = cap

        def _reader(cap=cap, stop=self._meter_stop, q=self._meter_q):
            env = 0.0
            att = 1.0 - np.exp(-1.0 / (0.003 * rate / frames))
            rel = 1.0 - np.exp(-1.0 / (0.120 * rate / frames))
            try:
                while not stop.is_set():
                    data = cap.read()
                    if not data:
                        break
                    arr = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                    rms = float(np.sqrt(np.mean(arr ** 2))) if len(arr) else 0.0
                    env += (att if rms > env else rel) * (rms - env)
                    if q.full():
                        try: q.get_nowait()
                        except queue.Empty: pass
                    try: q.put_nowait(env)
                    except queue.Full: pass
            finally:
                try:
                    cap.close()
                except Exception:
                    pass

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

    # ── Arraste do marcador do gate ───────────────────────────────────────────

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
        """Seção de seleção do modo de operação (VAD / Gate / PTT)."""
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

        self._btn_vad  = _make_btn(self._t("mode_vad"),  "vad")
        self._btn_gate = _make_btn(self._t("mode_gate"), "gate")
        self._btn_ptt  = _make_btn(self._t("mode_ptt"),  "ptt")
        self._btn_vad .grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self._btn_gate.grid(row=0, column=1, sticky="ew", padx=(0, 4))
        self._btn_ptt .grid(row=0, column=2, sticky="ew")

        # Quadro condicional — configuração do PTT (o gate usa barra própria abaixo do medidor)
        self._mode_cond = ctk.CTkFrame(self._card, fg_color="transparent")
        _mc_kw = dict(row=row, column=0, columnspan=2, sticky="ew", padx=20)
        self._mode_cond_kw = _mc_kw
        self._mode_cond.grid(**_mc_kw)
        row += 1

        # Subquadro do PTT
        self._ptt_info = ctk.CTkFrame(self._mode_cond, fg_color="transparent")
        ptt_row = ctk.CTkFrame(self._ptt_info, fg_color="transparent")
        ptt_row.pack(fill="x", pady=(2, 6))
        self._ptt_key_lbl = ctk.CTkLabel(
            ptt_row,
            text=self._ptt_key if self._ptt_key else self._t("ptt_none"),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.TEXT,
        )
        self._ptt_key_lbl.pack(side="left", padx=(0, 12))
        ctk.CTkButton(
            ptt_row, text=self._t("btn_configure"), width=140, height=28,
            fg_color=self.SEG_BG, hover_color=self.IBORDER,
            text_color=self.MUTED, border_width=1, border_color=self.IBORDER,
            corner_radius=8, font=ctk.CTkFont(size=11),
            command=self._capture_ptt_key,
        ).pack(side="left")

        self._update_mode_ui()
        # Inicia o ouvinte do PTT se já há tecla configurada ao abrir a janela
        if self._mode_var.get() == "ptt" and self._ptt_key:
            self._start_ptt_config_listener(self._ptt_key)
        return row

    def _set_mode(self, mode: str) -> None:
        """Altera o modo de operação do motor (vad/gate/ptt) e atualiza a interface."""
        self._mode_var.set(mode)
        if mode == "ptt" and self._ptt_key:
            self._start_ptt_config_listener(self._ptt_key)
        else:
            self._stop_ptt_config_listener()
        self._update_mode_ui()

    # ── Medidor ativo/cinza (retorno do PTT na configuração) ──────────────────

    def _meter_set_active(self, active: bool) -> None:
        """Redesenha o gradiente do medidor: colorido (ativo) ou cinza (PTT inativo)."""
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
        """Ouvinte na janela de configuração: detecta o PTT pressionado e colore o medidor."""
        self._stop_ptt_config_listener()
        if not key_str:
            return
        try:
            from pynput import keyboard as _kb, mouse as _ms
        except Exception:
            return   # pynput indisponível (Wayland/sem tela/não instalado) — o medidor só fica ativo
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
        """Constrói o painel direito de monitoramento (transcrição, tradução, registros)."""
        AMBER = "#F59E0B"
        RED   = "#EF4444"

        # Barra de status
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

        # Registro
        log_card = ctk.CTkFrame(self._right, fg_color=self.CARD,
                                 border_width=1, border_color=self.BORDER,
                                 corner_radius=10, height=90)
        log_card.pack(fill="x", padx=16, pady=(0, 12))
        log_card.pack_propagate(False)
        ctk.CTkLabel(log_card, text="Log", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self.MUTED).pack(anchor="w", padx=12, pady=(6, 2))
        self._log_box = ctk.CTkTextbox(log_card, fg_color=self.CARD,
                                        font=ctk.CTkFont(size=10, family=_MONO_FONT),
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

        # Mostra/oculta o subquadro do PTT (e o contêiner inteiro, para não deixar vão)
        for w in self._mode_cond.winfo_children():
            w.pack_forget()
        if mode == "ptt":
            self._ptt_info.pack(fill="x")
            self._mode_cond.grid(**self._mode_cond_kw)
        else:
            self._mode_cond.grid_remove()

        # Gate: mostra o marcador dentro do medidor + linha de info + liga o arraste
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

        # PTT: o medidor fica cinza quando o botão não está pressionado
        self._meter_set_active(mode != "ptt")

    def _capture_ptt_key(self) -> None:
        """Aguarda a próxima tecla ou botão do mouse e salva como PTT."""
        self._ptt_key_lbl.configure(text="Pressione qualquer tecla ou botão do mouse…")
        captured = []

        def _done(key_str: str) -> None:
            if captured:
                return
            captured.append(key_str)
            self._ptt_key = key_str
            self.after(0, lambda: self._ptt_key_lbl.configure(text=key_str))
            # Inicia o ouvinte de retorno logo após configurar a tecla
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

    # ── Auxiliares de layout ──────────────────────────────────────────────────

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
        self._show_clones = ctk.BooleanVar(value=False)
        tgt_code = self._tgt_code()

        # Caixa "Modelos clonados" — alterna entre Piper e clones
        ctk.CTkCheckBox(
            self._card,
            text=self._t("lbl_cloned_models"),
            variable=self._show_clones,
            command=self._on_clone_filter_toggle,
            fg_color=self.ACCENT, hover_color=self.HOVER,
            checkmark_color="#FFFFFF",
            text_color=self.TEXT,
            font=ctk.CTkFont(size=11),
        ).grid(row=row, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 4))
        row += 1

        filtered = self._filter_voices(tgt_code, clones_only=False)
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
            info_row, text=self._t("btn_test"), width=90, height=26,
            fg_color=self.SEG_BG, hover_color=self.IBORDER,
            text_color=self.MUTED, border_width=1, border_color=self.IBORDER,
            corner_radius=8, font=ctk.CTkFont(size=11),
            command=self._test_voice,
        )
        self._test_btn.grid(row=0, column=1, sticky="e")
        row += 1

        # Cartão de download — conteúdo gerado dinamicamente em _show_dl_card
        self._dl_card = ctk.CTkFrame(
            self._card, fg_color=self.CARD,
            border_width=1, border_color=self.IBORDER, corner_radius=8,
        )
        self._dl_card_kw = dict(row=row, column=0, columnspan=2,
                                 sticky="ew", padx=20, pady=(0, 12))
        self._dl_card.grid(**self._dl_card_kw)
        self._dl_card.grid_remove()

        # Quadro interno que é limpo e repreenchido ao mudar de idioma
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
        # extrai o código do sufixo "Nome  (código)"
        try:
            code = lbl.split("(")[-1].rstrip(")")
            if code in LANG_CODES:
                return code
        except (ValueError, IndexError):
            pass
        return self.cfg.get("tgt", "en")

    def _on_src_change(self) -> None:
        """Atualiza o seletor de voz bilateral quando o idioma de origem muda."""
        if not hasattr(self, "_voice_in_menu"):
            return
        try:
            # extrai o código do rótulo "Nome  (código)"
            raw = self.src_var.get()
            src_code = raw.split("(")[-1].rstrip(")")
            if src_code not in LANG_CODES:
                return
        except (ValueError, IndexError):
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
        clones_only = getattr(self, "_show_clones", None)
        clones_only = clones_only.get() if clones_only else False
        filtered = self._filter_voices(tgt_code, clones_only=clones_only)
        labels = [lbl for _, lbl in filtered]
        if labels:
            self._voice_menu.configure(values=labels)
            if self.voice_var.get() not in labels:
                self.voice_var.set(labels[0])
        else:
            empty = self._t("lbl_no_clones") if clones_only else "(nenhuma voz)"
            self._voice_menu.configure(values=[empty])
            self.voice_var.set(empty)

        # Mostra o cartão de download se houver vozes do catálogo ainda não baixadas
        remaining = [v for v in VOICE_CATALOG
                     if v["lang"] == tgt_code
                     and not (VOICES_DIR / _catalog_filename(v)).exists()]
        if remaining:
            self._show_dl_card(tgt_code)
        elif hasattr(self, "_dl_card"):
            self._dl_card.grid_remove()

    def _show_dl_card(self, lang_code: str) -> None:
        """Reconstrói o cartão de download listando TODAS as vozes do catálogo para o idioma."""
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

        # Barra de progresso + rótulo (ocultos até iniciar o download)
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
        """Download concluído: atualiza o menu de voz e mostra as vozes restantes ou esconde o cartão."""
        self._voices = get_voices()
        filtered = _voices_for_lang(self._voices, lang_code)
        if filtered and hasattr(self, "_voice_menu"):
            labels = [lbl for _, lbl in filtered]
            self._voice_menu.configure(values=labels)
            self.voice_var.set(labels[0])
        # Reexibe o cartão com vozes ainda não baixadas (ou oculta se todas foram baixadas)
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
                import wave
                voice = PiperVoice.load(voice_path)
                tmp_wav = plat.temp_path("praxis_voice_test.wav")
                with wave.open(tmp_wav, "wb") as wf:
                    voice.synthesize_wav(phrase, wf)
                plat.get_backend().play_file(tmp_wav, self._selected_output()).wait(60)
            except Exception as e:
                print(f"[praxis] teste de voz falhou: {e}", file=sys.stderr)
            finally:
                self.after(0, lambda: self._test_btn.configure(
                    state="normal", text=self._t("btn_test")))

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
    CLONE_PAGES = [
        # Página 1
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
        # Página 2
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
        # Página 3
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
        # Página 4
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
    CLONE_TEXT = " ".join(CLONE_PAGES)
    CLONES_DIR = VOICES_DIR / "clones"

    def _build_clone_tab(self, parent: ctk.CTkFrame) -> None:
        """Constrói a aba de clonagem de voz com OmniVoice (zero-shot)."""
        self.CLONES_DIR.mkdir(parents=True, exist_ok=True)
        self._meter_stream = None
        self._testing      = False

        scroll = ctk.CTkScrollableFrame(
            parent, fg_color="transparent",
            scrollbar_button_color=self.SEG_BG,
            scrollbar_button_hover_color=self.IBORDER,
        )
        scroll.pack(fill="both", expand=True, padx=4, pady=4)

        # Seção OmniVoice — único motor de clonagem
        self._ov_section  = ctk.CTkFrame(scroll, fg_color="transparent")

        # ── Medidor de volume ──────────────────────────────────────────────
        # Medidor compartilhado — exibido acima da seção OmniVoice
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
        # Botão monitor: envia o microfone → caixas de som em tempo real
        # ⚠ Use fones de ouvido para evitar eco
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
            command=self._toggle_clone_monitor,
        ).pack(side="right", padx=(0, 6))

        # Inicializa o estado ANTES de criar o canvas — <Configure> pode disparar no pack()
        self._clone_meter_W    = 0
        self._clone_meter_H    = 0
        self._clone_meter_peak = 0.0
        self._clone_meter_ids: dict = {}

        # Canvas com gradiente verde→amarelo→vermelho (igual ao medidor da aba Config)
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

        # Espera de 300 ms para o laço de eventos estar pronto antes de abrir o fluxo de áudio
        self.after(300, self._start_meter)

        # Empacota a seção OmniVoice APÓS o medidor para que apareça abaixo dele
        self._ov_section.pack(fill="x")

        # ── Seção OmniVoice (zero-shot) ─────────────────────────────────────
        # Exibida só quando mode="ov"
        _ov = self._ov_section
        self._ov_rec_frames: list = []
        self._ov_rec_active = False
        self._ov_ref_path   = ctk.StringVar(value="")
        _OV_REF_MAX_S = 15   # máximo de segundos da gravação de referência

        # Cartão de explicação
        _ov_info = ctk.CTkFrame(_ov, fg_color=self.SEG_BG,
                                corner_radius=10, border_width=1,
                                border_color=self.IBORDER)
        _ov_info.pack(fill="x", padx=16, pady=(14, 8))
        ctk.CTkLabel(_ov_info, text=self._t("ov_title"),
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=self.TEXT).pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(
            _ov_info,
            text=self._t("ov_desc"),
            font=ctk.CTkFont(size=11), text_color=self.MUTED,
            justify="left", anchor="w",
        ).pack(anchor="w", padx=12, pady=(0, 10))

        # ── Cartão de gravação de referência ───────────────────────────────
        # Grave ~10 s de fala natural
        _ov_rec_card = ctk.CTkFrame(_ov, fg_color=self.INPUT,
                                    border_color=self.IBORDER, border_width=1,
                                    corner_radius=8)
        _ov_rec_card.pack(fill="x", padx=16, pady=(0, 6))

        # Texto de exemplo para ler em voz alta
        ctk.CTkLabel(_ov_rec_card, text=self._t("ov_read_aloud"),
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self.MUTED).pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(
            _ov_rec_card,
            text=self._t("ov_ref_text"),
            font=ctk.CTkFont(size=12), text_color=self.TEXT,
            wraplength=380, justify="left", anchor="nw",
        ).pack(fill="x", padx=12, pady=(0, 8))

        # Controles de gravação
        _ov_ctl = ctk.CTkFrame(_ov_rec_card, fg_color="transparent")
        _ov_ctl.pack(fill="x", padx=12, pady=(0, 4))

        self._ov_rec_btn = ctk.CTkButton(
            _ov_ctl, text=self._t("btn_rec_ref"), width=150, height=32,
            fg_color="#DC2626", hover_color="#B91C1C",
            text_color="#FFFFFF", corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._ov_toggle_recording,
        )
        self._ov_rec_btn.pack(side="left", padx=(0, 10))

        self._ov_rec_status = ctk.CTkLabel(
            _ov_ctl, text=self._t("lbl_ready"),
            font=ctk.CTkFont(size=11), text_color=self.MUTED)
        self._ov_rec_status.pack(side="left")

        def _ov_import_audio(src_path: str) -> None:
            """Importa qualquer formato de áudio como referência OmniVoice,
            convertendo para WAV 24 kHz mono via ffmpeg interno se necessário."""
            import os, subprocess
            src_path = src_path.strip()
            if not src_path or not os.path.exists(src_path):
                self._ov_rec_status.configure(
                    text="❌ Arquivo não encontrado", text_color="#EF4444")
                return
            ext = os.path.splitext(src_path)[1].lower()
            if ext == ".wav":
                # Apara o WAV para ≤15 s sem recodificar
                try:
                    wav_path = self._trim_ref_wav(src_path, max_s=15.0,
                                                  out=plat.temp_path("ov_ref_import.wav"))
                except Exception:
                    self._ov_rec_status.configure(
                        text="❌ WAV inválido / não suportado", text_color="#EF4444")
                    return
            else:
                # Converte + apara para ≤15 s numa única passagem do ffmpeg
                self._ov_rec_status.configure(
                    text="Convertendo áudio…", text_color="#F59E0B")
                self.update_idletasks()
                wav_path = plat.temp_path("ov_ref_import.wav")
                ffmpeg = plat.ffmpeg_exe()
                if not ffmpeg:
                    self._ov_rec_status.configure(
                        text="❌ ffmpeg não encontrado — instale ffmpeg", text_color="#EF4444")
                    return
                try:
                    r = subprocess.run(
                        [ffmpeg, "-y", "-i", src_path, "-t", "15",
                         "-ar", "24000", "-ac", "1", "-sample_fmt", "s16", wav_path],
                        capture_output=True, timeout=60,
                    )
                except Exception:
                    r = None
                if r is None or r.returncode != 0:
                    self._ov_rec_status.configure(
                        text="❌ Conversão falhou", text_color="#EF4444")
                    return
            self._ov_ref_path.set(wav_path)
            # Atualiza o campo com o nome original do arquivo
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
            """Abre o diálogo de arquivo com todos os formatos de áudio suportados."""
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
        # Qualquer formato, convertido internamente pelo ffmpeg
        ctk.CTkLabel(_ov_rec_card,
                     text="— ou importe um áudio gravado —",
                     font=ctk.CTkFont(size=10), text_color=self.MUTED,
                     ).pack(pady=(0, 4))

        _ov_import_row = ctk.CTkFrame(_ov_rec_card, fg_color="transparent")
        _ov_import_row.pack(fill="x", padx=12, pady=(0, 10))

        ctk.CTkButton(
            _ov_import_row, text=self._t("btn_import"), width=100, height=28,
            fg_color=self.SEG_BG, hover_color=self.IBORDER,
            text_color=self.TEXT, border_width=1, border_color=self.IBORDER,
            corner_radius=8, font=ctk.CTkFont(size=12),
            command=_ov_browse,
        ).pack(side="left", padx=(0, 8))

        self._ov_import_entry = ctk.CTkEntry(
            _ov_import_row,
            placeholder_text=self._t("lbl_import_hint"),
            fg_color=self.SEG_BG, border_color=self.IBORDER,
            text_color=self.TEXT, font=ctk.CTkFont(size=11),
        )
        self._ov_import_entry.pack(side="left", fill="x", expand=True)
        # Enter no campo de caminho importa diretamente
        self._ov_import_entry.bind(
            "<Return>",
            lambda e: _ov_import_audio(self._ov_import_entry.get()),
        )

        # Transcrição (preenchida automaticamente após a gravação)
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

        # Botão para ouvir a gravação de referência
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

        # Campo de nome + botão para salvar a referência como clone OmniVoice
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

        # ── Cartão de geração ──────────────────────────────────────────────
        _ov_gen = ctk.CTkFrame(_ov, fg_color=self.INPUT,
                               border_color=self.IBORDER, border_width=1,
                               corner_radius=8)
        _ov_gen.pack(fill="x", padx=16, pady=(0, 6))

        # Frases genéricas por idioma — todos os idiomas suportados pela plataforma
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

        # Linha de seleção de idioma para o teste
        _lang_row = ctk.CTkFrame(_ov_gen, fg_color="transparent")
        _lang_row.pack(fill="x", padx=12, pady=(8, 4))

        ctk.CTkLabel(_lang_row, text="Testar por idioma:",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self.TEXT).pack(side="left")

        self._ov_test_lang_var = ctk.StringVar(value="🇧🇷 Português")
        self._ov_lang_code = "pt"  # código ISO passado ao generate()

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
            """Preenche o campo de texto com a frase genérica do idioma selecionado."""
            lang_label = self._ov_test_lang_var.get()
            _, phrase = _OV_LANG_PHRASES.get(lang_label, ("pt", "Olá! Teste de voz."))
            self._ov_gen_text.delete("1.0", "end")
            self._ov_gen_text.insert("1.0", phrase)

        # Botão para preencher a frase do idioma sem sobrescrever texto personalizado
        ctk.CTkButton(
            _lang_row, text="↺ Frase", width=72, height=28,
            fg_color=self.SEG_BG, hover_color=self.HOVER,
            text_color=self.TEXT, corner_radius=8,
            font=ctk.CTkFont(size=12),
            command=_ov_fill_test_phrase,
        ).pack(side="left", padx=(0, 6))

        # Testar gera o texto que JÁ ESTÁ no campo — não substitui
        ctk.CTkButton(
            _lang_row, text="🔊 Testar", width=90, height=28,
            fg_color=self.ACCENT, hover_color=self.HOVER,
            text_color="#FFFFFF", corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._ov_generate,
        ).pack(side="left")

        # Separador
        ctk.CTkLabel(_ov_gen, text="— ou edite o texto manualmente —",
                     font=ctk.CTkFont(size=10), text_color=self.MUTED).pack(pady=(0, 2))

        self._ov_gen_text = ctk.CTkTextbox(
            _ov_gen, height=72, wrap="word",
            fg_color=self.SEG_BG, border_color=self.IBORDER, border_width=1,
            text_color=self.TEXT, font=ctk.CTkFont(size=12),
        )
        self._ov_gen_text.pack(fill="x", padx=12, pady=(0, 8))
        # Pré-preenche com a frase em PT-BR
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

        # ── Texto para teste de vozes salvas ───────────────────────────────
        _test_lang_options = [
            "pt — Português", "en — English", "es — Español",
            "fr — Français", "de — Deutsch", "it — Italiano",
            "ru — Русский", "zh — 中文",
        ]
        self._test_lang_var = ctk.StringVar(value="pt — Português")

        _tcard = ctk.CTkFrame(_ov, fg_color=self.INPUT,
                               border_color=self.IBORDER, border_width=1,
                               corner_radius=10)
        _tcard.pack(fill="x", padx=16, pady=(12, 4))

        _trow = ctk.CTkFrame(_tcard, fg_color="transparent")
        _trow.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(_trow, text="Texto para teste de vozes:",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=self.TEXT).pack(side="left")
        ctk.CTkOptionMenu(
            _trow, values=_test_lang_options, variable=self._test_lang_var,
            fg_color=self.SEG_BG, button_color=self.IBORDER,
            button_hover_color=self.SEG_BG, text_color=self.TEXT,
            dropdown_fg_color=self.CARD, dropdown_text_color=self.TEXT,
            dropdown_hover_color=self.SEG_BG, font=ctk.CTkFont(size=12),
            width=160,
        ).pack(side="left", padx=(8, 8))

        def _fill_test_phrase() -> None:
            lang = self._test_lang_var.get().split(" ")[0]
            self._rvc_test_text.delete("1.0", "end")
            self._rvc_test_text.insert("1.0", TEST_PHRASES.get(lang, TEST_PHRASES["pt"]))

        ctk.CTkButton(
            _trow, text="↺ Frase", width=72, height=28,
            fg_color=self.SEG_BG, hover_color=self.HOVER,
            text_color=self.TEXT, corner_radius=8,
            font=ctk.CTkFont(size=12),
            command=_fill_test_phrase,
        ).pack(side="left")

        self._rvc_test_text = ctk.CTkTextbox(
            _tcard, height=72, wrap="word",
            fg_color=self.SEG_BG, border_color=self.IBORDER, border_width=1,
            text_color=self.TEXT, font=ctk.CTkFont(size=12),
        )
        self._rvc_test_text.pack(fill="x", padx=12, pady=(0, 10))
        self._rvc_test_text.insert("1.0", TEST_PHRASES["pt"])

        # ── Lista de vozes salvas ───────────────────────────────────────────
        ctk.CTkFrame(_ov, height=1, fg_color=self.BORDER).pack(fill="x", padx=16, pady=(4, 0))
        ctk.CTkLabel(_ov, text="VOZES SALVAS",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=self.MUTED).pack(anchor="w", padx=16, pady=(10, 6))
        self._clone_list_frame = ctk.CTkFrame(_ov, fg_color="transparent")
        self._clone_list_frame.pack(fill="x", padx=16)
        self._refresh_clone_list()

    # ── OmniVoice: gravação de referência ────────────────────────────────────

    _OV_REF_MAX_S = 15   # duração máxima da gravação de referência (s)

    def _ov_toggle_recording(self) -> None:
        """Alterna a gravação de referência OmniVoice."""
        if getattr(self, "_ov_rec_active", False):
            self._ov_stop_recording()
        else:
            self._ov_start_recording()

    def _ov_start_recording(self) -> None:
        """Inicia a gravação de referência OmniVoice usando o fluxo de áudio compartilhado."""
        if not self._meter_stream:
            self._ov_rec_status.configure(
                text="❌ Sem microfone — verifique o dispositivo na Config",
                text_color="#EF4444")
            return
        self._ov_rec_frames = []
        self._ov_rec_active = True
        self._ov_rec_btn.configure(text=self._t("btn_stop_rec"), fg_color="#7C3AED",
                                    hover_color="#6D28D9")
        self._ov_rec_status.configure(text="● Gravando — leia o texto acima",
                                       text_color="#DC2626")
        self._ov_rec_prog.set(0)
        self._ov_rec_timer = 0
        self._ov_rec_tick()

    def _ov_rec_tick(self) -> None:
        """Dispara a cada segundo durante a gravação de referência OmniVoice."""
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
        """Para a gravação de referência, salva o WAV e transcreve com o Whisper."""
        self._ov_rec_active = False
        self._ov_rec_btn.configure(text=self._t("btn_rec_ref"),
                                    fg_color="#DC2626", hover_color="#B91C1C")
        frames = list(self._ov_rec_frames)
        if not frames:
            self._ov_rec_status.configure(text="Sem áudio capturado",
                                           text_color="#EF4444")
            return

        self._ov_rec_status.configure(text="Salvando…", text_color=self.MUTED)

        def _save_and_transcribe():
            import numpy as np, soundfile as sf
            # O fluxo usa dtype=int16 → normalizar para [-1, 1] antes de sf.write
            # (PCM_16 espera float em [-1, 1])
            pcm = np.concatenate(frames, axis=0).flatten().astype(np.float32) / 32768.0
            out = plat.temp_path("ov_ref.wav")
            sr  = getattr(self, "_audio_sr", 44100)
            try:
                sf.write(out, pcm, sr, subtype="PCM_16")
            except Exception as e:
                msg = f"❌ {e}"
                self.after(0, lambda: self._ov_rec_status.configure(
                    text=msg, text_color="#EF4444"))
                return
            self.after(0, lambda: self._ov_ref_path.set(out))
            self.after(0, lambda: self._ov_rec_status.configure(
                text="Gravado — transcrevendo…", text_color=self.MUTED))
            # Habilita o botão de ouvir após gravar
            self.after(0, lambda: self._ov_play_ref_btn.configure(state="normal"))
            # Transcreve automaticamente
            self.after(0, self._ov_transcribe)

        threading.Thread(target=_save_and_transcribe, daemon=True).start()

    def _ov_play_ref(self) -> None:
        """Alterna tocar/parar do WAV de referência."""
        # Se já está tocando, encerra o processo e volta ao estado inicial
        player = getattr(self, "_ov_play_proc", None)
        if player is not None and not player.done:
            self._stop_ov_playback()
            self._ov_play_ref_btn.configure(text="▶ Ouvir referência")
            return

        path = self._ov_ref_path.get()
        if not path or not __import__("os").path.exists(path):
            return

        self._ov_play_ref_btn.configure(text="■ Parar")

        try:
            player = plat.get_backend().play_file(path, self._selected_output())
        except Exception as e:
            self._ov_play_ref_btn.configure(text="▶ Ouvir referência")
            self._ov_rec_status.configure(text=f"❌ {e}", text_color="#EF4444")
            return
        self._ov_play_proc = player

        def _wait(player=player):
            player.wait()
            # Quando terminar naturalmente, restaura o botão (só se ainda for o atual)
            def _restore():
                if getattr(self, "_ov_play_proc", None) is player:
                    self._ov_play_proc = None
                    self._ov_play_ref_btn.configure(text="▶ Ouvir referência")
            self.after(0, _restore)

        threading.Thread(target=_wait, daemon=True).start()

    def _stop_ov_playback(self) -> None:
        player = getattr(self, "_ov_play_proc", None)
        self._ov_play_proc = None
        if player is not None:
            try:
                player.stop()
            except Exception:
                pass

    def _selected_output(self) -> str | None:
        """Dispositivo de saída escolhido na aba Config (None = padrão do sistema)."""
        out_var = getattr(self, "out_var", None)
        if not out_var:
            return None
        return self._label_to_name(out_var.get(), self._outputs) or None

    def _ov_transcribe(self) -> None:
        """Transcreve o WAV de referência com o Whisper."""
        path = self._ov_ref_path.get()
        if not path:
            return
        self._ov_transcribe_btn.configure(state="disabled")
        self._ov_rec_status.configure(text="Transcrevendo…", text_color=self.MUTED)

        def _worker():
            try:
                # Usa faster_whisper (mesmo backend do Praxis)
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
        """Salva o WAV de referência + JSON de metadados na pasta de clones, como clone OmniVoice."""
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
        """Dispara a geração OmniVoice numa thread em segundo plano."""
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
        Evita o TorchCodec do OmniVoice."""
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
        """Substitui em tempo de execução o reconhecimento de fala interno do OmniVoice
        pelo faster-whisper.

        TorchCodec 0.14 é incompatível com PyTorch 2.6.0+cu124 (undefined symbol:
        aoti_torch_abi_version). O OmniVoice usa TorchCodec internamente para decodificar
        áudio antes do reconhecimento de fala. Substituindo o _asr_pipe (ou transcribe)
        por uma implementação com faster-whisper, podemos usar ref_text=None e deixar o
        OmniVoice transcrever o ref_audio com alinhamento perfeito — eliminando
        alucinações causadas por texto e áudio que não batem.
        """
        import tempfile, soundfile as _sf, numpy as _np

        def _fw_asr(audio_input):
            # audio_input pode ser uma tupla (array, sr) ou um caminho (str)
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

        # Tenta substituir via atributo _asr_pipe (OmniVoice >= 0.2)
        if hasattr(model, "_asr_pipe"):
            model._asr_pipe = _fw_asr
        # Alternativa: substitui direto o método transcribe (versões mais antigas)
        if hasattr(model, "transcribe"):
            model.transcribe = _fw_asr
        return model

    @staticmethod
    def _ov_warmup(model, torch_mod) -> None:
        """Aquece os kernels CUDA com uma inferência de teste (num_step=4, texto mínimo),
        para o primeiro teste real sair correto.

        Sem aquecimento: a primeira inferência usa kernels não compilados → o extrator
        de tom (RMVPE) produz estimativas erradas → timbre distorcido no primeiro teste.
        """
        import tempfile, soundfile as _sf, numpy as _np
        try:
            # Cria um WAV curto de silêncio como referência para o aquecimento.
            _dummy = _np.zeros(int(0.5 * 24000), dtype=_np.float32)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as _f:
                _sf.write(_f.name, _dummy, 24000, subtype="PCM_16")
                _dp = _f.name
            # Usa ref_text explícito — silêncio não tem transcrição útil
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
            pass  # falha no aquecimento não é fatal
        finally:
            if torch_mod.cuda.is_available():
                torch_mod.cuda.empty_cache()

    @staticmethod
    def _trim_ref_wav(wav_path: str, max_s: float = 15.0, out: str | None = None) -> str:
        """Apara o WAV de referência para max_s segundos, para não esgotar a memória em gravações longas."""
        import wave as _wave
        with _wave.open(wav_path, "rb") as wf:
            sr, nch, sw = wf.getframerate(), wf.getnchannels(), wf.getsampwidth()
            dur = wf.getnframes() / sr
            if dur <= max_s:
                return wav_path  # já é curto o suficiente
            raw = wf.readframes(int(sr * max_s))
        out = out or plat.new_temp_file(".wav")
        with _wave.open(out, "wb") as wf:
            wf.setnchannels(nch); wf.setsampwidth(sw); wf.setframerate(sr)
            wf.writeframes(raw)
        return out

    def _ov_generate_worker(self, ref_path: str, ref_text: str, gen_text: str, lang_code: str = "pt") -> None:
        """Thread de trabalho: roda o OmniVoice e salva o resultado em /tmp/ov_result.wav.
        Usa create_voice_clone_prompt(ref_text=None) para transcrição automática —
        evita ruído quando ref_text e ref_audio não batem."""
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
                # Ajuste: substitui o _asr_pipe do OmniVoice pelo faster-whisper local.
                # TorchCodec 0.14 é incompatível com PyTorch 2.6 (undefined symbol aoti_torch_abi_version).
                self._ov_model = self._patch_ov_transcribe(self._ov_model)
                # Aquece a placa de vídeo: compila os kernels CUDA para o primeiro teste ser preciso
                _st("Aquecendo GPU…")
                self._ov_warmup(self._ov_model, torch)

            # Apara para ≤5 s — fronteira mais limpa entre referência e texto gerado
            ref_path = self._trim_ref_wav(ref_path, max_s=5.0)

            # Libera o cache CUDA antes da inferência
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            # ref_text=None → o OmniVoice transcreve internamente via nosso ajuste com Whisper
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
            import numpy as _np
            _audio = _np.array(audio[0], dtype=_np.float32)
            _peak = float(_np.max(_np.abs(_audio)))
            if _peak > 1e-6:
                _audio = _audio / max(_peak, 1.0)
            out_path = plat.temp_path("ov_result.wav")
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
        """Reproduz o WAV de resultado do OmniVoice (/tmp/ov_result.wav)."""
        path = getattr(self, "_ov_result_path", plat.temp_path("ov_result.wav"))
        if not __import__("os").path.exists(path):
            return
        def _play():
            import sounddevice as sd, soundfile as sf
            data, sr = sf.read(path, dtype="float32")
            dev = self._selected_output()
            idx = None
            if dev and isinstance(plat.get_backend(), plat.SoundDeviceBackend):
                idx = plat.get_backend().device_index(dev, "output")
            sd.play(data, sr, device=idx)
            sd.wait()
        threading.Thread(target=_play, daemon=True).start()

    def _refresh_clone_list(self) -> None:
        """Atualiza a lista de clones existentes na aba de clonagem."""
        for w in self._clone_list_frame.winfo_children():
            w.destroy()
        profiles = sorted(self.CLONES_DIR.glob("*.json"))
        if not profiles:
            ctk.CTkLabel(self._clone_list_frame,
                         text=self._t("lbl_no_clones"),
                         font=ctk.CTkFont(size=11), text_color=self.MUTED).pack(
                             anchor="w", pady=4)
            return
        for jp in profiles:
            try:
                meta = json.loads(jp.read_text())
            except Exception:
                continue
            name           = meta.get("name", jp.stem)
            dur            = meta.get("duration_s", 0)
            _engine_lbl    = "OmniVoice"
            _engine_color  = "#7C3AED"

            row  = ctk.CTkFrame(self._clone_list_frame, fg_color=self.SEG_BG,
                                corner_radius=8, border_width=1,
                                border_color=self.IBORDER)
            row.pack(fill="x", pady=(0, 6))
            row.grid_columnconfigure(0, weight=1)

            # Linha de nome: nome + selo do motor
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
                btn_frame, text=self._t("btn_test"), width=80, height=26,
                fg_color=self.SEG_BG, hover_color=self.IBORDER,
                text_color=self.MUTED, border_width=1,
                border_color=self.IBORDER, corner_radius=6,
                font=ctk.CTkFont(size=11),
            )
            _tbtn.pack(side="left", padx=(0, 4))
            ctk.CTkButton(
                btn_frame, text=self._t("btn_use"), width=60, height=26,
                fg_color=self.ACCENT, hover_color=self.HOVER,
                text_color="#FFFFFF", corner_radius=6,
                font=ctk.CTkFont(size=11),
                command=lambda p=wav_path, n=name: self._use_clone(p, n),
            ).pack(side="left", padx=(0, 4))
            ctk.CTkButton(
                btn_frame, text="🗑 Apagar", width=80, height=26,
                fg_color=self.SEG_BG, hover_color="#FEE2E2",
                text_color="#EF4444", border_width=1,
                border_color="#EF4444", corner_radius=6,
                font=ctk.CTkFont(size=11),
                command=lambda jp=jp: self._delete_clone(jp),
            ).pack(side="left")

            # Barra de progresso + rótulo de status dentro do cartão, para retorno visual do teste
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
            _card_prog.grid_remove()   # oculta até o teste iniciar

            _tbtn.configure(
                command=lambda p=wav_path, rt=meta.get("ref_text", ""), b=_tbtn,
                              pg=_card_prog, st=_card_status:
                    self._test_clone(p, rt, b, pg, st))

    def _restart_audio_stream(self) -> None:
        """Reinicia o fluxo de áudio quando o dispositivo da aba Config muda."""
        self._stop_meter()
        import time; time.sleep(0.2)
        self._start_meter()

    def _clone_meter_configure(self, event: tk.Event) -> None:
        """Desenha o gradiente verde→amarelo→vermelho no canvas do medidor da aba de clonagem."""
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

        # Máscara cobre a parte não preenchida
        self._clone_meter_ids["mask"] = c.create_rectangle(
            0, 0, W, H, fill=self.INPUT, outline="")
        # Linha de pico
        self._clone_meter_ids["peak"] = c.create_line(
            0, 0, 0, H, fill=self.INPUT, width=2)

    def _clone_meter_update(self, level: float, db: float) -> None:
        """Atualiza a máscara e o pico do medidor da aba de clonagem a partir do nível de áudio."""
        W = self._clone_meter_W
        H = self._clone_meter_H
        if W < 2 or not self._clone_meter_ids:
            return
        c  = self._clone_meter_canvas
        mx = int(W * level)

        # Move a máscara para revelar o gradiente até o nível atual
        c.coords(self._clone_meter_ids["mask"], mx, 0, W, H)

        # Pico: sobe rápido, cai devagar (retenção + decaimento)
        if level >= self._clone_meter_peak:
            self._clone_meter_peak = level
        else:
            self._clone_meter_peak = max(0.0, self._clone_meter_peak - 0.008)
        px = int(W * self._clone_meter_peak)
        peak_color = "#EF4444" if db > -6 else "#F59E0B" if db > -18 else "#22C55E"
        c.coords(self._clone_meter_ids["peak"], px, 0, px, H)
        c.itemconfigure(self._clone_meter_ids["peak"], fill=peak_color)

        # Atualiza o rótulo de dB
        self._meter_db_lbl.configure(text=f"{db:.0f} dB")

    def _start_meter(self) -> None:
        """Fluxo de áudio de entrada e saída simultâneas, compartilhado: medidor + monitor + gravação.
        Herda o dispositivo selecionado na aba Config via self.mic_var."""
        # Obtém o nome PulseAudio do dispositivo configurado (sem o sufixo de canal :left/:right)
        mic_label = getattr(self, "mic_var", None)
        mic_name  = self._label_to_name(mic_label.get(), self._inputs) if mic_label else ""
        pa_in     = mic_name.split(":")[0] if mic_name else ""

        out_label = getattr(self, "out_var", None)
        out_name  = self._label_to_name(out_label.get(), self._outputs) if out_label else ""
        pa_out    = out_name.split(":")[0] if out_name else ""

        def _run():
            try:
                import sounddevice as sd, numpy as np

                backend = plat.get_backend()
                device = None
                if isinstance(backend, plat.PulseBackend):
                    # No Linux o PortAudio só enxerga o dispositivo "default" do PulseAudio,
                    # então apontamos os padrões para a seleção (restaurados ao fechar).
                    self._set_pulse_defaults(pa_in, pa_out)
                else:
                    device = (backend.device_index(pa_in, "input"),
                              backend.device_index(pa_out, "output"))

                SR = 44100  # fixo; o PipeWire converte a taxa se necessário

                self._audio_sr = SR

                def _cb(indata, outdata, frames, time_info, status):
                    # Medidor com gradiente (canvas igual ao da aba Config)
                    rms = float(np.sqrt(np.mean(indata.astype(np.float32) ** 2)))
                    db = 20 * np.log10(rms / 32768.0) if rms > 0 else -60.0
                    db = max(-60.0, min(0.0, db))
                    level = (db + 60.0) / 60.0
                    # Nunca mexer no Tk a partir da thread de áudio: publica o valor e
                    # deixa _clone_meter_poll() (thread principal, ~30 Hz) desenhá-lo.
                    self._clone_meter_val = (level, db)

                    # Monitor / retorno (entrada mono → todos os canais de saída)
                    if getattr(self, "_monitor_on", False):
                        outdata[:] = indata
                    else:
                        outdata.fill(0)

                    # Gravação de referência OmniVoice
                    if getattr(self, "_ov_rec_active", False):
                        self._ov_rec_frames.append(indata.copy())

                # Abre no dispositivo 'default', que agora aponta para a seleção do pactl.
                # Muitas saídas (ex.: alto-falantes do MacBook) recusam mono → abre a
                # saída com o número de canais do dispositivo (máx. 2).
                out_idx = device[1] if device else None
                try:
                    out_info = sd.query_devices(out_idx if out_idx is not None
                                                else sd.default.device[1], "output")
                    out_ch = max(1, min(2, int(out_info["max_output_channels"])))
                except Exception:
                    out_ch = 1
                with sd.Stream(
                    device=device,
                    samplerate=SR, channels=(1, out_ch), dtype="int16",
                    blocksize=128, latency="low", callback=_cb,
                ) as stream:
                    self._meter_stream = stream
                    while self._meter_stream is not None:
                        import time; time.sleep(0.05)
            except Exception:
                import traceback; traceback.print_exc()

        self._clone_meter_val = None
        self._meter_thread = threading.Thread(target=_run, daemon=True)
        self._meter_thread.start()
        if not getattr(self, "_clone_meter_poll_id", None):
            self._clone_meter_poll()

    def _clone_meter_poll(self) -> None:
        """Consulta periódica na thread principal que desenha o medidor da aba de clonagem (~30 Hz)."""
        val = getattr(self, "_clone_meter_val", None)
        if val is not None:
            self._clone_meter_val = None
            try:
                self._clone_meter_update(*val)
            except Exception:
                pass
        self._clone_meter_poll_id = self.after(33, self._clone_meter_poll)

    def _toggle_clone_monitor(self) -> None:
        """Liga/desliga o monitor de áudio (retorno microfone → caixas). Avisa sobre eco."""
        on = self._monitor_var.get()
        setattr(self, "_monitor_on", on)
        if on:
            # Aviso de eco quando o monitor está ligado
            self._monitor_lbl.configure(
                text="🎧 Monitor  ⚠ use fones", text_color="#F59E0B")
        else:
            self._monitor_lbl.configure(text="🎧 Monitor", text_color=self.MUTED)

    def _stop_meter(self) -> None:
        self._meter_stream = None
        pid = getattr(self, "_clone_meter_poll_id", None)
        self._clone_meter_poll_id = None
        if pid:
            try:
                self.after_cancel(pid)
            except Exception:
                pass
        t = getattr(self, "_meter_thread", None)
        if t is not None and t.is_alive() and t is not threading.current_thread():
            t.join(timeout=2)   # deixa o PortAudio fechar o fluxo antes de o Tk sumir

    def _set_pulse_defaults(self, src: str, sink: str) -> None:
        """Linux/PulseAudio: define temporariamente a entrada/saída padrão, lembrando
        as originais para que _restore_default_devices() as restaure ao fechar."""
        if not hasattr(self, "_orig_pa_defaults"):
            self._orig_pa_defaults = _pa_defaults()
        for kind, name in (("source", src), ("sink", sink)):
            if not name:
                continue
            try:
                subprocess.run(["pactl", f"set-default-{kind}", name],
                               capture_output=True, timeout=3)
            except Exception:
                pass

    def _restore_default_devices(self) -> None:
        orig = getattr(self, "_orig_pa_defaults", None)
        if not orig:
            return
        for kind, name in zip(("source", "sink"), orig):
            if not name:
                continue
            try:
                subprocess.run(["pactl", f"set-default-{kind}", name],
                               capture_output=True, timeout=3)
            except Exception:
                pass

    def _test_clone(self, wav_path: str, ref_text: str,
                    test_btn: ctk.CTkButton | None = None,
                    test_prog: ctk.CTkProgressBar | None = None,
                    test_status: ctk.CTkLabel | None = None) -> None:
        """Testa o clone de voz via OmniVoice (único motor disponível)."""
        if self._testing:
            return
        self._testing = True

        lang_code = getattr(self, "_test_lang_var", ctk.StringVar(value="pt")).get()
        lang_code = lang_code.split(" ")[0] if " " in lang_code else lang_code
        # Lê o texto da caixa de teste; se vazio, usa as frases padrão
        _txt_box = getattr(self, "_rvc_test_text", None)
        if _txt_box:
            try:
                phrase = _txt_box.get("1.0", "end").strip() or TEST_PHRASES.get(lang_code, "Teste de voz.")
            except Exception:
                phrase = TEST_PHRASES.get(lang_code, TEST_PHRASES.get("en", "Hello, this is a voice test."))
        else:
            phrase = TEST_PHRASES.get(lang_code, TEST_PHRASES.get("en", "Hello, this is a voice test."))

        if test_btn:
            try:
                test_btn.configure(state="disabled", text="…")
            except Exception:
                pass

        _anim_stop = threading.Event()
        _phase_range = [0.05, 0.50]

        def _set_prog(v: float) -> None:
            if test_prog:
                self.after(0, test_prog.set, v)

        def _animate():
            import time
            if test_prog:
                self.after(0, test_prog.grid)   # exibe a barra de progresso no cartão
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
                self.after(0, lambda kw=kw: test_status.configure(**kw))
            if phase:
                _phase_range[0], _phase_range[1] = phase

        def _done():
            _anim_stop.set()
            self._testing = False
            if test_btn:
                try:
                    self.after(0, lambda: test_btn.configure(
                        state="normal", text=self._t("btn_test")))
                except Exception:
                    pass

        def _worker_ov():
            # Backend OmniVoice: usa create_voice_clone_prompt(ref_text=None) para
            # transcrição automática interna — elimina ruído quando texto e áudio não batem.
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
                    # Troca o reconhecimento de fala interno pelo faster-whisper — TorchCodec 0.14 é incompatível.
                    self._ov_model = self._patch_ov_transcribe(self._ov_model)
                    # Aquece a placa de vídeo para o primeiro teste ser preciso
                    _update("Aquecendo GPU…", phase=(0.45, 0.50))
                    self._ov_warmup(self._ov_model, torch)
                else:
                    _update("OmniVoice em memória…", phase=(0.05, 0.15))

                # Apara para ≤5 s — fronteira mais limpa entre referência e texto gerado
                trimmed = self._trim_ref_wav(wav_path, max_s=5.0)

                # Libera o cache CUDA antes da inferência
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

                # ref_text=None → o OmniVoice transcreve internamente via nosso ajuste com Whisper
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
                # Normaliza para ±1.0 e salva como PCM_16 — o aplay lê o cabeçalho WAV
                # e toca no formato correto, sem distorção nem volume estourado.
                import numpy as _np
                _audio = _np.array(audio[0], dtype=_np.float32)
                _peak = float(_np.max(_np.abs(_audio)))
                if _peak > 1e-6:
                    _audio = _audio / max(_peak, 1.0)  # escala se pico > 1; mantém se ≤ 1
                tmp = plat.temp_path("praxis_clone_test.wav")
                sf.write(tmp, _audio, 24000, subtype="PCM_16")
                plat.get_backend().play_file(tmp, self._selected_output()).wait(120)
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
        threading.Thread(target=_worker_ov, daemon=True).start()

    def _use_clone(self, wav_path: str, name: str) -> None:
        """Define a voz clonada como voz de saída e vai para aba Config."""
        self._clone_voice_path = wav_path
        self._clone_voice_name = name
        # Ativa filtro de clones e mostra apenas clones no dropdown
        if hasattr(self, "_show_clones"):
            self._show_clones.set(True)
        if hasattr(self, "_voice_menu"):
            # Garante que o clone está na lista interna de vozes
            label = f"🎙 {name}"
            if not any(p == wav_path for p, _ in self._voices):
                self._voices.insert(0, (wav_path, label))
            # Mostra apenas clones
            clone_labels = [lbl for _, lbl in self._voices if lbl.startswith("🎙 ")]
            self._voice_menu.configure(values=clone_labels or [label])
            self.voice_var.set(label)
        self._tab_seg.set(self._t("tab_config"))
        self._on_tab_change(self._t("tab_config"))

    def _delete_clone(self, json_path: Path) -> None:
        """Remove um clone de voz: apaga o JSON, o WAV e os .pth associados."""
        try:
            meta = json.loads(json_path.read_text())
            wav  = self.CLONES_DIR / meta.get("wav", "")
            if wav.exists():
                wav.unlink()
            json_path.unlink()
        except Exception:
            pass
        self._refresh_clone_list()

    # ── Liga/desliga do monitor ───────────────────────────────────────────────

    def _toggle_monitor(self) -> None:
        """Alterna o monitor de áudio (ouvir a tradução na saída) e salva o estado."""
        self._monitor = not self._monitor
        if self._monitor:
            self._mon_btn.configure(
                text=self._t("mon_on"),
                fg_color=self.MON_ON, hover_color=self.HOVER,
                text_color="#FFFFFF",
            )
        else:
            self._mon_btn.configure(
                text=self._t("mon_off"),
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
        ctk.CTkLabel(hdr, text=self._t("bilat_label"),
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=self.MUTED).grid(row=0, column=0, sticky="w")
        row += 1

        # Botão liga/desliga
        self._bilat_btn = ctk.CTkButton(
            self._card,
            text=self._t("bilat_on") if self._bilateral else self._t("bilat_off"),
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
                     text=self._t("bilat_voice"),
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

        # Cartão de instrução de roteamento
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
                text=self._t("bilat_on"),
                fg_color=self.MON_ON, hover_color=self.HOVER,
                text_color="#FFFFFF",
            )
            self._bilat_voice_frame.grid()
            self._bilat_info.grid()
        else:
            self._bilat_btn.configure(
                text=self._t("bilat_off"),
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
        """Coleta todos os valores atuais da interface e os retorna como dicionário de configuração."""
        def code_of(label: str) -> str:
            # extrai o código do sufixo "Nome  (código)"
            try:
                code = label.split("(")[-1].rstrip(")")
                if code in LANG_CODES:
                    return code
            except (ValueError, IndexError):
                pass
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
            "ui_lang":        self.cfg.get("ui_lang", "pt"),
        }

    def _save(self) -> None:
        """Salva as configurações atuais no arquivo de configuração."""
        self.cfg.update(self._collect())
        save_cfg(self.cfg)
        messagebox.showinfo("Praxis", "Configurações salvas.")

    def _launch(self) -> None:
        """Valida a configuração e inicia o motor Praxis (praxis.py) como subprocesso."""
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
        self.cfg.update(cfg)
        save_cfg(self.cfg)

        # Para o motor anterior se ainda estiver rodando
        self._stop_engine(collapse=False)

        venv_python = plat.installed_python()
        python = str(venv_python) if venv_python else sys.executable

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

        # Reinicia a interface de monitoramento
        self._mon_set_status("Iniciando…", "#F59E0B")
        self._mon_prog_bar.set(0)
        self._mon_prog_frame.pack(fill="x", padx=14, pady=(0, 10))
        for box in (self._orig_box, self._trans_box, self._log_box):
            box.configure(state="normal")
            box.delete("1.0", "end")
            box.configure(state="disabled")

        # Inicia o motor — inclui o cuBLAS da Ollama no LD_LIBRARY_PATH para a placa de vídeo funcionar
        _env = plat.cuda_env(os.environ.copy())
        _env["PYTHONIOENCODING"] = "utf-8"   # linhas JSON com caracteres não ASCII no Windows
        self._close_engine_log()
        self._engine_log = open(plat.log_path(), "w", encoding="utf-8")
        try:
            self._engine_proc = subprocess.Popen(
                cmd_parts,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=self._engine_log,
                text=True,
                encoding="utf-8",
                bufsize=1,
                env=_env,
            )
        except OSError as e:
            messagebox.showerror("Praxis", f"Falha ao iniciar o motor:\n{e}")
            self._mon_set_status("Erro", "#EF4444")
            return
        threading.Thread(target=self._engine_reader, args=(self._engine_proc,),
                         daemon=True).start()

        # Exibe o painel de monitoramento à direita — _left encolhe, _right ocupa 560px
        self._left.pack_configure(expand=False)
        self._right.pack(side="left", fill="y")
        # Abre espaço para o painel sem vazar do monitor atual
        place_window(self, 1120, self._logical_height(), keep_position=True)
        self._iniciar_btn.configure(state="disabled", text="Rodando…")
        if hasattr(self, "_theme_btn"):
            self._theme_btn.configure(state="disabled")

    def _stop_engine(self, collapse: bool = True) -> None:
        """Para o subprocesso do motor Praxis. Se collapse=True, recolhe o painel de monitoramento."""
        proc = getattr(self, "_engine_proc", None)
        self._engine_proc = None   # o leitor ignora eventos de um processo antigo
        if proc is not None:
            threading.Thread(target=self._terminate_engine, args=(proc,),
                             daemon=True).start()

        if collapse:
            self._right.pack_forget()
            self._left.pack_configure(expand=True)  # restaura expansão total
            place_window(self, 560, self._logical_height(), keep_position=True)
            self._iniciar_btn.configure(state="normal", text=self._t("btn_start"))
            self._mon_set_status("Parado", "#EF4444")
        if hasattr(self, "_theme_btn"):
            self._theme_btn.configure(state="normal")
        if hasattr(self, "_apply_voice_btn"):
            self._apply_voice_btn.configure(state="disabled", text="⟳  Aplicar")

    @staticmethod
    def _terminate_engine(proc: subprocess.Popen) -> None:
        """Parada suave: JSON 'stop' → fecha a entrada padrão → SIGTERM → SIGKILL.
        O motor remove seus dispositivos virtuais ao sair; o processo é sempre recolhido."""
        if proc.poll() is None:
            try:
                proc.stdin.write(json.dumps({"cmd": "stop"}) + "\n")
                proc.stdin.flush()
            except Exception:
                pass
        try:
            proc.stdin.close()
        except Exception:
            pass
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()

    def _close_engine_log(self) -> None:
        log = getattr(self, "_engine_log", None)
        self._engine_log = None
        if log is not None:
            try:
                log.close()
            except Exception:
                pass

    def _post(self, fn, *args) -> None:
        """self.after() a partir de uma thread de trabalho, tolerando janela já destruída."""
        try:
            self.after(0, fn, *args)
        except (RuntimeError, tk.TclError):
            pass

    def _engine_reader(self, proc: subprocess.Popen) -> None:
        """Thread que lê a saída padrão do motor (um JSON por linha) e atualiza a interface
        de monitoramento. Eventos de um processo que não é mais o atual são descartados."""
        last_error = ""

        def _current() -> bool:
            return proc is self._engine_proc

        for raw in proc.stdout:
            if not _current():
                continue
            line = raw.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                self._post(self._log_append, line)
                continue
            if not isinstance(ev, dict):
                continue
            etype = ev.get("e")
            # Bilateral: a fala do interlocutor ("in") é marcada para não ser confundida com a sua
            prefix = "← " if ev.get("dir") == "in" else ""
            if etype == "progress":
                pct = ev.get("pct", 0) / 100
                msg = ev.get("msg", "")
                self._post(self._set_progress, pct, msg)
            elif etype == "model":
                note = ev.get("note") or ""
                self._post(self._log_append, f"[modelo] {ev.get('model')} (automático)"
                           + (f" — ⚠ {note}" if note else ""))
            elif etype == "accel":
                self._post(self._log_append,
                           f"[aceleração] Whisper: {ev.get('asr', '?').upper()} — {ev.get('reason', '')}")
            elif etype == "ready":
                self._post(self._on_engine_ready)
            elif etype == "transcript":
                self._post(self._mon_append, self._orig_box, prefix + ev.get("text", ""))
            elif etype == "translation":
                self._post(self._mon_append, self._trans_box, prefix + ev.get("text", ""))
            elif etype == "voice_reloaded":
                label = next((lbl for p, lbl in self._voices
                              if p == ev.get("path", "")), ev.get("path", ""))
                self._post(self._log_append, f"[voz] {label}")
                self._post(lambda: self._apply_voice_btn.configure(
                    state="normal", text="⟳  Aplicar") if hasattr(self, "_apply_voice_btn") else None)
            elif etype == "error":
                last_error = ev.get("msg", "")
                self._post(self._log_append, f"[erro] {last_error}")
                self._post(lambda: self._apply_voice_btn.configure(
                    state="normal", text="⟳  Aplicar") if hasattr(self, "_apply_voice_btn") else None)
        rc = proc.wait()
        if _current():
            # O motor parou sozinho (falha / erro na inicialização): libera a interface e diz o motivo
            self._engine_proc = None
            self._post(self._on_engine_exit, rc, last_error)

    def _on_engine_exit(self, rc: int, last_error: str) -> None:
        self._close_engine_log()
        self._iniciar_btn.configure(state="normal", text=self._t("btn_start"))
        if hasattr(self, "_theme_btn"):
            self._theme_btn.configure(state="normal")
        if hasattr(self, "_apply_voice_btn"):
            self._apply_voice_btn.configure(state="disabled", text="⟳  Aplicar")
        if rc == 0:
            self._mon_set_status("Encerrado", "#EF4444")
            return
        self._mon_set_status("Erro", "#EF4444")
        tail = ""
        try:
            tail = Path(plat.log_path()).read_text(encoding="utf-8", errors="replace")[-1500:]
        except Exception:
            pass
        self._log_append(f"[erro] motor encerrou (código {rc}). Log: {plat.log_path()}")
        messagebox.showerror(
            "Praxis", f"O motor encerrou com erro (código {rc}).\n\n"
                      f"{last_error or tail.strip()[-600:]}\n\nLog: {plat.log_path()}")

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


def _set_process_identity() -> None:
    """Mostra "Praxis" em vez de "Python" na barra de menus / Dock do macOS e
    agrupa o item da barra de tarefas do Windows sob Praxis. Melhor esforço;
    dependências opcionais."""
    try:
        if plat.IS_MAC:
            from Foundation import NSBundle  # pyobjc (opcional)
            info = NSBundle.mainBundle().localizedInfoDictionary() or \
                NSBundle.mainBundle().infoDictionary()
            if info is not None:
                info["CFBundleName"] = "Praxis"
        elif plat.IS_WIN:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Praxis.App")
    except Exception:
        pass


if __name__ == "__main__":
    _set_process_identity()
    app = ConfigWindow()
    app.mainloop()
