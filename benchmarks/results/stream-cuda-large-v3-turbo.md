_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · Python 3.12.3 · CUDA True_

Whisper `large-v3-turbo` on `cuda` — ~1 min of continuous real speech per pair, fed in real time

| Pair | Speech | Error rate | Translation fidelity (0–100) | Typical latency | 1-in-20 worst | Lag growth (2nd vs 1st half) | Backlog when speaker stops | Translated / original speech | Keeps up |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 71s | 4.8% words | 76.9 | 1.1 s | 3.6 s | +0.2 s | 3.6 s | 66% | ✅ |
| en->pt | 72s | 1.1% words | 74.6 | 1.1 s | 3.6 s | -0.5 s | 4.0 s | 78% | ✅ |
| es->en | 73s | 2.6% words | 70.6 | 0.9 s | 2.2 s | -0.0 s | 1.5 s | 56% | ✅ |
| fr->en | 62s | 8.2% words | 68.3 | 1.3 s | 3.1 s | -0.4 s | 3.3 s | 66% | ✅ |
| de->en | 63s | 17.9% words | 60.0 | 0.9 s | 2.8 s | -0.0 s | 2.1 s | 54% | ✅ |
| it->en | 78s | 13.6% words | 61.1 | 1.5 s | 3.8 s | -0.1 s | 4.2 s | 64% | ✅ |
| ru->en | 66s | 6.8% words | 77.1 | 1.8 s | 5.2 s | +0.0 s | 2.8 s | 54% | ✅ |
| zh->en | 62s | 12.6% chars | 38.5 | 1.4 s | 2.7 s | +0.2 s | 1.7 s | 50% | ✅ |
| nl->en | 66s | 12.2% words | 63.0 | 0.9 s | 2.7 s | +0.8 s | 4.0 s | 66% | ✅ |
| pl->en | 69s | 3.2% words | 65.4 | 0.9 s | 1.9 s | +0.1 s | 3.3 s | 76% | ✅ |
| uk->en | 69s | 8.3% words | 72.5 | 0.8 s | 3.2 s | -1.0 s | 3.9 s | 59% | ✅ |
| tr->en | 72s | 12.4% words | 65.4 | 1.4 s | 4.2 s | -1.0 s | 4.0 s | 49% | ✅ |
| ar->en | 74s | 13.3% words | 68.7 | 1.6 s | 3.5 s | +0.1 s | 3.4 s | 60% | ✅ |
| hi->en | 69s | 33.6% words | 50.7 | 0.9 s | 3.4 s | -0.5 s | 1.6 s | 57% | ✅ |
| ja->en | 64s | 13.6% chars | 56.6 | 1.8 s | 4.1 s | -0.8 s | 2.2 s | 51% | ✅ |
| ko->en | 69s | 26.7% words | 61.6 | 2.3 s | 2.9 s | +0.3 s | 3.8 s | 58% | ✅ |

### Where the time goes (typical, per segment)

| Pair | Waiting in queue | Transcription | Translation | Voice (1st sentence) | Waiting for previous speech |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 447 ms | 23 ms | 64 ms | 0 ms |
| en->pt | 0 ms | 445 ms | 28 ms | 83 ms | 0 ms |
| es->en | 0 ms | 438 ms | 24 ms | 40 ms | 0 ms |
| fr->en | 0 ms | 447 ms | 25 ms | 54 ms | 0 ms |
| de->en | 0 ms | 427 ms | 18 ms | 27 ms | 0 ms |
| it->en | 0 ms | 449 ms | 19 ms | 57 ms | 0 ms |
| ru->en | 0 ms | 460 ms | 26 ms | 63 ms | 0 ms |
| zh->en | 0 ms | 446 ms | 23 ms | 48 ms | 0 ms |
| nl->en | 0 ms | 453 ms | 30 ms | 65 ms | 0 ms |
| pl->en | 0 ms | 461 ms | 29 ms | 64 ms | 0 ms |
| uk->en | 0 ms | 452 ms | 21 ms | 53 ms | 0 ms |
| tr->en | 0 ms | 446 ms | 20 ms | 61 ms | 0 ms |
| ar->en | 0 ms | 472 ms | 26 ms | 73 ms | 0 ms |
| hi->en | 0 ms | 465 ms | 15 ms | 35 ms | 0 ms |
| ja->en | 0 ms | 475 ms | 35 ms | 86 ms | 0 ms |
| ko->en | 0 ms | 460 ms | 25 ms | 79 ms | 1 ms |

### Problems found

- **pt->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.6 s
- **en->pt**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.6 s
- **es->en**: nenhum problema detectado
- **fr->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.1 s
- **de->en**: 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **it->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.8 s
- **ru->en**: picos de atraso: 1 em cada 20 trechos demora mais de 5.2 s
- **zh->en**: nenhum problema detectado
- **nl->en**: 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **pl->en**: nenhum problema detectado
- **uk->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 3.2 s
- **tr->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.2 s
- **ar->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.5 s
- **hi->en**: transcrição ruim: 34% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.4 s
- **ja->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.1 s
- **ko->en**: transcrição ruim: 27% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa

Error rate = share of words (characters for zh/ja) transcribed wrong, skipped or invented. Translation fidelity compares the translation of what was heard with the translation of the true script. Latency = end of a speech segment → first translated audio. Lag growth ≈ 0 means it keeps pace.
