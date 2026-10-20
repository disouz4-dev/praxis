_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `large-v3-turbo` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 7.0% palavras | 4.0% | 78.4 | 10.6 s | 11.4 s | +3.5 s | 13.2 s | 65% | ❌ |
| en->pt | 20s | 3.7% palavras | 4.3% | 83.2 | 6.7 s | 7.8 s | +1.4 s | 5.3 s | 66% | ❌ |
| es->en | 21s | 4.4% palavras | 1.1% | 55.5 | 6.9 s | 8.7 s | +2.7 s | 6.9 s | 43% | ❌ |
| fr->en | 21s | 3.6% palavras | 1.6% | 68.8 | 6.7 s | 10.1 s | +1.9 s | 8.3 s | 62% | ❌ |
| de->en | 19s | 11.8% palavras | 2.2% | 68.2 | 11.3 s | 13.1 s | +3.2 s | 10.4 s | 40% | ❌ |
| it->en | 20s | 6.4% palavras | 2.6% | 58.9 | 9.5 s | 13.0 s | +3.9 s | 9.2 s | 54% | ❌ |
| ru->en | 19s | 11.5% palavras | 7.1% | 65.9 | 8.0 s | 8.2 s | +1.9 s | 8.7 s | 54% | ❌ |
| zh->en | 19s | 2.3% caracteres | 2.3% | 64.9 | 8.3 s | 9.9 s | +1.1 s | 7.2 s | 35% | ❌ |
| nl->en | 22s | 14.6% palavras | 4.9% | 72.1 | 11.0 s | 14.1 s | +6.7 s | 15.9 s | 80% | ❌ |
| pl->en | 18s | 2.6% palavras | 0.5% | 48.6 | 5.9 s | 6.4 s | +0.8 s | 5.1 s | 59% | ❌ |
| uk->en | 19s | 2.9% palavras | 1.6% | 78.3 | 11.9 s | 14.2 s | +3.6 s | 12.0 s | 60% | ❌ |
| tr->en | 17s | 0.0% palavras | 0.0% | 67.0 | 6.6 s | 6.8 s | +0.6 s | 3.5 s | 30% | ❌ |
| ar->en | 19s | 10.0% palavras | 3.2% | 60.1 | 6.7 s | 7.1 s | +0.1 s | 6.3 s | 54% | ❌ |
| hi->en | 20s | 34.2% palavras | 12.4% | 50.1 | 14.0 s | 21.4 s | +9.1 s | 17.1 s | 40% | ❌ |
| ja->en | 25s | 14.8% caracteres | 14.8% | 56.6 | 6.7 s | 8.7 s | -1.9 s | 7.4 s | 49% | ❌ |
| ko->en | 20s | 2.7% caracteres | 2.7% | 50.9 | 8.2 s | 9.3 s | +1.3 s | 1.1 s | 36% | ❌ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 5295 ms | 5440 ms | 26 ms | 67 ms | 0 ms |
| en->pt | 1003 ms | 5108 ms | 30 ms | 84 ms | 0 ms |
| es->en | 2136 ms | 5091 ms | 28 ms | 52 ms | 0 ms |
| fr->en | 1318 ms | 5254 ms | 32 ms | 66 ms | 0 ms |
| de->en | 7082 ms | 5211 ms | 32 ms | 45 ms | 0 ms |
| it->en | 4236 ms | 5207 ms | 21 ms | 63 ms | 0 ms |
| ru->en | 1472 ms | 5464 ms | 29 ms | 75 ms | 0 ms |
| zh->en | 1249 ms | 5350 ms | 17 ms | 32 ms | 0 ms |
| nl->en | 6406 ms | 5365 ms | 28 ms | 52 ms | 0 ms |
| pl->en | 323 ms | 5398 ms | 34 ms | 84 ms | 0 ms |
| uk->en | 8269 ms | 5337 ms | 25 ms | 61 ms | 0 ms |
| tr->en | 1187 ms | 5308 ms | 18 ms | 50 ms | 0 ms |
| ar->en | 631 ms | 5335 ms | 27 ms | 67 ms | 0 ms |
| hi->en | 9004 ms | 5426 ms | 15 ms | 34 ms | 0 ms |
| ja->en | 0 ms | 5337 ms | 38 ms | 96 ms | 0 ms |
| ko->en | 0 ms | 5389 ms | 38 ms | 90 ms | 0 ms |

### Problemas encontrados

- **pt->en**: não acompanha o falante: atraso típico 10.6 s, sobe +3.5 s da 1ª para a 2ª metade e sobram 13 s de tradução quando ele para; trechos esperam 5295 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **en->pt**: não acompanha o falante: atraso típico 6.7 s, sobe +1.4 s da 1ª para a 2ª metade e sobram 5 s de tradução quando ele para; trechos esperam 1003 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **es->en**: não acompanha o falante: atraso típico 6.9 s, sobe +2.7 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para; trechos esperam 2136 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **fr->en**: não acompanha o falante: atraso típico 6.7 s, sobe +1.9 s da 1ª para a 2ª metade e sobram 8 s de tradução quando ele para; trechos esperam 1318 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **de->en**: não acompanha o falante: atraso típico 11.3 s, sobe +3.2 s da 1ª para a 2ª metade e sobram 10 s de tradução quando ele para; trechos esperam 7082 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **it->en**: não acompanha o falante: atraso típico 9.5 s, sobe +3.9 s da 1ª para a 2ª metade e sobram 9 s de tradução quando ele para; trechos esperam 4236 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ru->en**: não acompanha o falante: atraso típico 8.0 s, sobe +1.9 s da 1ª para a 2ª metade e sobram 9 s de tradução quando ele para; trechos esperam 1472 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **zh->en**: não acompanha o falante: atraso típico 8.3 s, sobe +1.1 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para; trechos esperam 1249 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **nl->en**: não acompanha o falante: atraso típico 11.0 s, sobe +6.7 s da 1ª para a 2ª metade e sobram 16 s de tradução quando ele para; trechos esperam 6406 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **pl->en**: não acompanha o falante: atraso típico 5.9 s, sobe +0.8 s da 1ª para a 2ª metade e sobram 5 s de tradução quando ele para
- **uk->en**: não acompanha o falante: atraso típico 11.9 s, sobe +3.6 s da 1ª para a 2ª metade e sobram 12 s de tradução quando ele para; trechos esperam 8269 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **tr->en**: não acompanha o falante: atraso típico 6.6 s, sobe +0.6 s da 1ª para a 2ª metade e sobram 3 s de tradução quando ele para; trechos esperam 1187 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ar->en**: não acompanha o falante: atraso típico 6.7 s, sobe +0.1 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para; trechos esperam 631 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **hi->en**: transcrição ruim: 34% das palavras erradas; não acompanha o falante: atraso típico 14.0 s, sobe +9.1 s da 1ª para a 2ª metade e sobram 17 s de tradução quando ele para; trechos esperam 9004 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ja->en**: não acompanha o falante: atraso típico 6.7 s, sobe -1.9 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para
- **ko->en**: não acompanha o falante: atraso típico 8.2 s, sobe +1.3 s da 1ª para a 2ª metade e sobram 1 s de tradução quando ele para; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
