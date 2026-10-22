_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `base` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 14s | 12.1% palavras | 2.2% | 66.8 | 2.3 s | 3.1 s | -0.4 s | 3.7 s | 68% | ✅ |
| en->pt | 14s | 0.0% palavras | 0.0% | 76.4 | 1.4 s | 1.5 s | +0.6 s | 4.3 s | 86% | ✅ |
| es->en | 12s | 23.1% palavras | 6.7% | 65.2 | 0.6 s | 2.0 s | +0.0 s | 2.1 s | 58% | ✅ |
| fr->en | 14s | 20.0% palavras | 15.2% | 61.1 | 0.8 s | 1.4 s | +0.6 s | 3.5 s | 68% | ✅ |
| de->en | 14s | 45.8% palavras | 15.3% | 41.9 | 0.5 s | 0.5 s | -0.0 s | 2.8 s | 63% | ✅ |
| it->en | 16s | 37.8% palavras | 9.5% | 47.8 | 2.7 s | 4.0 s | +0.4 s | 4.6 s | 83% | ✅ |
| ru->en | 17s | 23.8% palavras | 6.0% | 56.3 | 1.3 s | 1.8 s | +0.2 s | 0.7 s | 54% | ✅ |
| zh->en | 15s | 22.9% caracteres | 22.9% | 48.1 | 1.3 s | 1.4 s | +0.2 s | 3.3 s | 74% | ✅ |
| nl->en | 15s | 37.0% palavras | 21.9% | 52.1 | 0.3 s | 0.4 s | +0.2 s | 3.3 s | 54% | ✅ |
| pl->en | 15s | 32.4% palavras | 5.9% | 48.3 | 0.8 s | 2.2 s | +0.0 s | 3.4 s | 78% | ✅ |
| uk->en | 15s | 33.3% palavras | 6.8% | 61.8 | 0.5 s | 0.6 s | +0.2 s | 2.8 s | 60% | ✅ |
| tr->en | 14s | 28.6% palavras | 11.7% | 53.2 | 1.2 s | 1.4 s | -0.2 s | 0.8 s | 44% | ✅ |
| ar->en | 15s | 41.4% palavras | 14.3% | 33.1 | 1.0 s | 1.2 s | +0.4 s | 1.0 s | 43% | ✅ |
| hi->en | 15s | 96.5% palavras | 95.8% | 20.2 | 0.6 s | 0.9 s | +0.1 s | 2.0 s | 65% | ✅ |
| ja->en | 14s | 23.9% caracteres | 23.9% | 45.6 | 2.1 s | 2.7 s | +0.7 s | 1.3 s | 42% | ✅ |
| ko->en | 12s | 18.0% caracteres | 18.0% | 45.3 | 1.8 s | 1.8 s | -0.0 s | 3.5 s | 62% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 67 ms | 23 ms | 56 ms | 1321 ms |
| en->pt | 0 ms | 73 ms | 32 ms | 75 ms | 1 ms |
| es->en | 0 ms | 60 ms | 24 ms | 44 ms | 114 ms |
| fr->en | 0 ms | 88 ms | 29 ms | 75 ms | 0 ms |
| de->en | 0 ms | 59 ms | 29 ms | 41 ms | 0 ms |
| it->en | 0 ms | 78 ms | 27 ms | 61 ms | 1718 ms |
| ru->en | 0 ms | 74 ms | 26 ms | 65 ms | 0 ms |
| zh->en | 0 ms | 103 ms | 31 ms | 92 ms | 0 ms |
| nl->en | 0 ms | 84 ms | 31 ms | 59 ms | 0 ms |
| pl->en | 0 ms | 82 ms | 29 ms | 67 ms | 201 ms |
| uk->en | 0 ms | 97 ms | 35 ms | 95 ms | 0 ms |
| tr->en | 0 ms | 83 ms | 27 ms | 73 ms | 268 ms |
| ar->en | 0 ms | 100 ms | 33 ms | 38 ms | 0 ms |
| hi->en | 0 ms | 63 ms | 20 ms | 38 ms | 203 ms |
| ja->en | 0 ms | 93 ms | 26 ms | 67 ms | 1147 ms |
| ko->en | 0 ms | 84 ms | 30 ms | 85 ms | 0 ms |

### Problemas encontrados

- **pt->en**: a tradução pronta espera 1321 ms a fala anterior terminar de tocar; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.1 s
- **en->pt**: nenhum problema detectado
- **es->en**: transcrição ruim: 23% das palavras erradas
- **fr->en**: nenhum problema detectado
- **de->en**: transcrição ruim: 46% das palavras erradas
- **it->en**: transcrição ruim: 38% das palavras erradas; a tradução pronta espera 1718 ms a fala anterior terminar de tocar; picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **ru->en**: transcrição ruim: 24% das palavras erradas
- **zh->en**: transcrição ruim: 23% dos caracteres erradas
- **nl->en**: transcrição ruim: 37% das palavras erradas
- **pl->en**: transcrição ruim: 32% das palavras erradas
- **uk->en**: transcrição ruim: 33% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **tr->en**: transcrição ruim: 29% das palavras erradas
- **ar->en**: transcrição ruim: 41% das palavras erradas
- **hi->en**: transcrição ruim: 97% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 6 palavras seguidas)
- **ja->en**: transcrição ruim: 24% dos caracteres erradas; a tradução pronta espera 1147 ms a fala anterior terminar de tocar
- **ko->en**: nenhum problema detectado

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
