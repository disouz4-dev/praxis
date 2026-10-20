_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `medium` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 12.1% palavras | 6.0% | 65.8 | 0.8 s | 1.4 s | +0.1 s | 1.5 s | 55% | ✅ |
| en->pt | 19s | 7.0% palavras | 6.4% | 47.8 | 0.7 s | 1.4 s | -0.0 s | 1.9 s | 69% | ✅ |
| es->en | 16s | 19.2% palavras | 9.6% | 55.1 | 0.6 s | 1.2 s | -0.5 s | 1.2 s | 52% | ✅ |
| fr->en | 19s | 12.5% palavras | 9.8% | 62.2 | 1.1 s | 2.4 s | -1.1 s | 3.6 s | 56% | ✅ |
| de->en | 19s | 25.0% palavras | 8.0% | 49.0 | 0.7 s | 0.8 s | +0.1 s | 1.5 s | 45% | ✅ |
| it->en | 21s | 24.3% palavras | 7.7% | 53.8 | 0.8 s | 1.0 s | -0.1 s | 1.6 s | 62% | ✅ |
| ru->en | 22s | 4.8% palavras | 1.5% | 56.4 | 1.6 s | 1.6 s | -0.1 s | 0.0 s | 37% | ✅ |
| zh->en | 20s | 20.5% caracteres | 20.5% | 49.9 | 0.8 s | 2.0 s | +0.5 s | 2.4 s | 81% | ✅ |
| nl->en | 20s | 22.2% palavras | 14.0% | 61.5 | 0.6 s | 0.8 s | +0.2 s | 4.2 s | 45% | ✅ |
| pl->en | 21s | 16.2% palavras | 3.2% | 58.6 | 1.3 s | 2.2 s | -0.5 s | 2.9 s | 64% | ✅ |
| uk->en | 20s | 4.2% palavras | 1.4% | 47.2 | 0.8 s | 1.3 s | -0.1 s | 0.1 s | 48% | ✅ |
| tr->en | 19s | 23.8% palavras | 10.6% | 61.1 | 0.8 s | 2.4 s | +0.0 s | 0.0 s | 35% | ✅ |
| ar->en | 20s | 20.7% palavras | 15.1% | 51.5 | 0.9 s | 1.6 s | -0.6 s | 0.9 s | 40% | ✅ |
| hi->en | 20s | 58.6% palavras | 22.5% | 28.9 | 0.8 s | 1.0 s | -0.1 s | 1.1 s | 45% | ✅ |
| ja->en | 19s | 2.2% caracteres | 2.2% | 64.8 | 1.4 s | 1.8 s | +0.9 s | 0.0 s | 39% | ✅ |
| ko->en | 17s | 0.0% caracteres | 0.0% | 49.9 | 2.2 s | 3.4 s | -0.5 s | 0.6 s | 42% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 322 ms | 17 ms | 39 ms | 0 ms |
| en->pt | 0 ms | 278 ms | 10 ms | 29 ms | 0 ms |
| es->en | 0 ms | 298 ms | 14 ms | 28 ms | 0 ms |
| fr->en | 0 ms | 363 ms | 17 ms | 43 ms | 0 ms |
| de->en | 0 ms | 324 ms | 14 ms | 29 ms | 0 ms |
| it->en | 0 ms | 359 ms | 16 ms | 45 ms | 0 ms |
| ru->en | 0 ms | 381 ms | 19 ms | 51 ms | 0 ms |
| zh->en | 0 ms | 342 ms | 14 ms | 32 ms | 0 ms |
| nl->en | 0 ms | 358 ms | 19 ms | 50 ms | 0 ms |
| pl->en | 0 ms | 380 ms | 22 ms | 66 ms | 0 ms |
| uk->en | 0 ms | 307 ms | 12 ms | 33 ms | 0 ms |
| tr->en | 0 ms | 339 ms | 16 ms | 58 ms | 0 ms |
| ar->en | 0 ms | 358 ms | 11 ms | 31 ms | 0 ms |
| hi->en | 0 ms | 398 ms | 12 ms | 27 ms | 0 ms |
| ja->en | 0 ms | 343 ms | 15 ms | 37 ms | 591 ms |
| ko->en | 0 ms | 359 ms | 21 ms | 57 ms | 0 ms |

### Problemas encontrados

- **pt->en**: nenhum problema detectado
- **en->pt**: nenhum problema detectado
- **es->en**: nenhum problema detectado
- **fr->en**: nenhum problema detectado
- **de->en**: transcrição ruim: 25% das palavras erradas
- **it->en**: transcrição ruim: 24% das palavras erradas
- **ru->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **zh->en**: transcrição ruim: 20% dos caracteres erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 6 caracteres seguidas); inventou 8 caracteres que não foram faladas
- **nl->en**: transcrição ruim: 22% das palavras erradas
- **pl->en**: nenhum problema detectado
- **uk->en**: nenhum problema detectado
- **tr->en**: transcrição ruim: 24% das palavras erradas
- **ar->en**: transcrição ruim: 21% das palavras erradas; 1 trecho(s) com fala viraram texto vazio
- **hi->en**: transcrição ruim: 59% das palavras erradas
- **ja->en**: nenhum problema detectado
- **ko->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.4 s

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
