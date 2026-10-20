_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `large-v3-turbo` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 7.0% palavras | 3.0% | 78.3 | 1.1 s | 4.0 s | -1.4 s | 3.9 s | 70% | ✅ |
| en->pt | 20s | 3.7% palavras | 4.3% | 83.2 | 1.6 s | 2.3 s | +0.7 s | 5.3 s | 88% | ✅ |
| es->en | 21s | 4.4% palavras | 1.1% | 61.3 | 0.9 s | 1.9 s | +0.1 s | 2.2 s | 55% | ✅ |
| fr->en | 21s | 7.1% palavras | 2.8% | 66.6 | 1.8 s | 2.8 s | -0.1 s | 4.0 s | 70% | ✅ |
| de->en | 19s | 20.6% palavras | 2.7% | 66.0 | 1.4 s | 2.5 s | -0.6 s | 4.2 s | 59% | ✅ |
| it->en | 20s | 4.3% palavras | 1.5% | 57.7 | 1.7 s | 2.5 s | -1.3 s | 4.2 s | 70% | ✅ |
| ru->en | 19s | 11.5% palavras | 7.1% | 65.9 | 1.7 s | 3.7 s | +0.5 s | 2.9 s | 56% | ✅ |
| zh->en | 19s | 2.3% caracteres | 2.3% | 64.9 | 1.6 s | 3.0 s | -0.6 s | 0.3 s | 41% | ✅ |
| nl->en | 22s | 16.7% palavras | 5.7% | 70.9 | 1.6 s | 2.6 s | +0.9 s | 3.7 s | 61% | ✅ |
| pl->en | 18s | 2.6% palavras | 0.5% | 48.6 | 0.9 s | 1.4 s | +0.3 s | 3.9 s | 75% | ✅ |
| uk->en | 19s | 2.9% palavras | 1.6% | 78.3 | 1.3 s | 2.8 s | -1.9 s | 3.0 s | 71% | ✅ |
| tr->en | 17s | 0.0% palavras | 0.0% | 56.5 | 0.9 s | 1.3 s | -0.5 s | 0.0 s | 34% | ✅ |
| ar->en | 19s | 10.0% palavras | 2.5% | 58.9 | 1.7 s | 2.5 s | -0.2 s | 2.5 s | 61% | ✅ |
| hi->en | 20s | 34.2% palavras | 12.4% | 49.0 | 0.9 s | 1.5 s | +0.5 s | 3.7 s | 55% | ✅ |
| ja->en | 25s | 14.8% caracteres | 14.8% | 56.6 | 1.2 s | 1.6 s | -0.4 s | 2.4 s | 47% | ✅ |
| ko->en | 20s | 2.7% caracteres | 2.7% | 50.9 | 2.1 s | 2.9 s | -1.4 s | 3.7 s | 60% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 439 ms | 23 ms | 56 ms | 0 ms |
| en->pt | 0 ms | 440 ms | 27 ms | 85 ms | 49 ms |
| es->en | 0 ms | 445 ms | 26 ms | 48 ms | 0 ms |
| fr->en | 0 ms | 448 ms | 30 ms | 52 ms | 839 ms |
| de->en | 0 ms | 445 ms | 30 ms | 54 ms | 0 ms |
| it->en | 0 ms | 456 ms | 22 ms | 49 ms | 0 ms |
| ru->en | 0 ms | 452 ms | 25 ms | 64 ms | 136 ms |
| zh->en | 0 ms | 419 ms | 16 ms | 28 ms | 0 ms |
| nl->en | 0 ms | 429 ms | 21 ms | 40 ms | 1 ms |
| pl->en | 0 ms | 468 ms | 32 ms | 68 ms | 0 ms |
| uk->en | 0 ms | 451 ms | 25 ms | 69 ms | 0 ms |
| tr->en | 0 ms | 462 ms | 17 ms | 41 ms | 0 ms |
| ar->en | 0 ms | 478 ms | 27 ms | 68 ms | 299 ms |
| hi->en | 0 ms | 421 ms | 14 ms | 31 ms | 0 ms |
| ja->en | 0 ms | 477 ms | 34 ms | 104 ms | 0 ms |
| ko->en | 0 ms | 455 ms | 35 ms | 81 ms | 0 ms |

### Problemas encontrados

- **pt->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **en->pt**: nenhum problema detectado
- **es->en**: nenhum problema detectado
- **fr->en**: a tradução pronta espera 839 ms a fala anterior terminar de tocar
- **de->en**: transcrição ruim: 21% das palavras erradas
- **it->en**: nenhum problema detectado
- **ru->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **zh->en**: nenhum problema detectado
- **nl->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **pl->en**: nenhum problema detectado
- **uk->en**: nenhum problema detectado
- **tr->en**: nenhum problema detectado
- **ar->en**: nenhum problema detectado
- **hi->en**: transcrição ruim: 34% das palavras erradas
- **ja->en**: nenhum problema detectado
- **ko->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
