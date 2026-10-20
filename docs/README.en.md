# ✦ Praxis

> **One message. Every language.**

<div align="center">

[🇧🇷 Português](../README.md) · **[🇺🇸 English](README.en.md)** · [🇪🇸 Español](README.es.md) · [🇫🇷 Français](README.fr.md) · [🇩🇪 Deutsch](README.de.md) · [🇮🇹 Italiano](README.it.md) · [🇷🇺 Русский](README.ru.md) · [🇨🇳 中文](README.zh.md) · [🇳🇱 Nederlands](README.nl.md) · [🇵🇱 Polski](README.pl.md) · [🇺🇦 Українська](README.uk.md) · [🇹🇷 Türkçe](README.tr.md) · [🇸🇦 العربية](README.ar.md) · [🇮🇳 हिन्दी](README.hi.md)

[![Linux](https://img.shields.io/badge/Linux-PulseAudio%2FPipeWire-informational?logo=linux)](https://github.com/disouz4-dev/praxis)
[![macOS](https://img.shields.io/badge/macOS-BlackHole-informational?logo=apple)](https://github.com/disouz4-dev/praxis)
[![Windows](https://img.shields.io/badge/Windows-VB--Cable-informational?logo=windows)](https://github.com/disouz4-dev/praxis)
[![CI](https://github.com/disouz4-dev/praxis/actions/workflows/ci.yml/badge.svg)](https://github.com/disouz4-dev/praxis/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://github.com/disouz4-dev/praxis)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Offline](https://img.shields.io/badge/100%25-offline-success)](https://github.com/disouz4-dev/praxis)

</div>

---

Communication has always been humanity's most powerful tool. Yet language remains one of the greatest barriers between people, cultures, and ideas.

**Praxis** was built to change that.

The idea is simple: let two people have a natural conversation, each speaking their own language, while the other hears it in their native tongue — in real time.

Picture a Brazilian speaking in Portuguese while an American hears every word in English. A moment later the American replies in English, and the Brazilian hears it in Portuguese. No translation pauses. No need to learn another language. Just a conversation.

More than a voice translator, **Praxis** aims to make technology invisible — letting communication happen the way it should: spontaneous, human, and accessible.

The name **Praxis** means action — the act of putting into practice what brings people together.

---

## Vision

Build a real-time voice translation platform that enables natural conversations between people anywhere in the world, preserving context, emotion, and fluency.

## Mission

Eliminate linguistic barriers so that ideas, knowledge, and relationships can cross borders without language being an obstacle.

## Principles

- Technology should bring people closer together.
- Every voice deserves to be understood.
- Language should not limit connections.
- Translation should be so natural it disappears from the conversation.
- A message can reach anyone, in any language.

---

## How it works

Praxis creates a **virtual microphone** in your operating system. You speak in your language; the voice comes out already translated — ready to be selected in Discord, WhatsApp, Google Meet, OBS, or any other app.

```
Real microphone  →  VAD  →  Whisper ASR  →  Argos Translate  →  Piper TTS
                                                                       ↓
                                                           Virtual sink (Praxis_Out)
                                                                       ↓
                                                       Praxis_Microfone  ←  Discord / Meet / OBS
```

Everything runs **100% locally** — no internet, no cloud, nothing leaves your machine.

---

## Activation modes

| Mode | Description |
|------|-------------|
| **Auto VAD** | Silero VAD detects when you're speaking and opens automatically |
| **Gate threshold** | Activates only above a volume threshold — drag the bar below the meter to adjust |
| **Push-to-Talk** | Hold a button (keyboard or mouse) to transmit |

---

## Supported languages

### Output language (with available Piper voice)

| Language | Code | Available voices |
|----------|------|-----------------|
| Português | `pt` | Faber, Cadu (BR) · Tugão (PT) |
| English | `en` | Lessac, Ryan (US) · Alan, Alba (GB) |
| Español | `es` | Sharvard (ES) · ALD (MX) |
| Français | `fr` | Siwis, Gilles |
| Deutsch | `de` | Thorsten, Karlsson, MLS |
| Italiano | `it` | Paola, Riccardo |
| Русский | `ru` | Dmitri, Irina |
| 中文 | `zh` | Huayan |
| Nederlands | `nl` | MLS |
| Polski | `pl` | Gosia |
| Українська | `uk` | Lada |
| Türkçe | `tr` | DFKI |
| العربية | `ar` | Kareem |
| हिन्दी | `hi` | Rohan |

### Input language (recognized by Whisper)

Portuguese · English · Spanish · French · German · Italian · Japanese · Chinese · Korean · Russian · Arabic · Hindi · Dutch · Polish · Ukrainian · Turkish — and dozens of other languages supported by Whisper.

> Translations between two non-English languages use **automatic English pivot** (e.g. pt→it goes pt→en→it).

---

## Installation

### Linux / macOS

```bash
git clone https://github.com/disouz4-dev/praxis.git
cd praxis
./install.sh
```

### Windows (PowerShell)

```powershell
git clone https://github.com/disouz4-dev/praxis.git
cd praxis
powershell -ExecutionPolicy Bypass -File install.ps1
```

The installer creates an isolated virtual environment, installs the dependencies (Whisper, Argos, Piper — **no PyTorch**), downloads a default voice and creates an app shortcut with icon (app menu on Linux, `~/Applications/Praxis.app` on macOS, Start Menu on Windows). Voice cloning (OmniVoice, needs PyTorch) is optional: `PRAXIS_WITH_CLONE=1 ./install.sh`.

### Requirements

| | Linux | macOS | Windows |
|---|---|---|---|
| Python | 3.10+ | 3.10+ (Homebrew) | 3.10+ (python.org) |
| Virtual microphone | created automatically (PulseAudio/PipeWire) | [BlackHole 2ch](https://existential.audio/blackhole/) — installed by `install.sh` | [VB-Audio Virtual Cable](https://vb-audio.com/Cable/) |
| Bilateral mode | automatic | + BlackHole 16ch | + VB-Cable A+B |
| GPU (automatic) | NVIDIA CUDA · AMD/Intel via Vulkan¹ | Apple Silicon via MLX · Intel: CPU² | NVIDIA CUDA · AMD/Intel via Vulkan¹ |

¹ opt-in: `PRAXIS_GPU=vulkan ./install.sh` (builds whisper.cpp; needs the Vulkan SDK). ² Measured: on Intel+AMD Macs whisper.cpp/Metal transcribes incorrectly and is slower than the CPU. Voice cloning (OmniVoice) uses CUDA or MPS. Force a backend with `--device cpu|cuda|mlx|whispercpp` or `PRAXIS_DEVICE`.

Quick diagnostics: `python praxis.py --check` (dependencies + audio) and `python praxis.py --list-devices`.

---

## Usage

```bash
praxis
```

In the configuration window, select:
1. **Activation mode** (VAD / Gate / PTT)
2. **Input microphone**
3. **Source and target language**
4. **Output voice** (download additional voices with the ⬇ Download button)
5. Click **✦ Start**

In your call app, select the virtual microphone: **Praxis_Microfone** (Linux), **BlackHole 2ch** (macOS) or **CABLE Output** (Windows).

---

## Technical pipeline

| Stage | Tool | Details |
|-------|------|---------|
| Speech segmentation | **Silero VAD (ONNX)** | Cut on silence (200 ms) or at the quietest point after 4s; 250 ms pre-roll |
| Transcription | **faster-whisper** | `small` model by default; GPU int8_float16 / CPU int8; repetition-loop filter |
| Translation | **Argos Translate** (CTranslate2) | 100% offline; English pivot; downloads pairs on first use |
| Voice synthesis | **Piper TTS** | Lightweight `.onnx` models; per-sentence parallel synthesis |
| Audio output | **PulseAudio** (Linux) · **PortAudio** (macOS/Windows) | Injected into the virtual microphone |

---

## Tests and quality

```bash
pip install -r requirements-dev.txt && pip install --no-deps argostranslate
pytest                                   # unit + smoke + GUI (fast, no models)
python benchmarks/fetch_speech_corpus.py # real human speech (LibriSpeech/MLS, CC BY 4.0)
pytest -m slow                           # transcription quality (WER) + latency gates
python benchmarks/run_benchmarks.py asr --models small --langs pt en es
python benchmarks/run_benchmarks.py latency --model small
```

CI runs on Linux, macOS and Windows on every push. Results and QA report: [`benchmarks/results/`](../benchmarks/results/) · [`docs/QA_REPORT.md`](QA_REPORT.md).

---

## Voice Cloning (OmniVoice)

The **"Clone my voice"** tab lets you clone any voice in seconds — just record or import an audio clip of 5–15 seconds. No training needed.

### How to use

1. Open the **🎙 Clone my voice** tab
2. Enter a name for the profile (e.g. `Diego`)
3. **Option A — Record:** click the microphone button and read a short generic text
   **Option B — Import:** click "Import audio" and select any WAV/MP3/OGG/OPUS/M4A/FLAC/AAC file (including WhatsApp voice messages)
4. Click **Test** to hear the cloned voice
5. Click **Use** to activate the cloned voice as the default output

### Technology

- **OmniVoice** (k2-fsa/OmniVoice) — zero-shot voice cloning, no training needed
- **faster-whisper** — automatic transcription of the reference audio
- **ffmpeg** — internal format conversion (any format → WAV 24 kHz)
- Clone saved in `voices/clones/` as `.wav` (reference) + `.json` (metadata)

> Reference audio is automatically trimmed to 15 seconds for best cloning quality.

---

## Roadmap

- [x] Zero-shot voice cloning with OmniVoice (no training required)
- [x] External audio import (WAV/MP3/OGG/OPUS/M4A and more)
- [ ] Full bidirectional translation (hear the other person translated too)
- [ ] Tray icon and global hotkey to pause/resume
- [ ] Streaming speech-to-speech for even lower latency
- [x] Cross-platform: Linux, macOS and Windows
- [x] Automated tests, CI and quality/latency benchmarks on real speech
- [ ] Packaging `.deb` / `.dmg` / `.msi`
- [ ] LAN server mode for presentations and conferences

---

<div align="center">

**One message. Every language.**

</div>
