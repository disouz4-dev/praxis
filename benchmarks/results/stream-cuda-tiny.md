_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `tiny` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 71s | 29.3% palavras | 9.0% | 60.8 | 0.8 s | 3.1 s | +0.2 s | 3.6 s | 71% | ✅ |
| en->pt | 72s | 6.3% palavras | 3.7% | 68.1 | 0.7 s | 2.5 s | -0.5 s | 4.0 s | 78% | ✅ |
| es->en | 73s | 19.1% palavras | 7.0% | 58.5 | 0.5 s | 1.5 s | -0.1 s | 1.2 s | 56% | ✅ |
| fr->en | 62s | 47.5% palavras | 22.9% | 54.1 | 0.9 s | 3.5 s | +0.6 s | 2.9 s | 71% | ✅ |
| de->en | 63s | 58.5% palavras | 23.4% | 47.3 | 0.5 s | 2.0 s | +0.0 s | 1.4 s | 60% | ✅ |
| it->en | 78s | 57.6% palavras | 13.5% | 44.9 | 1.1 s | 4.0 s | -0.5 s | 4.5 s | 73% | ✅ |
| ru->en | 66s | 27.3% palavras | 7.3% | 67.6 | 1.4 s | 4.9 s | +0.2 s | 3.0 s | 57% | ✅ |
| zh->en | 62s | 43.6% caracteres | 43.6% | 26.7 | 1.1 s | 2.4 s | +0.1 s | 0.8 s | 51% | ✅ |
| nl->en | 66s | 40.1% palavras | 18.1% | 47.5 | 0.4 s | 2.1 s | -0.1 s | 3.4 s | 60% | ✅ |
| pl->en | 69s | 49.4% palavras | 11.2% | 49.2 | 0.5 s | 1.4 s | +0.2 s | 3.3 s | 73% | ✅ |
| uk->en | 69s | 66.1% palavras | 18.0% | 49.0 | 0.7 s | 3.7 s | -1.4 s | 4.0 s | 61% | ✅ |
| tr->en | 72s | 65.0% palavras | 22.0% | 49.3 | 1.1 s | 2.9 s | -1.1 s | 4.1 s | 53% | ✅ |
| ar->en | 74s | 64.1% palavras | 22.2% | 45.4 | 1.3 s | 3.0 s | +0.1 s | 3.5 s | 59% | ✅ |
| hi->en | 69s | 100.0% palavras | 100.0% | 24.1 | 0.5 s | 2.7 s | -0.7 s | 3.4 s | 67% | ✅ |
| ja->en | 64s | 43.6% caracteres | 43.6% | 40.7 | 1.4 s | 3.7 s | -0.9 s | 0.5 s | 47% | ✅ |
| ko->en | 69s | 29.0% caracteres | 29.0% | 48.3 | 1.6 s | 2.5 s | +1.0 s | 1.3 s | 53% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 59 ms | 33 ms | 65 ms | 0 ms |
| en->pt | 0 ms | 57 ms | 48 ms | 82 ms | 0 ms |
| es->en | 0 ms | 44 ms | 29 ms | 48 ms | 0 ms |
| fr->en | 0 ms | 51 ms | 37 ms | 60 ms | 0 ms |
| de->en | 0 ms | 36 ms | 32 ms | 39 ms | 0 ms |
| it->en | 0 ms | 53 ms | 30 ms | 65 ms | 0 ms |
| ru->en | 0 ms | 58 ms | 35 ms | 64 ms | 0 ms |
| zh->en | 0 ms | 58 ms | 35 ms | 68 ms | 0 ms |
| nl->en | 0 ms | 57 ms | 35 ms | 57 ms | 0 ms |
| pl->en | 0 ms | 61 ms | 43 ms | 64 ms | 0 ms |
| uk->en | 0 ms | 53 ms | 36 ms | 49 ms | 0 ms |
| tr->en | 0 ms | 58 ms | 34 ms | 56 ms | 0 ms |
| ar->en | 0 ms | 71 ms | 36 ms | 66 ms | 0 ms |
| hi->en | 0 ms | 43 ms | 22 ms | 62 ms | 0 ms |
| ja->en | 0 ms | 72 ms | 44 ms | 75 ms | 0 ms |
| ko->en | 0 ms | 64 ms | 33 ms | 67 ms | 0 ms |

### Problemas encontrados

- **pt->en**: transcrição ruim: 29% das palavras erradas; inventou 9 palavras que não foram faladas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.1 s
- **en->pt**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **es->en**: nenhum problema detectado
- **fr->en**: transcrição ruim: 47% das palavras erradas; inventou 18 palavras que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 3.5 s
- **de->en**: transcrição ruim: 58% das palavras erradas; inventou 13 palavras que não foram faladas; 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **it->en**: transcrição ruim: 58% das palavras erradas; inventou 12 palavras que não foram faladas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **ru->en**: transcrição ruim: 27% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.9 s
- **zh->en**: transcrição ruim: 44% dos caracteres erradas
- **nl->en**: transcrição ruim: 40% das palavras erradas; inventou 9 palavras que não foram faladas; 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **pl->en**: transcrição ruim: 49% das palavras erradas; inventou 11 palavras que não foram faladas
- **uk->en**: transcrição ruim: 66% das palavras erradas; inventou 7 palavras que não foram faladas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **tr->en**: transcrição ruim: 65% das palavras erradas; inventou 16 palavras que não foram faladas
- **ar->en**: transcrição ruim: 64% das palavras erradas; inventou 11 palavras que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 3.0 s
- **hi->en**: transcrição ruim: 100% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 21 palavras seguidas)
- **ja->en**: transcrição ruim: 44% dos caracteres erradas; inventou 17 caracteres que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **ko->en**: transcrição ruim: 29% dos caracteres erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 11 caracteres seguidas); 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
