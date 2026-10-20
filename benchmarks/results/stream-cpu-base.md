_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · Python 3.12.3 · CUDA True_

Whisper `base` on `cpu` — ~1 min of continuous real speech per pair, fed in real time

| Pair | Speech | Error rate | Translation fidelity (0–100) | Typical latency | 1-in-20 worst | Lag growth (2nd vs 1st half) | Backlog when speaker stops | Translated / original speech | Keeps up |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 71s | 13.8% words | 65.0 | 1.1 s | 3.3 s | -0.0 s | 4.3 s | 69% | ✅ |
| en->pt | 72s | 6.3% words | 66.6 | 1.0 s | 2.7 s | -0.5 s | 4.3 s | 76% | ✅ |
| es->en | 73s | 12.5% words | 64.8 | 0.9 s | 2.5 s | +0.1 s | 1.8 s | 59% | ✅ |
| fr->en | 62s | 34.8% words | 57.4 | 1.4 s | 4.1 s | +0.4 s | 4.0 s | 72% | ✅ |
| de->en | 63s | 46.2% words | 53.6 | 0.9 s | 2.8 s | +0.0 s | 2.0 s | 58% | ✅ |
| it->en | 78s | 40.7% words | 53.2 | 1.6 s | 4.2 s | -0.4 s | 3.5 s | 69% | ✅ |
| ru->en | 66s | 28.4% words | 62.4 | 1.8 s | 5.2 s | -0.1 s | 3.4 s | 56% | ✅ |
| zh->en | 62s | 34.7% chars | 34.4 | 1.5 s | 3.5 s | +0.3 s | 1.6 s | 57% | ✅ |
| nl->en | 66s | 29.2% words | 49.0 | 0.8 s | 2.7 s | -0.1 s | 3.8 s | 62% | ✅ |
| pl->en | 69s | 40.5% words | 54.7 | 1.2 s | 3.2 s | +0.6 s | 3.8 s | 79% | ✅ |
| uk->en | 69s | 45.5% words | 48.6 | 0.8 s | 3.1 s | -1.0 s | 3.6 s | 58% | ✅ |
| tr->en | 72s | 46.4% words | 59.1 | 1.4 s | 3.8 s | -1.0 s | 4.1 s | 52% | ✅ |
| ar->en | 74s | 51.6% words | 48.2 | 1.7 s | 3.3 s | -0.0 s | 3.6 s | 57% | ✅ |
| hi->en | 69s | 100.0% words | 17.1 | 1.7 s | 35.2 s | +0.3 s | 74.8 s | 185% | ❌ |
| ja->en | 64s | 32.8% chars | 47.6 | 1.7 s | 3.5 s | -0.6 s | 2.2 s | 45% | ✅ |
| ko->en | 69s | 67.4% words | 51.0 | 2.2 s | 3.0 s | +0.1 s | 3.3 s | 55% | ✅ |

### Where the time goes (typical, per segment)

| Pair | Waiting in queue | Transcription | Translation | Voice (1st sentence) | Waiting for previous speech |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 448 ms | 28 ms | 75 ms | 0 ms |
| en->pt | 0 ms | 440 ms | 30 ms | 69 ms | 0 ms |
| es->en | 0 ms | 414 ms | 28 ms | 46 ms | 0 ms |
| fr->en | 0 ms | 457 ms | 26 ms | 59 ms | 0 ms |
| de->en | 0 ms | 404 ms | 21 ms | 32 ms | 0 ms |
| it->en | 0 ms | 457 ms | 20 ms | 54 ms | 0 ms |
| ru->en | 0 ms | 463 ms | 27 ms | 71 ms | 0 ms |
| zh->en | 0 ms | 443 ms | 19 ms | 63 ms | 0 ms |
| nl->en | 0 ms | 464 ms | 29 ms | 59 ms | 0 ms |
| pl->en | 0 ms | 479 ms | 32 ms | 63 ms | 0 ms |
| uk->en | 0 ms | 460 ms | 23 ms | 54 ms | 0 ms |
| tr->en | 0 ms | 462 ms | 24 ms | 46 ms | 0 ms |
| ar->en | 0 ms | 496 ms | 25 ms | 58 ms | 0 ms |
| hi->en | 0 ms | 420 ms | 21 ms | 46 ms | 441 ms |
| ja->en | 0 ms | 497 ms | 33 ms | 85 ms | 0 ms |
| ko->en | 0 ms | 495 ms | 29 ms | 69 ms | 0 ms |

### Problems found

- **pt->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.3 s
- **en->pt**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **es->en**: nenhum problema detectado
- **fr->en**: transcrição ruim: 35% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.1 s
- **de->en**: transcrição ruim: 46% das palavras erradas; inventou 9 palavras que não foram faladas; 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **it->en**: transcrição ruim: 41% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 4.2 s
- **ru->en**: transcrição ruim: 28% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 5.2 s
- **zh->en**: transcrição ruim: 35% dos caracteres erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.5 s
- **nl->en**: transcrição ruim: 29% das palavras erradas; 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **pl->en**: transcrição ruim: 41% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.2 s
- **uk->en**: transcrição ruim: 45% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 3.1 s
- **tr->en**: transcrição ruim: 46% das palavras erradas; inventou 10 palavras que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 3.8 s
- **ar->en**: transcrição ruim: 52% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.3 s
- **hi->en**: transcrição ruim: 100% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 8 palavras seguidas); não acompanha o falante: atraso típico 1.7 s, sobe +0.3 s da 1ª para a 2ª metade e sobram 75 s de tradução quando ele para; a fala traduzida dura 185% da original — quase não sobra folga para acompanhar
- **ja->en**: transcrição ruim: 33% dos caracteres erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.5 s
- **ko->en**: transcrição ruim: 67% das palavras erradas; inventou 24 palavras que não foram faladas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa

Error rate = share of words (characters for zh/ja) transcribed wrong, skipped or invented. Translation fidelity compares the translation of what was heard with the translation of the true script. Latency = end of a speech segment → first translated audio. Lag growth ≈ 0 means it keeps pace.
