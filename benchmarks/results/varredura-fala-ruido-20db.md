_Máquina: macOS-26.6.2-x86_64-i386-64bit · processador i386 · Python 3.12.15 · placa de vídeo CUDA: não_

Whisper `small` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 14.0% palavras | 5.1% | 74.4 | 3.0 s | 4.9 s | -1.0 s | 3.8 s | 67% | ✅ |
| en->pt | 20s | 0.0% palavras | 0.0% | 74.3 | 3.4 s | 4.1 s | +1.1 s | 7.4 s | 86% | ✅ |
| es->en | 21s | 11.1% palavras | 1.6% | 53.0 | 3.8 s | 4.4 s | +0.4 s | 4.7 s | 53% | ✅ |
| fr->en | 21s | 33.9% palavras | 13.9% | 58.1 | 5.3 s | 6.5 s | -0.1 s | 8.2 s | 79% | ❌ |
| de->en | 19s | 47.1% palavras | 16.3% | 55.7 | 3.0 s | 4.0 s | -0.5 s | 6.0 s | 58% | ✅ |
| it->en | 20s | 40.4% palavras | 11.3% | 46.2 | 3.2 s | 4.0 s | +0.2 s | 6.8 s | 76% | ✅ |
| ru->en | 19s | 26.9% palavras | 4.6% | 70.7 | 5.0 s | 6.8 s | -0.4 s | 5.6 s | 61% | ❌ |
| zh->en | 19s | 22.7% caracteres | 22.7% | 49.6 | 3.1 s | 4.1 s | -0.2 s | 2.5 s | 52% | ✅ |
| nl->en | 22s | 25.0% palavras | 9.2% | 62.3 | 3.1 s | 4.9 s | +2.0 s | 3.6 s | 60% | ❌ |
| pl->en | 18s | 15.4% palavras | 3.8% | 43.4 | 3.4 s | 4.3 s | +0.6 s | 6.3 s | 78% | ✅ |
| uk->en | 19s | 67.7% palavras | 49.5% | 29.0 | 4.3 s | 4.5 s | +0.2 s | 0.0 s | 35% | ❌ |
| tr->en | 17s | 8.3% palavras | 1.2% | 64.1 | 2.7 s | 3.0 s | -0.3 s | 1.6 s | 40% | ✅ |
| ar->en | 19s | 10.0% palavras | 2.5% | 55.6 | 3.5 s | 6.0 s | +1.2 s | 4.1 s | 55% | ✅ |
| hi->en | 20s | 65.8% palavras | 39.0% | 31.8 | 3.7 s | 4.5 s | +0.7 s | 6.4 s | 62% | ✅ |
| ja->en | 25s | 25.0% caracteres | 25.0% | 49.7 | 3.0 s | 3.7 s | -0.2 s | 4.4 s | 46% | ✅ |
| ko->en | 20s | 6.8% caracteres | 6.8% | 50.1 | 3.6 s | 4.7 s | -0.7 s | 6.2 s | 54% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 93 ms | 2177 ms | 59 ms | 111 ms | 276 ms |
| en->pt | 1 ms | 2165 ms | 99 ms | 187 ms | 1 ms |
| es->en | 0 ms | 2617 ms | 192 ms | 106 ms | 1 ms |
| fr->en | 0 ms | 2627 ms | 150 ms | 130 ms | 365 ms |
| de->en | 0 ms | 2319 ms | 89 ms | 114 ms | 0 ms |
| it->en | 0 ms | 2450 ms | 94 ms | 184 ms | 1 ms |
| ru->en | 1390 ms | 2464 ms | 109 ms | 158 ms | 1 ms |
| zh->en | 0 ms | 1441 ms | 57 ms | 81 ms | 0 ms |
| nl->en | 613 ms | 2249 ms | 90 ms | 115 ms | 2 ms |
| pl->en | 0 ms | 2542 ms | 162 ms | 164 ms | 200 ms |
| uk->en | 330 ms | 2293 ms | 148 ms | 152 ms | 522 ms |
| tr->en | 0 ms | 2186 ms | 83 ms | 112 ms | 1 ms |
| ar->en | 1 ms | 2200 ms | 65 ms | 119 ms | 1 ms |
| hi->en | 547 ms | 2231 ms | 67 ms | 79 ms | 0 ms |
| ja->en | 1 ms | 2233 ms | 153 ms | 229 ms | 0 ms |
| ko->en | 0 ms | 2357 ms | 123 ms | 185 ms | 1 ms |

### Problemas encontrados

- **pt->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.9 s
- **en->pt**: picos de atraso: 1 em cada 20 trechos demora mais de 4.1 s
- **es->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.4 s
- **fr->en**: transcrição ruim: 34% das palavras erradas; não acompanha o falante: atraso típico 5.3 s, sobe -0.1 s da 1ª para a 2ª metade e sobram 8 s de tradução quando ele para
- **de->en**: transcrição ruim: 47% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **it->en**: transcrição ruim: 40% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **ru->en**: transcrição ruim: 27% das palavras erradas; não acompanha o falante: atraso típico 5.0 s, sobe -0.4 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para; trechos esperam 1390 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **zh->en**: transcrição ruim: 23% dos caracteres erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.1 s
- **nl->en**: transcrição ruim: 25% das palavras erradas; não acompanha o falante: atraso típico 3.1 s, sobe +2.0 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para; trechos esperam 613 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) com fala viraram texto vazio
- **pl->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.3 s
- **uk->en**: transcrição ruim: 68% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 17 palavras seguidas); não acompanha o falante: atraso típico 4.3 s, sobe +0.2 s da 1ª para a 2ª metade e sobram 0 s de tradução quando ele para
- **tr->en**: nenhum problema detectado
- **ar->en**: picos de atraso: 1 em cada 20 trechos demora mais de 6.0 s
- **hi->en**: transcrição ruim: 66% das palavras erradas; trechos esperam 547 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); picos de atraso: 1 em cada 20 trechos demora mais de 4.5 s
- **ja->en**: transcrição ruim: 25% dos caracteres erradas; inventou 6 caracteres que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **ko->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 4.7 s

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
