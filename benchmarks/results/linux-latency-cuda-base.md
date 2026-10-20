_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · 16 cores · Python 3.12.3 · CUDA True_

Whisper model: `base` · backend: `cuda`

| Pair | N | VAD tail | ASR | MT | TTS 1st | **Total p50** | **Total p95** |
|---|---:|---:|---:|---:|---:|---:|---:|
| pt->en | 10 | 288 | 56 | 27 | 47 | **399 ms** | **494 ms** |
| en->pt | 10 | 272 | 56 | 23 | 56 | **402 ms** | **484 ms** |
| es->en | 10 | 256 | 64 | 32 | 57 | **413 ms** | **487 ms** |

Stage values are p50 in ms. Total = end of speech → first translated audio sample ready (playback start).
