_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · 16 cores · Python 3.12.3 · CUDA True_

Whisper model: `medium` · backend: `cuda`

| Pair | N | VAD tail | ASR | MT | TTS 1st | **Total p50** | **Total p95** |
|---|---:|---:|---:|---:|---:|---:|---:|
| pt->en | 10 | 288 | 314 | 19 | 48 | **644 ms** | **772 ms** |
| en->pt | 10 | 272 | 286 | 15 | 49 | **632 ms** | **724 ms** |
| es->en | 10 | 256 | 333 | 28 | 60 | **684 ms** | **782 ms** |

Stage values are p50 in ms. Total = end of speech → first translated audio sample ready (playback start).
