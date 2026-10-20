_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `medium` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 12.1% palavras | 6.0% | 65.8 | 5.9 s | 7.4 s | +2.1 s | 6.7 s | 51% | ❌ |
| en->pt | 19s | 9.3% palavras | 9.6% | 47.9 | 9.3 s | 15.3 s | +7.1 s | 16.2 s | 69% | ❌ |
| es->en | 16s | 19.2% palavras | 9.6% | 57.6 | 5.7 s | 6.8 s | +2.9 s | 6.1 s | 42% | ❌ |
| fr->en | 19s | 12.5% palavras | 9.8% | 62.2 | 5.4 s | 7.9 s | +0.5 s | 7.0 s | 57% | ❌ |
| de->en | 19s | 29.2% palavras | 10.2% | 50.5 | 5.7 s | 6.0 s | +0.6 s | 4.8 s | 39% | ❌ |
| it->en | 21s | 24.3% palavras | 7.1% | 53.8 | 4.2 s | 4.9 s | +0.6 s | 2.3 s | 54% | ❌ |
| ru->en | 22s | 4.8% palavras | 1.5% | 56.4 | 4.8 s | 5.0 s | -0.2 s | 1.8 s | 38% | ❌ |
| zh->en | 20s | 20.5% caracteres | 20.5% | 50.0 | 6.8 s | 10.3 s | +3.7 s | 11.0 s | 81% | ❌ |
| nl->en | 20s | 22.2% palavras | 14.9% | 62.9 | 4.5 s | 4.7 s | +0.0 s | 0.0 s | 27% | ❌ |
| pl->en | 21s | 16.2% palavras | 3.8% | 58.6 | 5.0 s | 6.0 s | -0.8 s | 7.0 s | 65% | ❌ |
| uk->en | 20s | 4.2% palavras | 1.4% | 47.2 | 5.9 s | 7.3 s | -0.2 s | 6.0 s | 45% | ❌ |
| tr->en | 19s | 19.1% palavras | 9.6% | 57.2 | 6.2 s | 6.2 s | +2.0 s | 4.1 s | 36% | ❌ |
| ar->en | 20s | 13.8% palavras | 10.9% | 59.0 | 7.5 s | 8.9 s | +3.3 s | 6.4 s | 34% | ❌ |
| hi->en | 20s | 58.6% palavras | 22.5% | 31.5 | 6.6 s | 8.5 s | +1.8 s | 6.3 s | 44% | ❌ |
| ja->en | 19s | 2.2% caracteres | 2.2% | 64.8 | 7.3 s | 7.6 s | +3.0 s | 1.9 s | 40% | ❌ |
| ko->en | 17s | 0.0% caracteres | 0.0% | 49.9 | 6.7 s | 7.3 s | +0.4 s | 5.1 s | 41% | ❌ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 2640 ms | 3325 ms | 18 ms | 36 ms | 0 ms |
| en->pt | 8121 ms | 3205 ms | 10 ms | 28 ms | 0 ms |
| es->en | 3398 ms | 3194 ms | 16 ms | 28 ms | 0 ms |
| fr->en | 1806 ms | 3383 ms | 18 ms | 49 ms | 0 ms |
| de->en | 2040 ms | 3346 ms | 16 ms | 31 ms | 0 ms |
| it->en | 0 ms | 3515 ms | 17 ms | 38 ms | 0 ms |
| ru->en | 0 ms | 3594 ms | 22 ms | 49 ms | 0 ms |
| zh->en | 2579 ms | 3403 ms | 15 ms | 34 ms | 0 ms |
| nl->en | 400 ms | 3480 ms | 19 ms | 41 ms | 0 ms |
| pl->en | 269 ms | 3594 ms | 24 ms | 61 ms | 0 ms |
| uk->en | 2258 ms | 3332 ms | 13 ms | 32 ms | 0 ms |
| tr->en | 2019 ms | 3418 ms | 17 ms | 43 ms | 0 ms |
| ar->en | 4780 ms | 3523 ms | 12 ms | 38 ms | 0 ms |
| hi->en | 2237 ms | 3825 ms | 15 ms | 30 ms | 0 ms |
| ja->en | 2211 ms | 3592 ms | 15 ms | 35 ms | 0 ms |
| ko->en | 658 ms | 3555 ms | 21 ms | 58 ms | 0 ms |

### Problemas encontrados

- **pt->en**: não acompanha o falante: atraso típico 5.9 s, sobe +2.1 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para; trechos esperam 2640 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **en->pt**: não acompanha o falante: atraso típico 9.3 s, sobe +7.1 s da 1ª para a 2ª metade e sobram 16 s de tradução quando ele para; trechos esperam 8121 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **es->en**: não acompanha o falante: atraso típico 5.7 s, sobe +2.9 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para; trechos esperam 3398 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **fr->en**: não acompanha o falante: atraso típico 5.4 s, sobe +0.5 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para; trechos esperam 1806 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **de->en**: transcrição ruim: 29% das palavras erradas; não acompanha o falante: atraso típico 5.7 s, sobe +0.6 s da 1ª para a 2ª metade e sobram 5 s de tradução quando ele para; trechos esperam 2040 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **it->en**: transcrição ruim: 24% das palavras erradas; não acompanha o falante: atraso típico 4.2 s, sobe +0.6 s da 1ª para a 2ª metade e sobram 2 s de tradução quando ele para
- **ru->en**: não acompanha o falante: atraso típico 4.8 s, sobe -0.2 s da 1ª para a 2ª metade e sobram 2 s de tradução quando ele para; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **zh->en**: transcrição ruim: 20% dos caracteres erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 6 caracteres seguidas); inventou 8 caracteres que não foram faladas; não acompanha o falante: atraso típico 6.8 s, sobe +3.7 s da 1ª para a 2ª metade e sobram 11 s de tradução quando ele para; trechos esperam 2579 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **nl->en**: transcrição ruim: 22% das palavras erradas; não acompanha o falante: atraso típico 4.5 s, sobe +0.0 s da 1ª para a 2ª metade e sobram 0 s de tradução quando ele para
- **pl->en**: não acompanha o falante: atraso típico 5.0 s, sobe -0.8 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para
- **uk->en**: não acompanha o falante: atraso típico 5.9 s, sobe -0.2 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para; trechos esperam 2258 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **tr->en**: não acompanha o falante: atraso típico 6.2 s, sobe +2.0 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para; trechos esperam 2019 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ar->en**: não acompanha o falante: atraso típico 7.5 s, sobe +3.3 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para; trechos esperam 4780 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) com fala viraram texto vazio
- **hi->en**: transcrição ruim: 59% das palavras erradas; não acompanha o falante: atraso típico 6.6 s, sobe +1.8 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para; trechos esperam 2237 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ja->en**: não acompanha o falante: atraso típico 7.3 s, sobe +3.0 s da 1ª para a 2ª metade e sobram 2 s de tradução quando ele para; trechos esperam 2211 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ko->en**: não acompanha o falante: atraso típico 6.7 s, sobe +0.4 s da 1ª para a 2ª metade e sobram 5 s de tradução quando ele para; trechos esperam 658 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
