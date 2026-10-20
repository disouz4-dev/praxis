_Máquina: macOS-26.6.2-x86_64-i386-64bit · processador i386 · Python 3.12.15 · placa de vídeo CUDA: não_

Whisper `small` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 14.0% palavras | 7.6% | 77.9 | 3.1 s | 5.0 s | +0.2 s | 5.8 s | 63% | ✅ |
| en->pt | 20s | 14.8% palavras | 13.7% | 64.4 | 3.3 s | 3.7 s | -0.2 s | 7.5 s | 76% | ✅ |
| es->en | 21s | 2.2% palavras | 0.5% | 48.8 | 3.4 s | 4.2 s | +0.5 s | 4.6 s | 49% | ✅ |
| fr->en | 21s | 26.8% palavras | 10.8% | 61.1 | 5.9 s | 7.2 s | +1.0 s | 7.2 s | 76% | ❌ |
| de->en | 19s | 26.5% palavras | 7.1% | 58.6 | 3.6 s | 5.0 s | -1.2 s | 6.3 s | 59% | ✅ |
| it->en | 20s | 36.2% palavras | 10.3% | 49.9 | 3.6 s | 4.7 s | -1.4 s | 6.8 s | 69% | ✅ |
| ru->en | 19s | 23.1% palavras | 4.1% | 73.8 | 3.8 s | 5.9 s | +0.7 s | 5.6 s | 57% | ✅ |
| zh->en | 19s | 13.6% caracteres | 13.6% | 50.0 | 4.3 s | 5.0 s | +0.3 s | 3.3 s | 46% | ❌ |
| nl->en | 22s | 27.1% palavras | 10.1% | 63.1 | 4.3 s | 6.3 s | +2.1 s | 5.9 s | 71% | ❌ |
| pl->en | 18s | 15.4% palavras | 3.8% | 50.1 | 3.3 s | 3.8 s | +0.5 s | 5.6 s | 74% | ✅ |
| uk->en | 19s | 23.5% palavras | 6.4% | 73.7 | 4.3 s | 7.0 s | -3.6 s | 5.0 s | 71% | ❌ |
| tr->en | 17s | 12.5% palavras | 1.8% | 69.6 | 2.8 s | 3.3 s | -0.6 s | 2.0 s | 41% | ✅ |
| ar->en | 19s | 10.0% palavras | 5.1% | 56.6 | 3.9 s | 4.7 s | -0.3 s | 4.8 s | 61% | ✅ |
| hi->en | 20s | 56.1% palavras | 23.7% | 24.0 | 4.2 s | 5.3 s | +0.5 s | 6.1 s | 58% | ❌ |
| ja->en | 25s | 18.2% caracteres | 18.2% | 49.5 | 3.3 s | 3.8 s | -0.3 s | 4.5 s | 41% | ✅ |
| ko->en | 20s | 4.0% caracteres | 4.0% | 39.4 | 4.0 s | 4.1 s | -0.5 s | 5.7 s | 47% | ❌ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 2283 ms | 104 ms | 181 ms | 1 ms |
| en->pt | 0 ms | 2237 ms | 124 ms | 194 ms | 1 ms |
| es->en | 0 ms | 2227 ms | 216 ms | 112 ms | 1 ms |
| fr->en | 0 ms | 2358 ms | 133 ms | 119 ms | 488 ms |
| de->en | 4 ms | 2235 ms | 134 ms | 132 ms | 1 ms |
| it->en | 0 ms | 2383 ms | 84 ms | 136 ms | 1 ms |
| ru->en | 0 ms | 2237 ms | 115 ms | 160 ms | 206 ms |
| zh->en | 0 ms | 2183 ms | 87 ms | 75 ms | 0 ms |
| nl->en | 643 ms | 2251 ms | 110 ms | 135 ms | 360 ms |
| pl->en | 0 ms | 2533 ms | 194 ms | 178 ms | 1 ms |
| uk->en | 0 ms | 2401 ms | 105 ms | 158 ms | 1 ms |
| tr->en | 0 ms | 2278 ms | 93 ms | 111 ms | 0 ms |
| ar->en | 0 ms | 2451 ms | 94 ms | 117 ms | 145 ms |
| hi->en | 670 ms | 2449 ms | 65 ms | 77 ms | 0 ms |
| ja->en | 0 ms | 2425 ms | 149 ms | 159 ms | 1 ms |
| ko->en | 0 ms | 2378 ms | 104 ms | 147 ms | 1 ms |

### Problemas encontrados

- **pt->en**: 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 5.0 s
- **en->pt**: pulou 1 trecho(s) inteiro(s) da fala (maior: 8 palavras seguidas); picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **es->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.2 s
- **fr->en**: transcrição ruim: 27% das palavras erradas; não acompanha o falante: atraso típico 5.9 s, sobe +1.0 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para
- **de->en**: transcrição ruim: 26% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 5.0 s
- **it->en**: transcrição ruim: 36% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.7 s
- **ru->en**: transcrição ruim: 23% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 5.9 s
- **zh->en**: não acompanha o falante: atraso típico 4.3 s, sobe +0.3 s da 1ª para a 2ª metade e sobram 3 s de tradução quando ele para
- **nl->en**: transcrição ruim: 27% das palavras erradas; inventou 5 palavras que não foram faladas; não acompanha o falante: atraso típico 4.3 s, sobe +2.1 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para; trechos esperam 643 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **pl->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.8 s
- **uk->en**: transcrição ruim: 24% das palavras erradas; não acompanha o falante: atraso típico 4.3 s, sobe -3.6 s da 1ª para a 2ª metade e sobram 5 s de tradução quando ele para
- **tr->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.3 s
- **ar->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.7 s
- **hi->en**: transcrição ruim: 56% das palavras erradas; não acompanha o falante: atraso típico 4.2 s, sobe +0.5 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para; trechos esperam 670 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ja->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.8 s
- **ko->en**: não acompanha o falante: atraso típico 4.0 s, sobe -0.5 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
