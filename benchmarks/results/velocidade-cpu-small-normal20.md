_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `small` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 14.0% palavras | 7.6% | 71.6 | 1.8 s | 3.8 s | +0.2 s | 4.7 s | 66% | ✅ |
| en->pt | 20s | 0.0% palavras | 0.0% | 79.6 | 2.4 s | 3.2 s | +0.5 s | 6.2 s | 87% | ✅ |
| es->en | 21s | 2.2% palavras | 0.5% | 56.5 | 1.9 s | 2.7 s | +0.3 s | 3.0 s | 55% | ✅ |
| fr->en | 21s | 28.6% palavras | 10.4% | 57.9 | 3.5 s | 4.6 s | +0.1 s | 6.2 s | 77% | ✅ |
| de->en | 19s | 23.5% palavras | 7.6% | 63.7 | 2.2 s | 3.7 s | -0.7 s | 4.9 s | 57% | ✅ |
| it->en | 20s | 36.2% palavras | 9.7% | 53.2 | 2.6 s | 3.4 s | -1.3 s | 5.4 s | 71% | ✅ |
| ru->en | 19s | 19.2% palavras | 3.6% | 74.3 | 2.6 s | 4.5 s | +0.6 s | 4.1 s | 56% | ✅ |
| zh->en | 19s | 20.4% caracteres | 20.4% | 48.9 | 2.3 s | 3.9 s | -0.7 s | 1.1 s | 44% | ✅ |
| nl->en | 22s | 18.8% palavras | 5.7% | 68.6 | 2.6 s | 3.6 s | +1.5 s | 5.3 s | 72% | ✅ |
| pl->en | 18s | 15.4% palavras | 3.3% | 50.7 | 2.0 s | 2.6 s | +0.5 s | 4.6 s | 76% | ✅ |
| uk->en | 19s | 14.7% palavras | 3.2% | 71.1 | 2.3 s | 3.9 s | -2.1 s | 3.9 s | 69% | ✅ |
| tr->en | 17s | 8.3% palavras | 1.2% | 61.3 | 1.8 s | 2.3 s | -0.6 s | 0.0 s | 34% | ✅ |
| ar->en | 19s | 20.0% palavras | 7.6% | 57.3 | 2.7 s | 3.4 s | -0.3 s | 3.4 s | 61% | ✅ |
| hi->en | 20s | 58.5% palavras | 28.8% | 26.6 | 2.0 s | 2.5 s | +0.6 s | 4.9 s | 54% | ✅ |
| ja->en | — | — | — | — | — | — | — | — | — | ⚠️ ModuleNotFoundError: No module named 'stanza' |
| ko->en | — | — | — | — | — | — | — | — | — | ⚠️ ModuleNotFoundError: No module named 'stanza' |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 1250 ms | 24 ms | 79 ms | 0 ms |
| en->pt | 0 ms | 1248 ms | 30 ms | 96 ms | 1 ms |
| es->en | 0 ms | 1201 ms | 28 ms | 37 ms | 0 ms |
| fr->en | 0 ms | 1368 ms | 31 ms | 44 ms | 1348 ms |
| de->en | 0 ms | 1254 ms | 28 ms | 38 ms | 0 ms |
| it->en | 0 ms | 1336 ms | 25 ms | 54 ms | 0 ms |
| ru->en | 0 ms | 1341 ms | 28 ms | 64 ms | 117 ms |
| zh->en | 0 ms | 1187 ms | 16 ms | 33 ms | 0 ms |
| nl->en | 6 ms | 1290 ms | 29 ms | 50 ms | 1 ms |
| pl->en | 0 ms | 1472 ms | 40 ms | 76 ms | 64 ms |
| uk->en | 0 ms | 1410 ms | 26 ms | 61 ms | 0 ms |
| tr->en | 0 ms | 1430 ms | 22 ms | 37 ms | 0 ms |
| ar->en | 0 ms | 1484 ms | 32 ms | 50 ms | 21 ms |
| hi->en | 0 ms | 1354 ms | 16 ms | 36 ms | 0 ms |

### Problemas encontrados

- **pt->en**: 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 3.8 s
- **en->pt**: picos de atraso: 1 em cada 20 trechos demora mais de 3.2 s
- **es->en**: nenhum problema detectado
- **fr->en**: transcrição ruim: 29% das palavras erradas; a tradução pronta espera 1348 ms a fala anterior terminar de tocar; picos de atraso: 1 em cada 20 trechos demora mais de 4.6 s
- **de->en**: transcrição ruim: 24% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **it->en**: transcrição ruim: 36% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.4 s
- **ru->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.5 s
- **zh->en**: transcrição ruim: 20% dos caracteres erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.9 s
- **nl->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.6 s
- **pl->en**: nenhum problema detectado
- **uk->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.9 s
- **tr->en**: nenhum problema detectado
- **ar->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.4 s
- **hi->en**: transcrição ruim: 59% das palavras erradas
- **ja->en**: nenhum problema detectado
- **ko->en**: nenhum problema detectado

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
