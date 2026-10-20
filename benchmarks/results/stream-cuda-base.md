_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · Python 3.12.3 · CUDA True_

Whisper `base` on `cuda` — ~1 min of continuous real speech per pair, fed in real time

| Pair | Speech | Error rate | Translation fidelity (0–100) | Typical latency | 1-in-20 worst | Lag growth (2nd vs 1st half) | Backlog when speaker stops | Translated / original speech | Keeps up |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 71s | 16.2% words | 65.4 | 0.9 s | 2.9 s | +0.2 s | 3.9 s | 68% | ✅ |
| en->pt | 72s | 3.2% words | 68.6 | 0.7 s | 2.5 s | -0.5 s | 4.0 s | 76% | ✅ |
| es->en | 73s | 10.5% words | 65.0 | 0.6 s | 2.0 s | +0.2 s | 1.4 s | 58% | ✅ |
| fr->en | 62s | 38.0% words | 56.1 | 0.7 s | 3.8 s | +0.8 s | 3.6 s | 70% | ✅ |
| de->en | 63s | 41.5% words | 54.4 | 0.6 s | 2.3 s | +0.0 s | 1.6 s | 58% | ✅ |
| it->en | 78s | 39.0% words | 56.0 | 1.0 s | 3.2 s | +0.1 s | 3.1 s | 63% | ✅ |
| ru->en | 66s | 28.4% words | 63.0 | 1.4 s | 4.7 s | -0.1 s | 3.0 s | 56% | ✅ |
| zh->en | 62s | 37.4% chars | 33.4 | 1.1 s | 2.7 s | +0.1 s | 0.0 s | 50% | ✅ |
| nl->en | 66s | 27.2% words | 52.0 | 0.4 s | 2.2 s | -0.1 s | 3.5 s | 61% | ✅ |
| pl->en | 69s | 37.3% words | 52.5 | 0.7 s | 2.5 s | +0.0 s | 3.1 s | 77% | ✅ |
| uk->en | 69s | 46.3% words | 50.8 | 0.6 s | 2.5 s | -0.9 s | 3.2 s | 58% | ✅ |
| tr->en | 72s | 44.3% words | 57.7 | 1.0 s | 3.5 s | -1.1 s | 3.5 s | 50% | ✅ |
| ar->en | 74s | 49.2% words | 50.2 | 1.3 s | 2.7 s | +0.0 s | 1.8 s | 60% | ✅ |
| hi->en | 69s | 99.3% words | 18.6 | 1.2 s | 7.3 s | -1.4 s | 10.0 s | 94% | ❌ |
| ja->en | 64s | 32.5% chars | 45.0 | 1.3 s | 3.3 s | -0.9 s | 1.9 s | 44% | ✅ |
| ko->en | 69s | 44.2% words | 54.8 | 1.7 s | 2.4 s | +0.6 s | 2.6 s | 55% | ✅ |

### Where the time goes (typical, per segment)

| Pair | Waiting in queue | Transcription | Translation | Voice (1st sentence) | Waiting for previous speech |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 83 ms | 27 ms | 72 ms | 0 ms |
| en->pt | 0 ms | 80 ms | 36 ms | 65 ms | 0 ms |
| es->en | 0 ms | 62 ms | 30 ms | 45 ms | 0 ms |
| fr->en | 0 ms | 72 ms | 28 ms | 63 ms | 0 ms |
| de->en | 0 ms | 57 ms | 27 ms | 31 ms | 0 ms |
| it->en | 0 ms | 78 ms | 25 ms | 51 ms | 0 ms |
| ru->en | 0 ms | 84 ms | 29 ms | 71 ms | 0 ms |
| zh->en | 0 ms | 74 ms | 24 ms | 52 ms | 0 ms |
| nl->en | 0 ms | 84 ms | 30 ms | 61 ms | 0 ms |
| pl->en | 0 ms | 86 ms | 34 ms | 66 ms | 0 ms |
| uk->en | 0 ms | 74 ms | 30 ms | 50 ms | 0 ms |
| tr->en | 0 ms | 85 ms | 23 ms | 53 ms | 0 ms |
| ar->en | 0 ms | 96 ms | 28 ms | 65 ms | 0 ms |
| hi->en | 0 ms | 63 ms | 24 ms | 40 ms | 645 ms |
| ja->en | 0 ms | 95 ms | 35 ms | 69 ms | 0 ms |
| ko->en | 0 ms | 84 ms | 31 ms | 63 ms | 0 ms |

### Problems found

- **pt->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **en->pt**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **es->en**: nenhum problema detectado
- **fr->en**: transcrição ruim: 38% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 8 palavras seguidas); inventou 8 palavras que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 3.8 s
- **de->en**: transcrição ruim: 42% das palavras erradas; 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **it->en**: transcrição ruim: 39% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.2 s
- **ru->en**: transcrição ruim: 28% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.7 s
- **zh->en**: transcrição ruim: 37% dos caracteres erradas
- **nl->en**: transcrição ruim: 27% das palavras erradas; 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **pl->en**: transcrição ruim: 37% das palavras erradas
- **uk->en**: transcrição ruim: 46% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **tr->en**: transcrição ruim: 44% das palavras erradas; inventou 9 palavras que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 3.5 s
- **ar->en**: transcrição ruim: 49% das palavras erradas
- **hi->en**: transcrição ruim: 99% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 10 palavras seguidas); não acompanha o falante: atraso típico 1.2 s, sobe -1.4 s da 1ª para a 2ª metade e sobram 10 s de tradução quando ele para
- **ja->en**: transcrição ruim: 32% dos caracteres erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.3 s
- **ko->en**: transcrição ruim: 44% das palavras erradas; inventou 7 palavras que não foram faladas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa

Error rate = share of words (characters for zh/ja) transcribed wrong, skipped or invented. Translation fidelity compares the translation of what was heard with the translation of the true script. Latency = end of a speech segment → first translated audio. Lag growth ≈ 0 means it keeps pace.
