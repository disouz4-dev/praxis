# ✦ Praxis

> **一条消息。所有语言。**

<div align="center">

[🇧🇷 Português](../README.md) · [🇺🇸 English](README.en.md) · [🇪🇸 Español](README.es.md) · [🇫🇷 Français](README.fr.md) · [🇩🇪 Deutsch](README.de.md) · [🇮🇹 Italiano](README.it.md) · [🇷🇺 Русский](README.ru.md) · **[🇨🇳 中文](README.zh.md)** · [🇳🇱 Nederlands](README.nl.md) · [🇵🇱 Polski](README.pl.md) · [🇺🇦 Українська](README.uk.md) · [🇹🇷 Türkçe](README.tr.md) · [🇸🇦 العربية](README.ar.md) · [🇮🇳 हिन्दी](README.hi.md)

[![Linux](https://img.shields.io/badge/Linux-PulseAudio%2FPipeWire-informational?logo=linux)](https://github.com/disouz4-dev/praxis)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://github.com/disouz4-dev/praxis)
[![License](https://img.shields.io/badge/许可证-MIT-green)](LICENSE)
[![Offline](https://img.shields.io/badge/100%25-离线-success)](https://github.com/disouz4-dev/praxis)

</div>

---

沟通一直是人类最强大的工具。然而，语言仍然是人与人之间、文化之间、思想之间最大的障碍之一。

**Praxis** 应运而生，为此而生。

理念很简单：让两个人自然地交谈，各自说自己的语言，而对方实时听到用自己母语说出的内容。

想象一个巴西人用葡萄牙语说话，而美国人每句话都用英语听到。片刻之后，美国人用英语回答，巴西人用葡萄牙语听到。没有翻译停顿，只是对话。

---

## 愿景

构建一个实时语音翻译平台，使世界各地的人能够进行自然对话，同时保留语境、情感和流利度。

## 使命

消除语言障碍，让思想、知识和关系跨越边界，不再受语言限制。

## 原则

- 技术应该拉近人们的距离。
- 每个声音都应该被理解。
- 语言不应限制连接。
- 翻译应该自然到从对话中消失。
- 一条消息可以用任何语言到达任何人。

---

## 工作原理

Praxis 在操作系统中创建一个**虚拟麦克风**。您用自己的语言说话；声音出来时已经翻译好了——随时可在 Discord、WhatsApp、Google Meet、OBS 或任何其他应用中选择。

```
真实麦克风  →  VAD  →  Whisper ASR  →  Argos Translate  →  Piper TTS
                                                                    ↓
                                                    虚拟 sink (Praxis_Out)
                                                                    ↓
                                              Praxis_Microfone  ←  Discord / Meet / OBS
```

一切**100% 本地运行** — 无需网络，无需云端，没有任何数据离开您的计算机。

---

## 激活模式

| 模式 | 描述 |
|------|------|
| **自动 VAD** | Silero VAD 检测您说话时自动激活 |
| **Gate 阈值** | 仅在音量超过阈值时激活 |
| **一键通话 (PTT)** | 按住按键（键盘或鼠标）进行传输 |

---

## 支持的语言

### 输出语言（含 Piper 语音）

| 语言 | 代码 | 可用语音 |
|------|------|---------|
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

### 输入语言（Whisper 识别）

Português · English · Español · Français · Deutsch · Italiano · 日本語 · 中文 · 한국어 · Русский · العربية · हिन्दी · Nederlands · Polski · Українська · Türkçe — 以及 Whisper 支持的数十种其他语言。

> 两种非英语语言之间的翻译使用**自动英语中转**（如 pt→it 经过 pt→en→it）。

---

## 安装

```bash
git clone https://github.com/disouz4-dev/praxis.git
cd praxis
chmod +x install.sh && ./install.sh
```

安装程序创建一个隔离的虚拟环境，安装所有依赖（PyTorch、Whisper、Argos、Piper），并使 `praxis` 命令全局可用。

### 系统要求

- 带 PulseAudio 或 PipeWire 的 Linux
- Python 3.10+
- `pulseaudio-utils`（`pactl`、`parec`）
- NVIDIA GPU（推荐，需 CUDA）或 CPU

---

## 使用方法

```bash
praxis
```

在配置窗口中选择：
1. **激活模式**（VAD / Gate / PTT）
2. **输入麦克风**
3. **源语言和目标语言**
4. **输出语音**（用 ⬇ 下载按钮下载更多语音）
5. 点击 **✦ 开始**

在通话应用中，选择 **Praxis_Microfone** 作为音频输入设备。

---

## 技术管线

| 阶段 | 工具 | 详情 |
|------|------|------|
| 语音分割 | **Silero VAD** | 按静音（200ms）或最大时长（4s）切割 |
| 转录 | **faster-whisper** | 默认 `small` 模型；GPU int8_float16 / CPU int8 |
| 翻译 | **Argos Translate** | 100% 离线；首次使用时下载语言对 |
| 语音合成 | **Piper TTS** | 轻量 `.onnx` 模型；按句子并行合成 |
| 音频输出 | **pacat + PulseAudio** | 直接注入虚拟 sink |

---

## 声音克隆 (OmniVoice)

**"克隆我的声音"** 标签页让您在几秒内克隆任何声音——只需录制或导入 5–15 秒的音频片段。无需训练，无需等待。

### 使用方法

1. 打开 **🎙 克隆我的声音** 标签页
2. 输入配置文件名称（如 `Diego`）
3. **选项 A — 录制：** 点击麦克风按钮，朗读一段简短的通用文本
   **选项 B — 导入：** 点击"导入音频"，选择任意 WAV/MP3/OGG/OPUS/M4A/FLAC/AAC 文件（包括 WhatsApp 语音消息）
4. 点击 **测试** 听取克隆的声音
5. 点击 **使用** 将其激活为默认输出

> 参考音频会自动截取到 15 秒，以获得最佳克隆质量。

---

## 路线图

- [x] 使用 OmniVoice 的零样本声音克隆（无需训练）
- [x] 外部音频导入（WAV/MP3/OGG/OPUS/M4A 等）
- [ ] 完整双向翻译（听到对方翻译后的声音）
- [ ] 系统托盘图标和全局快捷键暂停/恢复
- [ ] 超低延迟的流式语音到语音
- [ ] `.deb` / `.desktop` 打包
- [ ] 用于演示和会议的 LAN 服务器模式

---

<div align="center">

**一条消息。所有语言。**

</div>
