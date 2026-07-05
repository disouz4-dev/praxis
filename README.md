# ✦ Praxis

> **Uma mensagem. Todas as línguas.**

<div align="center">

**[🇧🇷 Português](README.md)** · [🇺🇸 English](README.en.md) · [🇪🇸 Español](README.es.md) · [🇫🇷 Français](README.fr.md) · [🇩🇪 Deutsch](README.de.md) · [🇮🇹 Italiano](README.it.md)

[![Linux](https://img.shields.io/badge/Linux-PulseAudio%2FPipeWire-informational?logo=linux)](https://github.com/disouz4-dev/praxis)
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

O nome **Praxis** representa a ação — a ideia de colocar em prática aquilo que aproxima pessoas. A inspiração por trás do projeto também remete à narrativa de Atos 2, onde homens e mulheres de diferentes nações ouviram uma mesma mensagem em suas próprias línguas. Independentemente da crença de cada pessoa, essa imagem simboliza algo universal: quando a linguagem deixa de ser uma barreira, a compreensão se torna possível.

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
                                                              Sink virtual (Praxis_Out)
                                                                      ↓
                                                          Praxis_Microfone  ←  Discord / Meet / OBS
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

```bash
git clone https://github.com/disouz4-dev/praxis.git
cd praxis
chmod +x install.sh && ./install.sh
```

O instalador cria um ambiente virtual isolado, instala todas as dependências (PyTorch, Whisper, Argos, Piper) e disponibiliza o comando `praxis` globalmente.

### Requisitos

- Linux com PulseAudio ou PipeWire
- Python 3.10+
- `pulseaudio-utils` (`pactl`, `parec`)
- GPU NVIDIA com CUDA (recomendado) ou CPU

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

No app de chamada, selecione **Praxis_Microfone** como dispositivo de entrada de áudio.

---

## Pipeline técnico

| Etapa | Ferramenta | Detalhes |
|-------|-----------|----------|
| Segmentação de fala | **Silero VAD** | Corte por silêncio (200ms) ou duração máxima (4s) |
| Transcrição | **faster-whisper** | Modelo `small` padrão; GPU int8_float16 / CPU int8 |
| Tradução | **Argos Translate** | 100% offline; baixa pares de idiomas no primeiro uso |
| Síntese de voz | **Piper TTS** | Modelos `.onnx` leves e rápidos; síntese por sentença em paralelo |
| Saída de áudio | **pacat + PulseAudio** | Injeção direta no sink virtual |

---

## Clonagem de voz (RVC)

A aba **"Clonar minha voz"** permite treinar um modelo RVC com a sua própria voz — sem precisar de ferramentas externas. Todo o pipeline roda dentro do Praxis.

### Como usar

1. Abra a aba **🎙 Clonar minha voz**
2. Digite um nome para o perfil (ex: `Diego`)
3. Leia o texto de referência em voz alta (4 páginas, ~1000 palavras)
   - Use os botões **← Anterior** / **Próximo →** para navegar entre páginas
   - Pode gravar várias sessões curtas — o áudio acumula automaticamente
4. Com **3 minutos ou mais** gravados, o botão **🎙 Treinar Voz** é liberado
5. Clique em **Treinar Voz** — o pipeline executa em 3 fases:
   - **Fase 1** — Pré-processamento do áudio (corte em chunks de 3s)
   - **Fase 2** — Extração de features (HuBERT + RMVPE para F0)
   - **Fase 3** — Treino do modelo (300 épocas, HiFi-GAN vocoder)
6. Após o treino (~10-30 min com GPU), clique em **Testar** para ouvir o resultado
7. Clique em **Usar** para ativar a voz clonada como saída padrão

### Tecnologia

- **RVC** (Retrieval-based Voice Conversion) — conversão de voz baseada em retrieval
- **Applio** — scripts de treino usados internamente (sem precisar abrir a interface web)
- **edge-tts** — TTS intermediário para síntese antes da conversão
- Modelo salvo em `voices/clones/` como `.pth` (pesos) + `.json` (metadados)

> O áudio de treinamento é acumulado automaticamente: você pode gravar em múltiplas sessões e o total vai crescendo até atingir o mínimo de 3 minutos.

---

## Roadmap

- [x] Clonagem de voz com RVC (treino e inferência nativos no Praxis)
- [ ] Tradução bidirecional completa (ouvir o interlocutor traduzido)
- [ ] Tray icon e atalho global para pausar/retomar
- [ ] Streaming speech-to-speech para latência menor ainda
- [ ] Empacotamento `.deb` / `.desktop`
- [ ] Modo servidor LAN para apresentações e conferências

---

<div align="center">

**Uma mensagem. Todas as línguas.**

</div>
