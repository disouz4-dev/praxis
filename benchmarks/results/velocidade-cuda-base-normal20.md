_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `base` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 18.6% palavras | 8.1% | 69.8 | 0.7 s | 3.0 s | -1.1 s | 3.1 s | 66% | ✅ |
| en->pt | 20s | 3.7% palavras | 0.0% | 74.3 | 1.1 s | 1.7 s | +0.6 s | 4.2 s | 83% | ✅ |
| es->en | 21s | 13.3% palavras | 2.2% | 54.3 | 0.5 s | 1.5 s | +0.1 s | 1.8 s | 54% | ✅ |
| fr->en | 21s | 44.6% palavras | 17.9% | 58.3 | 1.7 s | 3.1 s | +0.5 s | 5.0 s | 75% | ✅ |
| de->en | 19s | 38.2% palavras | 12.0% | 58.7 | 0.5 s | 1.0 s | -0.3 s | 4.2 s | 63% | ✅ |
| it->en | 20s | 38.3% palavras | 9.7% | 47.6 | 1.3 s | 2.5 s | -1.5 s | 4.3 s | 70% | ✅ |
| ru->en | 19s | 38.5% palavras | 5.6% | 62.7 | 1.5 s | 3.3 s | +0.8 s | 3.0 s | 58% | ✅ |
| zh->en | 19s | 15.9% caracteres | 15.9% | 51.0 | 1.5 s | 2.6 s | -0.3 s | 0.1 s | 47% | ✅ |
| nl->en | 22s | 35.4% palavras | 11.0% | 63.1 | 1.3 s | 2.2 s | +1.0 s | 3.8 s | 68% | ✅ |
| pl->en | 18s | 46.2% palavras | 7.1% | 47.8 | 0.8 s | 1.3 s | +0.6 s | 3.1 s | 84% | ✅ |
| uk->en | 19s | 50.0% palavras | 15.4% | 40.1 | 0.9 s | 2.4 s | -1.9 s | 1.7 s | 58% | ✅ |
| tr->en | 17s | 29.2% palavras | 4.9% | 63.2 | 0.6 s | 1.0 s | -0.5 s | 0.0 s | 46% | ✅ |
| ar->en | 19s | 43.3% palavras | 13.3% | 40.7 | 1.3 s | 1.4 s | -0.2 s | 1.4 s | 54% | ✅ |
| hi->en | 20s | 97.6% palavras | 100.0% | 18.7 | 0.5 s | 1.0 s | +0.1 s | 2.7 s | 61% | ✅ |
| ja->en | 25s | 27.3% caracteres | 27.3% | 48.8 | 1.3 s | 1.4 s | -0.7 s | 1.9 s | 46% | ✅ |
| ko->en | 20s | 43.2% caracteres | 43.2% | 31.1 | 1.3 s | 1.7 s | -0.8 s | 1.7 s | 43% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 81 ms | 28 ms | 62 ms | 0 ms |
| en->pt | 0 ms | 72 ms | 35 ms | 72 ms | 1 ms |
| es->en | 0 ms | 69 ms | 33 ms | 47 ms | 0 ms |
| fr->en | 0 ms | 78 ms | 36 ms | 44 ms | 890 ms |
| de->en | 0 ms | 75 ms | 39 ms | 48 ms | 0 ms |
| it->en | 0 ms | 83 ms | 22 ms | 49 ms | 0 ms |
| ru->en | 0 ms | 85 ms | 28 ms | 64 ms | 315 ms |
| zh->en | 0 ms | 58 ms | 21 ms | 44 ms | 0 ms |
| nl->en | 0 ms | 72 ms | 23 ms | 58 ms | 1 ms |
| pl->en | 0 ms | 98 ms | 47 ms | 82 ms | 268 ms |
| uk->en | 0 ms | 89 ms | 26 ms | 45 ms | 0 ms |
| tr->en | 0 ms | 86 ms | 23 ms | 45 ms | 0 ms |
| ar->en | 0 ms | 93 ms | 22 ms | 35 ms | 260 ms |
| hi->en | 0 ms | 64 ms | 25 ms | 39 ms | 18 ms |
| ja->en | 0 ms | 101 ms | 40 ms | 82 ms | 0 ms |
| ko->en | 0 ms | 94 ms | 25 ms | 61 ms | 0 ms |

### Problemas encontrados

- **pt->en**: nenhum problema detectado
- **en->pt**: nenhum problema detectado
- **es->en**: nenhum problema detectado
- **fr->en**: transcrição ruim: 45% das palavras erradas; inventou 7 palavras que não foram faladas; a tradução pronta espera 890 ms a fala anterior terminar de tocar; picos de atraso: 1 em cada 20 trechos demora mais de 3.1 s
- **de->en**: transcrição ruim: 38% das palavras erradas
- **it->en**: transcrição ruim: 38% das palavras erradas
- **ru->en**: transcrição ruim: 38% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.3 s
- **zh->en**: nenhum problema detectado
- **nl->en**: transcrição ruim: 35% das palavras erradas; inventou 4 palavras que não foram faladas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **pl->en**: transcrição ruim: 46% das palavras erradas; inventou 5 palavras que não foram faladas
- **uk->en**: transcrição ruim: 50% das palavras erradas
- **tr->en**: transcrição ruim: 29% das palavras erradas
- **ar->en**: transcrição ruim: 43% das palavras erradas
- **hi->en**: transcrição ruim: 98% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 6 palavras seguidas)
- **ja->en**: transcrição ruim: 27% dos caracteres erradas; inventou 6 caracteres que não foram faladas
- **ko->en**: transcrição ruim: 43% dos caracteres erradas; inventou 13 caracteres que não foram faladas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
