_Máquina: macOS-26.6.2-x86_64-i386-64bit · processador i386 · Python 3.12.15 · placa de vídeo CUDA: não_

Whisper `small` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 71s | 7.8% palavras | 1.5% | 72.8 | 2.6 s | 4.2 s | -0.2 s | 5.6 s | 69% | ✅ |
| en->pt | 72s | 2.1% palavras | 1.9% | 76.7 | 3.7 s | 9.9 s | +0.3 s | 8.2 s | 76% | ❌ |
| es->en | 73s | 2.0% palavras | 0.6% | 68.0 | 2.4 s | 3.8 s | +0.0 s | 7.4 s | 59% | ✅ |
| fr->en | 62s | 22.1% palavras | 12.4% | 59.4 | 2.9 s | 5.6 s | +0.6 s | 4.8 s | 73% | ✅ |
| de->en | 63s | 26.4% palavras | 7.5% | 58.1 | 2.2 s | 4.0 s | -0.0 s | 3.3 s | 55% | ✅ |
| it->en | 78s | 29.9% palavras | 7.6% | 58.2 | 2.7 s | 7.3 s | +0.4 s | 5.6 s | 68% | ✅ |
| ru->en | 66s | 10.2% palavras | 2.9% | 82.0 | 3.1 s | 3.5 s | +0.2 s | 5.5 s | 56% | ✅ |
| zh->en | 62s | 15.9% caracteres | 15.9% | 30.7 | 3.0 s | 4.5 s | +1.1 s | 5.6 s | 56% | ✅ |
| nl->en | 66s | 20.4% palavras | 9.3% | 56.5 | 2.4 s | 4.5 s | +0.3 s | 5.7 s | 62% | ✅ |
| pl->en | 69s | 13.9% palavras | 2.3% | 60.3 | 2.9 s | 4.1 s | +0.6 s | 5.2 s | 77% | ✅ |
| uk->en | 69s | 15.7% palavras | 3.3% | 78.6 | 3.0 s | 6.6 s | -0.7 s | 9.9 s | 64% | ❌ |
| tr->en | 72s | 27.8% palavras | 6.9% | 73.7 | 3.7 s | 5.2 s | -0.5 s | 6.3 s | 54% | ✅ |
| ar->en | 74s | 19.5% palavras | 5.8% | 70.3 | 3.8 s | 6.4 s | +0.1 s | 7.5 s | 60% | ✅ |
| hi->en | 69s | 69.8% palavras | 39.1% | 36.7 | 4.0 s | 7.0 s | -0.6 s | 5.9 s | 55% | ✅ |
| ja->en | 64s | 16.4% caracteres | 16.4% | 58.0 | 3.9 s | 4.5 s | -0.4 s | 4.4 s | 51% | ✅ |
| ko->en | 69s | 4.1% caracteres | 4.1% | 79.4 | 4.0 s | 5.4 s | +0.9 s | 7.4 s | 62% | ❌ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 1701 ms | 83 ms | 165 ms | 3 ms |
| en->pt | 0 ms | 1669 ms | 105 ms | 147 ms | 601 ms |
| es->en | 0 ms | 1521 ms | 135 ms | 95 ms | 1 ms |
| fr->en | 0 ms | 1666 ms | 90 ms | 147 ms | 12 ms |
| de->en | 0 ms | 1492 ms | 51 ms | 67 ms | 1 ms |
| it->en | 0 ms | 1662 ms | 62 ms | 157 ms | 1 ms |
| ru->en | 0 ms | 1726 ms | 97 ms | 218 ms | 1 ms |
| zh->en | 0 ms | 1552 ms | 62 ms | 94 ms | 1 ms |
| nl->en | 0 ms | 1659 ms | 100 ms | 152 ms | 1 ms |
| pl->en | 0 ms | 1718 ms | 104 ms | 156 ms | 2 ms |
| uk->en | 0 ms | 1682 ms | 576 ms | 128 ms | 1 ms |
| tr->en | 0 ms | 1796 ms | 690 ms | 203 ms | 1 ms |
| ar->en | 0 ms | 2020 ms | 999 ms | 288 ms | 1 ms |
| hi->en | 421 ms | 1937 ms | 399 ms | 99 ms | 1 ms |
| ja->en | 0 ms | 2332 ms | 1160 ms | 222 ms | 1 ms |
| ko->en | 0 ms | 2070 ms | 1217 ms | 339 ms | 1 ms |

### Problemas encontrados

- **pt->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.2 s
- **en->pt**: não acompanha o falante: atraso típico 3.7 s, sobe +0.3 s da 1ª para a 2ª metade e sobram 8 s de tradução quando ele para; 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **es->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.8 s
- **fr->en**: transcrição ruim: 22% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 5.6 s
- **de->en**: transcrição ruim: 26% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **it->en**: transcrição ruim: 30% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 7.3 s
- **ru->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.5 s
- **zh->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 4.5 s
- **nl->en**: transcrição ruim: 20% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 4.5 s
- **pl->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.1 s
- **uk->en**: não acompanha o falante: atraso típico 3.0 s, sobe -0.7 s da 1ª para a 2ª metade e sobram 10 s de tradução quando ele para
- **tr->en**: transcrição ruim: 28% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 5.2 s
- **ar->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 6.4 s
- **hi->en**: transcrição ruim: 70% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 21 palavras seguidas); picos de atraso: 1 em cada 20 trechos demora mais de 7.0 s
- **ja->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.5 s
- **ko->en**: não acompanha o falante: atraso típico 4.0 s, sobe +0.9 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
