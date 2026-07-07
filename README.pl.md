# ✦ Praxis

> **Jedna wiadomość. Każdy język.**

<div align="center">

[🇧🇷 Português](README.md) · [🇺🇸 English](README.en.md) · [🇪🇸 Español](README.es.md) · [🇫🇷 Français](README.fr.md) · [🇩🇪 Deutsch](README.de.md) · [🇮🇹 Italiano](README.it.md) · [🇷🇺 Русский](README.ru.md) · [🇨🇳 中文](README.zh.md) · [🇳🇱 Nederlands](README.nl.md) · **[🇵🇱 Polski](README.pl.md)** · [🇺🇦 Українська](README.uk.md) · [🇹🇷 Türkçe](README.tr.md) · [🇸🇦 العربية](README.ar.md) · [🇮🇳 हिन्दी](README.hi.md)

[![Linux](https://img.shields.io/badge/Linux-PulseAudio%2FPipeWire-informational?logo=linux)](https://github.com/disouz4-dev/praxis)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://github.com/disouz4-dev/praxis)
[![License](https://img.shields.io/badge/Licencja-MIT-green)](LICENSE)
[![Offline](https://img.shields.io/badge/100%25-offline-success)](https://github.com/disouz4-dev/praxis)

</div>

---

Komunikacja zawsze była najpotężniejszym narzędziem ludzkości. Jednak język nadal pozostaje jedną z największych barier między ludźmi, kulturami i ideami.

**Praxis** powstał, aby to zmienić.

Pomysł jest prosty: pozwolić dwóm osobom prowadzić naturalną rozmowę, każdej w swoim języku, podczas gdy druga słyszy wszystko w swoim ojczystym języku — w czasie rzeczywistym.

---

## Wizja

Zbudowanie platformy do tłumaczenia głosu w czasie rzeczywistym, umożliwiającej naturalne rozmowy między ludźmi na całym świecie, z zachowaniem kontekstu, emocji i płynności.

## Misja

Eliminacja barier językowych, aby idee, wiedza i relacje mogły przekraczać granice bez językowych przeszkód.

## Zasady

- Technologia powinna zbliżać ludzi.
- Każdy głos zasługuje na zrozumienie.
- Język nie powinien ograniczać połączeń.
- Tłumaczenie powinno być tak naturalne, że znika z rozmowy.
- Wiadomość może dotrzeć do każdego w każdym języku.

---

## Jak to działa

Praxis tworzy **wirtualny mikrofon** w systemie operacyjnym. Mówisz w swoim języku; głos wychodzi już przetłumaczony — gotowy do wybrania w Discord, WhatsApp, Google Meet, OBS lub dowolnej innej aplikacji.

```
Prawdziwy mikrofon  →  VAD  →  Whisper ASR  →  Argos Translate  →  Piper TTS
                                                                          ↓
                                                          Wirtualny sink (Praxis_Out)
                                                                          ↓
                                                    Praxis_Microfone  ←  Discord / Meet / OBS
```

Wszystko działa **100% lokalnie** — bez internetu, bez chmury, nic nie opuszcza Twojego komputera.

---

## Tryby aktywacji

| Tryb | Opis |
|------|------|
| **Auto VAD** | Silero VAD wykrywa mówienie i automatycznie aktywuje |
| **Próg Gate** | Aktywuje tylko powyżej progu głośności |
| **Push-to-Talk** | Przytrzymaj przycisk (klawiatura lub mysz) aby nadawać |

---

## Obsługiwane języki

### Język wyjściowy (z dostępnym głosem Piper)

| Język | Kod | Dostępne głosy |
|-------|-----|---------------|
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

### Język wejściowy (rozpoznawany przez Whisper)

Português · English · Español · Français · Deutsch · Italiano · 日本語 · 中文 · 한국어 · Русский · العربية · हिन्दी · Nederlands · Polski · Українська · Türkçe — i dziesiątki innych języków obsługiwanych przez Whisper.

> Tłumaczenie między dwoma językami nieangielskimi używa **automatycznego angielskiego pivot** (np. pt→it idzie przez pt→en→it).

---

## Instalacja

```bash
git clone https://github.com/disouz4-dev/praxis.git
cd praxis
chmod +x install.sh && ./install.sh
```

Instalator tworzy izolowane środowisko wirtualne, instaluje wszystkie zależności (PyTorch, Whisper, Argos, Piper) i udostępnia polecenie `praxis` globalnie.

### Wymagania

- Linux z PulseAudio lub PipeWire
- Python 3.10+
- `pulseaudio-utils` (`pactl`, `parec`)
- GPU NVIDIA z CUDA (zalecane) lub CPU

---

## Użycie

```bash
praxis
```

W oknie konfiguracji wybierz:
1. **Tryb** aktywacji (VAD / Gate / PTT)
2. **Mikrofon** wejściowy
3. **Język** źródłowy i docelowy
4. **Głos** wyjściowy (pobierz dodatkowe głosy przyciskiem ⬇ Pobierz)
5. Kliknij **✦ Uruchom**

W aplikacji do połączeń wybierz **Praxis_Microfone** jako urządzenie wejścia audio.

---

## Potok techniczny

| Etap | Narzędzie | Szczegóły |
|------|-----------|-----------|
| Segmentacja mowy | **Silero VAD** | Cięcie na ciszy (200ms) lub maks. czasie (4s) |
| Transkrypcja | **faster-whisper** | Domyślny model `small`; GPU int8_float16 / CPU int8 |
| Tłumaczenie | **Argos Translate** | 100% offline; pobiera pary językowe przy pierwszym użyciu |
| Synteza mowy | **Piper TTS** | Lekkie modele `.onnx`; równoległa synteza per zdanie |
| Wyjście audio | **pacat + PulseAudio** | Bezpośrednia iniekcja do wirtualnego sink |

---

## Klonowanie głosu (OmniVoice)

Zakładka **"Sklonuj mój głos"** pozwala sklonować dowolny głos w sekundy — wystarczy nagrać lub zaimportować klip audio 5–15 sekund. Bez treningu, bez czekania.

### Jak używać

1. Otwórz zakładkę **🎙 Sklonuj mój głos**
2. Wpisz nazwę profilu (np. `Diego`)
3. **Opcja A — Nagraj:** kliknij mikrofon i przeczytaj krótki ogólny tekst
   **Opcja B — Importuj:** kliknij "Importuj audio" i wybierz dowolny plik WAV/MP3/OGG/OPUS/M4A/FLAC/AAC (w tym wiadomości głosowe WhatsApp)
4. Kliknij **Test** aby usłyszeć sklonowany głos
5. Kliknij **Użyj** aby aktywować go jako domyślne wyjście

> Referencyjne audio jest automatycznie przycinane do 15 sekund dla najlepszej jakości klonowania.

---

## Mapa drogowa

- [x] Klonowanie głosu zero-shot z OmniVoice (bez treningu)
- [x] Import zewnętrznego audio (WAV/MP3/OGG/OPUS/M4A i więcej)
- [ ] Pełne tłumaczenie dwukierunkowe (słyszenie rozmówcy przetłumaczonego)
- [ ] Ikona zasobnika i globalny skrót do wstrzymania/wznowienia
- [ ] Strumieniowe mowa-na-mowę dla jeszcze niższego opóźnienia
- [ ] Pakowanie `.deb` / `.desktop`
- [ ] Tryb serwera LAN dla prezentacji i konferencji

---

<div align="center">

**Jedna wiadomość. Każdy język.**

</div>
