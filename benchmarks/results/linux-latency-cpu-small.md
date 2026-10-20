_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · 16 cores · Python 3.12.3 · CUDA True_

Whisper model: `small` · backend: `cpu`

| Pair | N | VAD tail | ASR | MT | TTS 1st | **Total p50** | **Total p95** |
|---|---:|---:|---:|---:|---:|---:|---:|
| pt->en | 10 | 288 | 1206 | 21 | 42 | **1532 ms** | **1778 ms** |
| en->pt | 10 | 272 | 1182 | 18 | 60 | **1553 ms** | **1607 ms** |
| es->en | 10 | 256 | 1252 | 31 | 52 | **1601 ms** | **1747 ms** |

Stage values are p50 in ms. Total = end of speech → first translated audio sample ready (playback start).
