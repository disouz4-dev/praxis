_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `medium` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 14s | 9.1% palavras | 1.5% | 78.3 | 6.1 s | 7.2 s | -0.4 s | 7.7 s | 68% | ❌ |
| en->pt | 14s | 7.0% palavras | 8.5% | 74.7 | 5.0 s | 6.1 s | +1.1 s | 9.0 s | 92% | ❌ |
| es->en | 12s | 7.7% palavras | 2.9% | 78.0 | 5.9 s | 6.9 s | +2.4 s | 4.8 s | 40% | ❌ |
| fr->en | 14s | 15.0% palavras | 9.2% | 56.7 | 4.6 s | 5.7 s | +1.1 s | 6.7 s | 68% | ❌ |
| de->en | 14s | 16.7% palavras | 5.1% | 56.7 | 4.7 s | 6.1 s | +2.1 s | 2.2 s | 34% | ❌ |
| it->en | 16s | 51.3% palavras | 23.8% | 45.3 | 6.9 s | 8.6 s | +0.4 s | 9.2 s | 88% | ❌ |
| ru->en | 17s | 4.8% palavras | 1.5% | 56.3 | 5.2 s | 5.4 s | +0.3 s | 4.2 s | 50% | ❌ |
| zh->en | 15s | 14.5% caracteres | 14.5% | 56.4 | 5.5 s | 5.8 s | +0.3 s | 8.1 s | 80% | ❌ |
| nl->en | 15s | 22.2% palavras | 14.9% | 62.7 | 3.7 s | 4.0 s | +0.6 s | 0.0 s | 32% | ✅ |
| pl->en | 15s | 10.8% palavras | 1.6% | 63.1 | 6.3 s | 6.7 s | +1.6 s | 4.8 s | 60% | ❌ |
| uk->en | 15s | 4.2% palavras | 1.4% | 89.3 | 4.6 s | 4.7 s | -0.3 s | 6.6 s | 55% | ❌ |
| tr->en | 14s | 19.1% palavras | 9.6% | 59.6 | 5.0 s | 5.1 s | -0.2 s | 4.9 s | 47% | ❌ |
| ar->en | 15s | 0.0% palavras | 0.0% | 79.8 | 5.1 s | 7.1 s | +1.4 s | 7.2 s | 58% | ❌ |
| hi->en | 15s | 55.2% palavras | 23.3% | 24.7 | 8.7 s | 11.0 s | +4.0 s | 10.3 s | 60% | ❌ |
| ja->en | 14s | 0.0% caracteres | 0.0% | 74.2 | 6.1 s | 6.9 s | +0.8 s | 6.0 s | 49% | ❌ |
| ko->en | 12s | 16.0% caracteres | 16.0% | 69.1 | 6.3 s | 6.7 s | +1.0 s | 7.7 s | 67% | ❌ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 1736 ms | 3544 ms | 23 ms | 58 ms | 177 ms |
| en->pt | 0 ms | 3602 ms | 29 ms | 65 ms | 1 ms |
| es->en | 2998 ms | 3276 ms | 22 ms | 38 ms | 0 ms |
| fr->en | 0 ms | 3679 ms | 30 ms | 73 ms | 0 ms |
| de->en | 1133 ms | 3352 ms | 18 ms | 31 ms | 0 ms |
| it->en | 1191 ms | 3744 ms | 26 ms | 69 ms | 878 ms |
| ru->en | 522 ms | 3567 ms | 22 ms | 44 ms | 0 ms |
| zh->en | 0 ms | 4291 ms | 34 ms | 87 ms | 0 ms |
| nl->en | 0 ms | 3791 ms | 30 ms | 69 ms | 0 ms |
| pl->en | 1954 ms | 3738 ms | 28 ms | 71 ms | 0 ms |
| uk->en | 0 ms | 3997 ms | 34 ms | 88 ms | 0 ms |
| tr->en | 336 ms | 3733 ms | 26 ms | 70 ms | 0 ms |
| ar->en | 0 ms | 4190 ms | 25 ms | 79 ms | 0 ms |
| hi->en | 4721 ms | 3769 ms | 11 ms | 29 ms | 0 ms |
| ja->en | 877 ms | 3896 ms | 33 ms | 69 ms | 464 ms |
| ko->en | 187 ms | 3836 ms | 38 ms | 86 ms | 498 ms |

### Problemas encontrados

- **pt->en**: não acompanha o falante: atraso típico 6.1 s, sobe -0.4 s da 1ª para a 2ª metade e sobram 8 s de tradução quando ele para; trechos esperam 1736 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **en->pt**: não acompanha o falante: atraso típico 5.0 s, sobe +1.1 s da 1ª para a 2ª metade e sobram 9 s de tradução quando ele para
- **es->en**: não acompanha o falante: atraso típico 5.9 s, sobe +2.4 s da 1ª para a 2ª metade e sobram 5 s de tradução quando ele para; trechos esperam 2998 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **fr->en**: não acompanha o falante: atraso típico 4.6 s, sobe +1.1 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para
- **de->en**: não acompanha o falante: atraso típico 4.7 s, sobe +2.1 s da 1ª para a 2ª metade e sobram 2 s de tradução quando ele para; trechos esperam 1133 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **it->en**: transcrição ruim: 51% das palavras erradas; inventou 8 palavras que não foram faladas; não acompanha o falante: atraso típico 6.9 s, sobe +0.4 s da 1ª para a 2ª metade e sobram 9 s de tradução quando ele para; trechos esperam 1191 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); a tradução pronta espera 878 ms a fala anterior terminar de tocar
- **ru->en**: não acompanha o falante: atraso típico 5.2 s, sobe +0.3 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para; trechos esperam 522 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **zh->en**: não acompanha o falante: atraso típico 5.5 s, sobe +0.3 s da 1ª para a 2ª metade e sobram 8 s de tradução quando ele para
- **nl->en**: transcrição ruim: 22% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **pl->en**: não acompanha o falante: atraso típico 6.3 s, sobe +1.6 s da 1ª para a 2ª metade e sobram 5 s de tradução quando ele para; trechos esperam 1954 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **uk->en**: não acompanha o falante: atraso típico 4.6 s, sobe -0.3 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **tr->en**: não acompanha o falante: atraso típico 5.0 s, sobe -0.2 s da 1ª para a 2ª metade e sobram 5 s de tradução quando ele para
- **ar->en**: não acompanha o falante: atraso típico 5.1 s, sobe +1.4 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para
- **hi->en**: transcrição ruim: 55% das palavras erradas; não acompanha o falante: atraso típico 8.7 s, sobe +4.0 s da 1ª para a 2ª metade e sobram 10 s de tradução quando ele para; trechos esperam 4721 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ja->en**: não acompanha o falante: atraso típico 6.1 s, sobe +0.8 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para; trechos esperam 877 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ko->en**: não acompanha o falante: atraso típico 6.3 s, sobe +1.0 s da 1ª para a 2ª metade e sobram 8 s de tradução quando ele para

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
