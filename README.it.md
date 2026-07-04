# ✦ Praxis

> **Un messaggio. Tutte le lingue.**

<div align="center">

[🇧🇷 Português](README.md) · [🇺🇸 English](README.en.md) · [🇪🇸 Español](README.es.md) · [🇫🇷 Français](README.fr.md) · [🇩🇪 Deutsch](README.de.md) · **[🇮🇹 Italiano](README.it.md)**

[![Linux](https://img.shields.io/badge/Linux-PulseAudio%2FPipeWire-informational?logo=linux)](https://github.com/disouz4-dev/praxis)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://github.com/disouz4-dev/praxis)
[![License](https://img.shields.io/badge/Licenza-MIT-green)](LICENSE)
[![Offline](https://img.shields.io/badge/100%25-offline-success)](https://github.com/disouz4-dev/praxis)

</div>

---

La comunicazione è sempre stata lo strumento più potente dell'umanità. Eppure la lingua rimane una delle maggiori barriere tra persone, culture e idee.

**Praxis** è nato per cambiare questo.

La proposta è semplice: permettere a due persone di conversare naturalmente, ciascuna parlando la propria lingua, mentre l'altra ascolta la conversazione nella propria lingua madre, in tempo reale.

Immagina un brasiliano che parla in portoghese mentre un americano lo sente in inglese. Poco dopo, l'americano risponde in inglese e il brasiliano sente la risposta in portoghese. Senza pause per la traduzione. Senza bisogno di imparare un'altra lingua. Solo una conversazione.

Più di un traduttore vocale, **Praxis** mira a rendere la tecnologia invisibile, permettendo alla comunicazione di avvenire come dovrebbe essere: spontanea, umana e accessibile.

Il nome **Praxis** rappresenta l'azione — l'idea di mettere in pratica ciò che avvicina le persone. L'ispirazione dietro al progetto evoca anche la narrativa degli Atti 2, dove uomini e donne di diverse nazioni udirono lo stesso messaggio nella propria lingua. Indipendentemente dalle credenze di ciascuno, quell'immagine simboleggia qualcosa di universale: quando il linguaggio smette di essere una barriera, la comprensione diventa possibile.

---

## Visione

Costruire una piattaforma di traduzione vocale in tempo reale che consenta conversazioni naturali tra persone di tutto il mondo, preservando contesto, emozione e fluidità.

## Missione

Eliminare le barriere linguistiche affinché idee, conoscenza e relazioni possano attraversare i confini senza che la lingua sia un ostacolo.

## Principi

- La tecnologia deve avvicinare le persone.
- Ogni voce merita di essere compresa.
- La lingua non deve limitare le connessioni.
- La traduzione deve essere così naturale da sparire dalla conversazione.
- Un messaggio può raggiungere chiunque, in qualsiasi lingua.

---

## Come funziona

Praxis crea un **microfono virtuale** nel sistema operativo. Parli nella tua lingua; la voce esce già tradotta — pronta per essere selezionata in Discord, WhatsApp, Google Meet, OBS o qualsiasi altra app.

```
Microfono reale  →  VAD  →  Whisper ASR  →  Argos Translate  →  Piper TTS
                                                                       ↓
                                                          Sink virtuale (Praxis_Out)
                                                                       ↓
                                                      Praxis_Microfone  ←  Discord / Meet / OBS
```

Tutto funziona **100% localmente** — nessuna internet, nessun cloud, nulla lascia il tuo computer.

---

## Modalità di attivazione

| Modalità | Descrizione |
|----------|-------------|
| **VAD automatico** | Silero VAD rileva quando stai parlando e si apre automaticamente |
| **Gate threshold** | Si attiva solo sopra una soglia di volume — trascina la barra sotto il misuratore |
| **Push-to-Talk** | Tieni premuto un pulsante (tastiera o mouse) per trasmettere |

---

## Lingue supportate

| Lingua | Codice | Voci Piper disponibili |
|--------|--------|------------------------|
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

> La traduzione tra due lingue non inglesi usa un **pivot automatico via inglese** (es: pt→it passa per pt→en→it).

---

## Installazione

```bash
git clone https://github.com/disouz4-dev/praxis.git
cd praxis
chmod +x install.sh && ./install.sh
```

### Requisiti

- Linux con PulseAudio o PipeWire
- Python 3.10+
- `pulseaudio-utils` (`pactl`, `parec`)
- GPU NVIDIA con CUDA (consigliato) o CPU

---

## Utilizzo

```bash
praxis
```

Nella finestra di configurazione, seleziona la modalità di attivazione, il microfono, le lingue di origine e destinazione, poi clicca su **✦ Avvia**. Nell'app di chiamata, seleziona **Praxis_Microfone** come dispositivo di input audio.

---

<div align="center">

**Un messaggio. Tutte le lingue.**

</div>
