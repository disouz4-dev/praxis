_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · 16 cores · Python 3.12.3 · CUDA True_

Whisper model: `small` · backend: `cuda`

| Pair | N | VAD tail | ASR | MT | TTS 1st | **Total p50** | **Total p95** |
|---|---:|---:|---:|---:|---:|---:|---:|
| pt->en | 10 | 288 | 127 | 19 | 40 | **458 ms** | **574 ms** |
| en->pt | 10 | 272 | 114 | 16 | 53 | **463 ms** | **542 ms** |
| es->en | 10 | 256 | 137 | 29 | 60 | **482 ms** | **582 ms** |

Stage values are p50 in ms. Total = end of speech → first translated audio sample ready (playback start).
