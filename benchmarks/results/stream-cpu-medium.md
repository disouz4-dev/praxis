_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `medium` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 71s | 4.8% palavras | 1.5% | 74.0 | 5.6 s | 7.0 s | -0.3 s | 2.6 s | 67% | ❌ |
| en->pt | 72s | 4.7% palavras | 3.9% | 73.6 | 4.2 s | 7.1 s | -0.5 s | 7.6 s | 80% | ❌ |
| es->en | 73s | 4.6% palavras | 1.3% | 69.0 | 6.5 s | 9.6 s | +3.7 s | 7.0 s | 60% | ❌ |
| fr->en | 62s | 17.1% palavras | 9.6% | 61.5 | 5.9 s | 8.8 s | +1.8 s | 4.0 s | 70% | ❌ |
| de->en | 63s | 18.9% palavras | 5.4% | 64.9 | 7.7 s | 10.4 s | +3.9 s | 9.3 s | 59% | ❌ |
| it->en | 78s | 26.0% palavras | 10.8% | 58.5 | 5.5 s | 8.7 s | +0.3 s | 4.0 s | 66% | ❌ |
| ru->en | 66s | 9.1% palavras | 2.9% | 76.9 | 5.2 s | 9.0 s | -0.1 s | 6.5 s | 57% | ❌ |
| zh->en | 62s | 12.8% caracteres | 12.8% | 35.3 | 5.5 s | 7.2 s | -1.0 s | 5.6 s | 59% | ❌ |
| nl->en | 66s | 17.0% palavras | 7.3% | 57.0 | 4.3 s | 6.3 s | +0.0 s | 7.4 s | 64% | ❌ |
| pl->en | 69s | 10.1% palavras | 1.6% | 63.4 | 6.6 s | 8.3 s | +0.2 s | 9.3 s | 79% | ❌ |
| uk->en | 69s | 14.1% palavras | 6.1% | 72.4 | 7.4 s | 9.8 s | +2.6 s | 9.0 s | 62% | ❌ |
| tr->en | 72s | 15.5% palavras | 4.6% | 64.9 | 5.2 s | 7.6 s | -0.2 s | 2.5 s | 44% | ❌ |
| ar->en | 74s | 18.8% palavras | 8.9% | 68.8 | 5.3 s | 7.4 s | -0.5 s | 6.6 s | 61% | ❌ |
| hi->en | 69s | 37.6% palavras | 15.2% | 42.9 | 16.0 s | 24.7 s | +10.8 s | 22.9 s | 57% | ❌ |
| ja->en | 64s | 14.4% caracteres | 14.4% | 59.1 | 5.7 s | 8.3 s | -0.4 s | 5.7 s | 53% | ❌ |
| ko->en | 69s | 7.4% caracteres | 7.4% | 60.7 | 5.7 s | 7.5 s | +0.8 s | 7.4 s | 58% | ❌ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 1268 ms | 3514 ms | 26 ms | 66 ms | 0 ms |
| en->pt | 0 ms | 3566 ms | 31 ms | 88 ms | 0 ms |
| es->en | 2383 ms | 3355 ms | 27 ms | 43 ms | 0 ms |
| fr->en | 1510 ms | 3619 ms | 27 ms | 62 ms | 0 ms |
| de->en | 3617 ms | 3410 ms | 21 ms | 29 ms | 0 ms |
| it->en | 1248 ms | 3702 ms | 22 ms | 54 ms | 0 ms |
| ru->en | 52 ms | 3723 ms | 28 ms | 61 ms | 0 ms |
| zh->en | 0 ms | 3630 ms | 24 ms | 62 ms | 0 ms |
| nl->en | 0 ms | 3755 ms | 30 ms | 73 ms | 0 ms |
| pl->en | 2277 ms | 3841 ms | 32 ms | 72 ms | 0 ms |
| uk->en | 3185 ms | 3753 ms | 23 ms | 59 ms | 0 ms |
| tr->en | 616 ms | 3717 ms | 22 ms | 67 ms | 0 ms |
| ar->en | 0 ms | 4069 ms | 25 ms | 76 ms | 0 ms |
| hi->en | 13073 ms | 4203 ms | 16 ms | 39 ms | 0 ms |
| ja->en | 0 ms | 4038 ms | 31 ms | 76 ms | 0 ms |
| ko->en | 0 ms | 3829 ms | 28 ms | 76 ms | 1 ms |

### Problemas encontrados

- **pt->en**: não acompanha o falante: atraso típico 5.6 s, sobe -0.3 s da 1ª para a 2ª metade e sobram 3 s de tradução quando ele para; trechos esperam 1268 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **en->pt**: não acompanha o falante: atraso típico 4.2 s, sobe -0.5 s da 1ª para a 2ª metade e sobram 8 s de tradução quando ele para; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **es->en**: não acompanha o falante: atraso típico 6.5 s, sobe +3.7 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para; trechos esperam 2383 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **fr->en**: não acompanha o falante: atraso típico 5.9 s, sobe +1.8 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para; trechos esperam 1510 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **de->en**: não acompanha o falante: atraso típico 7.7 s, sobe +3.9 s da 1ª para a 2ª metade e sobram 9 s de tradução quando ele para; trechos esperam 3617 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **it->en**: transcrição ruim: 26% das palavras erradas; inventou 11 palavras que não foram faladas; não acompanha o falante: atraso típico 5.5 s, sobe +0.3 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para; trechos esperam 1248 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **ru->en**: não acompanha o falante: atraso típico 5.2 s, sobe -0.1 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para
- **zh->en**: não acompanha o falante: atraso típico 5.5 s, sobe -1.0 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para
- **nl->en**: não acompanha o falante: atraso típico 4.3 s, sobe +0.0 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para; 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **pl->en**: não acompanha o falante: atraso típico 6.6 s, sobe +0.2 s da 1ª para a 2ª metade e sobram 9 s de tradução quando ele para; trechos esperam 2277 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **uk->en**: não acompanha o falante: atraso típico 7.4 s, sobe +2.6 s da 1ª para a 2ª metade e sobram 9 s de tradução quando ele para; trechos esperam 3185 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **tr->en**: não acompanha o falante: atraso típico 5.2 s, sobe -0.2 s da 1ª para a 2ª metade e sobram 3 s de tradução quando ele para; trechos esperam 616 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ar->en**: não acompanha o falante: atraso típico 5.3 s, sobe -0.5 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para; 1 trecho(s) com fala viraram texto vazio
- **hi->en**: transcrição ruim: 38% das palavras erradas; não acompanha o falante: atraso típico 16.0 s, sobe +10.8 s da 1ª para a 2ª metade e sobram 23 s de tradução quando ele para; trechos esperam 13073 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ja->en**: não acompanha o falante: atraso típico 5.7 s, sobe -0.4 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para
- **ko->en**: não acompanha o falante: atraso típico 5.7 s, sobe +0.8 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
