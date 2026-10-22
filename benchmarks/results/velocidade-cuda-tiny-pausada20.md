_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `tiny` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 27.3% palavras | 10.4% | 52.2 | 0.6 s | 1.2 s | +0.1 s | 1.3 s | 58% | ✅ |
| en->pt | 19s | 20.9% palavras | 14.9% | 47.9 | 0.4 s | 1.3 s | -0.0 s | 1.7 s | 72% | ✅ |
| es->en | 16s | 23.1% palavras | 13.5% | 61.8 | 0.3 s | 0.8 s | -0.5 s | 1.0 s | 44% | ✅ |
| fr->en | 19s | 37.5% palavras | 20.7% | 43.8 | 0.8 s | 1.3 s | -0.2 s | 2.9 s | 45% | ✅ |
| de->en | 19s | 91.7% palavras | 25.6% | 27.0 | 0.5 s | 0.7 s | +0.1 s | 1.1 s | 50% | ✅ |
| it->en | 21s | 67.6% palavras | 17.3% | 42.9 | 0.5 s | 0.5 s | +0.0 s | 2.0 s | 61% | ✅ |
| ru->en | 22s | 61.9% palavras | 12.7% | 46.3 | 1.3 s | 1.5 s | +0.2 s | 0.0 s | 46% | ✅ |
| zh->en | 20s | 43.4% caracteres | 43.4% | 36.6 | 0.5 s | 2.1 s | +0.4 s | 2.3 s | 78% | ✅ |
| nl->en | 20s | 55.6% palavras | 28.9% | 44.1 | 0.3 s | 0.4 s | +0.2 s | 4.1 s | 43% | ✅ |
| pl->en | 21s | 75.7% palavras | 31.9% | 32.1 | 1.0 s | 2.2 s | -1.3 s | 1.4 s | 63% | ✅ |
| uk->en | 20s | 62.5% palavras | 20.9% | 29.8 | 0.5 s | 1.1 s | +0.1 s | 0.0 s | 54% | ✅ |
| tr->en | 19s | 38.1% palavras | 13.8% | 58.7 | 0.6 s | 2.4 s | +0.1 s | 0.0 s | 37% | ✅ |
| ar->en | 20s | 55.2% palavras | 21.9% | 29.3 | 0.6 s | 1.5 s | -0.7 s | 0.5 s | 49% | ✅ |
| hi->en | 20s | 100.0% palavras | 110.8% | 16.7 | 0.4 s | 0.5 s | -0.0 s | 0.5 s | 45% | ✅ |
| ja->en | 19s | 39.1% caracteres | 39.1% | 40.1 | 1.0 s | 1.5 s | +0.9 s | 0.0 s | 33% | ✅ |
| ko->en | 17s | 26.0% caracteres | 26.0% | 36.9 | 1.9 s | 3.6 s | -0.8 s | 0.0 s | 42% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 42 ms | 21 ms | 47 ms | 0 ms |
| en->pt | 0 ms | 30 ms | 14 ms | 41 ms | 0 ms |
| es->en | 0 ms | 32 ms | 16 ms | 33 ms | 0 ms |
| fr->en | 0 ms | 46 ms | 39 ms | 39 ms | 0 ms |
| de->en | 0 ms | 37 ms | 30 ms | 41 ms | 0 ms |
| it->en | 0 ms | 48 ms | 26 ms | 46 ms | 0 ms |
| ru->en | 0 ms | 65 ms | 42 ms | 75 ms | 0 ms |
| zh->en | 0 ms | 36 ms | 21 ms | 56 ms | 0 ms |
| nl->en | 0 ms | 41 ms | 28 ms | 55 ms | 0 ms |
| pl->en | 0 ms | 48 ms | 39 ms | 49 ms | 0 ms |
| uk->en | 0 ms | 34 ms | 19 ms | 43 ms | 0 ms |
| tr->en | 0 ms | 47 ms | 25 ms | 56 ms | 141 ms |
| ar->en | 0 ms | 48 ms | 15 ms | 42 ms | 0 ms |
| hi->en | 0 ms | 36 ms | 21 ms | 44 ms | 0 ms |
| ja->en | 0 ms | 39 ms | 27 ms | 36 ms | 541 ms |
| ko->en | 0 ms | 47 ms | 34 ms | 58 ms | 0 ms |

### Problemas encontrados

- **pt->en**: transcrição ruim: 27% das palavras erradas
- **en->pt**: transcrição ruim: 21% das palavras erradas
- **es->en**: transcrição ruim: 23% das palavras erradas
- **fr->en**: transcrição ruim: 38% das palavras erradas
- **de->en**: transcrição ruim: 92% das palavras erradas; inventou 8 palavras que não foram faladas
- **it->en**: transcrição ruim: 68% das palavras erradas
- **ru->en**: transcrição ruim: 62% das palavras erradas; inventou 4 palavras que não foram faladas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **zh->en**: transcrição ruim: 43% dos caracteres erradas
- **nl->en**: transcrição ruim: 56% das palavras erradas; inventou 4 palavras que não foram faladas
- **pl->en**: transcrição ruim: 76% das palavras erradas; inventou 6 palavras que não foram faladas
- **uk->en**: transcrição ruim: 62% das palavras erradas
- **tr->en**: transcrição ruim: 38% das palavras erradas
- **ar->en**: transcrição ruim: 55% das palavras erradas
- **hi->en**: transcrição ruim: 100% das palavras erradas
- **ja->en**: transcrição ruim: 39% dos caracteres erradas
- **ko->en**: transcrição ruim: 26% dos caracteres erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.6 s

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
