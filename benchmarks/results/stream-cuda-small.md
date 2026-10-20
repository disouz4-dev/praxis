_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `small` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 71s | 7.8% palavras | 2.3% | 71.4 | 1.0 s | 3.6 s | +0.2 s | 3.5 s | 69% | ✅ |
| en->pt | 72s | 2.1% palavras | 0.7% | 72.2 | 0.8 s | 2.7 s | -0.5 s | 4.3 s | 79% | ✅ |
| es->en | 73s | 2.6% palavras | 0.6% | 67.9 | 0.8 s | 2.4 s | -0.1 s | 1.2 s | 59% | ✅ |
| fr->en | 62s | 25.3% palavras | 13.0% | 57.0 | 1.4 s | 3.8 s | +0.6 s | 3.0 s | 73% | ✅ |
| de->en | 63s | 28.3% palavras | 9.0% | 57.5 | 0.7 s | 2.6 s | +0.0 s | 1.7 s | 54% | ✅ |
| it->en | 78s | 33.3% palavras | 9.4% | 54.8 | 1.1 s | 3.8 s | +0.2 s | 4.1 s | 69% | ✅ |
| ru->en | 66s | 15.9% palavras | 4.9% | 71.4 | 1.5 s | 5.0 s | -0.1 s | 3.4 s | 58% | ✅ |
| zh->en | 62s | 26.2% caracteres | 26.2% | 30.1 | 1.2 s | 2.5 s | +0.2 s | 1.8 s | 53% | ✅ |
| nl->en | 66s | 22.4% palavras | 6.3% | 58.7 | 0.6 s | 2.5 s | -0.1 s | 3.8 s | 64% | ✅ |
| pl->en | 69s | 13.3% palavras | 2.3% | 63.5 | 0.7 s | 2.5 s | +0.2 s | 3.5 s | 78% | ✅ |
| uk->en | 69s | 17.4% palavras | 5.2% | 64.6 | 0.5 s | 3.0 s | -1.0 s | 3.3 s | 59% | ✅ |
| tr->en | 72s | 24.7% palavras | 6.6% | 55.7 | 0.8 s | 2.5 s | -0.9 s | 3.2 s | 42% | ✅ |
| ar->en | 74s | 28.1% palavras | 9.4% | 64.5 | 1.4 s | 3.7 s | +0.1 s | 3.9 s | 64% | ✅ |
| hi->en | 69s | 73.8% palavras | 45.2% | 28.3 | 0.6 s | 1.6 s | -0.4 s | 1.5 s | 44% | ✅ |
| ja->en | 64s | 20.0% caracteres | 20.0% | 50.6 | 1.4 s | 3.7 s | -1.5 s | 2.2 s | 46% | ✅ |
| ko->en | 69s | 8.6% caracteres | 8.6% | 57.9 | 2.0 s | 3.0 s | +0.3 s | 2.6 s | 60% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 166 ms | 25 ms | 70 ms | 0 ms |
| en->pt | 0 ms | 175 ms | 30 ms | 70 ms | 0 ms |
| es->en | 0 ms | 147 ms | 27 ms | 42 ms | 4 ms |
| fr->en | 0 ms | 166 ms | 24 ms | 57 ms | 0 ms |
| de->en | 0 ms | 141 ms | 19 ms | 33 ms | 0 ms |
| it->en | 0 ms | 175 ms | 20 ms | 58 ms | 0 ms |
| ru->en | 0 ms | 179 ms | 28 ms | 76 ms | 0 ms |
| zh->en | 0 ms | 162 ms | 19 ms | 51 ms | 0 ms |
| nl->en | 0 ms | 184 ms | 30 ms | 66 ms | 0 ms |
| pl->en | 0 ms | 187 ms | 31 ms | 75 ms | 0 ms |
| uk->en | 0 ms | 161 ms | 21 ms | 53 ms | 0 ms |
| tr->en | 0 ms | 180 ms | 22 ms | 37 ms | 0 ms |
| ar->en | 0 ms | 209 ms | 24 ms | 64 ms | 0 ms |
| hi->en | 0 ms | 256 ms | 15 ms | 30 ms | 0 ms |
| ja->en | 0 ms | 207 ms | 28 ms | 60 ms | 0 ms |
| ko->en | 0 ms | 186 ms | 30 ms | 79 ms | 1 ms |

### Problemas encontrados

- **pt->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.6 s
- **en->pt**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **es->en**: nenhum problema detectado
- **fr->en**: transcrição ruim: 25% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.8 s
- **de->en**: transcrição ruim: 28% das palavras erradas; 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **it->en**: transcrição ruim: 33% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 3.8 s
- **ru->en**: picos de atraso: 1 em cada 20 trechos demora mais de 5.0 s
- **zh->en**: transcrição ruim: 26% dos caracteres erradas
- **nl->en**: transcrição ruim: 22% das palavras erradas; 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **pl->en**: nenhum problema detectado
- **uk->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 3.0 s
- **tr->en**: transcrição ruim: 25% das palavras erradas
- **ar->en**: transcrição ruim: 28% das palavras erradas; inventou 10 palavras que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **hi->en**: transcrição ruim: 74% das palavras erradas; pulou 2 trecho(s) inteiro(s) da fala (maior: 18 palavras seguidas)
- **ja->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **ko->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.0 s

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
