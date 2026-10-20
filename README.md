# ✦ Praxis

> **Uma mensagem. Todas as línguas.**

<div align="center">

**[🇧🇷 Português](README.md)** · [🇺🇸 English](docs/README.en.md) · [🇪🇸 Español](docs/README.es.md) · [🇫🇷 Français](docs/README.fr.md) · [🇩🇪 Deutsch](docs/README.de.md) · [🇮🇹 Italiano](docs/README.it.md) · [🇷🇺 Русский](docs/README.ru.md) · [🇨🇳 中文](docs/README.zh.md) · [🇳🇱 Nederlands](docs/README.nl.md) · [🇵🇱 Polski](docs/README.pl.md) · [🇺🇦 Українська](docs/README.uk.md) · [🇹🇷 Türkçe](docs/README.tr.md) · [🇸🇦 العربية](docs/README.ar.md) · [🇮🇳 हिन्दी](docs/README.hi.md)

[![Linux](https://img.shields.io/badge/Linux-PulseAudio%2FPipeWire-informational?logo=linux)](https://github.com/disouz4-dev/praxis)
[![macOS](https://img.shields.io/badge/macOS-BlackHole-informational?logo=apple)](https://github.com/disouz4-dev/praxis)
[![Windows](https://img.shields.io/badge/Windows-VB--Cable-informational?logo=windows)](https://github.com/disouz4-dev/praxis)
[![CI](https://github.com/disouz4-dev/praxis/actions/workflows/ci.yml/badge.svg)](https://github.com/disouz4-dev/praxis/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://github.com/disouz4-dev/praxis)
[![License](https://img.shields.io/badge/Licença-MIT-green)](LICENSE)
[![Offline](https://img.shields.io/badge/100%25-offline-success)](https://github.com/disouz4-dev/praxis)

</div>

---

A comunicação sempre foi a ferramenta mais poderosa da humanidade. Ainda assim, o idioma continua sendo uma das maiores barreiras entre pessoas, culturas e ideias.

**Praxis** nasceu para mudar isso.

A proposta é simples: permitir que duas pessoas conversem naturalmente, cada uma falando sua própria língua, enquanto a outra escuta a conversa em seu idioma nativo, em tempo real.

Imagine um brasileiro falando em português enquanto um americano o ouve em inglês. Logo em seguida, o americano responde em inglês, e o brasileiro escuta a resposta em português. Sem pausas para tradução. Sem precisar aprender outro idioma. Apenas uma conversa.

Mais do que um tradutor de voz, **Praxis** busca tornar a tecnologia invisível, permitindo que a comunicação aconteça da forma como deveria ser: espontânea, humana e acessível.

O nome **Praxis** representa a ação — a ideia de colocar em prática aquilo que aproxima pessoas.

---

## Visão

Construir uma plataforma de tradução de voz em tempo real que permita conversas naturais entre pessoas de qualquer lugar do mundo, preservando contexto, emoção e fluidez.

## Missão

Eliminar barreiras linguísticas para que ideias, conhecimento e relacionamentos possam atravessar fronteiras sem que o idioma seja um obstáculo.

## Princípios

- A tecnologia deve aproximar pessoas.
- Toda voz merece ser compreendida.
- O idioma não deve limitar conexões.
- A tradução deve ser tão natural que desapareça da conversa.
- Uma mensagem pode alcançar qualquer pessoa, em qualquer língua.

---

## Como funciona

O Praxis cria um **microfone virtual** no sistema operacional. Você fala no seu idioma; a voz sai já traduzida — pronta para ser selecionada no Discord, WhatsApp, Google Meet, OBS ou qualquer outro app.

```
Microfone real  →  VAD  →  Whisper ASR  →  Argos Translate  →  Piper TTS
                                                                      ↓
                                                          Microfone virtual
                                              Linux: Praxis_Microfone · macOS: BlackHole · Windows: VB-Cable
                                                                      ↓
                                                          Discord / Meet / Zoom / OBS
```

Tudo roda **100% local**, sem internet, sem nuvem, sem enviar nada para fora da sua máquina.

---

## Modos de ativação

| Modo | Descrição |
|------|-----------|
| **VAD automático** | O Silero VAD detecta quando você está falando e abre automaticamente |
| **Gate threshold** | Só ativa acima de um limiar de volume — configurável arrastando a barra abaixo do medidor |
| **Push-to-Talk** | Você mantém um botão pressionado (teclado ou mouse) para transmitir |

---

## Idiomas suportados

### Idioma de saída (com voz Piper disponível)

| Idioma | Código | Vozes disponíveis |
|--------|--------|-------------------|
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

### Idioma de entrada (reconhecido pelo Whisper)

Português · English · Español · Français · Deutsch · Italiano · 日本語 · 中文 · 한국어 · Русский · العربية · हिन्दी · Nederlands · Polski · Українська · Türkçe — e dezenas de outros idiomas suportados pelo Whisper.

> Tradução entre idiomas não-ingleses usa **pivot automático via inglês** (ex: pt→it vai pt→en→it).

---

## Instalação

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

O instalador cria um ambiente virtual isolado, instala as dependências (Whisper, Argos, Piper — **sem PyTorch**), baixa uma voz padrão e cria o atalho do app com ícone (menu de aplicativos no Linux, `~/Applications/Praxis.app` no macOS, Menu Iniciar no Windows). Clonagem de voz (OmniVoice, requer PyTorch) é opcional: `PRAXIS_WITH_CLONE=1 ./install.sh`.

### Requisitos

| | Linux | macOS | Windows |
|---|---|---|---|
| Python | 3.10+ | 3.10+ (Homebrew) | 3.10+ (python.org) |
| Microfone virtual | criado automaticamente (PulseAudio/PipeWire) | [BlackHole 2ch](https://existential.audio/blackhole/) — instalado pelo `install.sh` | [VB-Audio Virtual Cable](https://vb-audio.com/Cable/) |
| Modo bilateral | automático | + BlackHole 16ch | + VB-Cable A+B |
| GPU (automático) | NVIDIA CUDA · AMD/Intel via Vulkan¹ | Apple Silicon via MLX · Intel: CPU² | NVIDIA CUDA · AMD/Intel via Vulkan¹ |

¹ opt-in: `PRAXIS_GPU=vulkan ./install.sh` (compila o whisper.cpp; requer Vulkan SDK). ² Medido: em Macs Intel+AMD o whisper.cpp/Metal transcreve errado e é mais lento que a CPU. A clonagem (OmniVoice) usa CUDA ou MPS. Force um backend com `--device cpu|cuda|mlx|whispercpp` ou `PRAXIS_DEVICE`.

Diagnóstico rápido: `python praxis.py --check` (dependências + áudio) e `python praxis.py --list-devices`.

---

## Uso

```bash
praxis
```

Na janela de configuração, selecione:
1. **Modo** de ativação (VAD / Gate / PTT)
2. **Microfone** de entrada
3. **Idioma** de origem e destino
4. **Voz** de saída (baixe vozes adicionais com o botão ⬇ Baixar)
5. Clique em **✦ Iniciar**

No app de chamada, selecione o microfone virtual: **Praxis_Microfone** (Linux), **BlackHole 2ch** (macOS) ou **CABLE Output** (Windows).

---

## Pipeline técnico

| Etapa | Ferramenta | Detalhes |
|-------|-----------|----------|
| Segmentação de fala | **Silero VAD (ONNX)** | Corte por silêncio (200 ms) ou no ponto mais silencioso após 6s; 250 ms de pre-roll |
| Transcrição | **faster-whisper** | Modelo `small` padrão; GPU int8_float16 / CPU int8; filtro de alucinações repetidas |
| Tradução | **Argos Translate** (CTranslate2) | 100% offline; pivot via inglês; baixa pares no primeiro uso |
| Síntese de voz | **Piper TTS** | Modelos `.onnx` leves; síntese por sentença em paralelo |
| Saída de áudio | **PulseAudio** (Linux) · **PortAudio** (macOS/Windows) | Injeção no microfone virtual |

---

## Testes e qualidade

```bash
pip install -r requirements-dev.txt && pip install --no-deps argostranslate
pytest                                   # unidade + smoke + GUI (rápido, sem modelos)
python benchmarks/fetch_speech_corpus.py # áudios reais (LibriSpeech/MLS, CC BY 4.0)
pytest -m slow                           # qualidade da transcrição (WER) + latência
python benchmarks/run_benchmarks.py asr --models small --langs pt en es
python benchmarks/run_benchmarks.py latency --model small
```

O CI roda em Linux, macOS e Windows a cada push. Resultados e relatório de QA: [`benchmarks/results/`](benchmarks/results/) · [`docs/QA_REPORT.md`](docs/QA_REPORT.md).

---

## Clonagem de voz (OmniVoice)

A aba **"Clonar minha voz"** permite clonar qualquer voz em segundos — basta gravar ou importar um áudio de 5 a 15 segundos. Sem treino, sem espera.

### Como usar

1. Abra a aba **🎙 Clonar minha voz**
2. Digite um nome para o perfil (ex: `Diego`)
3. **Opção A — Gravar:** clique no botão de microfone e leia um texto genérico curto
   **Opção B — Importar:** clique em "Importar áudio" e selecione qualquer WAV/MP3/OGG/OPUS/M4A/FLAC/AAC (incluindo áudios do WhatsApp)
4. Clique em **Testar** para ouvir o resultado
5. Clique em **Usar** para ativar a voz clonada como saída padrão

### Tecnologia

- **OmniVoice** (k2-fsa/OmniVoice) — clonagem zero-shot, sem necessidade de treino
- **faster-whisper** — transcrição automática do áudio de referência
- **ffmpeg** — conversão interna de formatos (qualquer formato → WAV 24 kHz)
- Clone salvo em `voices/clones/` como `.wav` (referência) + `.json` (metadados)

> O áudio de referência é cortado automaticamente para 15 segundos para melhor qualidade de clonagem.

---

## Roadmap

- [x] Clonagem de voz zero-shot com OmniVoice (sem treino)
- [x] Importação de áudio externo (WAV/MP3/OGG/OPUS/M4A e mais)
- [ ] Tradução bidirecional completa (ouvir o interlocutor traduzido)
- [ ] Tray icon e atalho global para pausar/retomar
- [ ] Streaming speech-to-speech para latência menor ainda
- [x] Multiplataforma: Linux, macOS e Windows
- [x] Testes automatizados, CI e benchmarks de qualidade/latência com fala real
- [ ] Empacotamento `.deb` / `.dmg` / `.msi`
- [ ] Modo servidor LAN para apresentações e conferências

---

<div align="center">

**Uma mensagem. Todas as línguas.**

</div>
