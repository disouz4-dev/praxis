# ✦ Praxis

> **Un mensaje. Todos los idiomas.**

<div align="center">

[🇧🇷 Português](README.md) · [🇺🇸 English](README.en.md) · **[🇪🇸 Español](README.es.md)** · [🇫🇷 Français](README.fr.md) · [🇩🇪 Deutsch](README.de.md) · [🇮🇹 Italiano](README.it.md)

[![Linux](https://img.shields.io/badge/Linux-PulseAudio%2FPipeWire-informational?logo=linux)](https://github.com/disouz4-dev/praxis)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://github.com/disouz4-dev/praxis)
[![License](https://img.shields.io/badge/Licencia-MIT-green)](LICENSE)
[![Offline](https://img.shields.io/badge/100%25-offline-success)](https://github.com/disouz4-dev/praxis)

</div>

---

La comunicación siempre ha sido la herramienta más poderosa de la humanidad. Sin embargo, el idioma sigue siendo una de las mayores barreras entre personas, culturas e ideas.

**Praxis** nació para cambiar eso.

La propuesta es simple: permitir que dos personas conversen de forma natural, cada una hablando su propio idioma, mientras la otra escucha la conversación en su lengua nativa, en tiempo real.

Imagina a un brasileño hablando en portugués mientras un estadounidense lo escucha en inglés. Enseguida, el estadounidense responde en inglés y el brasileño escucha la respuesta en portugués. Sin pausas para traducción. Sin necesidad de aprender otro idioma. Solo una conversación.

Más que un traductor de voz, **Praxis** busca hacer la tecnología invisible, permitiendo que la comunicación ocurra como debería ser: espontánea, humana y accesible.

El nombre **Praxis** representa la acción — la idea de llevar a la práctica aquello que une a las personas. La inspiración detrás del proyecto también evoca la narrativa de Hechos 2, donde hombres y mujeres de diferentes naciones escucharon el mismo mensaje en sus propias lenguas. Independientemente de las creencias de cada uno, esa imagen simboliza algo universal: cuando el lenguaje deja de ser una barrera, la comprensión se vuelve posible.

---

## Visión

Construir una plataforma de traducción de voz en tiempo real que permita conversaciones naturales entre personas de cualquier parte del mundo, preservando el contexto, la emoción y la fluidez.

## Misión

Eliminar barreras lingüísticas para que ideas, conocimiento y relaciones puedan cruzar fronteras sin que el idioma sea un obstáculo.

## Principios

- La tecnología debe acercar a las personas.
- Toda voz merece ser comprendida.
- El idioma no debe limitar conexiones.
- La traducción debe ser tan natural que desaparezca de la conversación.
- Un mensaje puede llegar a cualquier persona, en cualquier idioma.

---

## Cómo funciona

Praxis crea un **micrófono virtual** en el sistema operativo. Hablas en tu idioma; la voz sale ya traducida — lista para seleccionarse en Discord, WhatsApp, Google Meet, OBS o cualquier otra app.

```
Micrófono real  →  VAD  →  Whisper ASR  →  Argos Translate  →  Piper TTS
                                                                      ↓
                                                          Sink virtual (Praxis_Out)
                                                                      ↓
                                                      Praxis_Microfone  ←  Discord / Meet / OBS
```

Todo funciona **100% localmente** — sin internet, sin nube, sin enviar nada fuera de tu máquina.

---

## Modos de activación

| Modo | Descripción |
|------|-------------|
| **VAD automático** | Silero VAD detecta cuándo estás hablando y abre automáticamente |
| **Gate threshold** | Se activa solo por encima de un umbral de volumen — arrastra la barra bajo el medidor |
| **Push-to-Talk** | Mantén un botón presionado (teclado o ratón) para transmitir |

---

## Idiomas soportados

### Idioma de salida (con voz Piper disponible)

| Idioma | Código | Voces disponibles |
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

### Idioma de entrada (reconocido por Whisper)

Portugués · Inglés · Español · Francés · Alemán · Italiano · Japonés · Chino · Coreano · Ruso · Árabe · Hindi · Neerlandés · Polaco · Ucraniano · Turco — y decenas de otros idiomas compatibles con Whisper.

> La traducción entre idiomas no ingleses usa **pivot automático por inglés** (ej: pt→it va pt→en→it).

---

## Instalación

```bash
git clone https://github.com/disouz4-dev/praxis.git
cd praxis
chmod +x install.sh && ./install.sh
```

El instalador crea un entorno virtual aislado, instala todas las dependencias y pone el comando `praxis` disponible globalmente.

### Requisitos

- Linux con PulseAudio o PipeWire
- Python 3.10+
- `pulseaudio-utils` (`pactl`, `parec`)
- GPU NVIDIA con CUDA (recomendado) o CPU

---

## Uso

```bash
praxis
```

En la ventana de configuración, selecciona:
1. **Modo** de activación (VAD / Gate / PTT)
2. **Micrófono** de entrada
3. **Idioma** de origen y destino
4. **Voz** de salida (descarga voces adicionales con el botón ⬇ Descargar)
5. Haz clic en **✦ Iniciar**

En la app de llamadas, selecciona **Praxis_Microfone** como dispositivo de entrada de audio.

---

<div align="center">

**Un mensaje. Todos los idiomas.**

</div>
