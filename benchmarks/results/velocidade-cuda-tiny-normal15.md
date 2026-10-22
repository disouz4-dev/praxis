_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `tiny` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 14s | 27.3% palavras | 7.5% | 61.6 | 2.3 s | 3.4 s | -0.2 s | 4.1 s | 71% | ✅ |
| en->pt | 14s | 4.7% palavras | 4.3% | 73.5 | 1.4 s | 1.6 s | +0.7 s | 4.1 s | 85% | ✅ |
| es->en | 12s | 26.9% palavras | 14.4% | 57.9 | 0.6 s | 1.9 s | +0.0 s | 2.2 s | 56% | ✅ |
| fr->en | 14s | 25.0% palavras | 12.8% | 62.3 | 0.8 s | 1.7 s | +0.7 s | 3.0 s | 66% | ✅ |
| de->en | 14s | 83.3% palavras | 32.1% | 30.3 | 0.5 s | 0.6 s | -0.0 s | 3.2 s | 62% | ✅ |
| it->en | 16s | 62.2% palavras | 13.7% | 39.1 | 2.6 s | 3.8 s | +0.4 s | 3.6 s | 78% | ✅ |
| ru->en | 17s | 52.4% palavras | 10.4% | 53.1 | 1.2 s | 1.3 s | -0.2 s | 0.0 s | 47% | ✅ |
| zh->en | 15s | 24.1% caracteres | 24.1% | 42.8 | 1.3 s | 1.5 s | +0.3 s | 4.2 s | 81% | ✅ |
| nl->en | 15s | 55.6% palavras | 29.8% | 44.6 | 0.2 s | 0.4 s | +0.2 s | 4.0 s | 50% | ✅ |
| pl->en | 15s | 51.3% palavras | 15.1% | 32.6 | 0.5 s | 0.7 s | -0.3 s | 2.5 s | 60% | ✅ |
| uk->en | 15s | 66.7% palavras | 13.5% | 50.4 | 0.6 s | 2.2 s | -0.8 s | 2.7 s | 54% | ✅ |
| tr->en | 14s | 28.6% palavras | 12.8% | 57.2 | 1.1 s | 1.4 s | -0.3 s | 1.0 s | 45% | ✅ |
| ar->en | 15s | 55.2% palavras | 16.8% | 27.1 | 1.0 s | 1.0 s | +0.3 s | 0.9 s | 43% | ✅ |
| hi->en | 15s | 103.5% palavras | 100.0% | 19.6 | 0.9 s | 1.4 s | -0.4 s | 1.8 s | 71% | ✅ |
| ja->en | 14s | 30.4% caracteres | 30.4% | 39.3 | 1.8 s | 2.2 s | +0.4 s | 1.5 s | 44% | ✅ |
| ko->en | 12s | 28.0% caracteres | 28.0% | 40.2 | 1.8 s | 1.8 s | -0.0 s | 3.2 s | 54% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 46 ms | 40 ms | 56 ms | 1390 ms |
| en->pt | 0 ms | 48 ms | 50 ms | 75 ms | 254 ms |
| es->en | 0 ms | 37 ms | 26 ms | 33 ms | 51 ms |
| fr->en | 0 ms | 66 ms | 40 ms | 77 ms | 0 ms |
| de->en | 0 ms | 41 ms | 33 ms | 46 ms | 0 ms |
| it->en | 0 ms | 54 ms | 33 ms | 72 ms | 1643 ms |
| ru->en | 0 ms | 66 ms | 33 ms | 60 ms | 0 ms |
| zh->en | 0 ms | 73 ms | 38 ms | 104 ms | 0 ms |
| nl->en | 0 ms | 59 ms | 47 ms | 73 ms | 0 ms |
| pl->en | 0 ms | 69 ms | 39 ms | 53 ms | 0 ms |
| uk->en | 0 ms | 79 ms | 35 ms | 73 ms | 0 ms |
| tr->en | 0 ms | 60 ms | 41 ms | 80 ms | 168 ms |
| ar->en | 0 ms | 82 ms | 36 ms | 41 ms | 0 ms |
| hi->en | 0 ms | 33 ms | 17 ms | 49 ms | 724 ms |
| ja->en | 0 ms | 59 ms | 36 ms | 79 ms | 875 ms |
| ko->en | 0 ms | 63 ms | 42 ms | 68 ms | 0 ms |

### Problemas encontrados

- **pt->en**: transcrição ruim: 27% das palavras erradas; a tradução pronta espera 1390 ms a fala anterior terminar de tocar; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.4 s
- **en->pt**: nenhum problema detectado
- **es->en**: transcrição ruim: 27% das palavras erradas
- **fr->en**: transcrição ruim: 25% das palavras erradas
- **de->en**: transcrição ruim: 83% das palavras erradas; inventou 6 palavras que não foram faladas
- **it->en**: transcrição ruim: 62% das palavras erradas; a tradução pronta espera 1643 ms a fala anterior terminar de tocar; picos de atraso: 1 em cada 20 trechos demora mais de 3.8 s
- **ru->en**: transcrição ruim: 52% das palavras erradas
- **zh->en**: transcrição ruim: 24% dos caracteres erradas
- **nl->en**: transcrição ruim: 56% das palavras erradas
- **pl->en**: transcrição ruim: 51% das palavras erradas
- **uk->en**: transcrição ruim: 67% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **tr->en**: transcrição ruim: 29% das palavras erradas
- **ar->en**: transcrição ruim: 55% das palavras erradas
- **hi->en**: transcrição ruim: 103% das palavras erradas
- **ja->en**: transcrição ruim: 30% dos caracteres erradas; a tradução pronta espera 875 ms a fala anterior terminar de tocar
- **ko->en**: transcrição ruim: 28% dos caracteres erradas

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
