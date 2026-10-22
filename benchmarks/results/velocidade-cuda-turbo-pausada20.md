_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `large-v3-turbo` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 9.1% palavras | 5.2% | 78.9 | 1.0 s | 1.5 s | +0.2 s | 1.7 s | 56% | ✅ |
| en->pt | 19s | 4.7% palavras | 5.3% | 57.1 | 0.8 s | 1.7 s | +0.0 s | 2.0 s | 76% | ✅ |
| es->en | 16s | 7.7% palavras | 6.7% | 64.7 | 0.7 s | 1.3 s | -0.5 s | 1.3 s | 47% | ✅ |
| fr->en | 19s | 2.5% palavras | 0.6% | 75.7 | 1.2 s | 1.9 s | -0.6 s | 3.4 s | 51% | ✅ |
| de->en | 19s | 16.7% palavras | 5.1% | 47.5 | 0.8 s | 0.9 s | +0.0 s | 1.3 s | 42% | ✅ |
| it->en | 21s | 16.2% palavras | 4.2% | 55.4 | 0.8 s | 0.9 s | -0.0 s | 1.7 s | 55% | ✅ |
| ru->en | 22s | 4.8% palavras | 1.5% | 56.4 | 1.6 s | 1.7 s | -0.1 s | 0.0 s | 38% | ✅ |
| zh->en | 20s | 15.7% caracteres | 15.7% | 46.5 | 0.8 s | 2.0 s | +0.5 s | 2.4 s | 68% | ✅ |
| nl->en | 20s | 25.9% palavras | 13.2% | 68.4 | 0.7 s | 0.8 s | +0.2 s | 4.1 s | 43% | ✅ |
| pl->en | 21s | 2.7% palavras | 1.1% | 63.8 | 1.3 s | 1.8 s | -0.4 s | 2.5 s | 62% | ✅ |
| uk->en | 20s | 4.2% palavras | 2.0% | 59.8 | 0.9 s | 1.5 s | -0.1 s | 0.2 s | 52% | ✅ |
| tr->en | 19s | 19.1% palavras | 9.6% | 55.2 | 0.9 s | 2.4 s | +0.0 s | 0.0 s | 33% | ✅ |
| ar->en | 20s | 17.2% palavras | 4.2% | 64.1 | 0.9 s | 1.6 s | -0.5 s | 1.0 s | 44% | ✅ |
| hi->en | 20s | 55.2% palavras | 21.7% | 16.2 | 0.8 s | 0.9 s | -0.1 s | 0.2 s | 36% | ✅ |
| ja->en | 19s | 0.0% caracteres | 0.0% | 71.0 | 1.4 s | 1.9 s | +0.9 s | 0.0 s | 40% | ✅ |
| ko->en | 17s | 4.0% caracteres | 4.0% | 56.6 | 2.2 s | 3.5 s | -0.5 s | 0.6 s | 45% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 439 ms | 14 ms | 41 ms | 0 ms |
| en->pt | 0 ms | 392 ms | 12 ms | 31 ms | 0 ms |
| es->en | 0 ms | 412 ms | 15 ms | 29 ms | 0 ms |
| fr->en | 0 ms | 450 ms | 18 ms | 44 ms | 0 ms |
| de->en | 0 ms | 428 ms | 16 ms | 29 ms | 0 ms |
| it->en | 0 ms | 435 ms | 15 ms | 43 ms | 0 ms |
| ru->en | 0 ms | 458 ms | 20 ms | 47 ms | 0 ms |
| zh->en | 0 ms | 429 ms | 12 ms | 36 ms | 0 ms |
| nl->en | 0 ms | 437 ms | 18 ms | 42 ms | 0 ms |
| pl->en | 0 ms | 450 ms | 24 ms | 55 ms | 0 ms |
| uk->en | 0 ms | 401 ms | 12 ms | 35 ms | 0 ms |
| tr->en | 0 ms | 440 ms | 15 ms | 52 ms | 0 ms |
| ar->en | 0 ms | 436 ms | 12 ms | 32 ms | 0 ms |
| hi->en | 0 ms | 454 ms | 14 ms | 26 ms | 0 ms |
| ja->en | 0 ms | 412 ms | 22 ms | 37 ms | 556 ms |
| ko->en | 0 ms | 435 ms | 21 ms | 56 ms | 0 ms |

### Problemas encontrados

- **pt->en**: nenhum problema detectado
- **en->pt**: nenhum problema detectado
- **es->en**: nenhum problema detectado
- **fr->en**: nenhum problema detectado
- **de->en**: nenhum problema detectado
- **it->en**: nenhum problema detectado
- **ru->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **zh->en**: pulou 1 trecho(s) inteiro(s) da fala (maior: 6 caracteres seguidas)
- **nl->en**: transcrição ruim: 26% das palavras erradas
- **pl->en**: nenhum problema detectado
- **uk->en**: nenhum problema detectado
- **tr->en**: nenhum problema detectado
- **ar->en**: nenhum problema detectado
- **hi->en**: transcrição ruim: 55% das palavras erradas
- **ja->en**: nenhum problema detectado
- **ko->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.5 s

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
