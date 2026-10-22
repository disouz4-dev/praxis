_Máquina: macOS-26.6.2-x86_64-i386-64bit · processador i386 · Python 3.12.15 · placa de vídeo CUDA: não_

Whisper `small` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 18.6% palavras | 7.1% | 75.5 | 2.8 s | 4.7 s | -1.4 s | 3.7 s | 70% | ✅ |
| en->pt | 20s | 1.8% palavras | 2.3% | 75.9 | 3.1 s | 5.4 s | -1.7 s | 7.4 s | 85% | ✅ |
| es->en | 21s | 35.6% palavras | 15.8% | 45.8 | 3.9 s | 5.2 s | -0.8 s | 4.6 s | 57% | ✅ |
| fr->en | 21s | 55.4% palavras | 25.5% | 47.3 | 4.8 s | 5.9 s | +0.1 s | 6.9 s | 77% | ❌ |
| de->en | 19s | 64.7% palavras | 29.3% | 36.7 | 3.4 s | 3.5 s | +0.5 s | 5.3 s | 52% | ✅ |
| it->en | 20s | 42.5% palavras | 12.8% | 54.5 | 3.8 s | 6.0 s | -1.4 s | 7.0 s | 73% | ✅ |
| ru->en | 19s | 42.3% palavras | 14.8% | 70.1 | 3.1 s | 3.2 s | -0.6 s | 4.5 s | 59% | ✅ |
| zh->en | 19s | 52.3% caracteres | 52.3% | 33.7 | 2.1 s | 2.5 s | +0.0 s | 1.7 s | 29% | ✅ |
| nl->en | 22s | 33.3% palavras | 14.5% | 54.5 | 5.9 s | 7.2 s | +4.0 s | 6.2 s | 62% | ❌ |
| pl->en | 18s | 35.9% palavras | 14.2% | 39.7 | 3.0 s | 3.9 s | +0.8 s | 6.3 s | 81% | ✅ |
| uk->en | 19s | 88.2% palavras | 61.7% | 21.0 | 4.8 s | 5.1 s | +0.4 s | 0.0 s | 33% | ❌ |
| tr->en | 17s | 20.8% palavras | 7.4% | 56.7 | 3.6 s | 3.7 s | -0.6 s | 2.7 s | 46% | ✅ |
| ar->en | 19s | 20.0% palavras | 7.0% | 65.0 | 3.2 s | 5.1 s | +1.0 s | 5.6 s | 55% | ✅ |
| hi->en | 20s | 75.6% palavras | 89.8% | 14.8 | 2.8 s | 3.4 s | -0.1 s | 0.0 s | 41% | ✅ |
| ja->en | 25s | 23.9% caracteres | 23.9% | 46.1 | 3.1 s | 3.7 s | -0.3 s | 4.5 s | 46% | ✅ |
| ko->en | 20s | 13.5% caracteres | 13.5% | 43.4 | 3.8 s | 4.4 s | -1.2 s | 6.0 s | 54% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 96 ms | 2054 ms | 68 ms | 119 ms | 159 ms |
| en->pt | 1 ms | 2354 ms | 137 ms | 258 ms | 1 ms |
| es->en | 1460 ms | 2258 ms | 144 ms | 68 ms | 0 ms |
| fr->en | 0 ms | 2528 ms | 227 ms | 220 ms | 1450 ms |
| de->en | 1 ms | 2296 ms | 103 ms | 105 ms | 0 ms |
| it->en | 0 ms | 2741 ms | 138 ms | 236 ms | 1 ms |
| ru->en | 0 ms | 1643 ms | 82 ms | 144 ms | 2 ms |
| zh->en | 0 ms | 1415 ms | 55 ms | 68 ms | 0 ms |
| nl->en | 3180 ms | 2298 ms | 86 ms | 84 ms | 0 ms |
| pl->en | 0 ms | 2280 ms | 173 ms | 170 ms | 212 ms |
| uk->en | 498 ms | 2609 ms | 152 ms | 140 ms | 741 ms |
| tr->en | 0 ms | 2236 ms | 91 ms | 149 ms | 1 ms |
| ar->en | 0 ms | 2269 ms | 82 ms | 155 ms | 1 ms |
| hi->en | 0 ms | 2437 ms | 65 ms | 106 ms | 0 ms |
| ja->en | 0 ms | 2432 ms | 146 ms | 240 ms | 1 ms |
| ko->en | 0 ms | 2491 ms | 120 ms | 159 ms | 1 ms |

### Problemas encontrados

- **pt->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.7 s
- **en->pt**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 5.4 s
- **es->en**: transcrição ruim: 36% das palavras erradas; trechos esperam 1460 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); picos de atraso: 1 em cada 20 trechos demora mais de 5.2 s
- **fr->en**: transcrição ruim: 55% das palavras erradas; inventou 6 palavras que não foram faladas; não acompanha o falante: atraso típico 4.8 s, sobe +0.1 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para; a tradução pronta espera 1450 ms a fala anterior terminar de tocar; 1 trecho(s) com fala viraram texto vazio
- **de->en**: transcrição ruim: 65% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.5 s
- **it->en**: transcrição ruim: 43% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 6.0 s
- **ru->en**: transcrição ruim: 42% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.2 s
- **zh->en**: transcrição ruim: 52% dos caracteres erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 9 caracteres seguidas); 1 trecho(s) com fala viraram texto vazio
- **nl->en**: transcrição ruim: 33% das palavras erradas; não acompanha o falante: atraso típico 5.9 s, sobe +4.0 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para; trechos esperam 3180 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **pl->en**: transcrição ruim: 36% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.9 s
- **uk->en**: transcrição ruim: 88% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 16 palavras seguidas); inventou 4 palavras que não foram faladas; não acompanha o falante: atraso típico 4.8 s, sobe +0.4 s da 1ª para a 2ª metade e sobram 0 s de tradução quando ele para
- **tr->en**: transcrição ruim: 21% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **ar->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 5.1 s
- **hi->en**: transcrição ruim: 76% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 11 palavras seguidas); picos de atraso: 1 em cada 20 trechos demora mais de 3.4 s
- **ja->en**: transcrição ruim: 24% dos caracteres erradas; inventou 5 caracteres que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **ko->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.4 s

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
