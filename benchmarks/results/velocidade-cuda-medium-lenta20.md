_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `medium` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 9.1% palavras | 2.2% | 71.4 | 0.8 s | 1.1 s | +0.1 s | 2.0 s | 52% | ✅ |
| en->pt | 19s | 0.0% palavras | 0.0% | 77.9 | 1.8 s | 1.9 s | +1.0 s | 3.5 s | 68% | ✅ |
| es->en | 16s | 3.9% palavras | 1.9% | 77.2 | 0.8 s | 0.9 s | -0.0 s | 2.3 s | 47% | ✅ |
| fr->en | 19s | 7.5% palavras | 1.8% | 67.5 | 0.9 s | 1.0 s | +0.2 s | 2.9 s | 49% | ✅ |
| de->en | 19s | 33.3% palavras | 10.2% | 46.8 | 0.8 s | 1.1 s | +0.2 s | 3.3 s | 45% | ✅ |
| it->en | 21s | 24.3% palavras | 7.1% | 53.7 | 0.9 s | 1.3 s | +0.3 s | 1.3 s | 63% | ✅ |
| ru->en | 22s | 14.3% palavras | 7.5% | 54.6 | 1.8 s | 3.8 s | -1.7 s | 0.0 s | 44% | ✅ |
| zh->en | 20s | 18.1% caracteres | 18.1% | 54.4 | 1.6 s | 1.9 s | +0.7 s | 2.8 s | 70% | ✅ |
| nl->en | 20s | 22.2% palavras | 14.0% | 67.4 | 0.5 s | 0.7 s | +0.0 s | 3.8 s | 44% | ✅ |
| pl->en | 21s | 16.2% palavras | 4.3% | 59.7 | 1.1 s | 3.4 s | -1.8 s | 3.4 s | 61% | ✅ |
| uk->en | 20s | 8.3% palavras | 3.4% | 68.6 | 1.7 s | 3.2 s | +1.7 s | 1.8 s | 46% | ❌ |
| tr->en | 19s | 19.1% palavras | 9.6% | 49.1 | 1.1 s | 1.7 s | -0.9 s | 0.0 s | 33% | ✅ |
| ar->en | 20s | 17.2% palavras | 12.6% | 67.6 | 1.0 s | 1.9 s | +0.4 s | 1.2 s | 39% | ✅ |
| hi->en | 20s | 65.5% palavras | 23.3% | 20.8 | 0.8 s | 1.7 s | +0.3 s | 0.9 s | 45% | ✅ |
| ja->en | 19s | 15.2% caracteres | 15.2% | 55.6 | 0.9 s | 1.0 s | -0.1 s | 0.0 s | 35% | ✅ |
| ko->en | 17s | 2.0% caracteres | 2.0% | 56.6 | 2.6 s | 4.1 s | -1.0 s | 1.5 s | 46% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 378 ms | 26 ms | 51 ms | 0 ms |
| en->pt | 0 ms | 368 ms | 24 ms | 71 ms | 0 ms |
| es->en | 0 ms | 338 ms | 27 ms | 40 ms | 0 ms |
| fr->en | 0 ms | 370 ms | 19 ms | 48 ms | 0 ms |
| de->en | 0 ms | 334 ms | 17 ms | 34 ms | 0 ms |
| it->en | 0 ms | 352 ms | 18 ms | 46 ms | 0 ms |
| ru->en | 0 ms | 385 ms | 19 ms | 63 ms | 0 ms |
| zh->en | 0 ms | 446 ms | 27 ms | 85 ms | 73 ms |
| nl->en | 0 ms | 334 ms | 18 ms | 42 ms | 0 ms |
| pl->en | 0 ms | 387 ms | 23 ms | 53 ms | 0 ms |
| uk->en | 0 ms | 389 ms | 20 ms | 55 ms | 454 ms |
| tr->en | 0 ms | 368 ms | 16 ms | 40 ms | 0 ms |
| ar->en | 0 ms | 413 ms | 21 ms | 65 ms | 0 ms |
| hi->en | 0 ms | 373 ms | 11 ms | 21 ms | 0 ms |
| ja->en | 0 ms | 430 ms | 29 ms | 82 ms | 0 ms |
| ko->en | 0 ms | 362 ms | 20 ms | 50 ms | 0 ms |

### Problemas encontrados

- **pt->en**: nenhum problema detectado
- **en->pt**: nenhum problema detectado
- **es->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **fr->en**: nenhum problema detectado
- **de->en**: transcrição ruim: 33% das palavras erradas; 1 trecho(s) com fala viraram texto vazio
- **it->en**: transcrição ruim: 24% das palavras erradas
- **ru->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.8 s
- **zh->en**: inventou 6 caracteres que não foram faladas
- **nl->en**: transcrição ruim: 22% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **pl->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.4 s
- **uk->en**: não acompanha o falante: atraso típico 1.7 s, sobe +1.7 s da 1ª para a 2ª metade e sobram 2 s de tradução quando ele para; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **tr->en**: nenhum problema detectado
- **ar->en**: 1 trecho(s) com fala viraram texto vazio
- **hi->en**: transcrição ruim: 66% das palavras erradas
- **ja->en**: nenhum problema detectado
- **ko->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.1 s

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
