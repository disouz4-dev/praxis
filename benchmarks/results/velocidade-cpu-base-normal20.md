_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `base` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 14.0% palavras | 7.6% | 71.8 | 1.0 s | 3.4 s | -1.1 s | 3.6 s | 69% | ✅ |
| en->pt | 20s | 3.7% palavras | 0.0% | 73.4 | 1.6 s | 2.1 s | +0.8 s | 4.5 s | 82% | ✅ |
| es->en | 21s | 13.3% palavras | 2.2% | 54.3 | 0.9 s | 1.9 s | +0.1 s | 1.8 s | 54% | ✅ |
| fr->en | 21s | 42.9% palavras | 15.9% | 58.7 | 2.4 s | 3.6 s | +0.2 s | 5.2 s | 77% | ✅ |
| de->en | 19s | 44.1% palavras | 13.6% | 50.0 | 1.4 s | 2.8 s | -0.6 s | 4.7 s | 62% | ✅ |
| it->en | 20s | 36.2% palavras | 9.7% | 47.5 | 1.6 s | 3.4 s | -1.6 s | 4.5 s | 78% | ✅ |
| ru->en | 19s | 34.6% palavras | 6.6% | 69.2 | 1.9 s | 3.6 s | +0.8 s | 3.2 s | 58% | ✅ |
| zh->en | 19s | 15.9% caracteres | 15.9% | 55.8 | 2.4 s | 3.0 s | +0.3 s | 1.1 s | 48% | ✅ |
| nl->en | 22s | 33.3% palavras | 9.7% | 61.9 | 1.7 s | 2.7 s | +1.3 s | 3.8 s | 69% | ✅ |
| pl->en | 18s | 38.5% palavras | 7.1% | 44.4 | 1.3 s | 1.8 s | +0.8 s | 4.0 s | 80% | ✅ |
| uk->en | 19s | 52.9% palavras | 14.9% | 51.1 | 1.3 s | 2.2 s | -1.6 s | 2.4 s | 60% | ✅ |
| tr->en | 17s | 29.2% palavras | 4.9% | 63.2 | 0.9 s | 1.4 s | -0.5 s | 0.4 s | 47% | ✅ |
| ar->en | 19s | 36.7% palavras | 10.8% | 46.5 | 1.7 s | 2.3 s | -0.2 s | 2.4 s | 56% | ✅ |
| hi->en | 20s | 97.6% palavras | 96.0% | 21.6 | 1.1 s | 1.5 s | -0.2 s | 4.7 s | 71% | ✅ |
| ja->en | 25s | 26.1% caracteres | 26.1% | 46.3 | 1.4 s | 1.7 s | -0.5 s | 2.4 s | 45% | ✅ |
| ko->en | 20s | 116.2% caracteres | 116.2% | 24.3 | 2.0 s | 2.1 s | +0.2 s | 1.9 s | 37% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 439 ms | 27 ms | 69 ms | 0 ms |
| en->pt | 0 ms | 426 ms | 29 ms | 72 ms | 173 ms |
| es->en | 0 ms | 405 ms | 29 ms | 49 ms | 0 ms |
| fr->en | 0 ms | 463 ms | 34 ms | 50 ms | 1216 ms |
| de->en | 0 ms | 452 ms | 31 ms | 48 ms | 0 ms |
| it->en | 0 ms | 463 ms | 27 ms | 45 ms | 1 ms |
| ru->en | 0 ms | 457 ms | 25 ms | 66 ms | 354 ms |
| zh->en | 0 ms | 372 ms | 15 ms | 32 ms | 0 ms |
| nl->en | 0 ms | 436 ms | 22 ms | 48 ms | 1 ms |
| pl->en | 0 ms | 496 ms | 44 ms | 73 ms | 392 ms |
| uk->en | 0 ms | 485 ms | 22 ms | 58 ms | 0 ms |
| tr->en | 0 ms | 478 ms | 17 ms | 44 ms | 0 ms |
| ar->en | 0 ms | 489 ms | 22 ms | 37 ms | 1 ms |
| hi->en | 0 ms | 400 ms | 19 ms | 41 ms | 212 ms |
| ja->en | 0 ms | 492 ms | 39 ms | 83 ms | 0 ms |
| ko->en | 0 ms | 468 ms | 30 ms | 54 ms | 0 ms |

### Problemas encontrados

- **pt->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.4 s
- **en->pt**: nenhum problema detectado
- **es->en**: nenhum problema detectado
- **fr->en**: transcrição ruim: 43% das palavras erradas; inventou 7 palavras que não foram faladas; a tradução pronta espera 1216 ms a fala anterior terminar de tocar; picos de atraso: 1 em cada 20 trechos demora mais de 3.6 s
- **de->en**: transcrição ruim: 44% das palavras erradas
- **it->en**: transcrição ruim: 36% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.4 s
- **ru->en**: transcrição ruim: 35% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.6 s
- **zh->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.0 s
- **nl->en**: transcrição ruim: 33% das palavras erradas; inventou 5 palavras que não foram faladas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **pl->en**: transcrição ruim: 38% das palavras erradas
- **uk->en**: transcrição ruim: 53% das palavras erradas
- **tr->en**: transcrição ruim: 29% das palavras erradas
- **ar->en**: transcrição ruim: 37% das palavras erradas
- **hi->en**: transcrição ruim: 98% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 8 palavras seguidas)
- **ja->en**: transcrição ruim: 26% dos caracteres erradas; inventou 6 caracteres que não foram faladas
- **ko->en**: transcrição ruim: 116% dos caracteres erradas; inventou 59 caracteres que não foram faladas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
