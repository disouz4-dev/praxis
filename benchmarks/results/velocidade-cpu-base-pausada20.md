_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `base` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 21.2% palavras | 9.0% | 58.7 | 0.9 s | 1.0 s | +0.1 s | 1.5 s | 55% | ✅ |
| en->pt | 19s | 20.9% palavras | 18.6% | 44.8 | 0.7 s | 1.5 s | +0.0 s | 1.9 s | 70% | ✅ |
| es->en | 16s | 46.2% palavras | 23.1% | 48.3 | 0.6 s | 1.0 s | -0.4 s | 1.3 s | 47% | ✅ |
| fr->en | 19s | 25.0% palavras | 18.3% | 60.4 | 1.1 s | 1.7 s | -0.2 s | 4.2 s | 53% | ✅ |
| de->en | 19s | 54.2% palavras | 21.2% | 29.5 | 0.8 s | 0.9 s | +0.1 s | 1.2 s | 49% | ✅ |
| it->en | 21s | 56.8% palavras | 14.3% | 45.9 | 0.8 s | 0.9 s | -0.0 s | 1.7 s | 53% | ✅ |
| ru->en | 22s | 23.8% palavras | 6.7% | 59.1 | 1.7 s | 1.8 s | +0.1 s | 0.0 s | 40% | ✅ |
| zh->en | 20s | 30.1% caracteres | 30.1% | 33.4 | 0.8 s | 2.6 s | +0.2 s | 2.9 s | 75% | ✅ |
| nl->en | 20s | 48.1% palavras | 27.2% | 47.5 | 0.7 s | 0.8 s | +0.3 s | 4.8 s | 44% | ✅ |
| pl->en | 21s | 51.3% palavras | 17.3% | 40.0 | 1.0 s | 1.9 s | -0.4 s | 2.4 s | 60% | ✅ |
| uk->en | 20s | 37.5% palavras | 14.9% | 44.6 | 0.9 s | 1.9 s | -0.1 s | 0.4 s | 55% | ✅ |
| tr->en | 19s | 42.9% palavras | 17.0% | 52.9 | 1.0 s | 2.7 s | +0.1 s | 0.0 s | 39% | ✅ |
| ar->en | 20s | 41.4% palavras | 16.8% | 39.6 | 1.0 s | 1.2 s | -0.3 s | 1.1 s | 49% | ✅ |
| hi->en | 20s | 100.0% palavras | 100.0% | 14.9 | 0.9 s | 2.4 s | +0.3 s | 1.3 s | 53% | ✅ |
| ja->en | 19s | 28.3% caracteres | 28.3% | 44.3 | 1.3 s | 1.7 s | +0.7 s | 0.0 s | 34% | ✅ |
| ko->en | 17s | 8.0% caracteres | 8.0% | 52.0 | 2.2 s | 4.4 s | -1.0 s | 0.6 s | 49% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 420 ms | 19 ms | 35 ms | 0 ms |
| en->pt | 0 ms | 344 ms | 11 ms | 31 ms | 0 ms |
| es->en | 0 ms | 344 ms | 15 ms | 28 ms | 0 ms |
| fr->en | 0 ms | 429 ms | 23 ms | 53 ms | 0 ms |
| de->en | 0 ms | 371 ms | 18 ms | 28 ms | 0 ms |
| it->en | 0 ms | 431 ms | 17 ms | 35 ms | 0 ms |
| ru->en | 0 ms | 449 ms | 27 ms | 57 ms | 0 ms |
| zh->en | 0 ms | 371 ms | 12 ms | 34 ms | 0 ms |
| nl->en | 0 ms | 432 ms | 19 ms | 38 ms | 0 ms |
| pl->en | 0 ms | 454 ms | 25 ms | 55 ms | 0 ms |
| uk->en | 0 ms | 375 ms | 13 ms | 30 ms | 0 ms |
| tr->en | 0 ms | 431 ms | 16 ms | 52 ms | 130 ms |
| ar->en | 0 ms | 438 ms | 22 ms | 42 ms | 0 ms |
| hi->en | 0 ms | 380 ms | 17 ms | 37 ms | 0 ms |
| ja->en | 0 ms | 389 ms | 13 ms | 22 ms | 483 ms |
| ko->en | 0 ms | 434 ms | 22 ms | 60 ms | 0 ms |

### Problemas encontrados

- **pt->en**: transcrição ruim: 21% das palavras erradas; 1 trecho(s) com fala viraram texto vazio
- **en->pt**: transcrição ruim: 21% das palavras erradas
- **es->en**: transcrição ruim: 46% das palavras erradas
- **fr->en**: transcrição ruim: 25% das palavras erradas; 1 trecho(s) com fala viraram texto vazio
- **de->en**: transcrição ruim: 54% das palavras erradas
- **it->en**: transcrição ruim: 57% das palavras erradas
- **ru->en**: transcrição ruim: 24% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **zh->en**: transcrição ruim: 30% dos caracteres erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 6 caracteres seguidas)
- **nl->en**: transcrição ruim: 48% das palavras erradas
- **pl->en**: transcrição ruim: 51% das palavras erradas; inventou 4 palavras que não foram faladas
- **uk->en**: transcrição ruim: 38% das palavras erradas
- **tr->en**: transcrição ruim: 43% das palavras erradas
- **ar->en**: transcrição ruim: 41% das palavras erradas; 1 trecho(s) com fala viraram texto vazio
- **hi->en**: transcrição ruim: 100% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 9 palavras seguidas)
- **ja->en**: transcrição ruim: 28% dos caracteres erradas
- **ko->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.4 s

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
