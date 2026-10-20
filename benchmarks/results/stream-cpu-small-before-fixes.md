_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · Python 3.12.3 · CUDA True_

Whisper `small` on `cpu` — ~1 min of continuous real speech per pair, fed in real time

| Pair | Speech | Error rate | Translation fidelity (0–100) | Typical latency | 1-in-20 worst | Lag growth (2nd vs 1st half) | Backlog when speaker stops | Translated / original speech | Keeps up |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 71s | 7.8% words | 67.6 | 2.0 s | 4.3 s | +0.4 s | 5.3 s | 71% | ✅ |
| en->pt | 72s | 3.2% words | 71.6 | 1.9 s | 4.0 s | -0.4 s | 5.9 s | 81% | ✅ |
| es->en | 73s | 3.3% words | 58.4 | 1.9 s | 3.4 s | +0.1 s | 2.6 s | 60% | ✅ |
| fr->en | 62s | 24.7% words | 57.8 | 2.5 s | 5.3 s | +0.8 s | 4.2 s | 76% | ✅ |
| de->en | 63s | 29.2% words | 59.5 | 1.9 s | 3.9 s | +0.0 s | 2.8 s | 55% | ✅ |
| it->en | 78s | 33.9% words | 8.5 | 2.3 s | 5.1 s | +0.0 s | 5.4 s | 69% | ✅ |
| ru->en | 66s | 15.9% words | 73.6 | 2.7 s | 6.3 s | -0.1 s | 4.5 s | 59% | ✅ |
| zh->en | 62s | 41.0% chars | 31.8 | 2.1 s | 3.6 s | -0.3 s | 3.0 s | 47% | ✅ |
| nl->en | 66s | 20.4% words | 60.3 | 1.7 s | 3.8 s | -0.0 s | 5.3 s | 66% | ✅ |
| pl->en | 69s | 16.5% words | 54.7 | 2.1 s | 3.4 s | +0.6 s | 5.2 s | 80% | ✅ |
| uk->en | 69s | 21.5% words | 67.7 | 1.9 s | 4.3 s | -1.1 s | 4.2 s | 57% | ✅ |
| tr->en | 72s | 23.7% words | 58.4 | 2.0 s | 3.9 s | -0.8 s | 4.6 s | 45% | ✅ |
| ar->en | 74s | 31.2% words | 64.5 | 2.7 s | 5.2 s | +0.0 s | 5.8 s | 66% | ✅ |
| hi->en | 69s | 69.1% words | 30.5 | 2.3 s | 4.8 s | -0.9 s | 3.0 s | 48% | ✅ |
| ja->en | — | — | — | — | — | — | — | — | ⚠️ ModuleNotFoundError: No module named 'stanza' |
| ko->en | — | — | — | — | — | — | — | — | ⚠️ ModuleNotFoundError: No module named 'stanza' |

### Where the time goes (typical, per segment)

| Pair | Waiting in queue | Transcription | Translation | Voice (1st sentence) | Waiting for previous speech |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 1267 ms | 27 ms | 72 ms | 0 ms |
| en->pt | 0 ms | 1277 ms | 30 ms | 77 ms | 0 ms |
| es->en | 0 ms | 1187 ms | 27 ms | 45 ms | 108 ms |
| fr->en | 0 ms | 1282 ms | 25 ms | 62 ms | 0 ms |
| de->en | 0 ms | 1169 ms | 19 ms | 33 ms | 0 ms |
| it->en | 0 ms | 1327 ms | 21 ms | 62 ms | 0 ms |
| ru->en | 0 ms | 1364 ms | 28 ms | 67 ms | 53 ms |
| zh->en | 0 ms | 1287 ms | 19 ms | 43 ms | 0 ms |
| nl->en | 0 ms | 1338 ms | 29 ms | 71 ms | 0 ms |
| pl->en | 0 ms | 1367 ms | 30 ms | 70 ms | 0 ms |
| uk->en | 0 ms | 1292 ms | 22 ms | 52 ms | 0 ms |
| tr->en | 0 ms | 1341 ms | 23 ms | 36 ms | 0 ms |
| ar->en | 0 ms | 1485 ms | 26 ms | 60 ms | 0 ms |
| hi->en | 0 ms | 1684 ms | 18 ms | 36 ms | 0 ms |

### Problems found

- **pt->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 4.3 s
- **en->pt**: 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **es->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.4 s
- **fr->en**: transcrição ruim: 25% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 5.3 s
- **de->en**: transcrição ruim: 29% das palavras erradas; 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 3.9 s
- **it->en**: transcrição ruim: 34% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 2 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 5.1 s
- **ru->en**: picos de atraso: 1 em cada 20 trechos demora mais de 6.3 s
- **zh->en**: transcrição ruim: 41% dos caracteres erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 30 caracteres seguidas); 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 3.6 s
- **nl->en**: transcrição ruim: 20% das palavras erradas; 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 3.8 s
- **pl->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.4 s
- **uk->en**: transcrição ruim: 21% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 2 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 4.3 s
- **tr->en**: transcrição ruim: 24% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.9 s
- **ar->en**: transcrição ruim: 31% das palavras erradas; inventou 10 palavras que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 5.2 s
- **hi->en**: transcrição ruim: 69% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 14 palavras seguidas); 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 4.8 s
- **ja->en**: nenhum problema detectado
- **ko->en**: nenhum problema detectado

Error rate = share of words (characters for zh/ja) transcribed wrong, skipped or invented. Translation fidelity compares the translation of what was heard with the translation of the true script. Latency = end of a speech segment → first translated audio. Lag growth ≈ 0 means it keeps pace.
