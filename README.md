# ✦ Praxis

> **Uma mensagem. Todas as línguas.**

<div align="center">

**[🇧🇷 Português](README.md)** · [🇺🇸 English](docs/README.en.md) · [🇪🇸 Español](docs/README.es.md) · [🇫🇷 Français](docs/README.fr.md) · [🇩🇪 Deutsch](docs/README.de.md) · [🇮🇹 Italiano](docs/README.it.md) · [🇷🇺 Русский](docs/README.ru.md) · [🇨🇳 中文](docs/README.zh.md) · [🇳🇱 Nederlands](docs/README.nl.md) · [🇵🇱 Polski](docs/README.pl.md) · [🇺🇦 Українська](docs/README.uk.md) · [🇹🇷 Türkçe](docs/README.tr.md) · [🇸🇦 العربية](docs/README.ar.md) · [🇮🇳 हिन्दी](docs/README.hi.md)

[![Linux](https://img.shields.io/badge/Linux-PulseAudio%2FPipeWire-informational?logo=linux)](https://github.com/disouz4-dev/praxis)
[![macOS](https://img.shields.io/badge/macOS-em%20breve-lightgrey?logo=apple)](https://github.com/disouz4-dev/praxis)
[![Windows](https://img.shields.io/badge/Windows-VB--Cable-informational?logo=windows)](https://github.com/disouz4-dev/praxis)
[![Motor em Rust](https://github.com/disouz4-dev/praxis/actions/workflows/rust.yml/badge.svg)](https://github.com/disouz4-dev/praxis/actions/workflows/rust.yml)
[![Rust](https://img.shields.io/badge/Rust-motor-orange?logo=rust)](app/engine)
[![Tauri](https://img.shields.io/badge/Tauri-2-24C8DB?logo=tauri)](app/desktop)
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

O Praxis faz **tradução simultânea**: enquanto você fala, a tradução já vai sendo falada para a outra pessoa, como um intérprete — sem esperar você terminar o raciocínio. A meta é que ela ouça a tradução **na sua própria voz, clonada**.

Ele cria um **microfone virtual** no sistema: você escolhe esse microfone no Discord, WhatsApp, Google Meet, Zoom, OBS ou qualquer outro app, e o que sai dele é a sua fala já traduzida. No modo **bilateral**, a voz da outra pessoa (que chega pelo app de chamada) também é traduzida para você.

```
microfone ─► detector de fala ─► reconhecimento em fluxo ─► tradução incremental ─► voz ─► microfone virtual ─► app de chamada
              (Silero)            (Whisper / Parakeet)       (NLLB, continua o        (Kokoro / Supertonic;
                                  relê a cada 0,6 s e         que já foi falado)       voz clonada em construção)
                                  confirma as palavras
```

Tudo roda **no seu computador**, sem internet depois da instalação e sem enviar nada para fora.

### Tecnologia

| Parte | O que usa |
|---|---|
| Aplicativo | **Rust** + **Tauri 2** (janela em HTML/CSS/JavaScript), leve: ~30 MB de pacote |
| Motor | Rust (`app/engine`): áudio pelo **cpal**, modelos pelo **CTranslate2** (ct2rs), **sherpa-onnx** e **onnxruntime** |
| Detector de fala | **Silero VAD v6** |
| Reconhecimento | **Whisper large-v3 / large-v3-turbo** (com placa de vídeo) e **Parakeet** da NVIDIA (ultra, v2 para inglês, japonês) — o melhor medido para cada idioma |
| Tradução | **NLLB-200** (Meta, 600M) com continuação da frase já falada; **Argos Translate** como reserva |
| Voz | **Kokoro** e **Supertonic 3**; voz clonada da própria pessoa em construção |
| Placa de vídeo | NVIDIA pelo CUDA quando existe (o motor principal); processador quando não |
| Instalação | `.deb` (Linux) e instalador `.exe` (Windows), com **atualização automática** |

A versão anterior, em Python (`praxis.py`), continua no repositório como bancada de testes e medições (`benchmarks/`).

---

## Instalação

O instalador sempre pergunta ao GitHub qual é a versão mais atual e instala essa. Depois de instalado, o Praxis **se atualiza sozinho**: as versões novas chegam pela atualização do sistema, e o próprio aplicativo avisa e atualiza com um clique.

### Linux — pacote .deb (Debian, Ubuntu e derivados)

Baixe o `praxis_<versão>_amd64.deb` da [página de versões](https://github.com/disouz4-dev/praxis/releases/latest) e abra com dois cliques, ou:

```bash
sudo apt install ./praxis_*_amd64.deb
```

Com placa de vídeo NVIDIA, a instalação baixa as bibliotecas oficiais da placa (~1,8 GB, uma vez só).

### Linux — pelo terminal

```bash
curl -fsSL https://disouz4-dev.github.io/praxis/install.sh | bash
```

### Windows — pelo PowerShell

```powershell
irm https://disouz4-dev.github.io/praxis/install.ps1 | iex
```

Instala também o microfone virtual (VB-Audio Virtual Cable). Ou baixe o `Praxis_*_x64-setup.exe` da [página de versões](https://github.com/disouz4-dev/praxis/releases/latest).


### macOS

Por enquanto, a versão anterior em Python: `scripts/instalar-python.sh`.

### Requisitos

| | Linux | Windows | macOS |
|---|---|---|---|
| Sistema | Debian, Ubuntu e derivados (64 bits) | Windows 10/11 (64 bits) | em preparação |
| Microfone virtual | criado automaticamente (PulseAudio/PipeWire) | VB-Audio Virtual Cable (instalado pelo `install.ps1`) | — |
| Placa de vídeo | NVIDIA (opcional, recomendada) | NVIDIA (opcional) | — |

---

## Uso

Abra o **Praxis** pelo menu de aplicativos, escolha os dois idiomas e clique em **Iniciar**. Na primeira vez ele baixa os modelos para os seus idiomas. No app de chamada, escolha o microfone **Praxis_Microfone** (Linux) ou **CABLE Output** (Windows).

---

## Qualidade e testes

Medido com fala real de várias pessoas (Google FLEURS), descontando diferença de escrita e de número:

| | Com placa de vídeo | Sem placa de vídeo |
|---|---:|---:|
| Português | 2,2% de palavras erradas | 2,9% |
| Inglês | 2,0% | 2,0% |
| Espanhol | 1,6% | 2,0% |
| Alemão | 2,0% | 2,7% |
| Italiano | 1,7% | 1,8% |

Detalhes: [`docs/RESUMO_TESTES.md`](docs/RESUMO_TESTES.md). Antes de cada versão roda a [lista de verificação completa](docs/QA_LISTA.md), com uma conversa bilateral de 5 minutos no equipamento real.

```bash
cd app && scripts/cargo-linux.sh test -p praxis-engine --lib    # testes do motor (Linux)
```

---

## Roadmap

- [x] Aplicativo leve em Rust + Tauri, Linux e Windows
- [x] Tradução simultânea (fala a tradução enquanto a pessoa fala)
- [x] Modo bilateral
- [x] Instalação por `.deb` / `.exe` e atualização automática
- [ ] **Voz clonada da própria pessoa** (rápida, com ~10 s de amostra; e treinada, com alguns minutos)
- [ ] macOS
- [ ] Modos "segurar uma tecla para falar" e por volume

---

<div align="center">

**Uma mensagem. Todas as línguas.**

</div>
