_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `base` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 71s | 16.2% palavras | 4.5% | 65.4 | 0.9 s | 2.9 s | +0.2 s | 3.9 s | 68% | ✅ |
| en->pt | 72s | 3.2% palavras | 1.4% | 68.6 | 0.7 s | 2.5 s | -0.5 s | 4.0 s | 76% | ✅ |
| es->en | 73s | 10.5% palavras | 2.7% | 65.0 | 0.6 s | 2.0 s | +0.2 s | 1.4 s | 58% | ✅ |
| fr->en | 62s | 38.0% palavras | 22.5% | 56.1 | 0.7 s | 3.8 s | +0.8 s | 3.6 s | 70% | ✅ |
| de->en | 63s | 41.5% palavras | 13.6% | 54.4 | 0.6 s | 2.3 s | +0.0 s | 1.6 s | 58% | ✅ |
| it->en | 78s | 39.0% palavras | 9.5% | 56.0 | 1.0 s | 3.2 s | +0.1 s | 3.1 s | 63% | ✅ |
| ru->en | 66s | 28.4% palavras | 7.3% | 63.0 | 1.4 s | 4.7 s | -0.1 s | 3.0 s | 56% | ✅ |
| zh->en | 62s | 33.9% caracteres | 33.9% | 33.4 | 1.1 s | 2.7 s | +0.1 s | 0.0 s | 50% | ✅ |
| nl->en | 66s | 27.2% palavras | 13.2% | 52.0 | 0.4 s | 2.2 s | -0.1 s | 3.5 s | 61% | ✅ |
| pl->en | 69s | 37.3% palavras | 6.7% | 52.5 | 0.7 s | 2.5 s | +0.0 s | 3.1 s | 77% | ✅ |
| uk->en | 69s | 46.3% palavras | 11.0% | 50.8 | 0.6 s | 2.5 s | -0.9 s | 3.2 s | 58% | ✅ |
| tr->en | 72s | 44.3% palavras | 10.6% | 57.7 | 1.0 s | 3.5 s | -1.1 s | 3.5 s | 50% | ✅ |
| ar->en | 74s | 49.2% palavras | 17.0% | 50.2 | 1.3 s | 2.7 s | +0.0 s | 1.8 s | 60% | ✅ |
| hi->en | 69s | 99.3% palavras | 99.2% | 18.6 | 1.2 s | 7.3 s | -1.4 s | 10.0 s | 94% | ❌ |
| ja->en | 64s | 31.6% caracteres | 31.6% | 45.0 | 1.3 s | 3.3 s | -0.9 s | 1.9 s | 44% | ✅ |
| ko->en | 69s | 24.2% caracteres | 24.2% | 54.8 | 1.7 s | 2.4 s | +0.6 s | 2.6 s | 55% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 83 ms | 27 ms | 72 ms | 0 ms |
| en->pt | 0 ms | 80 ms | 36 ms | 65 ms | 0 ms |
| es->en | 0 ms | 62 ms | 30 ms | 45 ms | 0 ms |
| fr->en | 0 ms | 72 ms | 28 ms | 63 ms | 0 ms |
| de->en | 0 ms | 57 ms | 27 ms | 31 ms | 0 ms |
| it->en | 0 ms | 78 ms | 25 ms | 51 ms | 0 ms |
| ru->en | 0 ms | 84 ms | 29 ms | 71 ms | 0 ms |
| zh->en | 0 ms | 74 ms | 24 ms | 52 ms | 0 ms |
| nl->en | 0 ms | 84 ms | 30 ms | 61 ms | 0 ms |
| pl->en | 0 ms | 86 ms | 34 ms | 66 ms | 0 ms |
| uk->en | 0 ms | 74 ms | 30 ms | 50 ms | 0 ms |
| tr->en | 0 ms | 85 ms | 23 ms | 53 ms | 0 ms |
| ar->en | 0 ms | 96 ms | 28 ms | 65 ms | 0 ms |
| hi->en | 0 ms | 63 ms | 24 ms | 40 ms | 645 ms |
| ja->en | 0 ms | 95 ms | 35 ms | 69 ms | 0 ms |
| ko->en | 0 ms | 84 ms | 31 ms | 63 ms | 0 ms |

### Problemas encontrados

- **pt->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **en->pt**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **es->en**: nenhum problema detectado
- **fr->en**: transcrição ruim: 38% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 8 palavras seguidas); inventou 8 palavras que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 3.8 s
- **de->en**: transcrição ruim: 42% das palavras erradas; 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **it->en**: transcrição ruim: 39% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.2 s
- **ru->en**: transcrição ruim: 28% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.7 s
- **zh->en**: transcrição ruim: 34% dos caracteres erradas
- **nl->en**: transcrição ruim: 27% das palavras erradas; 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **pl->en**: transcrição ruim: 37% das palavras erradas
- **uk->en**: transcrição ruim: 46% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **tr->en**: transcrição ruim: 44% das palavras erradas; inventou 9 palavras que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 3.5 s
- **ar->en**: transcrição ruim: 49% das palavras erradas
- **hi->en**: transcrição ruim: 99% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 10 palavras seguidas); não acompanha o falante: atraso típico 1.2 s, sobe -1.4 s da 1ª para a 2ª metade e sobram 10 s de tradução quando ele para
- **ja->en**: transcrição ruim: 32% dos caracteres erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.3 s
- **ko->en**: transcrição ruim: 24% dos caracteres erradas; inventou 23 caracteres que não foram faladas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
