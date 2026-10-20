_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · Python 3.12.3 · CUDA True_

Whisper `small` on `cuda` — ~1 min of continuous real speech per pair, fed in real time

| Pair | Speech | Error rate | Translation fidelity (0–100) | Typical latency | 1-in-20 worst | Lag growth (2nd vs 1st half) | Backlog when speaker stops | Translated / original speech | Keeps up |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 71s | 7.8% words | 71.4 | 1.0 s | 3.6 s | +0.2 s | 3.5 s | 69% | ✅ |
| en->pt | 72s | 2.1% words | 72.2 | 0.8 s | 2.7 s | -0.5 s | 4.3 s | 79% | ✅ |
| es->en | 73s | 2.6% words | 67.9 | 0.8 s | 2.4 s | -0.1 s | 1.2 s | 59% | ✅ |
| fr->en | 62s | 25.3% words | 57.0 | 1.4 s | 3.8 s | +0.6 s | 3.0 s | 73% | ✅ |
| de->en | 63s | 28.3% words | 57.5 | 0.7 s | 2.6 s | +0.0 s | 1.7 s | 54% | ✅ |
| it->en | 78s | 33.3% words | 54.8 | 1.1 s | 3.8 s | +0.2 s | 4.1 s | 69% | ✅ |
| ru->en | 66s | 15.9% words | 71.4 | 1.5 s | 5.0 s | -0.1 s | 3.4 s | 58% | ✅ |
| zh->en | 62s | 30.2% chars | 30.1 | 1.2 s | 2.5 s | +0.2 s | 1.8 s | 53% | ✅ |
| nl->en | 66s | 22.4% words | 58.7 | 0.6 s | 2.5 s | -0.1 s | 3.8 s | 64% | ✅ |
| pl->en | 69s | 13.3% words | 63.5 | 0.7 s | 2.5 s | +0.2 s | 3.5 s | 78% | ✅ |
| uk->en | 69s | 17.4% words | 64.6 | 0.5 s | 3.0 s | -1.0 s | 3.3 s | 59% | ✅ |
| tr->en | 72s | 24.7% words | 55.7 | 0.8 s | 2.5 s | -0.9 s | 3.2 s | 42% | ✅ |
| ar->en | 74s | 28.1% words | 64.5 | 1.4 s | 3.7 s | +0.1 s | 3.9 s | 64% | ✅ |
| hi->en | 69s | 73.8% words | 28.3 | 0.6 s | 1.6 s | -0.4 s | 1.5 s | 44% | ✅ |
| ja->en | 64s | 21.5% chars | 50.6 | 1.4 s | 3.7 s | -1.5 s | 2.2 s | 46% | ✅ |
| ko->en | 69s | 38.4% words | 57.9 | 2.0 s | 3.0 s | +0.3 s | 2.6 s | 60% | ✅ |

### Where the time goes (typical, per segment)

| Pair | Waiting in queue | Transcription | Translation | Voice (1st sentence) | Waiting for previous speech |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 166 ms | 25 ms | 70 ms | 0 ms |
| en->pt | 0 ms | 175 ms | 30 ms | 70 ms | 0 ms |
| es->en | 0 ms | 147 ms | 27 ms | 42 ms | 4 ms |
| fr->en | 0 ms | 166 ms | 24 ms | 57 ms | 0 ms |
| de->en | 0 ms | 141 ms | 19 ms | 33 ms | 0 ms |
| it->en | 0 ms | 175 ms | 20 ms | 58 ms | 0 ms |
| ru->en | 0 ms | 179 ms | 28 ms | 76 ms | 0 ms |
| zh->en | 0 ms | 162 ms | 19 ms | 51 ms | 0 ms |
| nl->en | 0 ms | 184 ms | 30 ms | 66 ms | 0 ms |
| pl->en | 0 ms | 187 ms | 31 ms | 75 ms | 0 ms |
| uk->en | 0 ms | 161 ms | 21 ms | 53 ms | 0 ms |
| tr->en | 0 ms | 180 ms | 22 ms | 37 ms | 0 ms |
| ar->en | 0 ms | 209 ms | 24 ms | 64 ms | 0 ms |
| hi->en | 0 ms | 256 ms | 15 ms | 30 ms | 0 ms |
| ja->en | 0 ms | 207 ms | 28 ms | 60 ms | 0 ms |
| ko->en | 0 ms | 186 ms | 30 ms | 79 ms | 1 ms |

### Problems found

- **pt->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.6 s
- **en->pt**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **es->en**: nenhum problema detectado
- **fr->en**: transcrição ruim: 25% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.8 s
- **de->en**: transcrição ruim: 28% das palavras erradas; 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **it->en**: transcrição ruim: 33% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 3.8 s
- **ru->en**: picos de atraso: 1 em cada 20 trechos demora mais de 5.0 s
- **zh->en**: transcrição ruim: 30% dos caracteres erradas
- **nl->en**: transcrição ruim: 22% das palavras erradas; 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **pl->en**: nenhum problema detectado
- **uk->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 3.0 s
- **tr->en**: transcrição ruim: 25% das palavras erradas
- **ar->en**: transcrição ruim: 28% das palavras erradas; inventou 10 palavras que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **hi->en**: transcrição ruim: 74% das palavras erradas; pulou 2 trecho(s) inteiro(s) da fala (maior: 18 palavras seguidas)
- **ja->en**: transcrição ruim: 22% dos caracteres erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **ko->en**: transcrição ruim: 38% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.0 s

Error rate = share of words (characters for zh/ja) transcribed wrong, skipped or invented. Translation fidelity compares the translation of what was heard with the translation of the true script. Latency = end of a speech segment → first translated audio. Lag growth ≈ 0 means it keeps pace.
