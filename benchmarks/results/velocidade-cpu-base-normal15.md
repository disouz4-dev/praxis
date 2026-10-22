_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `base` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 14s | 9.1% palavras | 1.5% | 72.7 | 2.7 s | 3.6 s | -0.5 s | 4.0 s | 68% | ✅ |
| en->pt | 14s | 0.0% palavras | 0.0% | 75.3 | 2.1 s | 2.2 s | +0.9 s | 4.7 s | 86% | ✅ |
| es->en | 12s | 23.1% palavras | 6.7% | 65.2 | 1.0 s | 2.3 s | +0.0 s | 2.6 s | 58% | ✅ |
| fr->en | 14s | 22.5% palavras | 16.5% | 55.3 | 1.2 s | 1.8 s | +0.6 s | 4.4 s | 72% | ✅ |
| de->en | 14s | 37.5% palavras | 10.2% | 47.8 | 0.8 s | 0.9 s | +0.0 s | 3.3 s | 57% | ✅ |
| it->en | 16s | 37.8% palavras | 8.3% | 47.8 | 2.8 s | 4.2 s | +0.6 s | 5.0 s | 80% | ✅ |
| ru->en | 17s | 28.6% palavras | 7.5% | 55.2 | 1.7 s | 2.0 s | +0.1 s | 1.0 s | 52% | ✅ |
| zh->en | 15s | 25.3% caracteres | 25.3% | 40.8 | 1.7 s | 2.3 s | +0.5 s | 4.3 s | 79% | ✅ |
| nl->en | 15s | 37.0% palavras | 24.6% | 50.7 | 0.6 s | 0.8 s | +0.2 s | 3.9 s | 52% | ✅ |
| pl->en | 15s | 29.7% palavras | 6.5% | 56.8 | 1.5 s | 3.0 s | +0.5 s | 3.7 s | 80% | ✅ |
| uk->en | 15s | 33.3% palavras | 6.8% | 65.2 | 0.9 s | 1.0 s | +0.1 s | 3.3 s | 57% | ✅ |
| tr->en | 14s | 33.3% palavras | 12.8% | 50.5 | 1.6 s | 1.8 s | -0.2 s | 0.8 s | 41% | ✅ |
| ar->en | 15s | 41.4% palavras | 14.3% | 33.1 | 1.4 s | 1.7 s | +0.4 s | 1.5 s | 43% | ✅ |
| hi->en | 15s | 96.5% palavras | 94.2% | 19.0 | 1.3 s | 1.4 s | -0.2 s | 2.4 s | 69% | ✅ |
| ja->en | 14s | 23.9% caracteres | 23.9% | 45.6 | 2.4 s | 2.9 s | +0.6 s | 1.6 s | 42% | ✅ |
| ko->en | 12s | 16.0% caracteres | 16.0% | 43.4 | 2.2 s | 2.2 s | -0.0 s | 3.6 s | 63% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 410 ms | 21 ms | 55 ms | 1388 ms |
| en->pt | 0 ms | 430 ms | 29 ms | 59 ms | 413 ms |
| es->en | 0 ms | 379 ms | 24 ms | 41 ms | 128 ms |
| fr->en | 0 ms | 459 ms | 30 ms | 91 ms | 0 ms |
| de->en | 0 ms | 416 ms | 17 ms | 28 ms | 0 ms |
| it->en | 0 ms | 452 ms | 24 ms | 66 ms | 1467 ms |
| ru->en | 0 ms | 458 ms | 27 ms | 61 ms | 0 ms |
| zh->en | 0 ms | 509 ms | 32 ms | 112 ms | 0 ms |
| nl->en | 0 ms | 464 ms | 31 ms | 64 ms | 0 ms |
| pl->en | 0 ms | 461 ms | 29 ms | 62 ms | 462 ms |
| uk->en | 0 ms | 512 ms | 34 ms | 93 ms | 0 ms |
| tr->en | 0 ms | 462 ms | 27 ms | 56 ms | 317 ms |
| ar->en | 0 ms | 506 ms | 35 ms | 45 ms | 0 ms |
| hi->en | 0 ms | 396 ms | 15 ms | 33 ms | 529 ms |
| ja->en | 0 ms | 472 ms | 26 ms | 67 ms | 1028 ms |
| ko->en | 0 ms | 483 ms | 31 ms | 83 ms | 11 ms |

### Problemas encontrados

- **pt->en**: a tradução pronta espera 1388 ms a fala anterior terminar de tocar; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.6 s
- **en->pt**: nenhum problema detectado
- **es->en**: transcrição ruim: 23% das palavras erradas
- **fr->en**: transcrição ruim: 22% das palavras erradas
- **de->en**: transcrição ruim: 38% das palavras erradas
- **it->en**: transcrição ruim: 38% das palavras erradas; a tradução pronta espera 1467 ms a fala anterior terminar de tocar; picos de atraso: 1 em cada 20 trechos demora mais de 4.2 s
- **ru->en**: transcrição ruim: 29% das palavras erradas
- **zh->en**: transcrição ruim: 25% dos caracteres erradas
- **nl->en**: transcrição ruim: 37% das palavras erradas
- **pl->en**: transcrição ruim: 30% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.0 s
- **uk->en**: transcrição ruim: 33% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **tr->en**: transcrição ruim: 33% das palavras erradas
- **ar->en**: transcrição ruim: 41% das palavras erradas
- **hi->en**: transcrição ruim: 97% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 8 palavras seguidas)
- **ja->en**: transcrição ruim: 24% dos caracteres erradas; a tradução pronta espera 1028 ms a fala anterior terminar de tocar
- **ko->en**: nenhum problema detectado

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
