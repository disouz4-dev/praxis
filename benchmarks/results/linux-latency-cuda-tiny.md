_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · 16 cores · Python 3.12.3 · CUDA True_

Whisper model: `tiny` · backend: `cuda`

| Pair | N | VAD tail | ASR | MT | TTS 1st | **Total p50** | **Total p95** |
|---|---:|---:|---:|---:|---:|---:|---:|
| pt->en | 10 | 288 | 39 | 33 | 50 | **392 ms** | **472 ms** |
| en->pt | 10 | 272 | 35 | 25 | 61 | **400 ms** | **480 ms** |
| es->en | 10 | 256 | 42 | 41 | 58 | **396 ms** | **472 ms** |

Stage values are p50 in ms. Total = end of speech → first translated audio sample ready (playback start).
