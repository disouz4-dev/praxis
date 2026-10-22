_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `tiny` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 44.2% palavras | 13.1% | 64.7 | 0.7 s | 2.9 s | -1.0 s | 3.4 s | 72% | ✅ |
| en->pt | 20s | 7.4% palavras | 5.1% | 68.8 | 1.1 s | 1.6 s | +0.5 s | 4.3 s | 81% | ✅ |
| es->en | 21s | 6.7% palavras | 1.6% | 55.1 | 0.6 s | 1.4 s | +0.2 s | 1.6 s | 55% | ✅ |
| fr->en | 21s | 58.9% palavras | 28.3% | 49.3 | 2.0 s | 3.5 s | -0.1 s | 4.7 s | 80% | ✅ |
| de->en | 19s | 50.0% palavras | 15.8% | 54.5 | 0.7 s | 1.1 s | -0.6 s | 3.7 s | 63% | ✅ |
| it->en | 20s | 55.3% palavras | 15.4% | 39.5 | 0.8 s | 2.4 s | -1.5 s | 4.4 s | 67% | ✅ |
| ru->en | 19s | 19.2% palavras | 3.6% | 65.0 | 1.3 s | 3.3 s | +0.5 s | 3.0 s | 56% | ✅ |
| zh->en | 19s | 20.4% caracteres | 20.4% | 42.9 | 1.5 s | 2.6 s | -0.3 s | 0.0 s | 42% | ✅ |
| nl->en | 22s | 64.6% palavras | 21.6% | 39.4 | 1.3 s | 2.4 s | +1.3 s | 3.0 s | 63% | ✅ |
| pl->en | 18s | 56.4% palavras | 6.6% | 46.7 | 0.5 s | 0.5 s | +0.0 s | 2.4 s | 73% | ✅ |
| uk->en | 19s | 55.9% palavras | 21.3% | 48.3 | 1.0 s | 3.3 s | -2.3 s | 2.6 s | 74% | ✅ |
| tr->en | 17s | 37.5% palavras | 6.8% | 57.6 | 0.5 s | 0.9 s | -0.5 s | 0.0 s | 47% | ✅ |
| ar->en | 19s | 66.7% palavras | 20.2% | 38.2 | 1.3 s | 3.2 s | -0.1 s | 3.3 s | 59% | ✅ |
| hi->en | 20s | 107.3% palavras | 101.1% | 21.2 | 0.8 s | 1.2 s | -0.4 s | 2.4 s | 60% | ✅ |
| ja->en | 25s | 33.0% caracteres | 33.0% | 59.0 | 1.3 s | 3.1 s | -1.7 s | 2.7 s | 55% | ✅ |
| ko->en | 20s | 25.7% caracteres | 25.7% | 35.1 | 1.5 s | 1.7 s | -0.8 s | 2.5 s | 45% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 55 ms | 40 ms | 79 ms | 0 ms |
| en->pt | 0 ms | 48 ms | 51 ms | 87 ms | 131 ms |
| es->en | 0 ms | 47 ms | 28 ms | 59 ms | 0 ms |
| fr->en | 0 ms | 55 ms | 48 ms | 54 ms | 1365 ms |
| de->en | 0 ms | 49 ms | 40 ms | 57 ms | 0 ms |
| it->en | 0 ms | 62 ms | 27 ms | 51 ms | 0 ms |
| ru->en | 0 ms | 64 ms | 31 ms | 65 ms | 138 ms |
| zh->en | 0 ms | 36 ms | 23 ms | 45 ms | 0 ms |
| nl->en | 0 ms | 51 ms | 32 ms | 51 ms | 0 ms |
| pl->en | 0 ms | 67 ms | 47 ms | 72 ms | 0 ms |
| uk->en | 0 ms | 57 ms | 33 ms | 61 ms | 144 ms |
| tr->en | 0 ms | 57 ms | 35 ms | 58 ms | 0 ms |
| ar->en | 0 ms | 72 ms | 39 ms | 74 ms | 0 ms |
| hi->en | 0 ms | 35 ms | 19 ms | 42 ms | 491 ms |
| ja->en | 0 ms | 70 ms | 50 ms | 105 ms | 0 ms |
| ko->en | 0 ms | 62 ms | 44 ms | 58 ms | 0 ms |

### Problemas encontrados

- **pt->en**: transcrição ruim: 44% das palavras erradas; inventou 6 palavras que não foram faladas
- **en->pt**: nenhum problema detectado
- **es->en**: nenhum problema detectado
- **fr->en**: transcrição ruim: 59% das palavras erradas; inventou 8 palavras que não foram faladas; a tradução pronta espera 1365 ms a fala anterior terminar de tocar; picos de atraso: 1 em cada 20 trechos demora mais de 3.5 s
- **de->en**: transcrição ruim: 50% das palavras erradas; inventou 4 palavras que não foram faladas
- **it->en**: transcrição ruim: 55% das palavras erradas; inventou 4 palavras que não foram faladas
- **ru->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.3 s
- **zh->en**: transcrição ruim: 20% dos caracteres erradas
- **nl->en**: transcrição ruim: 65% das palavras erradas; inventou 9 palavras que não foram faladas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **pl->en**: transcrição ruim: 56% das palavras erradas; inventou 6 palavras que não foram faladas
- **uk->en**: transcrição ruim: 56% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.3 s
- **tr->en**: transcrição ruim: 38% das palavras erradas
- **ar->en**: transcrição ruim: 67% das palavras erradas; inventou 5 palavras que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 3.2 s
- **hi->en**: transcrição ruim: 107% das palavras erradas
- **ja->en**: transcrição ruim: 33% dos caracteres erradas; inventou 9 caracteres que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 3.1 s
- **ko->en**: transcrição ruim: 26% dos caracteres erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
