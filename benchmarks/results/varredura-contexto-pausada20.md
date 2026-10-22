_Máquina: macOS-26.6.2-x86_64-i386-64bit · processador i386 · Python 3.12.15 · placa de vídeo CUDA: não_

Whisper `small` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 9.1% palavras | 1.5% | 63.8 | 4.5 s | 5.8 s | +0.9 s | 4.6 s | 52% | ❌ |
| en->pt | 19s | 48.8% palavras | 41.5% | 53.6 | 7.6 s | 12.9 s | +5.9 s | 13.8 s | 93% | ❌ |
| es->en | 16s | 7.7% palavras | 3.9% | 59.3 | 4.7 s | 5.2 s | +1.7 s | 3.9 s | 38% | ❌ |
| fr->en | 19s | 12.5% palavras | 9.2% | 62.5 | 4.7 s | 6.0 s | -0.3 s | 6.9 s | 59% | ❌ |
| de->en | 19s | 33.3% palavras | 10.9% | 41.5 | 3.5 s | 4.2 s | +0.1 s | 4.8 s | 46% | ✅ |
| it->en | 21s | 35.1% palavras | 8.3% | 44.2 | 3.7 s | 4.0 s | +0.2 s | 4.5 s | 62% | ✅ |
| ru->en | 22s | 19.1% palavras | 6.0% | 52.9 | 4.4 s | 4.5 s | -0.0 s | 1.2 s | 39% | ❌ |
| zh->en | 20s | 19.3% caracteres | 19.3% | 44.9 | 4.2 s | 6.4 s | +1.2 s | 6.9 s | 70% | ❌ |
| nl->en | 20s | 48.1% palavras | 20.2% | 58.0 | 3.2 s | 3.6 s | +0.6 s | 6.9 s | 42% | ✅ |
| pl->en | 21s | 27.0% palavras | 8.6% | 42.3 | 3.9 s | 5.1 s | -1.3 s | 3.5 s | 59% | ✅ |
| uk->en | 20s | 29.2% palavras | 7.4% | 41.5 | 4.3 s | 5.1 s | -0.8 s | 3.7 s | 50% | ❌ |
| tr->en | 19s | 23.8% palavras | 10.6% | 57.4 | 4.5 s | 5.5 s | +0.9 s | 2.2 s | 38% | ❌ |
| ar->en | 20s | 24.1% palavras | 10.1% | 60.3 | 6.6 s | 6.7 s | +1.4 s | 4.1 s | 36% | ❌ |
| hi->en | 20s | 58.6% palavras | 31.7% | 25.8 | 4.1 s | 5.4 s | +0.5 s | 3.4 s | 49% | ❌ |
| ja->en | 19s | 8.7% caracteres | 8.7% | 65.9 | 6.8 s | 6.8 s | +2.9 s | 0.9 s | 41% | ❌ |
| ko->en | 17s | 12.0% caracteres | 12.0% | 53.6 | 5.3 s | 7.1 s | -0.6 s | 3.7 s | 50% | ❌ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 1158 ms | 2725 ms | 91 ms | 97 ms | 1 ms |
| en->pt | 6419 ms | 2656 ms | 68 ms | 94 ms | 2 ms |
| es->en | 2028 ms | 2594 ms | 156 ms | 74 ms | 0 ms |
| fr->en | 1376 ms | 2726 ms | 116 ms | 93 ms | 2 ms |
| de->en | 295 ms | 2610 ms | 90 ms | 89 ms | 0 ms |
| it->en | 1 ms | 2837 ms | 86 ms | 116 ms | 1 ms |
| ru->en | 0 ms | 2820 ms | 162 ms | 149 ms | 1 ms |
| zh->en | 1034 ms | 2852 ms | 74 ms | 112 ms | 0 ms |
| nl->en | 0 ms | 2671 ms | 125 ms | 120 ms | 1 ms |
| pl->en | 0 ms | 2830 ms | 150 ms | 154 ms | 1 ms |
| uk->en | 1528 ms | 2646 ms | 85 ms | 95 ms | 0 ms |
| tr->en | 1139 ms | 2741 ms | 89 ms | 145 ms | 1 ms |
| ar->en | 2774 ms | 2833 ms | 55 ms | 98 ms | 0 ms |
| hi->en | 821 ms | 2954 ms | 75 ms | 94 ms | 1 ms |
| ja->en | 1597 ms | 2850 ms | 79 ms | 112 ms | 864 ms |
| ko->en | 47 ms | 2895 ms | 117 ms | 172 ms | 1 ms |

### Problemas encontrados

- **pt->en**: não acompanha o falante: atraso típico 4.5 s, sobe +0.9 s da 1ª para a 2ª metade e sobram 5 s de tradução quando ele para; trechos esperam 1158 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **en->pt**: transcrição ruim: 49% das palavras erradas; inventou 12 palavras que não foram faladas; não acompanha o falante: atraso típico 7.6 s, sobe +5.9 s da 1ª para a 2ª metade e sobram 14 s de tradução quando ele para; trechos esperam 6419 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **es->en**: não acompanha o falante: atraso típico 4.7 s, sobe +1.7 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para; trechos esperam 2028 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **fr->en**: não acompanha o falante: atraso típico 4.7 s, sobe -0.3 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para; trechos esperam 1376 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **de->en**: transcrição ruim: 33% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.2 s
- **it->en**: transcrição ruim: 35% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **ru->en**: não acompanha o falante: atraso típico 4.4 s, sobe -0.0 s da 1ª para a 2ª metade e sobram 1 s de tradução quando ele para; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **zh->en**: pulou 1 trecho(s) inteiro(s) da fala (maior: 6 caracteres seguidas); não acompanha o falante: atraso típico 4.2 s, sobe +1.2 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para; trechos esperam 1034 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **nl->en**: transcrição ruim: 48% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.6 s
- **pl->en**: transcrição ruim: 27% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 5.1 s
- **uk->en**: transcrição ruim: 29% das palavras erradas; não acompanha o falante: atraso típico 4.3 s, sobe -0.8 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para; trechos esperam 1528 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **tr->en**: transcrição ruim: 24% das palavras erradas; não acompanha o falante: atraso típico 4.5 s, sobe +0.9 s da 1ª para a 2ª metade e sobram 2 s de tradução quando ele para; trechos esperam 1139 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ar->en**: transcrição ruim: 24% das palavras erradas; não acompanha o falante: atraso típico 6.6 s, sobe +1.4 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para; trechos esperam 2774 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) com fala viraram texto vazio
- **hi->en**: transcrição ruim: 59% das palavras erradas; não acompanha o falante: atraso típico 4.1 s, sobe +0.5 s da 1ª para a 2ª metade e sobram 3 s de tradução quando ele para; trechos esperam 821 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ja->en**: não acompanha o falante: atraso típico 6.8 s, sobe +2.9 s da 1ª para a 2ª metade e sobram 1 s de tradução quando ele para; trechos esperam 1597 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); a tradução pronta espera 864 ms a fala anterior terminar de tocar
- **ko->en**: não acompanha o falante: atraso típico 5.3 s, sobe -0.6 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
