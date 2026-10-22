_Máquina: macOS-26.6.2-x86_64-i386-64bit · processador i386 · Python 3.12.15 · placa de vídeo CUDA: não_

Whisper `small` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 18.6% palavras | 11.6% | 73.3 | 2.2 s | 2.9 s | +0.1 s | 4.8 s | 66% | ✅ |
| en->pt | 20s | 5.6% palavras | 3.1% | 71.4 | 3.0 s | 3.2 s | -0.0 s | 6.0 s | 81% | ✅ |
| es->en | 21s | 17.8% palavras | 5.4% | 54.8 | 2.4 s | 3.3 s | -0.2 s | 3.9 s | 57% | ✅ |
| fr->en | 21s | 55.4% palavras | 25.9% | 46.8 | 2.5 s | 4.7 s | -1.2 s | 7.2 s | 81% | ✅ |
| de->en | 19s | 44.1% palavras | 15.2% | 50.9 | 2.2 s | 4.1 s | -1.5 s | 5.3 s | 60% | ✅ |
| it->en | 20s | 40.4% palavras | 14.4% | 47.1 | 3.4 s | 5.2 s | +0.0 s | 5.4 s | 66% | ✅ |
| ru->en | 19s | 38.5% palavras | 23.0% | 58.8 | 2.4 s | 2.4 s | -0.2 s | 4.3 s | 46% | ✅ |
| zh->en | 19s | 65.9% caracteres | 65.9% | 31.6 | 2.7 s | 3.0 s | +0.1 s | 1.4 s | 33% | ✅ |
| nl->en | 22s | 20.8% palavras | 6.6% | 60.4 | 2.1 s | 3.1 s | +0.4 s | 6.6 s | 84% | ✅ |
| pl->en | 18s | 23.1% palavras | 8.1% | 49.8 | 2.2 s | 2.4 s | +0.1 s | 5.1 s | 74% | ✅ |
| uk->en | 19s | 61.8% palavras | 46.3% | 46.8 | 3.8 s | 4.7 s | -2.4 s | 0.0 s | 53% | ✅ |
| tr->en | 17s | 12.5% palavras | 1.8% | 52.9 | 3.4 s | 4.3 s | +0.1 s | 3.3 s | 43% | ✅ |
| ar->en | 19s | 33.3% palavras | 9.5% | 62.0 | 3.6 s | 5.0 s | -0.3 s | 5.3 s | 65% | ✅ |
| hi->en | 20s | 87.8% palavras | 58.8% | 30.5 | 5.1 s | 8.2 s | +2.6 s | 11.3 s | 72% | ❌ |
| ja->en | 25s | 31.8% caracteres | 31.8% | 45.3 | 3.3 s | 4.4 s | -0.8 s | 4.0 s | 55% | ✅ |
| ko->en | 20s | 5.4% caracteres | 5.4% | 39.5 | 3.3 s | 4.0 s | -1.2 s | 3.6 s | 58% | ✅ |

### Eco (a tradução tocada volta pelo microfone)

| Par | Trechos traduzidos depois que o falante parou | Palavras nesses trechos |
|---|---:|---:|
| pt->en | 0 | 0 |
| en->pt | 0 | 0 |
| es->en | 0 | 0 |
| fr->en | 1 | 3 |
| de->en | 0 | 0 |
| it->en | 0 | 0 |
| ru->en | 0 | 0 |
| zh->en | 0 | 0 |
| nl->en | 1 | 1 |
| pl->en | 0 | 0 |
| uk->en | 0 | 0 |
| tr->en | 0 | 0 |
| ar->en | 0 | 0 |
| hi->en | 0 | 0 |
| ja->en | 0 | 0 |
| ko->en | 0 | 0 |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 1373 ms | 78 ms | 139 ms | 4 ms |
| en->pt | 0 ms | 1490 ms | 96 ms | 162 ms | 152 ms |
| es->en | 0 ms | 1441 ms | 130 ms | 110 ms | 2 ms |
| fr->en | 0 ms | 1475 ms | 80 ms | 95 ms | 4 ms |
| de->en | 0 ms | 1440 ms | 81 ms | 67 ms | 2 ms |
| it->en | 0 ms | 1487 ms | 63 ms | 119 ms | 3 ms |
| ru->en | 0 ms | 1538 ms | 69 ms | 145 ms | 2 ms |
| zh->en | 0 ms | 1417 ms | 48 ms | 60 ms | 1 ms |
| nl->en | 0 ms | 1402 ms | 61 ms | 76 ms | 322 ms |
| pl->en | 0 ms | 1493 ms | 118 ms | 141 ms | 2 ms |
| uk->en | 732 ms | 1476 ms | 496 ms | 105 ms | -70 ms |
| tr->en | 0 ms | 1434 ms | 553 ms | 129 ms | 2 ms |
| ar->en | 0 ms | 1532 ms | 650 ms | 135 ms | 2 ms |
| hi->en | 1318 ms | 1669 ms | 408 ms | 78 ms | 2 ms |
| ja->en | 0 ms | 1405 ms | 705 ms | 158 ms | 2 ms |
| ko->en | 0 ms | 1477 ms | 494 ms | 128 ms | 2 ms |

### Problemas encontrados

- **pt->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 3 trecho(s) com fala viraram texto vazio
- **en->pt**: 2 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 3.2 s
- **es->en**: 2 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 3.3 s
- **fr->en**: transcrição ruim: 55% das palavras erradas; inventou 8 palavras que não foram faladas; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 4.7 s
- **de->en**: transcrição ruim: 44% das palavras erradas; inventou 4 palavras que não foram faladas; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 4.1 s
- **it->en**: transcrição ruim: 40% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 5.2 s
- **ru->en**: transcrição ruim: 38% das palavras erradas
- **zh->en**: transcrição ruim: 66% dos caracteres erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 6 caracteres seguidas)
- **nl->en**: transcrição ruim: 21% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.1 s
- **pl->en**: transcrição ruim: 23% das palavras erradas; 2 trecho(s) com fala viraram texto vazio
- **uk->en**: transcrição ruim: 62% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 10 palavras seguidas); trechos esperam 732 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); picos de atraso: 1 em cada 20 trechos demora mais de 4.7 s
- **tr->en**: 2 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 4.3 s
- **ar->en**: transcrição ruim: 33% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 2 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 5.0 s
- **hi->en**: transcrição ruim: 88% das palavras erradas; inventou 7 palavras que não foram faladas; não acompanha o falante: atraso típico 5.1 s, sobe +2.6 s da 1ª para a 2ª metade e sobram 11 s de tradução quando ele para; trechos esperam 1318 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) com fala viraram texto vazio
- **ja->en**: transcrição ruim: 32% dos caracteres erradas; inventou 14 caracteres que não foram faladas; 2 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 4.4 s
- **ko->en**: 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
