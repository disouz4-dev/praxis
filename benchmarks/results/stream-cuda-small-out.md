_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · Python 3.12.3 · CUDA True_

Whisper `small` on `cuda` — ~1 min of continuous real speech per pair, fed in real time

| Pair | Speech | Error rate | Translation fidelity (0–100) | Typical latency | 1-in-20 worst | Lag growth (2nd vs 1st half) | Backlog when speaker stops | Translated / original speech | Keeps up |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| en->pt | 72s | 2.1% words | 72.2 | 0.8 s | 2.8 s | -0.5 s | 4.4 s | 79% | ✅ |
| en->es | 72s | 2.1% words | 75.7 | 0.8 s | 2.8 s | -0.5 s | 5.1 s | 84% | ✅ |
| en->fr | 72s | 2.1% words | 74.4 | 0.8 s | 2.8 s | -0.5 s | 4.8 s | 79% | ✅ |
| en->de | 72s | 2.1% words | 69.3 | 1.0 s | 2.8 s | -0.4 s | 4.7 s | 82% | ✅ |
| en->it | 72s | 2.1% words | 75.8 | 0.8 s | 2.6 s | -0.5 s | 4.5 s | 76% | ✅ |
| en->ru | 72s | 2.1% words | 70.4 | 0.8 s | 2.5 s | -0.5 s | 4.5 s | 76% | ✅ |
| en->zh | 72s | 2.1% words | 27.0 | 0.8 s | 4.0 s | -0.5 s | 4.4 s | 75% | ✅ |
| en->nl | 72s | 2.1% words | 72.8 | 3.6 s | 5.3 s | +3.1 s | 12.5 s | 111% | ❌ |
| en->pl | 72s | 2.1% words | 67.5 | 1.2 s | 3.2 s | -0.6 s | 6.7 s | 89% | ✅ |
| en->uk | 72s | 2.1% words | 65.4 | 1.0 s | 2.9 s | -0.2 s | 6.1 s | 88% | ✅ |
| en->tr | 72s | 2.1% words | 59.0 | 0.8 s | 3.3 s | -0.5 s | 4.2 s | 79% | ✅ |
| en->ar | 72s | 2.1% words | 53.7 | 2.8 s | 3.7 s | +0.8 s | 9.9 s | 105% | ❌ |
| en->hi | 72s | 2.1% words | 66.0 | 1.2 s | 6.0 s | -1.8 s | 8.0 s | 101% | ✅ |

### Where the time goes (typical, per segment)

| Pair | Waiting in queue | Transcription | Translation | Voice (1st sentence) | Waiting for previous speech |
|---|---:|---:|---:|---:|---:|
| en->pt | 0 ms | 173 ms | 30 ms | 73 ms | 0 ms |
| en->es | 0 ms | 172 ms | 28 ms | 84 ms | 0 ms |
| en->fr | 0 ms | 174 ms | 32 ms | 76 ms | 0 ms |
| en->de | 0 ms | 170 ms | 40 ms | 379 ms | 0 ms |
| en->it | 0 ms | 176 ms | 27 ms | 71 ms | 0 ms |
| en->ru | 0 ms | 174 ms | 52 ms | 76 ms | 0 ms |
| en->zh | 0 ms | 173 ms | 25 ms | 87 ms | 0 ms |
| en->nl | 0 ms | 175 ms | 30 ms | 96 ms | 2500 ms |
| en->pl | 0 ms | 173 ms | 30 ms | 80 ms | 1 ms |
| en->uk | 0 ms | 172 ms | 34 ms | 52 ms | 0 ms |
| en->tr | 0 ms | 172 ms | 24 ms | 75 ms | 0 ms |
| en->ar | 0 ms | 170 ms | 25 ms | 128 ms | 1585 ms |
| en->hi | 0 ms | 171 ms | 32 ms | 98 ms | 311 ms |

### Problems found

- **en->pt**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **en->es**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **en->fr**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **en->de**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **en->it**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **en->ru**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **en->zh**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **en->nl**: não acompanha o falante: atraso típico 3.6 s, sobe +3.1 s da 1ª para a 2ª metade e sobram 13 s de tradução quando ele para; a tradução pronta espera 2500 ms a fala anterior terminar de tocar; a fala traduzida dura 111% da original — quase não sobra folga para acompanhar; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **en->pl**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.2 s
- **en->uk**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **en->tr**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.3 s
- **en->ar**: não acompanha o falante: atraso típico 2.8 s, sobe +0.8 s da 1ª para a 2ª metade e sobram 10 s de tradução quando ele para; a tradução pronta espera 1585 ms a fala anterior terminar de tocar; a fala traduzida dura 105% da original — quase não sobra folga para acompanhar; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **en->hi**: a fala traduzida dura 101% da original — quase não sobra folga para acompanhar; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 6.0 s

Error rate = share of words (characters for zh/ja) transcribed wrong, skipped or invented. Translation fidelity compares the translation of what was heard with the translation of the true script. Latency = end of a speech segment → first translated audio. Lag growth ≈ 0 means it keeps pace.
