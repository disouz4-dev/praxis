_Máquina: macOS-26.6.2-x86_64-i386-64bit · processador i386 · Python 3.12.15 · placa de vídeo CUDA: não_

Whisper `small` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 51.2% palavras | 41.9% | 67.2 | 4.9 s | 8.7 s | +1.8 s | 16.4 s | 91% | ❌ |
| en->pt | 20s | 29.6% palavras | 20.3% | 65.2 | 4.1 s | 6.1 s | +0.9 s | 10.4 s | 90% | ❌ |
| es->en | 21s | 82.2% palavras | 63.6% | 39.5 | 3.9 s | 4.6 s | +0.8 s | 9.7 s | 54% | ❌ |
| fr->en | 21s | 117.9% palavras | 86.5% | 45.3 | 5.3 s | 6.7 s | -0.4 s | 17.1 s | 122% | ❌ |
| de->en | 19s | 55.9% palavras | 26.1% | 52.9 | 4.3 s | 6.0 s | -1.8 s | 8.7 s | 57% | ❌ |
| it->en | 20s | 85.1% palavras | 54.4% | 43.8 | 4.1 s | 5.2 s | -0.9 s | 12.8 s | 96% | ❌ |
| ru->en | 19s | 119.2% palavras | 67.3% | 36.9 | 2.4 s | 2.7 s | -0.5 s | 9.5 s | 66% | ❌ |
| zh->en | 19s | 379.6% caracteres | 379.6% | 36.3 | 2.2 s | 3.5 s | -0.6 s | 11.2 s | 82% | ❌ |
| nl->en | 22s | 110.4% palavras | 76.6% | 35.7 | 3.1 s | 4.7 s | +1.0 s | 13.9 s | 114% | ❌ |
| pl->en | 18s | 66.7% palavras | 37.9% | 46.8 | 2.7 s | 3.8 s | +0.9 s | 10.0 s | 93% | ❌ |
| uk->en | 19s | 173.5% palavras | 120.7% | 38.7 | 3.9 s | 4.9 s | -0.5 s | 13.2 s | 115% | ❌ |
| tr->en | 17s | 54.2% palavras | 33.7% | 66.5 | 2.3 s | 2.9 s | -0.8 s | 3.4 s | 51% | ✅ |
| ar->en | 19s | 90.0% palavras | 57.0% | 45.4 | 3.0 s | 4.8 s | -0.8 s | 10.1 s | 84% | ❌ |
| hi->en | 20s | 122.0% palavras | 180.2% | 15.5 | 4.7 s | 7.1 s | +4.2 s | 24.2 s | 149% | ❌ |
| ja->en | 25s | 71.6% caracteres | 71.6% | 45.4 | 2.9 s | 3.7 s | +0.1 s | 7.2 s | 52% | ✅ |
| ko->en | 20s | 60.8% caracteres | 60.8% | 31.5 | 3.5 s | 7.6 s | +2.5 s | 8.6 s | 73% | ❌ |

### Eco (a tradução tocada volta pelo microfone)

| Par | Trechos traduzidos depois que o falante parou | Palavras nesses trechos |
|---|---:|---:|
| pt->en | 4 | 16 |
| en->pt | 1 | 8 |
| es->en | 2 | 22 |
| fr->en | 1 | 10 |
| de->en | 1 | 5 |
| it->en | 2 | 18 |
| ru->en | 1 | 11 |
| zh->en | 4 | 22 |
| nl->en | 1 | 17 |
| pl->en | 1 | 9 |
| uk->en | 1 | 23 |
| tr->en | 1 | 9 |
| ar->en | 1 | 2 |
| hi->en | 1 | 2 |
| ja->en | 1 | 1 |
| ko->en | 1 | 4 |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 1861 ms | 2768 ms | 88 ms | 142 ms | 1 ms |
| en->pt | 1 ms | 3162 ms | 193 ms | 149 ms | 3 ms |
| es->en | 2 ms | 2877 ms | 252 ms | 137 ms | 1 ms |
| fr->en | 0 ms | 3144 ms | 216 ms | 282 ms | 380 ms |
| de->en | 946 ms | 2770 ms | 116 ms | 118 ms | 1 ms |
| it->en | 219 ms | 3009 ms | 114 ms | 193 ms | 1 ms |
| ru->en | 0 ms | 1753 ms | 82 ms | 145 ms | 1 ms |
| zh->en | 126 ms | 1639 ms | 62 ms | 73 ms | 0 ms |
| nl->en | 1 ms | 1850 ms | 121 ms | 169 ms | 1 ms |
| pl->en | 0 ms | 1735 ms | 128 ms | 137 ms | 1 ms |
| uk->en | 0 ms | 1902 ms | 113 ms | 132 ms | 157 ms |
| tr->en | 0 ms | 1835 ms | 70 ms | 101 ms | 0 ms |
| ar->en | 0 ms | 1867 ms | 94 ms | 116 ms | 1 ms |
| hi->en | 0 ms | 2031 ms | 69 ms | 108 ms | 1 ms |
| ja->en | 0 ms | 1723 ms | 76 ms | 134 ms | 1 ms |
| ko->en | 1 ms | 1681 ms | 80 ms | 131 ms | 634 ms |

### Problemas encontrados

- **pt->en**: transcrição ruim: 51% das palavras erradas; inventou 11 palavras que não foram faladas; não acompanha o falante: atraso típico 4.9 s, sobe +1.8 s da 1ª para a 2ª metade e sobram 16 s de tradução quando ele para; trechos esperam 1861 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **en->pt**: transcrição ruim: 30% das palavras erradas; inventou 8 palavras que não foram faladas; não acompanha o falante: atraso típico 4.1 s, sobe +0.9 s da 1ª para a 2ª metade e sobram 10 s de tradução quando ele para
- **es->en**: transcrição ruim: 82% das palavras erradas; inventou 11 palavras que não foram faladas; não acompanha o falante: atraso típico 3.9 s, sobe +0.8 s da 1ª para a 2ª metade e sobram 10 s de tradução quando ele para
- **fr->en**: transcrição ruim: 118% das palavras erradas; inventou 33 palavras que não foram faladas; não acompanha o falante: atraso típico 5.3 s, sobe -0.4 s da 1ª para a 2ª metade e sobram 17 s de tradução quando ele para; a fala traduzida dura 122% da original — quase não sobra folga para acompanhar
- **de->en**: transcrição ruim: 56% das palavras erradas; inventou 7 palavras que não foram faladas; não acompanha o falante: atraso típico 4.3 s, sobe -1.8 s da 1ª para a 2ª metade e sobram 9 s de tradução quando ele para; trechos esperam 946 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **it->en**: transcrição ruim: 85% das palavras erradas; inventou 17 palavras que não foram faladas; não acompanha o falante: atraso típico 4.1 s, sobe -0.9 s da 1ª para a 2ª metade e sobram 13 s de tradução quando ele para; a fala traduzida dura 96% da original — quase não sobra folga para acompanhar
- **ru->en**: transcrição ruim: 119% das palavras erradas; inventou 14 palavras que não foram faladas; não acompanha o falante: atraso típico 2.4 s, sobe -0.5 s da 1ª para a 2ª metade e sobram 10 s de tradução quando ele para
- **zh->en**: transcrição ruim: 380% dos caracteres erradas; inventou 143 caracteres que não foram faladas; não acompanha o falante: atraso típico 2.2 s, sobe -0.6 s da 1ª para a 2ª metade e sobram 11 s de tradução quando ele para
- **nl->en**: transcrição ruim: 110% das palavras erradas; inventou 27 palavras que não foram faladas; não acompanha o falante: atraso típico 3.1 s, sobe +1.0 s da 1ª para a 2ª metade e sobram 14 s de tradução quando ele para; a fala traduzida dura 114% da original — quase não sobra folga para acompanhar
- **pl->en**: transcrição ruim: 67% das palavras erradas; inventou 13 palavras que não foram faladas; não acompanha o falante: atraso típico 2.7 s, sobe +0.9 s da 1ª para a 2ª metade e sobram 10 s de tradução quando ele para; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **uk->en**: transcrição ruim: 174% das palavras erradas; inventou 39 palavras que não foram faladas; não acompanha o falante: atraso típico 3.9 s, sobe -0.5 s da 1ª para a 2ª metade e sobram 13 s de tradução quando ele para; a fala traduzida dura 115% da original — quase não sobra folga para acompanhar; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **tr->en**: transcrição ruim: 54% das palavras erradas; inventou 9 palavras que não foram faladas
- **ar->en**: transcrição ruim: 90% das palavras erradas; inventou 15 palavras que não foram faladas; não acompanha o falante: atraso típico 3.0 s, sobe -0.8 s da 1ª para a 2ª metade e sobram 10 s de tradução quando ele para; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **hi->en**: transcrição ruim: 122% das palavras erradas; inventou 22 palavras que não foram faladas; não acompanha o falante: atraso típico 4.7 s, sobe +4.2 s da 1ª para a 2ª metade e sobram 24 s de tradução quando ele para; a fala traduzida dura 149% da original — quase não sobra folga para acompanhar
- **ja->en**: transcrição ruim: 72% dos caracteres erradas; inventou 49 caracteres que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **ko->en**: transcrição ruim: 61% dos caracteres erradas; inventou 17 caracteres que não foram faladas; não acompanha o falante: atraso típico 3.5 s, sobe +2.5 s da 1ª para a 2ª metade e sobram 9 s de tradução quando ele para

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
