_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · 16 cores · Python 3.12.3 · CUDA True_

Whisper model: `large-v2` · backend: `cuda`

| Pair | N | VAD tail | ASR | MT | TTS 1st | **Total p50** | **Total p95** |
|---|---:|---:|---:|---:|---:|---:|---:|
| pt->en | 10 | 288 | 545 | 20 | 47 | **876 ms** | **1033 ms** |
| en->pt | 10 | 272 | 507 | 16 | 47 | **871 ms** | **936 ms** |
| es->en | 10 | 256 | 586 | 28 | 50 | **932 ms** | **1067 ms** |

Stage values are p50 in ms. Total = end of speech → first translated audio sample ready (playback start).
