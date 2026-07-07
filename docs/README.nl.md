# ✦ Praxis

> **Één bericht. Elke taal.**

<div align="center">

[🇧🇷 Português](../README.md) · [🇺🇸 English](README.en.md) · [🇪🇸 Español](README.es.md) · [🇫🇷 Français](README.fr.md) · [🇩🇪 Deutsch](README.de.md) · [🇮🇹 Italiano](README.it.md) · [🇷🇺 Русский](README.ru.md) · [🇨🇳 中文](README.zh.md) · **[🇳🇱 Nederlands](README.nl.md)** · [🇵🇱 Polski](README.pl.md) · [🇺🇦 Українська](README.uk.md) · [🇹🇷 Türkçe](README.tr.md) · [🇸🇦 العربية](README.ar.md) · [🇮🇳 हिन्दी](README.hi.md)

[![Linux](https://img.shields.io/badge/Linux-PulseAudio%2FPipeWire-informational?logo=linux)](https://github.com/disouz4-dev/praxis)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://github.com/disouz4-dev/praxis)
[![License](https://img.shields.io/badge/Licentie-MIT-green)](LICENSE)
[![Offline](https://img.shields.io/badge/100%25-offline-success)](https://github.com/disouz4-dev/praxis)

</div>

---

Communicatie is altijd het krachtigste instrument van de mensheid geweest. Toch blijft taal een van de grootste barrières tussen mensen, culturen en ideeën.

**Praxis** is gebouwd om dat te veranderen.

Het idee is eenvoudig: twee mensen laten een natuurlijk gesprek voeren, elk in hun eigen taal, terwijl de ander alles in zijn moedertaal hoort — in realtime.

---

## Visie

Een realtime spraakvertaalplatform bouwen dat natuurlijke gesprekken mogelijk maakt tussen mensen overal ter wereld, met behoud van context, emotie en vloeiendheid.

## Missie

Taalbarrières elimineren zodat ideeën, kennis en relaties grenzen kunnen overschrijden zonder dat taal een obstakel is.

## Principes

- Technologie moet mensen nader tot elkaar brengen.
- Elke stem verdient gehoord te worden.
- Taal mag verbindingen niet beperken.
- Vertaling moet zo natuurlijk zijn dat het uit het gesprek verdwijnt.
- Een bericht kan iedereen bereiken, in elke taal.

---

## Hoe het werkt

Praxis maakt een **virtuele microfoon** in het besturingssysteem. U spreekt in uw taal; de stem klinkt al vertaald — klaar om te selecteren in Discord, WhatsApp, Google Meet, OBS of elke andere app.

```
Echte microfoon  →  VAD  →  Whisper ASR  →  Argos Translate  →  Piper TTS
                                                                       ↓
                                                        Virtuele sink (Praxis_Out)
                                                                       ↓
                                                 Praxis_Microfone  ←  Discord / Meet / OBS
```

Alles draait **100% lokaal** — geen internet, geen cloud, niets verlaat uw machine.

---

## Activeringsmodi

| Modus | Beschrijving |
|-------|-------------|
| **Auto VAD** | Silero VAD detecteert wanneer u spreekt en activeert automatisch |
| **Gate drempel** | Activeert alleen boven een volumedrempel |
| **Push-to-Talk** | Houd een knop ingedrukt (toetsenbord of muis) om te zenden |

---

## Ondersteunde talen

### Uitvoertaal (met beschikbare Piper-stem)

| Taal | Code | Beschikbare stemmen |
|------|------|---------------------|
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

### Invoertaal (herkend door Whisper)

Português · English · Español · Français · Deutsch · Italiano · 日本語 · 中文 · 한국어 · Русский · العربية · हिन्दी · Nederlands · Polski · Українська · Türkçe — en tientallen andere talen die Whisper ondersteunt.

> Vertaling tussen twee niet-Engelse talen gebruikt **automatische Engelse pivot** (bijv. pt→it gaat via pt→en→it).

---

## Installatie

```bash
git clone https://github.com/disouz4-dev/praxis.git
cd praxis
chmod +x install.sh && ./install.sh
```

Het installatieprogramma maakt een geïsoleerde virtuele omgeving, installeert alle afhankelijkheden (PyTorch, Whisper, Argos, Piper) en maakt het commando `praxis` globaal beschikbaar.

### Vereisten

- Linux met PulseAudio of PipeWire
- Python 3.10+
- `pulseaudio-utils` (`pactl`, `parec`)
- NVIDIA GPU met CUDA (aanbevolen) of CPU

---

## Gebruik

```bash
praxis
```

Selecteer in het configuratievenster:
1. **Activeringsmodus** (VAD / Gate / PTT)
2. **Invoermicrofoon**
3. **Bron- en doeltaal**
4. **Uitvoerstem** (download extra stemmen met de ⬇ Downloaden knop)
5. Klik op **✦ Starten**

Selecteer in uw belapp **Praxis_Microfone** als audio-invoerapparaat.

---

## Technische pipeline

| Fase | Tool | Details |
|------|------|---------|
| Spraaksegmentatie | **Silero VAD** | Knipt op stilte (200ms) of maximale duur (4s) |
| Transcriptie | **faster-whisper** | `small` model standaard; GPU int8_float16 / CPU int8 |
| Vertaling | **Argos Translate** | 100% offline; downloadt taalparen bij eerste gebruik |
| Spraaksynthese | **Piper TTS** | Lichte `.onnx` modellen; parallelle synthese per zin |
| Audio-uitvoer | **pacat + PulseAudio** | Directe injectie in virtuele sink |

---

## Stem klonen (OmniVoice)

Het tabblad **"Mijn stem klonen"** laat u elke stem in seconden klonen — neem gewoon een audioclip van 5–15 seconden op of importeer er een. Geen training, geen wachten.

### Hoe te gebruiken

1. Open het tabblad **🎙 Mijn stem klonen**
2. Voer een naam in voor het profiel (bijv. `Diego`)
3. **Optie A — Opnemen:** klik op de microfoon en lees een korte algemene tekst voor
   **Optie B — Importeren:** klik op "Audio importeren" en selecteer een WAV/MP3/OGG/OPUS/M4A/FLAC/AAC-bestand (inclusief WhatsApp-spraakmemo's)
4. Klik op **Testen** om de gekloonde stem te horen
5. Klik op **Gebruiken** om het te activeren als standaarduitvoer

> Referentieaudio wordt automatisch bijgesneden tot 15 seconden voor de beste kloonkwaliteit.

---

## Roadmap

- [x] Zero-shot stemklonen met OmniVoice (geen training vereist)
- [x] Externe audio importeren (WAV/MP3/OGG/OPUS/M4A en meer)
- [ ] Volledige bidirectionele vertaling (de ander ook vertaald horen)
- [ ] Systeemvak-pictogram en globale sneltoets om te pauzeren/hervatten
- [ ] Streaming spraak-naar-spraak voor nog lagere latentie
- [ ] `.deb` / `.desktop` packaging
- [ ] LAN-servermodus voor presentaties en conferenties

---

<div align="center">

**Één bericht. Elke taal.**

</div>
