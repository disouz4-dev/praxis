_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `small` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 6.1% palavras | 0.8% | 77.2 | 1.7 s | 2.0 s | +0.1 s | 2.9 s | 49% | ✅ |
| en->pt | 19s | 0.0% palavras | 0.0% | 77.9 | 2.6 s | 2.8 s | +0.9 s | 4.3 s | 69% | ✅ |
| es->en | 16s | 7.7% palavras | 1.0% | 79.0 | 1.7 s | 1.8 s | -0.1 s | 3.3 s | 42% | ✅ |
| fr->en | 19s | 7.5% palavras | 7.3% | 54.9 | 1.9 s | 2.2 s | -0.0 s | 4.4 s | 55% | ✅ |
| de->en | 19s | 20.8% palavras | 10.9% | 50.4 | 1.5 s | 2.0 s | +0.3 s | 3.4 s | 39% | ✅ |
| it->en | 21s | 37.8% palavras | 8.9% | 48.4 | 1.7 s | 1.7 s | -0.0 s | 2.2 s | 58% | ✅ |
| ru->en | 22s | 33.3% palavras | 11.9% | 50.5 | 2.7 s | 4.1 s | -1.4 s | 0.8 s | 43% | ✅ |
| zh->en | 20s | 16.9% caracteres | 16.9% | 44.7 | 2.5 s | 3.5 s | +0.7 s | 4.7 s | 73% | ✅ |
| nl->en | 20s | 44.4% palavras | 17.5% | 61.7 | 1.4 s | 1.6 s | +0.0 s | 4.8 s | 44% | ✅ |
| pl->en | 21s | 21.6% palavras | 4.3% | 58.5 | 1.7 s | 2.2 s | -0.6 s | 4.4 s | 63% | ✅ |
| uk->en | 20s | 16.7% palavras | 4.7% | 53.2 | 2.6 s | 3.7 s | +1.3 s | 2.2 s | 38% | ✅ |
| tr->en | 19s | 23.8% palavras | 13.8% | 45.1 | 1.8 s | 2.6 s | -1.0 s | 0.1 s | 33% | ✅ |
| ar->en | 20s | 17.2% palavras | 10.1% | 67.3 | 2.5 s | 3.1 s | -0.2 s | 2.4 s | 41% | ✅ |
| hi->en | 20s | 96.5% palavras | 39.2% | 15.9 | 1.8 s | 2.3 s | +0.4 s | 1.4 s | 46% | ✅ |
| ja->en | 19s | 37.0% caracteres | 37.0% | 44.3 | 1.8 s | 2.0 s | -0.2 s | 0.0 s | 29% | ✅ |
| ko->en | 17s | 2.0% caracteres | 2.0% | 55.9 | 3.6 s | 4.9 s | -1.0 s | 2.4 s | 45% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 1245 ms | 24 ms | 49 ms | 0 ms |
| en->pt | 0 ms | 1226 ms | 26 ms | 76 ms | 0 ms |
| es->en | 0 ms | 1188 ms | 24 ms | 39 ms | 0 ms |
| fr->en | 0 ms | 1231 ms | 22 ms | 58 ms | 0 ms |
| de->en | 0 ms | 1195 ms | 17 ms | 37 ms | 0 ms |
| it->en | 0 ms | 1255 ms | 15 ms | 43 ms | 0 ms |
| ru->en | 0 ms | 1276 ms | 22 ms | 56 ms | 0 ms |
| zh->en | 0 ms | 1402 ms | 28 ms | 85 ms | 0 ms |
| nl->en | 0 ms | 1220 ms | 18 ms | 44 ms | 0 ms |
| pl->en | 0 ms | 1296 ms | 25 ms | 60 ms | 0 ms |
| uk->en | 0 ms | 1365 ms | 20 ms | 46 ms | 441 ms |
| tr->en | 0 ms | 1287 ms | 17 ms | 48 ms | 0 ms |
| ar->en | 0 ms | 1347 ms | 18 ms | 58 ms | 0 ms |
| hi->en | 0 ms | 1267 ms | 15 ms | 28 ms | 0 ms |
| ja->en | 0 ms | 1314 ms | 23 ms | 59 ms | 0 ms |
| ko->en | 0 ms | 1262 ms | 21 ms | 56 ms | 0 ms |

### Problemas encontrados

- **pt->en**: nenhum problema detectado
- **en->pt**: nenhum problema detectado
- **es->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **fr->en**: nenhum problema detectado
- **de->en**: transcrição ruim: 21% das palavras erradas; 1 trecho(s) com fala viraram texto vazio
- **it->en**: transcrição ruim: 38% das palavras erradas
- **ru->en**: transcrição ruim: 33% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.1 s
- **zh->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.5 s
- **nl->en**: transcrição ruim: 44% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **pl->en**: transcrição ruim: 22% das palavras erradas
- **uk->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **tr->en**: transcrição ruim: 24% das palavras erradas
- **ar->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.1 s
- **hi->en**: transcrição ruim: 97% das palavras erradas; inventou 4 palavras que não foram faladas
- **ja->en**: transcrição ruim: 37% dos caracteres erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 10 caracteres seguidas)
- **ko->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.9 s

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
