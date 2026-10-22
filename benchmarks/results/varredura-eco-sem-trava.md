_Máquina: macOS-26.6.2-x86_64-i386-64bit · processador i386 · Python 3.12.15 · placa de vídeo CUDA: não_

Whisper `small` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 51.2% palavras | 35.4% | 60.6 | 4.0 s | 4.7 s | +0.4 s | 11.7 s | 76% | ❌ |
| en->pt | 20s | 25.9% palavras | 15.6% | 63.3 | 4.1 s | 5.3 s | +0.6 s | 8.8 s | 84% | ❌ |
| es->en | 21s | 84.4% palavras | 69.6% | 48.2 | 4.2 s | 4.9 s | +0.6 s | 10.6 s | 66% | ❌ |
| fr->en | 21s | 112.5% palavras | 84.1% | 47.0 | 5.0 s | 6.9 s | -0.7 s | 16.2 s | 115% | ❌ |
| de->en | 19s | 61.8% palavras | 42.9% | 48.8 | 4.1 s | 5.6 s | -1.4 s | 7.2 s | 51% | ❌ |
| it->en | 20s | 53.2% palavras | 34.4% | 45.8 | 4.3 s | 5.3 s | -1.2 s | 7.7 s | 72% | ❌ |
| ru->en | 19s | 42.3% palavras | 32.1% | 54.3 | 3.9 s | 4.5 s | +0.0 s | 9.2 s | 60% | ❌ |
| zh->en | 19s | 140.9% caracteres | 140.9% | 32.7 | 3.5 s | 4.7 s | +0.6 s | 8.4 s | 57% | ❌ |
| nl->en | 22s | 91.7% palavras | 66.5% | 45.2 | 4.8 s | 6.4 s | +1.4 s | 16.1 s | 91% | ❌ |
| pl->en | 18s | 66.7% palavras | 49.8% | 41.4 | 4.6 s | 5.0 s | +1.1 s | 7.8 s | 78% | ❌ |
| uk->en | 19s | 144.1% palavras | 93.6% | 38.3 | 6.1 s | 7.9 s | -1.2 s | 16.9 s | 115% | ❌ |
| tr->en | 17s | 79.2% palavras | 44.2% | 67.3 | 5.2 s | 8.0 s | +1.7 s | 15.8 s | 58% | ❌ |
| ar->en | 19s | 90.0% palavras | 58.2% | 49.0 | 7.5 s | 9.0 s | +3.8 s | 13.3 s | 90% | ❌ |
| hi->en | 20s | 82.9% palavras | 65.0% | 22.9 | 4.7 s | 6.8 s | +0.6 s | 9.2 s | 65% | ❌ |
| ja->en | 25s | 65.9% caracteres | 65.9% | 44.7 | 4.0 s | 5.1 s | -0.6 s | 10.2 s | 66% | ❌ |
| ko->en | 20s | 62.2% caracteres | 62.2% | 28.9 | 4.7 s | 4.9 s | -0.5 s | 11.2 s | 73% | ❌ |

### Eco (a tradução tocada volta pelo microfone)

| Par | Trechos traduzidos depois que o falante parou | Palavras nesses trechos |
|---|---:|---:|
| pt->en | 2 | 11 |
| en->pt | 1 | 8 |
| es->en | 2 | 22 |
| fr->en | 2 | 22 |
| de->en | 1 | 9 |
| it->en | 1 | 4 |
| ru->en | 2 | 5 |
| zh->en | 2 | 9 |
| nl->en | 2 | 22 |
| pl->en | 1 | 12 |
| uk->en | 2 | 22 |
| tr->en | 3 | 14 |
| ar->en | 1 | 3 |
| hi->en | 2 | 7 |
| ja->en | 1 | 2 |
| ko->en | 0 | 0 |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 45 ms | 2674 ms | 93 ms | 142 ms | 0 ms |
| en->pt | 0 ms | 2662 ms | 129 ms | 152 ms | 3 ms |
| es->en | 0 ms | 2751 ms | 323 ms | 171 ms | 1 ms |
| fr->en | 1 ms | 2929 ms | 172 ms | 144 ms | 532 ms |
| de->en | 0 ms | 2648 ms | 130 ms | 152 ms | 1 ms |
| it->en | 1 ms | 2817 ms | 127 ms | 193 ms | 1 ms |
| ru->en | 297 ms | 2667 ms | 89 ms | 110 ms | 0 ms |
| zh->en | 2 ms | 2621 ms | 99 ms | 103 ms | 0 ms |
| nl->en | 1 ms | 2828 ms | 159 ms | 195 ms | 2 ms |
| pl->en | 0 ms | 3181 ms | 228 ms | 273 ms | 2 ms |
| uk->en | 1852 ms | 2938 ms | 180 ms | 250 ms | 483 ms |
| tr->en | 671 ms | 2858 ms | 87 ms | 132 ms | 1 ms |
| ar->en | 335 ms | 3084 ms | 142 ms | 231 ms | 849 ms |
| hi->en | 922 ms | 3041 ms | 94 ms | 123 ms | 1 ms |
| ja->en | 375 ms | 2708 ms | 98 ms | 159 ms | 1 ms |
| ko->en | 0 ms | 2868 ms | 132 ms | 182 ms | 1 ms |

### Problemas encontrados

- **pt->en**: transcrição ruim: 51% das palavras erradas; inventou 10 palavras que não foram faladas; não acompanha o falante: atraso típico 4.0 s, sobe +0.4 s da 1ª para a 2ª metade e sobram 12 s de tradução quando ele para; 1 trecho(s) com fala viraram texto vazio
- **en->pt**: transcrição ruim: 26% das palavras erradas; inventou 5 palavras que não foram faladas; não acompanha o falante: atraso típico 4.1 s, sobe +0.6 s da 1ª para a 2ª metade e sobram 9 s de tradução quando ele para
- **es->en**: transcrição ruim: 84% das palavras erradas; inventou 24 palavras que não foram faladas; não acompanha o falante: atraso típico 4.2 s, sobe +0.6 s da 1ª para a 2ª metade e sobram 11 s de tradução quando ele para
- **fr->en**: transcrição ruim: 112% das palavras erradas; inventou 32 palavras que não foram faladas; não acompanha o falante: atraso típico 5.0 s, sobe -0.7 s da 1ª para a 2ª metade e sobram 16 s de tradução quando ele para; a fala traduzida dura 115% da original — quase não sobra folga para acompanhar
- **de->en**: transcrição ruim: 62% das palavras erradas; inventou 6 palavras que não foram faladas; não acompanha o falante: atraso típico 4.1 s, sobe -1.4 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para
- **it->en**: transcrição ruim: 53% das palavras erradas; inventou 6 palavras que não foram faladas; não acompanha o falante: atraso típico 4.3 s, sobe -1.2 s da 1ª para a 2ª metade e sobram 8 s de tradução quando ele para
- **ru->en**: transcrição ruim: 42% das palavras erradas; não acompanha o falante: atraso típico 3.9 s, sobe +0.0 s da 1ª para a 2ª metade e sobram 9 s de tradução quando ele para
- **zh->en**: transcrição ruim: 141% dos caracteres erradas; inventou 42 caracteres que não foram faladas; não acompanha o falante: atraso típico 3.5 s, sobe +0.6 s da 1ª para a 2ª metade e sobram 8 s de tradução quando ele para
- **nl->en**: transcrição ruim: 92% das palavras erradas; inventou 28 palavras que não foram faladas; não acompanha o falante: atraso típico 4.8 s, sobe +1.4 s da 1ª para a 2ª metade e sobram 16 s de tradução quando ele para
- **pl->en**: transcrição ruim: 67% das palavras erradas; inventou 12 palavras que não foram faladas; não acompanha o falante: atraso típico 4.6 s, sobe +1.1 s da 1ª para a 2ª metade e sobram 8 s de tradução quando ele para
- **uk->en**: transcrição ruim: 144% das palavras erradas; inventou 29 palavras que não foram faladas; não acompanha o falante: atraso típico 6.1 s, sobe -1.2 s da 1ª para a 2ª metade e sobram 17 s de tradução quando ele para; trechos esperam 1852 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); a fala traduzida dura 115% da original — quase não sobra folga para acompanhar
- **tr->en**: transcrição ruim: 79% das palavras erradas; inventou 15 palavras que não foram faladas; não acompanha o falante: atraso típico 5.2 s, sobe +1.7 s da 1ª para a 2ª metade e sobram 16 s de tradução quando ele para; trechos esperam 671 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ar->en**: transcrição ruim: 90% das palavras erradas; inventou 12 palavras que não foram faladas; não acompanha o falante: atraso típico 7.5 s, sobe +3.8 s da 1ª para a 2ª metade e sobram 13 s de tradução quando ele para; a tradução pronta espera 849 ms a fala anterior terminar de tocar; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **hi->en**: transcrição ruim: 83% das palavras erradas; não acompanha o falante: atraso típico 4.7 s, sobe +0.6 s da 1ª para a 2ª metade e sobram 9 s de tradução quando ele para; trechos esperam 922 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ja->en**: transcrição ruim: 66% dos caracteres erradas; inventou 44 caracteres que não foram faladas; não acompanha o falante: atraso típico 4.0 s, sobe -0.6 s da 1ª para a 2ª metade e sobram 10 s de tradução quando ele para
- **ko->en**: transcrição ruim: 62% dos caracteres erradas; inventou 26 caracteres que não foram faladas; não acompanha o falante: atraso típico 4.7 s, sobe -0.5 s da 1ª para a 2ª metade e sobram 11 s de tradução quando ele para

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
