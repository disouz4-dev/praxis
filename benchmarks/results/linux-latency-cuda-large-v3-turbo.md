_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · 16 cores · Python 3.12.3 · CUDA True_

Whisper model: `large-v3-turbo` · backend: `cuda`

| Pair | N | VAD tail | ASR | MT | TTS 1st | **Total p50** | **Total p95** |
|---|---:|---:|---:|---:|---:|---:|---:|
| pt->en | 10 | 288 | 399 | 19 | 49 | **738 ms** | **839 ms** |
| en->pt | 10 | 272 | 390 | 16 | 48 | **735 ms** | **808 ms** |
| es->en | 10 | 256 | 407 | 27 | 54 | **747 ms** | **824 ms** |

Stage values are p50 in ms. Total = end of speech → first translated audio sample ready (playback start).
