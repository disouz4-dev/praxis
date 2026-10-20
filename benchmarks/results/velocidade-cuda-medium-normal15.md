_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `medium` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 14s | 15.2% palavras | 6.0% | 73.8 | 2.6 s | 3.8 s | -0.6 s | 4.1 s | 72% | ✅ |
| en->pt | 14s | 7.0% palavras | 8.5% | 74.7 | 1.8 s | 2.9 s | +1.2 s | 5.8 s | 93% | ✅ |
| es->en | 12s | 3.9% palavras | 1.9% | 77.0 | 0.9 s | 0.9 s | -0.1 s | 2.5 s | 60% | ✅ |
| fr->en | 14s | 15.0% palavras | 9.2% | 56.7 | 1.1 s | 2.4 s | +1.0 s | 3.5 s | 69% | ✅ |
| de->en | 14s | 12.5% palavras | 3.6% | 56.2 | 0.8 s | 0.9 s | +0.0 s | 3.1 s | 56% | ✅ |
| it->en | 16s | 56.8% palavras | 32.1% | 44.7 | 3.5 s | 5.1 s | +0.3 s | 5.7 s | 90% | ✅ |
| ru->en | 17s | 4.8% palavras | 1.5% | 56.3 | 1.6 s | 2.1 s | +0.2 s | 0.7 s | 52% | ✅ |
| zh->en | 15s | 14.5% caracteres | 14.5% | 56.4 | 1.9 s | 2.2 s | +0.5 s | 4.3 s | 81% | ✅ |
| nl->en | 15s | 18.5% palavras | 13.2% | 69.2 | 0.6 s | 0.7 s | +0.2 s | 4.2 s | 62% | ✅ |
| pl->en | 15s | 10.8% palavras | 1.6% | 63.1 | 1.4 s | 2.8 s | +0.3 s | 3.7 s | 80% | ✅ |
| uk->en | 15s | 4.2% palavras | 1.4% | 89.3 | 0.9 s | 0.9 s | +0.1 s | 3.1 s | 56% | ✅ |
| tr->en | 14s | 19.1% palavras | 9.6% | 59.6 | 1.7 s | 1.8 s | -0.1 s | 1.6 s | 48% | ✅ |
| ar->en | 15s | 0.0% palavras | 0.0% | 79.8 | 1.4 s | 3.2 s | +1.3 s | 3.0 s | 55% | ✅ |
| hi->en | 15s | 48.3% palavras | 20.0% | 23.0 | 0.9 s | 1.3 s | +0.4 s | 2.1 s | 59% | ✅ |
| ja->en | 14s | 0.0% caracteres | 0.0% | 74.2 | 2.7 s | 3.6 s | +0.9 s | 2.8 s | 50% | ✅ |
| ko->en | 12s | 16.0% caracteres | 16.0% | 69.1 | 2.8 s | 3.3 s | +1.1 s | 4.2 s | 68% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 342 ms | 22 ms | 59 ms | 1410 ms |
| en->pt | 0 ms | 398 ms | 25 ms | 60 ms | 1 ms |
| es->en | 0 ms | 339 ms | 28 ms | 42 ms | 0 ms |
| fr->en | 0 ms | 421 ms | 28 ms | 87 ms | 0 ms |
| de->en | 0 ms | 325 ms | 16 ms | 34 ms | 0 ms |
| it->en | 0 ms | 399 ms | 24 ms | 74 ms | 2158 ms |
| ru->en | 0 ms | 373 ms | 19 ms | 56 ms | 0 ms |
| zh->en | 0 ms | 524 ms | 33 ms | 82 ms | 519 ms |
| nl->en | 0 ms | 413 ms | 28 ms | 75 ms | 0 ms |
| pl->en | 0 ms | 397 ms | 27 ms | 66 ms | 411 ms |
| uk->en | 0 ms | 468 ms | 32 ms | 90 ms | 0 ms |
| tr->en | 0 ms | 414 ms | 24 ms | 77 ms | 424 ms |
| ar->en | 0 ms | 499 ms | 24 ms | 76 ms | 0 ms |
| hi->en | 0 ms | 381 ms | 10 ms | 27 ms | 0 ms |
| ja->en | 0 ms | 434 ms | 31 ms | 77 ms | 1419 ms |
| ko->en | 0 ms | 431 ms | 36 ms | 93 ms | 600 ms |

### Problemas encontrados

- **pt->en**: a tradução pronta espera 1410 ms a fala anterior terminar de tocar; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.8 s
- **en->pt**: nenhum problema detectado
- **es->en**: nenhum problema detectado
- **fr->en**: nenhum problema detectado
- **de->en**: nenhum problema detectado
- **it->en**: transcrição ruim: 57% das palavras erradas; inventou 10 palavras que não foram faladas; a tradução pronta espera 2158 ms a fala anterior terminar de tocar; picos de atraso: 1 em cada 20 trechos demora mais de 5.1 s
- **ru->en**: nenhum problema detectado
- **zh->en**: nenhum problema detectado
- **nl->en**: nenhum problema detectado
- **pl->en**: nenhum problema detectado
- **uk->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **tr->en**: nenhum problema detectado
- **ar->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.2 s
- **hi->en**: transcrição ruim: 48% das palavras erradas
- **ja->en**: a tradução pronta espera 1419 ms a fala anterior terminar de tocar; picos de atraso: 1 em cada 20 trechos demora mais de 3.6 s
- **ko->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.3 s

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
