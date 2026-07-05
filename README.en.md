# ✦ Praxis

> **One message. Every language.**

<div align="center">

[🇧🇷 Português](README.md) · **[🇺🇸 English](README.en.md)** · [🇪🇸 Español](README.es.md) · [🇫🇷 Français](README.fr.md) · [🇩🇪 Deutsch](README.de.md) · [🇮🇹 Italiano](README.it.md)

[![Linux](https://img.shields.io/badge/Linux-PulseAudio%2FPipeWire-informational?logo=linux)](https://github.com/disouz4-dev/praxis)
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

The name **Praxis** means action — the act of putting into practice what brings people together. The inspiration behind the project also echoes the story of Acts 2, where men and women from different nations heard the same message in their own languages. Regardless of anyone's beliefs, that image stands for something universal: when language stops being a barrier, understanding becomes possible.

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

```bash
git clone https://github.com/disouz4-dev/praxis.git
cd praxis
chmod +x install.sh && ./install.sh
```

The installer creates an isolated virtual environment, installs all dependencies (PyTorch, Whisper, Argos, Piper), and makes the `praxis` command globally available.

### Requirements

- Linux with PulseAudio or PipeWire
- Python 3.10+
- `pulseaudio-utils` (`pactl`, `parec`)
- NVIDIA GPU with CUDA (recommended) or CPU

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

In your call app, select **Praxis_Microfone** as the audio input device.

---

## Technical pipeline

| Stage | Tool | Details |
|-------|------|---------|
| Speech segmentation | **Silero VAD** | Cut on silence (200ms) or max duration (4s) |
| Transcription | **faster-whisper** | `small` model by default; GPU int8_float16 / CPU int8 |
| Translation | **Argos Translate** | 100% offline; downloads language pairs on first use |
| Voice synthesis | **Piper TTS** | Lightweight `.onnx` models; per-sentence parallel synthesis |
| Audio output | **pacat + PulseAudio** | Direct injection into virtual sink |

---

---

## Voice Cloning (RVC)

The **"Clone my voice"** tab lets you train an RVC model with your own voice — no external tools needed. The entire pipeline runs inside Praxis.

### How to use

1. Open the **🎙 Clone my voice** tab
2. Enter a name for the profile (e.g. `Diego`)
3. Read the reference text aloud (4 pages, ~1000 words)
   - Use **← Previous** / **Next →** buttons to navigate between pages
   - You can record in multiple short sessions — audio accumulates automatically
4. With **3 minutes or more** recorded, the **🎙 Train Voice** button is unlocked
5. Click **Train Voice** — the pipeline runs in 3 phases:
   - **Phase 1** — Audio preprocessing (cut into 3s chunks)
   - **Phase 2** — Feature extraction (HuBERT + RMVPE for F0)
   - **Phase 3** — Model training (300 epochs, HiFi-GAN vocoder)
6. After training (~10-30 min with GPU), click **Test** to hear the result
7. Click **Use** to activate the cloned voice as the default output

### Technology

- **RVC** (Retrieval-based Voice Conversion)
- **Applio** — training scripts used internally (no need to open the web UI)
- **edge-tts** — intermediate TTS for synthesis before conversion
- Model saved in `voices/clones/` as `.pth` (weights) + `.json` (metadata)

> Training audio accumulates automatically: you can record in multiple sessions and the total grows until it reaches the 3-minute minimum.

---

## Roadmap

- [x] Voice cloning with RVC (native training and inference in Praxis)
- [ ] Full bidirectional translation (hear the other person translated too)
- [ ] Tray icon and global hotkey to pause/resume
- [ ] Streaming speech-to-speech for even lower latency
- [ ] `.deb` / `.desktop` packaging
- [ ] LAN server mode for presentations and conferences

---

<div align="center">

**One message. Every language.**

</div>
