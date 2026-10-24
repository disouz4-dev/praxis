# ✦ Praxis

> **Uma mensagem. Todas as línguas.**

**🌐 Site: [disouz4-dev.github.io/praxis](https://disouz4-dev.github.io/praxis/)** — conheça o Praxis, veja o aplicativo funcionando e baixe.

<div align="center">

**[🇧🇷 Português](README.md)** · [🇺🇸 English](docs/README.en.md) · [🇪🇸 Español](docs/README.es.md) · [🇫🇷 Français](docs/README.fr.md) · [🇩🇪 Deutsch](docs/README.de.md) · [🇮🇹 Italiano](docs/README.it.md) · [🇷🇺 Русский](docs/README.ru.md) · [🇨🇳 中文](docs/README.zh.md) · [🇳🇱 Nederlands](docs/README.nl.md) · [🇵🇱 Polski](docs/README.pl.md) · [🇺🇦 Українська](docs/README.uk.md) · [🇹🇷 Türkçe](docs/README.tr.md) · [🇸🇦 العربية](docs/README.ar.md) · [🇮🇳 हिन्दी](docs/README.hi.md)

[![Linux](https://img.shields.io/badge/Linux-PulseAudio%2FPipeWire-informational?logo=linux)](https://github.com/disouz4-dev/praxis)
[![macOS](https://img.shields.io/badge/macOS-em%20breve-lightgrey?logo=apple)](https://github.com/disouz4-dev/praxis)
[![Windows](https://img.shields.io/badge/Windows-VB--Cable-informational?logo=windows)](https://github.com/disouz4-dev/praxis)
[![Motor em Rust](https://github.com/disouz4-dev/praxis/actions/workflows/rust.yml/badge.svg)](https://github.com/disouz4-dev/praxis/actions/workflows/rust.yml)
[![Rust](https://img.shields.io/badge/Rust-motor-orange?logo=rust)](app/engine)
[![Tauri](https://img.shields.io/badge/Tauri-2-24C8DB?logo=tauri)](app/desktop)
[![Site](https://img.shields.io/badge/Site-disouz4--dev.github.io%2Fpraxis-6ea8ff)](https://disouz4-dev.github.io/praxis/)
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

O Praxis faz **tradução simultânea**: enquanto você fala, a tradução já vai sendo falada para a outra pessoa, como um intérprete — sem esperar você terminar o raciocínio — **na sua própria voz, clonada** a partir de uma gravação de ~30 s feita no próprio aplicativo.

Ele cria um **microfone virtual** no sistema: você escolhe esse microfone no Discord, WhatsApp, Google Meet, Zoom, OBS ou qualquer outro app, e o que sai dele é a sua fala já traduzida. No modo **bilateral**, a voz da outra pessoa (que chega pelo app de chamada) também é traduzida para você.

```
microfone ─► detector de fala ─► reconhecimento em fluxo ─► tradução incremental ─► voz ─► microfone virtual ─► app de chamada
              (Silero)            (Whisper / Parakeet)       (NLLB, continua o        (a SUA voz clonada:
                                  relê a cada 0,6 s e         que já foi falado)       OmniVoice na placa ou
                                  confirma as palavras                                  voz leve no processador)
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
| Voz clonada fiel | **OmniVoice** (k2-fsa) pelo **omnivoice.cpp** na placa de vídeo: **Vulkan** (AMD, Intel e NVIDIA; nos Macs Intel com AMD pelo **MoltenVK**), Metal nos Macs com chip Apple |
| Voz clonada leve | **Supertonic 3** ajustado à impressão de voz da pessoa (ajuste fino feito no próprio computador, sem placa) |
| Placa de vídeo | NVIDIA pelo CUDA no reconhecimento e na tradução; voz clonada pelo CUDA em toda NVIDIA compatível no Linux, da GeForce 900 à RTX 50 (baixado na instalação, ~160 MB; 10–15% mais rápido que o Vulkan; placa mais antiga ou driver anterior ao 525 fica no Vulkan) e pelo Vulkan nas outras placas e no Windows; processador quando não há |
| Hardware | o Praxis identifica sozinho processador, placas de vídeo e memória (tipo DDR, velocidade, fabricante) e mostra o uso de cada um na tela |
| Instalação | `.deb` (Linux) e instalador `.exe` (Windows), com **atualização automática** |

A versão anterior, em Python (`praxis.py`), continua no repositório como bancada de testes e medições (`benchmarks/`).

---

## Instalação

O jeito mais fácil: entre no **[site do Praxis](https://disouz4-dev.github.io/praxis/#baixar)** e siga o botão do seu sistema.

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

Medidos com a tradução simultânea de fala real (Ryzen 7 5700X + RTX 3050; máquina virtual Windows 11 sem placa de vídeo):

| | Mínimo (sem placa de vídeo) | Recomendado (com placa de vídeo) |
|---|---|---|
| Processador | 4 núcleos, 64 bits (com 2 a tradução fica para trás) | 6 núcleos ou mais |
| Memória | 8 GB (o Praxis usa ~1,3 GB) | 16 GB |
| Placa de vídeo | — | com Vulkan e 4 GB ou mais para a voz clonada fiel (NVIDIA, AMD, Intel; Macs com AMD ou chip Apple); NVIDIA com 6 GB acelera também o reconhecimento |
| Espaço | ~1,5 GB por par de idiomas | ~5 GB |
| Idiomas | português, inglês, espanhol, alemão e italiano | os 16, com o menor erro |
| Sistema | Windows 10 (2004+) ou 11, 64 bits · Debian, Ubuntu, Mint e derivados | igual |

Microfone virtual: no Linux o Praxis cria sozinho; no Windows o `install.ps1` instala o VB-Audio Virtual Cable e o renomeia para **Praxis Mic**; no Mac, o driver próprio do Praxis (`app/macos/driver`).

**Voz clonada e a placa de vídeo.** Na primeira vez, o Praxis mede quanto a placa leva para gerar a voz clonada fiel (OmniVoice, 8 passos) e escolhe sozinho:

| Placa (medido) | Segundos de cálculo por segundo de fala | Voz usada na escolha automática |
|---|---:|---|
| NVIDIA RTX 3050 (Vulkan) | 0,2–0,35 | fiel (simultânea) |
| AMD Radeon Pro 5500M, MacBook Pro 2019 (Vulkan/MoltenVK) | ~0,85 | leve (a fiel atrasaria 3–6 s) |
| sem placa | — | leve |

A tela diz qual voz está em uso e por quê; em **Voz da tradução** dá para forçar a fiel ou a leve.

---

## Uso

Abra o **Praxis**. Na primeira vez, o tutorial pede que você **grave a sua voz** (~30 s lendo um texto): é dela que sai o clone — sem a voz gravada, o Praxis não traduz. Depois, na tela principal, escolha os dois idiomas e a **voz da tradução** e clique em **Começar a traduzir**. Na primeira vez ele baixa os modelos para os seus idiomas. No app de chamada, escolha o microfone **Praxis Mic**.

A tela principal mostra a conversa (você de um lado, a outra pessoa do outro), a **monitoria** (ouvir a sua própria tradução, liga e desliga a qualquer momento) e o **uso do computador** — processador, cada placa de vídeo (com a memória ocupada) e memória, pelo nome. O resto (microfone, sua voz, Praxis Mic, modo bilateral, detalhes do hardware) fica em **⚙ Configurações**.

**Bilateral** (a outra pessoa também é traduzida):

| Onde | Microfone | Saída de som |
|---|---|---|
| App de chamada | **Praxis Mic** | **Praxis Speaker** |
| Praxis | o seu microfone | o seu fone |

```
Você fala ─► seu microfone ─► Praxis ─► Praxis Mic ─► app de chamada ─► a outra pessoa ouve traduzido
A outra pessoa ─► app de chamada ─► Praxis Speaker ─► Praxis ─► seu fone (você ouve traduzido)
```

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
- [x] **Voz clonada da própria pessoa**: fiel (OmniVoice na placa, Vulkan/Metal) e leve (ajuste fino no processador), escolhida automaticamente pela placa
- [x] Identificação do hardware e monitor de uso na tela
- [ ] Voz fiel em placas modestas: treinar o OmniVoice para 4 passos (destilação)
- [ ] macOS
- [ ] Modos "segurar uma tecla para falar" e por volume

---

<div align="center">

**Uma mensagem. Todas as línguas.**

</div>
