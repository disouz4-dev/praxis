_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `large-v3-turbo` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 14s | 9.1% palavras | 1.5% | 82.3 | 2.5 s | 3.4 s | -0.2 s | 4.1 s | 65% | ✅ |
| en->pt | 14s | 4.7% palavras | 5.9% | 80.3 | 2.0 s | 2.5 s | +1.1 s | 5.1 s | 90% | ✅ |
| es->en | 12s | 0.0% palavras | 0.0% | 91.0 | 1.0 s | 2.4 s | +0.1 s | 2.4 s | 58% | ✅ |
| fr->en | 14s | 0.0% palavras | 0.0% | 74.9 | 1.1 s | 1.9 s | +0.6 s | 3.4 s | 67% | ✅ |
| de->en | 14s | 4.2% palavras | 2.2% | 60.9 | 0.8 s | 0.9 s | +0.0 s | 3.3 s | 54% | ✅ |
| it->en | 16s | 21.6% palavras | 4.2% | 51.0 | 3.0 s | 4.1 s | +0.3 s | 4.0 s | 76% | ✅ |
| ru->en | 17s | 4.8% palavras | 1.5% | 56.4 | 1.7 s | 1.7 s | -0.0 s | 0.7 s | 50% | ✅ |
| zh->en | 15s | 12.0% caracteres | 12.0% | 53.8 | 1.5 s | 1.8 s | +0.1 s | 3.9 s | 78% | ✅ |
| nl->en | 15s | 25.9% palavras | 13.2% | 69.2 | 0.7 s | 0.8 s | +0.2 s | 4.0 s | 59% | ✅ |
| pl->en | 15s | 0.0% palavras | 0.0% | 63.4 | 1.3 s | 2.5 s | +0.2 s | 3.2 s | 76% | ✅ |
| uk->en | 15s | 4.2% palavras | 2.0% | 97.1 | 0.9 s | 0.9 s | +0.2 s | 2.9 s | 55% | ✅ |
| tr->en | 14s | 19.1% palavras | 9.6% | 57.4 | 1.4 s | 1.8 s | -0.4 s | 1.2 s | 44% | ✅ |
| ar->en | 15s | 3.5% palavras | 2.5% | 82.6 | 1.4 s | 3.1 s | +1.2 s | 2.9 s | 54% | ✅ |
| hi->en | 15s | 41.4% palavras | 16.7% | 26.7 | 0.9 s | 1.5 s | +0.7 s | 1.5 s | 53% | ✅ |
| ja->en | 14s | 0.0% caracteres | 0.0% | 74.2 | 2.6 s | 3.3 s | +0.8 s | 2.6 s | 49% | ✅ |
| ko->en | 12s | 6.0% caracteres | 6.0% | 68.8 | 2.6 s | 3.0 s | +0.8 s | 3.9 s | 65% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 417 ms | 20 ms | 51 ms | 1222 ms |
| en->pt | 0 ms | 455 ms | 29 ms | 58 ms | 208 ms |
| es->en | 0 ms | 416 ms | 21 ms | 39 ms | 143 ms |
| fr->en | 0 ms | 450 ms | 27 ms | 87 ms | 0 ms |
| de->en | 0 ms | 432 ms | 16 ms | 31 ms | 0 ms |
| it->en | 0 ms | 433 ms | 22 ms | 64 ms | 1636 ms |
| ru->en | 0 ms | 447 ms | 21 ms | 53 ms | 0 ms |
| zh->en | 0 ms | 496 ms | 34 ms | 71 ms | 202 ms |
| nl->en | 0 ms | 471 ms | 28 ms | 75 ms | 0 ms |
| pl->en | 0 ms | 453 ms | 28 ms | 57 ms | 284 ms |
| uk->en | 0 ms | 474 ms | 32 ms | 88 ms | 0 ms |
| tr->en | 0 ms | 473 ms | 25 ms | 69 ms | 47 ms |
| ar->en | 0 ms | 483 ms | 26 ms | 74 ms | 0 ms |
| hi->en | 0 ms | 417 ms | 13 ms | 23 ms | 7 ms |
| ja->en | 0 ms | 457 ms | 31 ms | 74 ms | 1258 ms |
| ko->en | 0 ms | 459 ms | 37 ms | 95 ms | 424 ms |

### Problemas encontrados

- **pt->en**: a tradução pronta espera 1222 ms a fala anterior terminar de tocar; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.4 s
- **en->pt**: nenhum problema detectado
- **es->en**: nenhum problema detectado
- **fr->en**: nenhum problema detectado
- **de->en**: nenhum problema detectado
- **it->en**: transcrição ruim: 22% das palavras erradas; a tradução pronta espera 1636 ms a fala anterior terminar de tocar; picos de atraso: 1 em cada 20 trechos demora mais de 4.1 s
- **ru->en**: nenhum problema detectado
- **zh->en**: nenhum problema detectado
- **nl->en**: transcrição ruim: 26% das palavras erradas
- **pl->en**: nenhum problema detectado
- **uk->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **tr->en**: nenhum problema detectado
- **ar->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.1 s
- **hi->en**: transcrição ruim: 41% das palavras erradas
- **ja->en**: a tradução pronta espera 1258 ms a fala anterior terminar de tocar; picos de atraso: 1 em cada 20 trechos demora mais de 3.3 s
- **ko->en**: nenhum problema detectado

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
