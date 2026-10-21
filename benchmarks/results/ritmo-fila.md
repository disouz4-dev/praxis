_Máquina: macOS-26.6.2-x86_64-i386-64bit · processador i386 · Python 3.12.15 · placa de vídeo CUDA: não_

Whisper `small` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 71s | 7.8% palavras | 3.0% | 72.3 | 2.4 s | 4.8 s | +0.3 s | 5.8 s | 70% | ✅ |
| en->pt | 72s | 2.6% palavras | 1.0% | 70.6 | 2.3 s | 4.2 s | -0.4 s | 5.9 s | 79% | ✅ |
| es->en | 73s | 2.0% palavras | 0.6% | 68.1 | 2.3 s | 3.7 s | +0.2 s | 3.1 s | 60% | ✅ |
| fr->en | 62s | 24.7% palavras | 13.3% | 57.2 | 2.9 s | 5.6 s | +0.6 s | 4.7 s | 73% | ✅ |
| de->en | 63s | 29.2% palavras | 9.2% | 57.8 | 2.1 s | 4.2 s | -0.0 s | 3.3 s | 55% | ✅ |
| it->en | 78s | 32.8% palavras | 8.9% | 55.6 | 3.0 s | 5.5 s | +0.4 s | 5.4 s | 68% | ✅ |
| ru->en | 66s | 20.4% palavras | 5.6% | 71.5 | 3.0 s | 6.6 s | -0.1 s | 4.6 s | 57% | ✅ |
| zh->en | 62s | 15.4% caracteres | 15.4% | 30.7 | 2.6 s | 3.9 s | +0.1 s | 3.2 s | 55% | ✅ |
| nl->en | 66s | 20.4% palavras | 9.2% | 53.0 | 2.1 s | 4.3 s | -0.1 s | 5.9 s | 67% | ✅ |
| pl->en | 69s | 14.6% palavras | 2.4% | 60.1 | 2.5 s | 4.2 s | +0.5 s | 5.2 s | 78% | ✅ |
| uk->en | 69s | 16.5% palavras | 4.9% | 74.2 | 2.8 s | 5.7 s | -1.1 s | 6.6 s | 66% | ✅ |
| tr->en | 72s | 24.7% palavras | 6.5% | 65.6 | 3.6 s | 6.5 s | -0.9 s | 5.9 s | 54% | ✅ |
| ar->en | 74s | 31.2% palavras | 10.7% | 62.5 | 3.6 s | 6.6 s | -0.0 s | 7.1 s | 68% | ✅ |
| hi->en | 69s | 78.5% palavras | 48.8% | 34.6 | 5.1 s | 8.1 s | -3.3 s | 5.4 s | 58% | ❌ |
| ja->en | 64s | 20.0% caracteres | 20.0% | 54.3 | 4.0 s | 6.6 s | -0.0 s | 4.2 s | 53% | ✅ |
| ko->en | 69s | 8.2% caracteres | 8.2% | 58.8 | 4.1 s | 5.3 s | +0.9 s | 5.8 s | 56% | ❌ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 1 ms | 1495 ms | 70 ms | 131 ms | 1 ms |
| en->pt | 0 ms | 1502 ms | 83 ms | 142 ms | 1 ms |
| es->en | 0 ms | 1423 ms | 116 ms | 88 ms | 2 ms |
| fr->en | 0 ms | 1472 ms | 69 ms | 122 ms | 1 ms |
| de->en | 0 ms | 1381 ms | 47 ms | 70 ms | 0 ms |
| it->en | 0 ms | 1500 ms | 47 ms | 118 ms | 1 ms |
| ru->en | 0 ms | 1505 ms | 67 ms | 135 ms | 1 ms |
| zh->en | 0 ms | 1463 ms | 63 ms | 103 ms | 1 ms |
| nl->en | 0 ms | 1519 ms | 83 ms | 137 ms | 1 ms |
| pl->en | 0 ms | 1531 ms | 89 ms | 139 ms | 1 ms |
| uk->en | 0 ms | 1489 ms | 519 ms | 128 ms | 1 ms |
| tr->en | 0 ms | 1637 ms | 577 ms | 149 ms | 1 ms |
| ar->en | 0 ms | 1582 ms | 545 ms | 148 ms | 1 ms |
| hi->en | 1165 ms | 1749 ms | 282 ms | 68 ms | 1 ms |
| ja->en | 0 ms | 1731 ms | 797 ms | 149 ms | 2 ms |
| ko->en | 0 ms | 1709 ms | 691 ms | 148 ms | 3 ms |

### Problemas encontrados

- **pt->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 4.8 s
- **en->pt**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 4.2 s
- **es->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **fr->en**: transcrição ruim: 25% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 5.6 s
- **de->en**: transcrição ruim: 29% das palavras erradas; 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 4.2 s
- **it->en**: transcrição ruim: 33% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 5.5 s
- **ru->en**: transcrição ruim: 20% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 6.6 s
- **zh->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.9 s
- **nl->en**: transcrição ruim: 20% das palavras erradas; 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 4.3 s
- **pl->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.2 s
- **uk->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 5.7 s
- **tr->en**: transcrição ruim: 25% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 6.5 s
- **ar->en**: transcrição ruim: 31% das palavras erradas; inventou 11 palavras que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 6.6 s
- **hi->en**: transcrição ruim: 79% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 17 palavras seguidas); inventou 14 palavras que não foram faladas; não acompanha o falante: atraso típico 5.1 s, sobe -3.3 s da 1ª para a 2ª metade e sobram 5 s de tradução quando ele para; trechos esperam 1165 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ja->en**: picos de atraso: 1 em cada 20 trechos demora mais de 6.6 s
- **ko->en**: não acompanha o falante: atraso típico 4.1 s, sobe +0.9 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
