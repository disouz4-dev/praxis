_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · Python 3.12.3 · CUDA True_

Whisper `large-v3` on `cuda` — ~1 min of continuous real speech per pair, fed in real time

| Pair | Speech | Error rate | Translation fidelity (0–100) | Typical latency | 1-in-20 worst | Lag growth (2nd vs 1st half) | Backlog when speaker stops | Translated / original speech | Keeps up |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 71s | 6.0% words | 76.9 | 1.7 s | 3.9 s | +0.8 s | 3.9 s | 69% | ✅ |
| en->pt | 72s | 3.2% words | 74.0 | 1.4 s | 3.8 s | -0.5 s | 4.3 s | 78% | ✅ |
| es->en | 73s | 3.3% words | 68.0 | 1.2 s | 2.4 s | +0.1 s | 1.8 s | 58% | ✅ |
| fr->en | 62s | 17.1% words | 65.0 | 1.8 s | 4.5 s | +0.8 s | 3.8 s | 74% | ✅ |
| de->en | 63s | 16.0% words | 59.8 | 1.2 s | 3.1 s | +0.1 s | 2.1 s | 56% | ✅ |
| it->en | 78s | 12.4% words | 65.2 | 1.9 s | 4.1 s | -0.5 s | 4.0 s | 65% | ✅ |
| ru->en | 66s | 10.2% words | 74.9 | 2.1 s | 5.5 s | -0.1 s | 3.3 s | 58% | ✅ |
| zh->en | 62s | 12.2% chars | 40.5 | 2.0 s | 3.0 s | -0.3 s | 2.4 s | 51% | ✅ |
| nl->en | 66s | 15.0% words | 66.5 | 1.1 s | 2.9 s | -0.1 s | 3.6 s | 60% | ✅ |
| pl->en | 69s | 2.5% words | 65.3 | 1.3 s | 2.7 s | +0.2 s | 3.6 s | 78% | ✅ |
| uk->en | 69s | 8.3% words | 73.5 | 1.2 s | 3.7 s | -1.0 s | 4.1 s | 60% | ✅ |
| tr->en | 72s | 10.3% words | 65.9 | 1.6 s | 4.2 s | -1.2 s | 4.4 s | 49% | ✅ |
| ar->en | 74s | 14.8% words | 68.1 | 2.0 s | 4.0 s | +0.0 s | 3.9 s | 61% | ✅ |
| hi->en | 69s | 26.2% words | 52.6 | 1.5 s | 4.4 s | -0.5 s | 2.2 s | 57% | ✅ |
| ja->en | 64s | 13.6% chars | 58.6 | 2.1 s | 4.8 s | -1.0 s | 2.8 s | 50% | ✅ |
| ko->en | 69s | 24.4% words | 65.7 | 2.7 s | 4.3 s | +0.5 s | 4.1 s | 62% | ✅ |

### Where the time goes (typical, per segment)

| Pair | Waiting in queue | Transcription | Translation | Voice (1st sentence) | Waiting for previous speech |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 650 ms | 24 ms | 64 ms | 0 ms |
| en->pt | 0 ms | 677 ms | 28 ms | 77 ms | 0 ms |
| es->en | 0 ms | 596 ms | 24 ms | 40 ms | 0 ms |
| fr->en | 0 ms | 677 ms | 26 ms | 63 ms | 0 ms |
| de->en | 0 ms | 557 ms | 18 ms | 28 ms | 0 ms |
| it->en | 0 ms | 682 ms | 20 ms | 52 ms | 0 ms |
| ru->en | 0 ms | 692 ms | 24 ms | 63 ms | 0 ms |
| zh->en | 0 ms | 663 ms | 22 ms | 60 ms | 0 ms |
| nl->en | 0 ms | 698 ms | 25 ms | 73 ms | 0 ms |
| pl->en | 0 ms | 735 ms | 29 ms | 68 ms | 0 ms |
| uk->en | 0 ms | 650 ms | 21 ms | 60 ms | 0 ms |
| tr->en | 0 ms | 709 ms | 21 ms | 66 ms | 0 ms |
| ar->en | 0 ms | 831 ms | 26 ms | 80 ms | 0 ms |
| hi->en | 0 ms | 787 ms | 15 ms | 37 ms | 0 ms |
| ja->en | 0 ms | 824 ms | 32 ms | 81 ms | 0 ms |
| ko->en | 0 ms | 724 ms | 26 ms | 74 ms | 1 ms |

### Problems found

- **pt->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.9 s
- **en->pt**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.8 s
- **es->en**: nenhum problema detectado
- **fr->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.5 s
- **de->en**: 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.1 s
- **it->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 4.1 s
- **ru->en**: picos de atraso: 1 em cada 20 trechos demora mais de 5.5 s
- **zh->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.0 s
- **nl->en**: 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **pl->en**: nenhum problema detectado
- **uk->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **tr->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.2 s
- **ar->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **hi->en**: transcrição ruim: 26% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.4 s
- **ja->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.8 s
- **ko->en**: transcrição ruim: 24% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 4.3 s

Error rate = share of words (characters for zh/ja) transcribed wrong, skipped or invented. Translation fidelity compares the translation of what was heard with the translation of the true script. Latency = end of a speech segment → first translated audio. Lag growth ≈ 0 means it keeps pace.
