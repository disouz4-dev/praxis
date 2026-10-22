_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `large-v3-turbo` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 12.1% palavras | 2.2% | 69.0 | 0.9 s | 1.2 s | +0.1 s | 2.2 s | 52% | ✅ |
| en->pt | 19s | 0.0% palavras | 0.0% | 83.7 | 1.9 s | 2.1 s | +1.0 s | 3.5 s | 66% | ✅ |
| es->en | 16s | 3.9% palavras | 1.0% | 81.6 | 0.9 s | 1.0 s | +0.0 s | 2.2 s | 44% | ✅ |
| fr->en | 19s | 0.0% palavras | 0.0% | 71.2 | 1.0 s | 1.0 s | +0.2 s | 2.9 s | 49% | ✅ |
| de->en | 19s | 25.0% palavras | 7.3% | 49.0 | 0.9 s | 3.0 s | +0.3 s | 2.9 s | 40% | ✅ |
| it->en | 21s | 21.6% palavras | 6.6% | 48.5 | 0.9 s | 1.0 s | -0.0 s | 1.4 s | 57% | ✅ |
| ru->en | 22s | 4.8% palavras | 1.5% | 49.9 | 1.8 s | 3.7 s | -1.6 s | 0.0 s | 40% | ✅ |
| zh->en | 20s | 15.7% caracteres | 15.7% | 47.3 | 1.5 s | 2.8 s | +0.6 s | 2.6 s | 68% | ✅ |
| nl->en | 20s | 22.2% palavras | 14.0% | 62.4 | 0.6 s | 0.7 s | -0.0 s | 3.9 s | 47% | ✅ |
| pl->en | 21s | 5.4% palavras | 2.2% | 58.0 | 1.0 s | 1.2 s | -0.4 s | 3.3 s | 63% | ✅ |
| uk->en | 20s | 8.3% palavras | 2.0% | 64.6 | 1.6 s | 2.6 s | +1.4 s | 1.3 s | 40% | ✅ |
| tr->en | 19s | 19.1% palavras | 9.6% | 39.7 | 1.1 s | 1.8 s | -0.9 s | 0.0 s | 33% | ✅ |
| ar->en | 20s | 13.8% palavras | 14.3% | 73.6 | 1.6 s | 2.2 s | -0.2 s | 1.2 s | 43% | ✅ |
| hi->en | 20s | 55.2% palavras | 22.5% | 27.4 | 0.8 s | 1.2 s | +0.1 s | 0.4 s | 42% | ✅ |
| ja->en | 19s | 50.0% caracteres | 50.0% | 37.5 | 0.9 s | 1.0 s | -0.1 s | 0.0 s | 24% | ✅ |
| ko->en | 17s | 6.0% caracteres | 6.0% | 58.3 | 2.7 s | 4.3 s | -1.1 s | 1.5 s | 47% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 446 ms | 22 ms | 51 ms | 0 ms |
| en->pt | 0 ms | 440 ms | 25 ms | 73 ms | 0 ms |
| es->en | 0 ms | 419 ms | 20 ms | 41 ms | 0 ms |
| fr->en | 0 ms | 445 ms | 19 ms | 50 ms | 0 ms |
| de->en | 0 ms | 421 ms | 16 ms | 29 ms | 0 ms |
| it->en | 0 ms | 435 ms | 16 ms | 44 ms | 0 ms |
| ru->en | 0 ms | 451 ms | 17 ms | 52 ms | 0 ms |
| zh->en | 0 ms | 466 ms | 26 ms | 94 ms | 0 ms |
| nl->en | 0 ms | 438 ms | 17 ms | 46 ms | 0 ms |
| pl->en | 0 ms | 449 ms | 24 ms | 52 ms | 0 ms |
| uk->en | 0 ms | 438 ms | 19 ms | 53 ms | 102 ms |
| tr->en | 0 ms | 445 ms | 16 ms | 48 ms | 0 ms |
| ar->en | 0 ms | 467 ms | 17 ms | 51 ms | 0 ms |
| hi->en | 0 ms | 437 ms | 11 ms | 27 ms | 0 ms |
| ja->en | 0 ms | 450 ms | 19 ms | 60 ms | 0 ms |
| ko->en | 0 ms | 447 ms | 21 ms | 54 ms | 0 ms |

### Problemas encontrados

- **pt->en**: nenhum problema detectado
- **en->pt**: nenhum problema detectado
- **es->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **fr->en**: nenhum problema detectado
- **de->en**: transcrição ruim: 25% das palavras erradas
- **it->en**: transcrição ruim: 22% das palavras erradas
- **ru->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **zh->en**: nenhum problema detectado
- **nl->en**: transcrição ruim: 22% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **pl->en**: nenhum problema detectado
- **uk->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **tr->en**: nenhum problema detectado
- **ar->en**: nenhum problema detectado
- **hi->en**: transcrição ruim: 55% das palavras erradas
- **ja->en**: transcrição ruim: 50% dos caracteres erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 19 caracteres seguidas)
- **ko->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.3 s

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
