_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `base` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 9.1% palavras | 1.5% | 72.3 | 0.5 s | 0.8 s | +0.1 s | 2.0 s | 50% | ✅ |
| en->pt | 19s | 2.3% palavras | 1.1% | 75.5 | 1.5 s | 1.5 s | +1.0 s | 2.8 s | 66% | ✅ |
| es->en | 16s | 26.9% palavras | 7.7% | 61.7 | 0.5 s | 0.6 s | +0.0 s | 2.0 s | 42% | ✅ |
| fr->en | 19s | 25.0% palavras | 17.1% | 59.7 | 0.7 s | 0.7 s | +0.1 s | 3.0 s | 52% | ✅ |
| de->en | 19s | 62.5% palavras | 21.9% | 34.6 | 0.5 s | 2.5 s | +0.3 s | 2.3 s | 49% | ✅ |
| it->en | 21s | 62.2% palavras | 17.9% | 46.7 | 0.6 s | 1.3 s | +0.4 s | 1.1 s | 61% | ✅ |
| ru->en | 22s | 42.9% palavras | 13.4% | 45.7 | 1.5 s | 2.3 s | -1.0 s | 0.0 s | 34% | ✅ |
| zh->en | 20s | 27.7% caracteres | 27.7% | 36.5 | 1.1 s | 1.6 s | +0.6 s | 2.4 s | 65% | ✅ |
| nl->en | 20s | 44.4% palavras | 25.4% | 51.4 | 0.2 s | 0.4 s | -0.0 s | 4.0 s | 44% | ✅ |
| pl->en | 21s | 40.5% palavras | 11.9% | 49.7 | 0.5 s | 0.8 s | -0.4 s | 2.7 s | 61% | ✅ |
| uk->en | 20s | 33.3% palavras | 12.2% | 51.1 | 1.4 s | 2.6 s | +1.4 s | 1.4 s | 43% | ✅ |
| tr->en | 19s | 23.8% palavras | 11.7% | 48.6 | 0.6 s | 1.4 s | -1.0 s | 0.0 s | 32% | ✅ |
| ar->en | 20s | 44.8% palavras | 16.0% | 33.3 | 0.9 s | 1.6 s | +0.2 s | 1.4 s | 41% | ✅ |
| hi->en | 20s | 110.3% palavras | 110.0% | 16.7 | 0.5 s | 1.6 s | +0.3 s | 1.0 s | 56% | ✅ |
| ja->en | 19s | 30.4% caracteres | 30.4% | 45.9 | 0.6 s | 0.7 s | -0.1 s | 0.0 s | 33% | ✅ |
| ko->en | 17s | 20.0% caracteres | 20.0% | 44.6 | 2.3 s | 3.8 s | -0.9 s | 1.3 s | 49% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 70 ms | 30 ms | 59 ms | 0 ms |
| en->pt | 0 ms | 73 ms | 31 ms | 81 ms | 0 ms |
| es->en | 0 ms | 58 ms | 37 ms | 43 ms | 0 ms |
| fr->en | 0 ms | 71 ms | 27 ms | 60 ms | 0 ms |
| de->en | 0 ms | 61 ms | 29 ms | 36 ms | 0 ms |
| it->en | 0 ms | 69 ms | 25 ms | 38 ms | 0 ms |
| ru->en | 0 ms | 75 ms | 22 ms | 39 ms | 0 ms |
| zh->en | 0 ms | 89 ms | 31 ms | 76 ms | 0 ms |
| nl->en | 0 ms | 59 ms | 28 ms | 36 ms | 0 ms |
| pl->en | 0 ms | 83 ms | 32 ms | 69 ms | 0 ms |
| uk->en | 0 ms | 86 ms | 22 ms | 56 ms | 459 ms |
| tr->en | 0 ms | 69 ms | 23 ms | 51 ms | 0 ms |
| ar->en | 0 ms | 86 ms | 23 ms | 45 ms | 0 ms |
| hi->en | 0 ms | 52 ms | 15 ms | 38 ms | 0 ms |
| ja->en | 0 ms | 87 ms | 24 ms | 72 ms | 0 ms |
| ko->en | 0 ms | 84 ms | 26 ms | 68 ms | 0 ms |

### Problemas encontrados

- **pt->en**: nenhum problema detectado
- **en->pt**: nenhum problema detectado
- **es->en**: transcrição ruim: 27% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **fr->en**: transcrição ruim: 25% das palavras erradas
- **de->en**: transcrição ruim: 62% das palavras erradas
- **it->en**: transcrição ruim: 62% das palavras erradas; inventou 4 palavras que não foram faladas
- **ru->en**: transcrição ruim: 43% das palavras erradas
- **zh->en**: transcrição ruim: 28% dos caracteres erradas
- **nl->en**: transcrição ruim: 44% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **pl->en**: transcrição ruim: 41% das palavras erradas
- **uk->en**: transcrição ruim: 33% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **tr->en**: transcrição ruim: 24% das palavras erradas
- **ar->en**: transcrição ruim: 45% das palavras erradas
- **hi->en**: transcrição ruim: 110% das palavras erradas
- **ja->en**: transcrição ruim: 30% dos caracteres erradas
- **ko->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.8 s

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
