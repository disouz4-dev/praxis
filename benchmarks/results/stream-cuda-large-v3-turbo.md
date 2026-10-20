_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `large-v3-turbo` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 71s | 4.8% palavras | 1.4% | 76.9 | 1.1 s | 3.6 s | +0.2 s | 3.6 s | 66% | ✅ |
| en->pt | 72s | 1.1% palavras | 0.7% | 74.6 | 1.1 s | 3.6 s | -0.5 s | 4.0 s | 78% | ✅ |
| es->en | 73s | 2.6% palavras | 0.8% | 70.6 | 0.9 s | 2.2 s | -0.0 s | 1.5 s | 56% | ✅ |
| fr->en | 62s | 8.2% palavras | 5.6% | 68.3 | 1.3 s | 3.1 s | -0.4 s | 3.3 s | 66% | ✅ |
| de->en | 63s | 17.9% palavras | 5.4% | 60.0 | 0.9 s | 2.8 s | -0.0 s | 2.1 s | 54% | ✅ |
| it->en | 78s | 13.6% palavras | 4.5% | 61.1 | 1.5 s | 3.8 s | -0.1 s | 4.2 s | 64% | ✅ |
| ru->en | 66s | 6.8% palavras | 4.4% | 77.1 | 1.8 s | 5.2 s | +0.0 s | 2.8 s | 54% | ✅ |
| zh->en | 62s | 5.6% caracteres | 5.6% | 38.5 | 1.4 s | 2.7 s | +0.2 s | 1.7 s | 50% | ✅ |
| nl->en | 66s | 12.2% palavras | 3.5% | 63.0 | 0.9 s | 2.7 s | +0.8 s | 4.0 s | 66% | ✅ |
| pl->en | 69s | 3.2% palavras | 0.6% | 65.4 | 0.9 s | 1.9 s | +0.1 s | 3.3 s | 76% | ✅ |
| uk->en | 69s | 8.3% palavras | 4.3% | 72.5 | 0.8 s | 3.2 s | -1.0 s | 3.9 s | 59% | ✅ |
| tr->en | 72s | 12.4% palavras | 4.1% | 65.4 | 1.4 s | 4.2 s | -1.0 s | 4.0 s | 49% | ✅ |
| ar->en | 74s | 13.3% palavras | 6.1% | 68.7 | 1.6 s | 3.5 s | +0.1 s | 3.4 s | 60% | ✅ |
| hi->en | 69s | 33.6% palavras | 14.6% | 50.7 | 0.9 s | 3.4 s | -0.5 s | 1.6 s | 57% | ✅ |
| ja->en | 64s | 11.2% caracteres | 11.2% | 56.6 | 1.8 s | 4.1 s | -0.8 s | 2.2 s | 51% | ✅ |
| ko->en | 69s | 6.7% caracteres | 6.7% | 61.6 | 2.3 s | 2.9 s | +0.3 s | 3.8 s | 58% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 447 ms | 23 ms | 64 ms | 0 ms |
| en->pt | 0 ms | 445 ms | 28 ms | 83 ms | 0 ms |
| es->en | 0 ms | 438 ms | 24 ms | 40 ms | 0 ms |
| fr->en | 0 ms | 447 ms | 25 ms | 54 ms | 0 ms |
| de->en | 0 ms | 427 ms | 18 ms | 27 ms | 0 ms |
| it->en | 0 ms | 449 ms | 19 ms | 57 ms | 0 ms |
| ru->en | 0 ms | 460 ms | 26 ms | 63 ms | 0 ms |
| zh->en | 0 ms | 446 ms | 23 ms | 48 ms | 0 ms |
| nl->en | 0 ms | 453 ms | 30 ms | 65 ms | 0 ms |
| pl->en | 0 ms | 461 ms | 29 ms | 64 ms | 0 ms |
| uk->en | 0 ms | 452 ms | 21 ms | 53 ms | 0 ms |
| tr->en | 0 ms | 446 ms | 20 ms | 61 ms | 0 ms |
| ar->en | 0 ms | 472 ms | 26 ms | 73 ms | 0 ms |
| hi->en | 0 ms | 465 ms | 15 ms | 35 ms | 0 ms |
| ja->en | 0 ms | 475 ms | 35 ms | 86 ms | 0 ms |
| ko->en | 0 ms | 460 ms | 25 ms | 79 ms | 1 ms |

### Problemas encontrados

- **pt->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.6 s
- **en->pt**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.6 s
- **es->en**: nenhum problema detectado
- **fr->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.1 s
- **de->en**: 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **it->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.8 s
- **ru->en**: picos de atraso: 1 em cada 20 trechos demora mais de 5.2 s
- **zh->en**: nenhum problema detectado
- **nl->en**: 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **pl->en**: nenhum problema detectado
- **uk->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 3.2 s
- **tr->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.2 s
- **ar->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.5 s
- **hi->en**: transcrição ruim: 34% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.4 s
- **ja->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.1 s
- **ko->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
