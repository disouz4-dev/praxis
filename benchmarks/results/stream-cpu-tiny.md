_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `tiny` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 71s | 32.3% palavras | 10.1% | 60.1 | 1.1 s | 3.6 s | -0.1 s | 3.9 s | 72% | ✅ |
| en->pt | 72s | 6.8% palavras | 3.4% | 69.1 | 0.9 s | 2.6 s | -0.5 s | 4.2 s | 78% | ✅ |
| es->en | 73s | 17.8% palavras | 5.8% | 60.4 | 0.7 s | 1.7 s | -0.1 s | 1.3 s | 57% | ✅ |
| fr->en | 62s | 50.6% palavras | 23.8% | 54.1 | 1.2 s | 5.0 s | +0.6 s | 2.9 s | 73% | ✅ |
| de->en | 63s | 57.6% palavras | 21.1% | 53.8 | 0.8 s | 3.1 s | -0.0 s | 1.7 s | 63% | ✅ |
| it->en | 78s | 58.8% palavras | 13.9% | 46.0 | 1.4 s | 4.0 s | -0.4 s | 4.6 s | 70% | ✅ |
| ru->en | 66s | 22.7% palavras | 6.8% | 72.4 | 1.6 s | 4.7 s | +0.1 s | 3.2 s | 56% | ✅ |
| zh->en | 62s | 44.6% caracteres | 44.6% | 25.3 | 1.2 s | 2.6 s | -0.6 s | 1.1 s | 51% | ✅ |
| nl->en | 66s | 42.9% palavras | 19.6% | 46.6 | 0.6 s | 2.4 s | -0.1 s | 3.7 s | 61% | ✅ |
| pl->en | 69s | 50.0% palavras | 11.9% | 51.9 | 0.8 s | 1.8 s | +0.1 s | 3.4 s | 75% | ✅ |
| uk->en | 69s | 64.5% palavras | 19.2% | 46.8 | 0.8 s | 3.9 s | -1.3 s | 4.5 s | 62% | ✅ |
| tr->en | 72s | 65.0% palavras | 23.6% | 46.7 | 1.1 s | 2.9 s | -1.1 s | 4.3 s | 51% | ✅ |
| ar->en | 74s | 65.6% palavras | 23.4% | 43.5 | 1.5 s | 4.8 s | +0.0 s | 1.6 s | 66% | ✅ |
| hi->en | 69s | 157.1% palavras | 112.6% | 23.0 | 1.3 s | 4.5 s | -0.7 s | 6.0 s | 78% | ✅ |
| ja->en | 64s | 42.8% caracteres | 42.8% | 39.5 | 1.6 s | 4.6 s | -0.6 s | 2.9 s | 52% | ✅ |
| ko->en | 69s | 50.2% caracteres | 50.2% | 36.3 | 1.1 s | 2.1 s | -0.3 s | 0.0 s | 40% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 257 ms | 27 ms | 69 ms | 0 ms |
| en->pt | 0 ms | 255 ms | 31 ms | 78 ms | 0 ms |
| es->en | 0 ms | 243 ms | 27 ms | 36 ms | 0 ms |
| fr->en | 0 ms | 256 ms | 26 ms | 53 ms | 70 ms |
| de->en | 0 ms | 223 ms | 26 ms | 35 ms | 0 ms |
| it->en | 0 ms | 267 ms | 20 ms | 53 ms | 0 ms |
| ru->en | 0 ms | 269 ms | 29 ms | 64 ms | 0 ms |
| zh->en | 0 ms | 258 ms | 27 ms | 56 ms | 0 ms |
| nl->en | 0 ms | 269 ms | 30 ms | 53 ms | 0 ms |
| pl->en | 0 ms | 275 ms | 34 ms | 63 ms | 0 ms |
| uk->en | 0 ms | 259 ms | 27 ms | 44 ms | 0 ms |
| tr->en | 0 ms | 276 ms | 24 ms | 47 ms | 0 ms |
| ar->en | 0 ms | 282 ms | 34 ms | 67 ms | 0 ms |
| hi->en | 0 ms | 261 ms | 22 ms | 47 ms | 0 ms |
| ja->en | 0 ms | 291 ms | 37 ms | 93 ms | 0 ms |
| ko->en | 0 ms | 299 ms | 22 ms | 66 ms | 0 ms |

### Problemas encontrados

- **pt->en**: transcrição ruim: 32% das palavras erradas; inventou 9 palavras que não foram faladas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.6 s
- **en->pt**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **es->en**: nenhum problema detectado
- **fr->en**: transcrição ruim: 51% das palavras erradas; inventou 19 palavras que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 5.0 s
- **de->en**: transcrição ruim: 58% das palavras erradas; inventou 17 palavras que não foram faladas; 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.1 s
- **it->en**: transcrição ruim: 59% das palavras erradas; inventou 12 palavras que não foram faladas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **ru->en**: transcrição ruim: 23% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.7 s
- **zh->en**: transcrição ruim: 45% dos caracteres erradas
- **nl->en**: transcrição ruim: 43% das palavras erradas; inventou 12 palavras que não foram faladas; 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **pl->en**: transcrição ruim: 50% das palavras erradas; inventou 8 palavras que não foram faladas
- **uk->en**: transcrição ruim: 64% das palavras erradas; inventou 8 palavras que não foram faladas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 3.9 s
- **tr->en**: transcrição ruim: 65% das palavras erradas; inventou 15 palavras que não foram faladas
- **ar->en**: transcrição ruim: 66% das palavras erradas; inventou 13 palavras que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 4.8 s
- **hi->en**: transcrição ruim: 157% das palavras erradas; inventou 85 palavras que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 4.5 s
- **ja->en**: transcrição ruim: 43% dos caracteres erradas; inventou 14 caracteres que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 4.6 s
- **ko->en**: transcrição ruim: 50% dos caracteres erradas; pulou 5 trecho(s) inteiro(s) da fala (maior: 20 caracteres seguidas); 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
