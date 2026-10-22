_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `large-v3-turbo` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 14s | 9.1% palavras | 1.5% | 82.3 | 11.0 s | 11.1 s | +1.9 s | 13.2 s | 60% | ❌ |
| en->pt | 14s | 4.7% palavras | 5.9% | 80.3 | 7.6 s | 8.2 s | +1.3 s | 9.1 s | 74% | ❌ |
| es->en | 12s | 0.0% palavras | 0.0% | 88.3 | 11.2 s | 14.6 s | +6.5 s | 12.8 s | 42% | ❌ |
| fr->en | 14s | 0.0% palavras | 0.0% | 74.9 | 8.1 s | 9.6 s | +3.2 s | 5.4 s | 43% | ❌ |
| de->en | 14s | 4.2% palavras | 2.2% | 60.9 | 11.2 s | 16.1 s | +7.3 s | 12.6 s | 30% | ❌ |
| it->en | 16s | 21.6% palavras | 4.2% | 51.0 | 10.6 s | 11.8 s | +3.1 s | 13.4 s | 73% | ❌ |
| ru->en | 17s | 4.8% palavras | 1.5% | 56.4 | 8.5 s | 9.5 s | +2.2 s | 5.8 s | 40% | ❌ |
| zh->en | 15s | 12.0% caracteres | 12.0% | 53.8 | 8.3 s | 8.9 s | +1.5 s | 8.3 s | 62% | ❌ |
| nl->en | 15s | 25.9% palavras | 13.2% | 69.2 | 6.5 s | 6.8 s | +0.7 s | 3.7 s | 37% | ❌ |
| pl->en | 15s | 0.0% palavras | 0.0% | 63.4 | 10.1 s | 12.9 s | +4.6 s | 11.5 s | 60% | ❌ |
| uk->en | 15s | 4.2% palavras | 2.0% | 97.1 | 6.6 s | 6.6 s | +0.0 s | 2.4 s | 30% | ❌ |
| tr->en | 14s | 19.1% palavras | 9.6% | 57.4 | 7.4 s | 7.4 s | +0.0 s | 4.1 s | 25% | ❌ |
| ar->en | 15s | 3.5% palavras | 2.5% | 82.6 | 7.4 s | 7.7 s | +0.8 s | 8.4 s | 48% | ❌ |
| hi->en | 15s | 41.4% palavras | 16.7% | 27.0 | 15.3 s | 21.4 s | +9.5 s | 21.6 s | 47% | ❌ |
| ja->en | 14s | 0.0% caracteres | 0.0% | 71.4 | 7.6 s | 7.6 s | +0.0 s | 6.1 s | 33% | ❌ |
| ko->en | 12s | 10.0% caracteres | 10.0% | 55.2 | 8.0 s | 8.0 s | +0.0 s | 5.6 s | 33% | ❌ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 4775 ms | 5776 ms | 20 ms | 52 ms | 0 ms |
| en->pt | 822 ms | 6045 ms | 28 ms | 80 ms | 0 ms |
| es->en | 6863 ms | 5943 ms | 23 ms | 38 ms | 0 ms |
| fr->en | 3107 ms | 6093 ms | 30 ms | 74 ms | 0 ms |
| de->en | 6611 ms | 5936 ms | 18 ms | 31 ms | 0 ms |
| it->en | 4325 ms | 6073 ms | 22 ms | 71 ms | 0 ms |
| ru->en | 3078 ms | 6066 ms | 22 ms | 46 ms | 0 ms |
| zh->en | 1463 ms | 6353 ms | 35 ms | 81 ms | 0 ms |
| nl->en | 0 ms | 6151 ms | 31 ms | 76 ms | 0 ms |
| pl->en | 5227 ms | 6113 ms | 29 ms | 64 ms | 0 ms |
| uk->en | 0 ms | 6190 ms | 34 ms | 87 ms | 0 ms |
| tr->en | 1489 ms | 6042 ms | 26 ms | 73 ms | 0 ms |
| ar->en | 663 ms | 6196 ms | 25 ms | 71 ms | 0 ms |
| hi->en | 10096 ms | 6141 ms | 13 ms | 29 ms | 0 ms |
| ja->en | 2048 ms | 6208 ms | 35 ms | 80 ms | 0 ms |
| ko->en | 1295 ms | 6169 ms | 41 ms | 93 ms | 0 ms |

### Problemas encontrados

- **pt->en**: não acompanha o falante: atraso típico 11.0 s, sobe +1.9 s da 1ª para a 2ª metade e sobram 13 s de tradução quando ele para; trechos esperam 4775 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **en->pt**: não acompanha o falante: atraso típico 7.6 s, sobe +1.3 s da 1ª para a 2ª metade e sobram 9 s de tradução quando ele para; trechos esperam 822 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **es->en**: não acompanha o falante: atraso típico 11.2 s, sobe +6.5 s da 1ª para a 2ª metade e sobram 13 s de tradução quando ele para; trechos esperam 6863 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **fr->en**: não acompanha o falante: atraso típico 8.1 s, sobe +3.2 s da 1ª para a 2ª metade e sobram 5 s de tradução quando ele para; trechos esperam 3107 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **de->en**: não acompanha o falante: atraso típico 11.2 s, sobe +7.3 s da 1ª para a 2ª metade e sobram 13 s de tradução quando ele para; trechos esperam 6611 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **it->en**: transcrição ruim: 22% das palavras erradas; não acompanha o falante: atraso típico 10.6 s, sobe +3.1 s da 1ª para a 2ª metade e sobram 13 s de tradução quando ele para; trechos esperam 4325 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ru->en**: não acompanha o falante: atraso típico 8.5 s, sobe +2.2 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para; trechos esperam 3078 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **zh->en**: não acompanha o falante: atraso típico 8.3 s, sobe +1.5 s da 1ª para a 2ª metade e sobram 8 s de tradução quando ele para; trechos esperam 1463 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **nl->en**: transcrição ruim: 26% das palavras erradas; não acompanha o falante: atraso típico 6.5 s, sobe +0.7 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para
- **pl->en**: não acompanha o falante: atraso típico 10.1 s, sobe +4.6 s da 1ª para a 2ª metade e sobram 12 s de tradução quando ele para; trechos esperam 5227 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **uk->en**: não acompanha o falante: atraso típico 6.6 s, sobe +0.0 s da 1ª para a 2ª metade e sobram 2 s de tradução quando ele para; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **tr->en**: não acompanha o falante: atraso típico 7.4 s, sobe +0.0 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para; trechos esperam 1489 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ar->en**: não acompanha o falante: atraso típico 7.4 s, sobe +0.8 s da 1ª para a 2ª metade e sobram 8 s de tradução quando ele para; trechos esperam 663 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **hi->en**: transcrição ruim: 41% das palavras erradas; não acompanha o falante: atraso típico 15.3 s, sobe +9.5 s da 1ª para a 2ª metade e sobram 22 s de tradução quando ele para; trechos esperam 10096 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ja->en**: não acompanha o falante: atraso típico 7.6 s, sobe +0.0 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para; trechos esperam 2048 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ko->en**: não acompanha o falante: atraso típico 8.0 s, sobe +0.0 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para; trechos esperam 1295 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
