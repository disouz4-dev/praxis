_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `medium` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 71s | 4.8% palavras | 1.5% | 74.0 | 1.3 s | 3.5 s | +0.4 s | 3.6 s | 70% | ✅ |
| en->pt | 72s | 3.7% palavras | 3.1% | 73.5 | 1.0 s | 3.6 s | -0.5 s | 3.9 s | 79% | ✅ |
| es->en | 73s | 4.6% palavras | 1.3% | 69.0 | 1.0 s | 2.5 s | +0.1 s | 1.5 s | 59% | ✅ |
| fr->en | 62s | 16.5% palavras | 9.3% | 61.5 | 1.4 s | 3.6 s | +1.0 s | 3.4 s | 73% | ✅ |
| de->en | 63s | 17.9% palavras | 5.4% | 64.8 | 0.8 s | 2.9 s | -0.1 s | 2.2 s | 60% | ✅ |
| it->en | 78s | 27.1% palavras | 12.2% | 58.9 | 1.8 s | 5.0 s | -0.4 s | 3.2 s | 70% | ✅ |
| ru->en | 66s | 11.4% palavras | 2.9% | 76.8 | 1.7 s | 5.3 s | -0.1 s | 3.3 s | 57% | ✅ |
| zh->en | 62s | 11.8% caracteres | 11.8% | 34.5 | 1.5 s | 2.7 s | +0.1 s | 2.0 s | 54% | ✅ |
| nl->en | 66s | 17.7% palavras | 7.8% | 57.6 | 0.8 s | 2.8 s | -0.1 s | 3.8 s | 63% | ✅ |
| pl->en | 69s | 10.8% palavras | 1.9% | 63.7 | 1.1 s | 2.8 s | +0.3 s | 3.5 s | 80% | ✅ |
| uk->en | 69s | 15.7% palavras | 5.2% | 70.6 | 0.8 s | 3.3 s | -1.1 s | 3.1 s | 59% | ✅ |
| tr->en | 72s | 19.6% palavras | 5.8% | 60.3 | 1.3 s | 4.0 s | -1.2 s | 4.2 s | 49% | ✅ |
| ar->en | 74s | 23.4% palavras | 13.5% | 68.9 | 1.7 s | 3.2 s | -0.1 s | 2.8 s | 61% | ✅ |
| hi->en | 69s | 36.2% palavras | 13.8% | 46.2 | 1.0 s | 3.6 s | -0.3 s | 2.4 s | 58% | ✅ |
| ja->en | 64s | 14.0% caracteres | 14.0% | 60.3 | 1.8 s | 4.2 s | -0.8 s | 2.0 s | 51% | ✅ |
| ko->en | 69s | 8.6% caracteres | 8.6% | 59.9 | 2.3 s | 3.1 s | +0.5 s | 3.9 s | 58% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 381 ms | 26 ms | 69 ms | 0 ms |
| en->pt | 0 ms | 400 ms | 28 ms | 77 ms | 0 ms |
| es->en | 0 ms | 346 ms | 25 ms | 41 ms | 0 ms |
| fr->en | 0 ms | 379 ms | 27 ms | 62 ms | 0 ms |
| de->en | 0 ms | 329 ms | 18 ms | 32 ms | 0 ms |
| it->en | 0 ms | 398 ms | 22 ms | 58 ms | 108 ms |
| ru->en | 0 ms | 400 ms | 25 ms | 68 ms | 0 ms |
| zh->en | 0 ms | 387 ms | 23 ms | 54 ms | 0 ms |
| nl->en | 0 ms | 407 ms | 29 ms | 71 ms | 0 ms |
| pl->en | 0 ms | 419 ms | 30 ms | 78 ms | 63 ms |
| uk->en | 0 ms | 378 ms | 22 ms | 62 ms | 0 ms |
| tr->en | 0 ms | 409 ms | 21 ms | 63 ms | 0 ms |
| ar->en | 0 ms | 466 ms | 23 ms | 71 ms | 0 ms |
| hi->en | 0 ms | 494 ms | 16 ms | 34 ms | 0 ms |
| ja->en | 0 ms | 474 ms | 34 ms | 77 ms | 0 ms |
| ko->en | 0 ms | 408 ms | 27 ms | 72 ms | 1 ms |

### Problemas encontrados

- **pt->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.5 s
- **en->pt**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.6 s
- **es->en**: nenhum problema detectado
- **fr->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.6 s
- **de->en**: 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **it->en**: transcrição ruim: 27% das palavras erradas; inventou 13 palavras que não foram faladas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 5.0 s
- **ru->en**: picos de atraso: 1 em cada 20 trechos demora mais de 5.3 s
- **zh->en**: nenhum problema detectado
- **nl->en**: 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **pl->en**: nenhum problema detectado
- **uk->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 3.3 s
- **tr->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **ar->en**: transcrição ruim: 23% das palavras erradas; inventou 7 palavras que não foram faladas; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 3.2 s
- **hi->en**: transcrição ruim: 36% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.6 s
- **ja->en**: inventou 13 caracteres que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 4.2 s
- **ko->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.1 s

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
