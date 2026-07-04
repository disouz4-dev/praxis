# ✦ Praxis

> **Eine Nachricht. Alle Sprachen.**

<div align="center">

[🇧🇷 Português](README.md) · [🇺🇸 English](README.en.md) · [🇪🇸 Español](README.es.md) · [🇫🇷 Français](README.fr.md) · **[🇩🇪 Deutsch](README.de.md)** · [🇮🇹 Italiano](README.it.md)

[![Linux](https://img.shields.io/badge/Linux-PulseAudio%2FPipeWire-informational?logo=linux)](https://github.com/disouz4-dev/praxis)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://github.com/disouz4-dev/praxis)
[![License](https://img.shields.io/badge/Lizenz-MIT-green)](LICENSE)
[![Offline](https://img.shields.io/badge/100%25-offline-success)](https://github.com/disouz4-dev/praxis)

</div>

---

Kommunikation war schon immer das mächtigste Werkzeug der Menschheit. Dennoch bleibt die Sprache eine der größten Barrieren zwischen Menschen, Kulturen und Ideen.

**Praxis** wurde entwickelt, um das zu ändern.

Die Idee ist einfach: Zwei Menschen sollen natürlich miteinander sprechen können, jeder in seiner eigenen Sprache, während der andere das Gespräch in seiner Muttersprache hört — in Echtzeit.

Stellen Sie sich einen Brasilianer vor, der auf Portugiesisch spricht, während ein Amerikaner ihn auf Englisch hört. Kurz darauf antwortet der Amerikaner auf Englisch, und der Brasilianer hört die Antwort auf Portugiesisch. Keine Übersetzungspausen. Keine Notwendigkeit, eine andere Sprache zu lernen. Einfach ein Gespräch.

Mehr als ein Sprachübersetzer strebt **Praxis** danach, die Technologie unsichtbar zu machen und Kommunikation so zu ermöglichen, wie sie sein sollte: spontan, menschlich und zugänglich.

Der Name **Praxis** steht für Handlung — die Idee, das in die Praxis umzusetzen, was Menschen einander näherbringt. Die Inspiration hinter dem Projekt erinnert auch an die Erzählung der Apostelgeschichte 2, wo Männer und Frauen aus verschiedenen Nationen dieselbe Botschaft in ihren eigenen Sprachen hörten. Unabhängig von den Überzeugungen jedes Einzelnen symbolisiert dieses Bild etwas Universelles: Wenn Sprache aufhört, eine Barriere zu sein, wird Verständigung möglich.

---

## Vision

Eine Echtzeit-Sprachübersetzungsplattform aufbauen, die natürliche Gespräche zwischen Menschen aus aller Welt ermöglicht und dabei Kontext, Emotion und Fluss bewahrt.

## Mission

Sprachbarrieren beseitigen, damit Ideen, Wissen und Beziehungen Grenzen überschreiten können, ohne dass die Sprache ein Hindernis darstellt.

## Grundsätze

- Technologie soll Menschen einander näherbringen.
- Jede Stimme verdient es, verstanden zu werden.
- Sprache soll Verbindungen nicht einschränken.
- Übersetzung soll so natürlich sein, dass sie im Gespräch verschwindet.
- Eine Botschaft kann jeden Menschen in jeder Sprache erreichen.

---

## Wie es funktioniert

Praxis erstellt ein **virtuelles Mikrofon** im Betriebssystem. Sie sprechen in Ihrer Sprache; die Stimme kommt bereits übersetzt heraus — bereit zur Auswahl in Discord, WhatsApp, Google Meet, OBS oder jeder anderen App.

```
Echtes Mikrofon  →  VAD  →  Whisper ASR  →  Argos Translate  →  Piper TTS
                                                                       ↓
                                                         Virtueller Sink (Praxis_Out)
                                                                       ↓
                                                     Praxis_Microfone  ←  Discord / Meet / OBS
```

Alles läuft **100% lokal** — kein Internet, keine Cloud, nichts verlässt Ihren Rechner.

---

## Aktivierungsmodi

| Modus | Beschreibung |
|-------|-------------|
| **Automatischer VAD** | Silero VAD erkennt, wann Sie sprechen, und öffnet automatisch |
| **Gate-Schwellenwert** | Aktiviert sich nur oberhalb eines Lautstärkeschwellenwerts — Leiste unter dem Pegelmesser verschieben |
| **Push-to-Talk** | Taste gedrückt halten (Tastatur oder Maus), um zu senden |

---

## Unterstützte Sprachen

| Sprache | Code | Verfügbare Piper-Stimmen |
|---------|------|--------------------------|
| Português | `pt` | pt_BR · pt_PT |
| English | `en` | en_US · en_GB |
| Español | `es` | es_ES · es_MX |
| Français | `fr` | fr_FR |
| Deutsch | `de` | de_DE |
| Italiano | `it` | it_IT |
| 日本語 | `ja` | ja_JP |
| 中文 | `zh` | zh_CN |
| 한국어 | `ko` | ko_KR |
| Русский | `ru` | ru_RU |

> Übersetzungen zwischen zwei Nicht-Englisch-Sprachen verwenden **automatisches Englisch-Pivot** (z.B. pt→it geht über pt→en→it).

---

## Installation

```bash
git clone https://github.com/disouz4-dev/praxis.git
cd praxis
chmod +x install.sh && ./install.sh
```

### Voraussetzungen

- Linux mit PulseAudio oder PipeWire
- Python 3.10+
- `pulseaudio-utils` (`pactl`, `parec`)
- NVIDIA-GPU mit CUDA (empfohlen) oder CPU

---

## Verwendung

```bash
praxis
```

Wählen Sie im Konfigurationsfenster den Aktivierungsmodus, das Mikrofon, Quell- und Zielsprache, dann klicken Sie auf **✦ Starten**. Wählen Sie in Ihrer Anruf-App **Praxis_Microfone** als Audioeingabegerät.

---

<div align="center">

**Eine Nachricht. Alle Sprachen.**

</div>
