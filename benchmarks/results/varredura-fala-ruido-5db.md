_Máquina: macOS-26.6.2-x86_64-i386-64bit · processador i386 · Python 3.12.15 · placa de vídeo CUDA: não_

Whisper `small` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 30.2% palavras | 12.6% | 70.1 | 2.4 s | 4.0 s | +0.1 s | 3.7 s | 71% | ✅ |
| en->pt | 20s | 5.6% palavras | 4.7% | 79.5 | 3.1 s | 5.5 s | -1.6 s | 7.5 s | 85% | ✅ |
| es->en | 21s | 64.4% palavras | 40.2% | 37.0 | 4.2 s | 4.9 s | -1.8 s | 3.8 s | 58% | ❌ |
| fr->en | 21s | 71.4% palavras | 44.6% | 30.9 | 3.1 s | 5.3 s | +1.9 s | 6.9 s | 63% | ❌ |
| de->en | 19s | 94.1% palavras | 47.3% | 31.2 | 4.4 s | 4.7 s | -0.3 s | 6.2 s | 71% | ❌ |
| it->en | 20s | 53.2% palavras | 22.1% | 41.1 | 2.7 s | 2.7 s | -0.4 s | 5.5 s | 71% | ✅ |
| ru->en | 19s | 100.0% palavras | 40.3% | 29.2 | 2.6 s | 3.2 s | +0.1 s | 4.7 s | 58% | ✅ |
| zh->en | 19s | 75.0% caracteres | 75.0% | 16.1 | 2.5 s | 2.7 s | +0.1 s | 2.6 s | 22% | ✅ |
| nl->en | 22s | 45.8% palavras | 20.3% | 52.4 | 3.1 s | 3.5 s | -0.0 s | 4.7 s | 73% | ✅ |
| pl->en | 18s | 79.5% palavras | 37.0% | 29.4 | 2.8 s | 3.5 s | +0.6 s | 6.3 s | 70% | ✅ |
| uk->en | 19s | 94.1% palavras | 71.3% | 16.8 | 6.1 s | 7.1 s | +1.0 s | 0.0 s | 41% | ❌ |
| tr->en | 17s | 62.5% palavras | 42.3% | 39.1 | 3.3 s | 4.5 s | -1.5 s | 3.0 s | 50% | ✅ |
| ar->en | 19s | 50.0% palavras | 20.2% | 50.5 | 4.2 s | 6.9 s | +0.8 s | 7.9 s | 68% | ❌ |
| hi->en | 20s | 92.7% palavras | 63.3% | 15.7 | 3.6 s | 4.2 s | +0.7 s | 0.1 s | 35% | ✅ |
| ja->en | 25s | 22.7% caracteres | 22.7% | 59.0 | 4.6 s | 7.4 s | -2.5 s | 5.5 s | 56% | ❌ |
| ko->en | 20s | 29.7% caracteres | 29.7% | 30.6 | 4.4 s | 5.0 s | -0.9 s | 5.4 s | 45% | ❌ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 4 ms | 2000 ms | 63 ms | 105 ms | 1 ms |
| en->pt | 0 ms | 2400 ms | 142 ms | 257 ms | 2 ms |
| es->en | 731 ms | 2225 ms | 208 ms | 112 ms | 3 ms |
| fr->en | 0 ms | 2335 ms | 142 ms | 168 ms | 1 ms |
| de->en | 1783 ms | 2242 ms | 121 ms | 137 ms | 1 ms |
| it->en | 0 ms | 2323 ms | 101 ms | 183 ms | 1 ms |
| ru->en | 605 ms | 1979 ms | 110 ms | 184 ms | 2 ms |
| zh->en | 3 ms | 2150 ms | 75 ms | 79 ms | 0 ms |
| nl->en | 771 ms | 1980 ms | 73 ms | 89 ms | 0 ms |
| pl->en | 0 ms | 2467 ms | 184 ms | 185 ms | 1 ms |
| uk->en | 905 ms | 2970 ms | 247 ms | 242 ms | 1126 ms |
| tr->en | 0 ms | 2710 ms | 103 ms | 143 ms | 1 ms |
| ar->en | 2 ms | 2962 ms | 125 ms | 221 ms | 762 ms |
| hi->en | 0 ms | 3355 ms | 125 ms | 101 ms | 0 ms |
| ja->en | 0 ms | 3178 ms | 218 ms | 278 ms | 1 ms |
| ko->en | 1 ms | 3033 ms | 215 ms | 220 ms | 1 ms |

### Problemas encontrados

- **pt->en**: transcrição ruim: 30% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **en->pt**: picos de atraso: 1 em cada 20 trechos demora mais de 5.5 s
- **es->en**: transcrição ruim: 64% das palavras erradas; não acompanha o falante: atraso típico 4.2 s, sobe -1.8 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para; trechos esperam 731 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) com fala viraram texto vazio
- **fr->en**: transcrição ruim: 71% das palavras erradas; não acompanha o falante: atraso típico 3.1 s, sobe +1.9 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para; 1 trecho(s) com fala viraram texto vazio
- **de->en**: transcrição ruim: 94% das palavras erradas; inventou 10 palavras que não foram faladas; não acompanha o falante: atraso típico 4.4 s, sobe -0.3 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para; trechos esperam 1783 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **it->en**: transcrição ruim: 53% das palavras erradas
- **ru->en**: transcrição ruim: 100% das palavras erradas; inventou 5 palavras que não foram faladas; trechos esperam 605 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 2 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 3.2 s
- **zh->en**: transcrição ruim: 75% dos caracteres erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 18 caracteres seguidas); 3 trecho(s) com fala viraram texto vazio
- **nl->en**: transcrição ruim: 46% das palavras erradas; inventou 5 palavras que não foram faladas; trechos esperam 771 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.5 s
- **pl->en**: transcrição ruim: 79% das palavras erradas; inventou 4 palavras que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 3.5 s
- **uk->en**: transcrição ruim: 94% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 9 palavras seguidas); não acompanha o falante: atraso típico 6.1 s, sobe +1.0 s da 1ª para a 2ª metade e sobram 0 s de tradução quando ele para; trechos esperam 905 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); a tradução pronta espera 1126 ms a fala anterior terminar de tocar
- **tr->en**: transcrição ruim: 62% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.5 s
- **ar->en**: transcrição ruim: 50% das palavras erradas; não acompanha o falante: atraso típico 4.2 s, sobe +0.8 s da 1ª para a 2ª metade e sobram 8 s de tradução quando ele para; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **hi->en**: transcrição ruim: 93% das palavras erradas; inventou 6 palavras que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 4.2 s
- **ja->en**: transcrição ruim: 23% dos caracteres erradas; não acompanha o falante: atraso típico 4.6 s, sobe -2.5 s da 1ª para a 2ª metade e sobram 5 s de tradução quando ele para
- **ko->en**: transcrição ruim: 30% dos caracteres erradas; não acompanha o falante: atraso típico 4.4 s, sobe -0.9 s da 1ª para a 2ª metade e sobram 5 s de tradução quando ele para

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
