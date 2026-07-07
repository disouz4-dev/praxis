# ✦ Praxis

> **Un message. Toutes les langues.**

<div align="center">

[🇧🇷 Português](README.md) · [🇺🇸 English](README.en.md) · [🇪🇸 Español](README.es.md) · **[🇫🇷 Français](README.fr.md)** · [🇩🇪 Deutsch](README.de.md) · [🇮🇹 Italiano](README.it.md) · [🇷🇺 Русский](README.ru.md) · [🇨🇳 中文](README.zh.md) · [🇳🇱 Nederlands](README.nl.md) · [🇵🇱 Polski](README.pl.md) · [🇺🇦 Українська](README.uk.md) · [🇹🇷 Türkçe](README.tr.md) · [🇸🇦 العربية](README.ar.md) · [🇮🇳 हिन्दी](README.hi.md)

[![Linux](https://img.shields.io/badge/Linux-PulseAudio%2FPipeWire-informational?logo=linux)](https://github.com/disouz4-dev/praxis)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://github.com/disouz4-dev/praxis)
[![License](https://img.shields.io/badge/Licence-MIT-green)](LICENSE)
[![Offline](https://img.shields.io/badge/100%25-hors%20ligne-success)](https://github.com/disouz4-dev/praxis)

</div>

---

La communication a toujours été l'outil le plus puissant de l'humanité. Pourtant, la langue reste l'une des plus grandes barrières entre les personnes, les cultures et les idées.

**Praxis** est né pour changer cela.

La proposition est simple : permettre à deux personnes de converser naturellement, chacune parlant sa propre langue, pendant que l'autre entend la conversation dans sa langue maternelle, en temps réel.

Imaginez un Brésilien parlant en portugais pendant qu'un Américain l'entend en anglais. Ensuite, l'Américain répond en anglais et le Brésilien entend la réponse en portugais. Sans pauses pour la traduction. Sans avoir besoin d'apprendre une autre langue. Juste une conversation.

Plus qu'un traducteur vocal, **Praxis** cherche à rendre la technologie invisible, permettant à la communication de se dérouler comme elle devrait être : spontanée, humaine et accessible.

Le nom **Praxis** représente l'action — l'idée de mettre en pratique ce qui rapproche les personnes. L'inspiration derrière le projet évoque également le récit des Actes 2, où des hommes et des femmes de différentes nations entendirent le même message dans leurs propres langues. Indépendamment des croyances de chacun, cette image symbolise quelque chose d'universel : quand le langage cesse d'être une barrière, la compréhension devient possible.

---

## Vision

Construire une plateforme de traduction vocale en temps réel permettant des conversations naturelles entre des personnes du monde entier, en préservant le contexte, l'émotion et la fluidité.

## Mission

Éliminer les barrières linguistiques pour que les idées, les connaissances et les relations puissent traverser les frontières sans que la langue soit un obstacle.

## Principes

- La technologie doit rapprocher les personnes.
- Toute voix mérite d'être comprise.
- La langue ne doit pas limiter les connexions.
- La traduction doit être si naturelle qu'elle disparaisse de la conversation.
- Un message peut atteindre n'importe qui, dans n'importe quelle langue.

---

## Comment ça fonctionne

Praxis crée un **microphone virtuel** dans le système d'exploitation. Vous parlez dans votre langue ; la voix sort déjà traduite — prête à être sélectionnée dans Discord, WhatsApp, Google Meet, OBS ou toute autre application.

```
Microphone réel  →  VAD  →  Whisper ASR  →  Argos Translate  →  Piper TTS
                                                                       ↓
                                                           Sink virtuel (Praxis_Out)
                                                                       ↓
                                                       Praxis_Microfone  ←  Discord / Meet / OBS
```

Tout fonctionne **100% localement** — sans internet, sans cloud, rien ne quitte votre machine.

---

## Modes d'activation

| Mode | Description |
|------|-------------|
| **VAD automatique** | Silero VAD détecte quand vous parlez et s'ouvre automatiquement |
| **Gate threshold** | S'active seulement au-dessus d'un seuil de volume — faites glisser la barre sous le VU-mètre |
| **Push-to-Talk** | Maintenez un bouton enfoncé (clavier ou souris) pour transmettre |

---

## Langues prises en charge

### Langue de sortie (avec voix Piper disponible)

| Langue | Code | Voix disponibles |
|--------|------|------------------|
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

### Langue d'entrée (reconnue par Whisper)

Portugais · Anglais · Espagnol · Français · Allemand · Italien · Japonais · Chinois · Coréen · Russe · Arabe · Hindi · Néerlandais · Polonais · Ukrainien · Turc — et des dizaines d'autres langues prises en charge par Whisper.

> La traduction entre deux langues non anglaises utilise un **pivot automatique via l'anglais** (ex : pt→it passe par pt→en→it).

---

## Installation

```bash
git clone https://github.com/disouz4-dev/praxis.git
cd praxis
chmod +x install.sh && ./install.sh
```

### Prérequis

- Linux avec PulseAudio ou PipeWire
- Python 3.10+
- `pulseaudio-utils` (`pactl`, `parec`)
- GPU NVIDIA avec CUDA (recommandé) ou CPU

---

## Utilisation

```bash
praxis
```

Dans la fenêtre de configuration, sélectionnez le mode d'activation, le microphone, les langues source et cible, puis cliquez sur **✦ Démarrer**. Dans votre application d'appel, choisissez **Praxis_Microfone** comme périphérique d'entrée audio.

---

## Clonage de voix (OmniVoice)

L'onglet **"Cloner ma voix"** permet de cloner n'importe quelle voix en quelques secondes — enregistrez ou importez simplement un clip audio de 5 à 15 secondes. Sans entraînement, sans attente.

### Comment utiliser

1. Ouvrez l'onglet **🎙 Cloner ma voix**
2. Saisissez un nom pour le profil (ex. `Diego`)
3. **Option A — Enregistrer :** cliquez sur le microphone et lisez un texte générique court
   **Option B — Importer :** cliquez sur "Importer audio" et sélectionnez tout WAV/MP3/OGG/OPUS/M4A/FLAC/AAC (y compris les messages vocaux WhatsApp)
4. Cliquez sur **Tester** pour écouter la voix clonée
5. Cliquez sur **Utiliser** pour l'activer comme sortie par défaut

> L'audio de référence est automatiquement coupé à 15 secondes pour une meilleure qualité de clonage.

---

<div align="center">

**Un message. Toutes les langues.**

</div>
