_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `medium` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 7.0% palavras | 3.5% | 74.8 | 1.0 s | 3.6 s | -1.2 s | 3.8 s | 71% | ✅ |
| en->pt | 20s | 5.6% palavras | 6.2% | 78.6 | 1.5 s | 3.0 s | +0.6 s | 5.3 s | 90% | ✅ |
| es->en | 21s | 4.4% palavras | 1.1% | 61.6 | 1.0 s | 1.8 s | +0.3 s | 2.0 s | 54% | ✅ |
| fr->en | 21s | 19.6% palavras | 6.0% | 48.1 | 1.8 s | 3.1 s | +0.6 s | 4.6 s | 70% | ✅ |
| de->en | 19s | 11.8% palavras | 4.9% | 67.1 | 0.8 s | 1.3 s | -0.3 s | 4.6 s | 61% | ✅ |
| it->en | 20s | 19.1% palavras | 5.6% | 47.3 | 1.6 s | 2.9 s | -1.6 s | 2.9 s | 65% | ✅ |
| ru->en | 19s | 15.4% palavras | 2.5% | 75.6 | 1.7 s | 4.0 s | +0.6 s | 3.7 s | 59% | ✅ |
| zh->en | 19s | 9.1% caracteres | 9.1% | 62.0 | 2.1 s | 2.9 s | -0.0 s | 0.8 s | 50% | ✅ |
| nl->en | 22s | 12.5% palavras | 3.1% | 71.5 | 1.6 s | 2.5 s | +1.0 s | 3.6 s | 64% | ✅ |
| pl->en | 18s | 7.7% palavras | 0.9% | 49.3 | 0.9 s | 1.7 s | +0.5 s | 4.5 s | 79% | ✅ |
| uk->en | 19s | 8.8% palavras | 4.3% | 78.5 | 1.2 s | 2.7 s | -1.9 s | 2.9 s | 72% | ✅ |
| tr->en | 17s | 0.0% palavras | 0.0% | 56.5 | 0.8 s | 1.3 s | -0.5 s | 0.0 s | 34% | ✅ |
| ar->en | 19s | 13.3% palavras | 9.5% | 57.8 | 1.6 s | 2.2 s | -0.1 s | 2.3 s | 51% | ✅ |
| hi->en | 20s | 46.3% palavras | 18.1% | 24.0 | 0.9 s | 1.3 s | +0.5 s | 3.1 s | 54% | ✅ |
| ja->en | 25s | 15.9% caracteres | 15.9% | 62.5 | 1.7 s | 3.1 s | -1.5 s | 2.0 s | 47% | ✅ |
| ko->en | 20s | 4.0% caracteres | 4.0% | 61.5 | 2.0 s | 2.6 s | -1.2 s | 3.7 s | 62% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 397 ms | 25 ms | 65 ms | 0 ms |
| en->pt | 0 ms | 394 ms | 27 ms | 85 ms | 1 ms |
| es->en | 0 ms | 366 ms | 26 ms | 39 ms | 0 ms |
| fr->en | 0 ms | 435 ms | 29 ms | 50 ms | 647 ms |
| de->en | 0 ms | 379 ms | 30 ms | 43 ms | 0 ms |
| it->en | 0 ms | 396 ms | 20 ms | 54 ms | 0 ms |
| ru->en | 0 ms | 419 ms | 26 ms | 71 ms | 119 ms |
| zh->en | 0 ms | 314 ms | 14 ms | 33 ms | 1 ms |
| nl->en | 0 ms | 368 ms | 21 ms | 46 ms | 1 ms |
| pl->en | 0 ms | 455 ms | 36 ms | 80 ms | 0 ms |
| uk->en | 0 ms | 446 ms | 25 ms | 63 ms | 0 ms |
| tr->en | 0 ms | 403 ms | 16 ms | 34 ms | 0 ms |
| ar->en | 0 ms | 440 ms | 20 ms | 60 ms | 0 ms |
| hi->en | 0 ms | 393 ms | 11 ms | 30 ms | 0 ms |
| ja->en | 0 ms | 468 ms | 30 ms | 84 ms | 0 ms |
| ko->en | 0 ms | 425 ms | 33 ms | 85 ms | 0 ms |

### Problemas encontrados

- **pt->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.6 s
- **en->pt**: nenhum problema detectado
- **es->en**: nenhum problema detectado
- **fr->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.1 s
- **de->en**: nenhum problema detectado
- **it->en**: nenhum problema detectado
- **ru->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **zh->en**: nenhum problema detectado
- **nl->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **pl->en**: nenhum problema detectado
- **uk->en**: nenhum problema detectado
- **tr->en**: nenhum problema detectado
- **ar->en**: nenhum problema detectado
- **hi->en**: transcrição ruim: 46% das palavras erradas
- **ja->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.1 s
- **ko->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
