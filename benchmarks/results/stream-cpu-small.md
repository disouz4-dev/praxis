_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · Python 3.12.3 · CUDA True_

Whisper `small` on `cpu` — ~1 min of continuous real speech per pair, fed in real time

| Pair | Speech | Error rate | Translation fidelity (0–100) | Typical latency | 1-in-20 worst | Lag growth (2nd vs 1st half) | Backlog when speaker stops | Translated / original speech | Keeps up |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 71s | 7.8% words | 71.7 | 2.0 s | 4.3 s | +0.1 s | 5.3 s | 70% | ✅ |
| en->pt | 72s | 3.2% words | 72.8 | 1.9 s | 3.9 s | -0.4 s | 5.4 s | 79% | ✅ |
| es->en | 73s | 3.3% words | 68.1 | 1.9 s | 3.4 s | -0.0 s | 2.2 s | 58% | ✅ |
| fr->en | 62s | 24.7% words | 57.8 | 2.6 s | 5.4 s | +0.5 s | 4.3 s | 74% | ✅ |
| de->en | 63s | 29.2% words | 58.0 | 1.8 s | 3.9 s | +0.0 s | 2.6 s | 53% | ✅ |
| it->en | 78s | 32.2% words | 54.9 | 2.3 s | 4.9 s | +0.3 s | 5.2 s | 67% | ✅ |
| ru->en | 66s | 15.9% words | 73.6 | 2.7 s | 6.3 s | -0.1 s | 4.2 s | 57% | ✅ |
| zh->en | 62s | 32.9% chars | 29.5 | 2.3 s | 4.0 s | +0.4 s | 2.6 s | 53% | ✅ |
| nl->en | 66s | 21.1% words | 57.0 | 1.8 s | 3.7 s | -0.0 s | 5.1 s | 64% | ✅ |
| pl->en | 69s | 16.5% words | 63.0 | 2.1 s | 3.5 s | +0.3 s | 4.8 s | 77% | ✅ |
| uk->en | 69s | 19.0% words | 67.9 | 1.9 s | 4.4 s | -1.1 s | 4.4 s | 58% | ✅ |
| tr->en | 72s | 23.7% words | 58.4 | 2.0 s | 4.0 s | -0.9 s | 4.7 s | 44% | ✅ |
| ar->en | 74s | 31.2% words | 64.5 | 2.7 s | 5.1 s | -0.0 s | 5.4 s | 64% | ✅ |
| hi->en | 69s | 69.8% words | 30.8 | 2.2 s | 4.6 s | -0.9 s | 2.9 s | 49% | ✅ |
| ja->en | 64s | 21.5% chars | 52.3 | 2.7 s | 4.9 s | -1.3 s | 3.4 s | 48% | ✅ |
| ko->en | 69s | 37.2% words | 56.3 | 3.0 s | 3.7 s | +0.4 s | 3.9 s | 56% | ✅ |

### Where the time goes (typical, per segment)

| Pair | Waiting in queue | Transcription | Translation | Voice (1st sentence) | Waiting for previous speech |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 1287 ms | 27 ms | 69 ms | 0 ms |
| en->pt | 0 ms | 1292 ms | 31 ms | 73 ms | 0 ms |
| es->en | 0 ms | 1202 ms | 27 ms | 43 ms | 0 ms |
| fr->en | 0 ms | 1303 ms | 25 ms | 61 ms | 0 ms |
| de->en | 0 ms | 1179 ms | 19 ms | 35 ms | 0 ms |
| it->en | 0 ms | 1333 ms | 21 ms | 51 ms | 0 ms |
| ru->en | 0 ms | 1351 ms | 28 ms | 65 ms | 0 ms |
| zh->en | 0 ms | 1305 ms | 20 ms | 49 ms | 0 ms |
| nl->en | 0 ms | 1343 ms | 30 ms | 73 ms | 0 ms |
| pl->en | 0 ms | 1390 ms | 31 ms | 67 ms | 0 ms |
| uk->en | 0 ms | 1290 ms | 20 ms | 49 ms | 0 ms |
| tr->en | 0 ms | 1346 ms | 22 ms | 35 ms | 0 ms |
| ar->en | 0 ms | 1479 ms | 25 ms | 71 ms | 0 ms |
| hi->en | 0 ms | 1677 ms | 16 ms | 33 ms | 0 ms |
| ja->en | 0 ms | 1498 ms | 30 ms | 64 ms | 0 ms |
| ko->en | 0 ms | 1380 ms | 28 ms | 68 ms | 1 ms |

### Problems found

- **pt->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 4.3 s
- **en->pt**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.9 s
- **es->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.4 s
- **fr->en**: transcrição ruim: 25% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 5.4 s
- **de->en**: transcrição ruim: 29% das palavras erradas; 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.9 s
- **it->en**: transcrição ruim: 32% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 4.9 s
- **ru->en**: picos de atraso: 1 em cada 20 trechos demora mais de 6.3 s
- **zh->en**: transcrição ruim: 33% dos caracteres erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **nl->en**: transcrição ruim: 21% das palavras erradas; 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **pl->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.5 s
- **uk->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 4.4 s
- **tr->en**: transcrição ruim: 24% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **ar->en**: transcrição ruim: 31% das palavras erradas; inventou 10 palavras que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 5.1 s
- **hi->en**: transcrição ruim: 70% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 14 palavras seguidas); picos de atraso: 1 em cada 20 trechos demora mais de 4.6 s
- **ja->en**: transcrição ruim: 22% dos caracteres erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.9 s
- **ko->en**: transcrição ruim: 37% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s

Error rate = share of words (characters for zh/ja) transcribed wrong, skipped or invented. Translation fidelity compares the translation of what was heard with the translation of the true script. Latency = end of a speech segment → first translated audio. Lag growth ≈ 0 means it keeps pace.
