_Machine: macOS-26.6.2-x86_64-i386-64bit · i386 · 16 cores · Python 3.12.15 · CUDA False_

Whisper model: `small` · backend: `cpu`

| Pair | N | VAD tail | ASR | MT | TTS 1st | **Total p50** | **Total p95** |
|---|---:|---:|---:|---:|---:|---:|---:|
| pt->en | 10 | 288 | 1666 | 56 | 110 | **2112 ms** | **2595 ms** |
| en->pt | 10 | 272 | 1392 | 48 | 92 | **1841 ms** | **1921 ms** |
| es->en | 10 | 256 | 1467 | 135 | 108 | **1962 ms** | **2182 ms** |

Stage values are p50 in ms. Total = end of speech → first translated audio sample ready (playback start).
