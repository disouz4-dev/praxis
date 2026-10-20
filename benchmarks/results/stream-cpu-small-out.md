_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · Python 3.12.3 · CUDA True_

Whisper `small` on `cpu` — ~1 min of continuous real speech per pair, fed in real time

| Pair | Speech | Error rate | Translation fidelity (0–100) | Typical latency | 1-in-20 worst | Lag growth (2nd vs 1st half) | Backlog when speaker stops | Translated / original speech | Keeps up |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| en->pt | 72s | 3.2% words | 72.8 | 1.9 s | 4.0 s | -0.4 s | 5.6 s | 80% | ✅ |
| en->es | 72s | 3.2% words | 75.8 | 1.9 s | 3.8 s | -0.1 s | 6.1 s | 83% | ✅ |
| en->fr | 72s | 3.2% words | 73.8 | 1.9 s | 3.9 s | -0.4 s | 5.7 s | 79% | ✅ |
| en->de | 72s | 3.2% words | 69.2 | 3.9 s | 7.0 s | -1.0 s | 38.6 s | 146% | ❌ |
| en->it | 72s | 3.2% words | 76.0 | 1.9 s | 3.9 s | -0.4 s | 5.6 s | 75% | ✅ |
| en->ru | 72s | 3.2% words | 70.4 | 2.0 s | 3.7 s | -0.5 s | 5.6 s | 76% | ✅ |
| en->zh | 72s | 3.2% words | 27.3 | 2.0 s | 5.2 s | -0.5 s | 5.6 s | 76% | ✅ |
| en->nl | 72s | 3.2% words | 72.5 | 3.5 s | 5.7 s | -1.1 s | 11.0 s | 108% | ❌ |
| en->pl | 72s | 3.2% words | 68.9 | 2.6 s | 4.3 s | -0.7 s | 7.6 s | 89% | ✅ |
| en->uk | 72s | 3.2% words | 64.3 | 2.0 s | 4.3 s | -0.5 s | 7.7 s | 89% | ✅ |
| en->tr | 72s | 3.2% words | 57.2 | 1.9 s | 4.5 s | -0.7 s | 5.1 s | 80% | ✅ |
| en->ar | 72s | 3.2% words | 53.3 | 4.9 s | 6.5 s | +0.9 s | 12.2 s | 107% | ❌ |
| en->hi | 72s | 3.2% words | 65.6 | 2.8 s | 7.2 s | -1.5 s | 9.1 s | 101% | ❌ |

### Where the time goes (typical, per segment)

| Pair | Waiting in queue | Transcription | Translation | Voice (1st sentence) | Waiting for previous speech |
|---|---:|---:|---:|---:|---:|
| en->pt | 0 ms | 1305 ms | 31 ms | 68 ms | 0 ms |
| en->es | 0 ms | 1275 ms | 27 ms | 89 ms | 0 ms |
| en->fr | 0 ms | 1295 ms | 35 ms | 80 ms | 0 ms |
| en->de | 0 ms | 1323 ms | 41 ms | 121 ms | 1848 ms |
| en->it | 0 ms | 1319 ms | 28 ms | 74 ms | 0 ms |
| en->ru | 0 ms | 1326 ms | 57 ms | 85 ms | 0 ms |
| en->zh | 0 ms | 1313 ms | 24 ms | 92 ms | 0 ms |
| en->nl | 0 ms | 1320 ms | 32 ms | 90 ms | 1378 ms |
| en->pl | 0 ms | 1322 ms | 32 ms | 89 ms | 1 ms |
| en->uk | 0 ms | 1305 ms | 37 ms | 56 ms | 1 ms |
| en->tr | 0 ms | 1314 ms | 26 ms | 75 ms | 0 ms |
| en->ar | 0 ms | 1331 ms | 24 ms | 134 ms | 2974 ms |
| en->hi | 0 ms | 1324 ms | 31 ms | 84 ms | 824 ms |

### Problems found

- **en->pt**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **en->es**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.8 s
- **en->fr**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.9 s
- **en->de**: não acompanha o falante: atraso típico 3.9 s, sobe -1.0 s da 1ª para a 2ª metade e sobram 39 s de tradução quando ele para; a tradução pronta espera 1848 ms a fala anterior terminar de tocar; a fala traduzida dura 146% da original — quase não sobra folga para acompanhar; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **en->it**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.9 s
- **en->ru**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **en->zh**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 5.2 s
- **en->nl**: não acompanha o falante: atraso típico 3.5 s, sobe -1.1 s da 1ª para a 2ª metade e sobram 11 s de tradução quando ele para; a tradução pronta espera 1378 ms a fala anterior terminar de tocar; a fala traduzida dura 108% da original — quase não sobra folga para acompanhar; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **en->pl**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 4.3 s
- **en->uk**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 4.3 s
- **en->tr**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 4.5 s
- **en->ar**: não acompanha o falante: atraso típico 4.9 s, sobe +0.9 s da 1ª para a 2ª metade e sobram 12 s de tradução quando ele para; a tradução pronta espera 2974 ms a fala anterior terminar de tocar; a fala traduzida dura 107% da original — quase não sobra folga para acompanhar; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **en->hi**: não acompanha o falante: atraso típico 2.8 s, sobe -1.5 s da 1ª para a 2ª metade e sobram 9 s de tradução quando ele para; a tradução pronta espera 824 ms a fala anterior terminar de tocar; a fala traduzida dura 101% da original — quase não sobra folga para acompanhar; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa

Error rate = share of words (characters for zh/ja) transcribed wrong, skipped or invented. Translation fidelity compares the translation of what was heard with the translation of the true script. Latency = end of a speech segment → first translated audio. Lag growth ≈ 0 means it keeps pace.
