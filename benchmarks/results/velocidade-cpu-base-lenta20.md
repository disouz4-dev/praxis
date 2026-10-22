_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `base` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 9.1% palavras | 1.5% | 72.3 | 0.9 s | 1.1 s | +0.1 s | 2.1 s | 50% | ✅ |
| en->pt | 19s | 2.3% palavras | 1.1% | 75.5 | 1.8 s | 1.8 s | +1.0 s | 3.2 s | 65% | ✅ |
| es->en | 16s | 26.9% palavras | 7.7% | 61.7 | 0.9 s | 0.9 s | +0.0 s | 2.3 s | 41% | ✅ |
| fr->en | 19s | 25.0% palavras | 17.1% | 59.7 | 1.0 s | 1.0 s | +0.2 s | 3.1 s | 50% | ✅ |
| de->en | 19s | 79.2% palavras | 28.5% | 36.8 | 0.9 s | 3.1 s | +0.3 s | 2.9 s | 47% | ✅ |
| it->en | 21s | 64.9% palavras | 15.5% | 47.9 | 0.9 s | 1.7 s | +0.7 s | 1.4 s | 59% | ✅ |
| ru->en | 22s | 23.8% palavras | 9.0% | 56.9 | 1.8 s | 2.6 s | -0.9 s | 0.0 s | 35% | ✅ |
| zh->en | 20s | 27.7% caracteres | 27.7% | 33.5 | 1.5 s | 1.8 s | +0.6 s | 2.8 s | 62% | ✅ |
| nl->en | 20s | 44.4% palavras | 26.3% | 50.1 | 0.6 s | 0.8 s | +0.0 s | 4.2 s | 42% | ✅ |
| pl->en | 21s | 35.1% palavras | 11.9% | 51.8 | 1.3 s | 3.7 s | -1.9 s | 3.1 s | 61% | ✅ |
| uk->en | 20s | 37.5% palavras | 18.2% | 44.0 | 1.6 s | 3.1 s | +1.6 s | 1.7 s | 40% | ❌ |
| tr->en | 19s | 23.8% palavras | 11.7% | 48.6 | 1.0 s | 1.8 s | -0.9 s | 0.0 s | 31% | ✅ |
| ar->en | 20s | 37.9% palavras | 13.5% | 39.0 | 1.4 s | 2.0 s | +0.0 s | 1.2 s | 40% | ✅ |
| hi->en | 20s | 100.0% palavras | 111.7% | 16.9 | 0.8 s | 2.0 s | +0.6 s | 2.2 s | 60% | ✅ |
| ja->en | 19s | 30.4% caracteres | 30.4% | 45.9 | 1.0 s | 1.0 s | -0.1 s | 0.0 s | 33% | ✅ |
| ko->en | 17s | 16.0% caracteres | 16.0% | 42.9 | 2.7 s | 4.3 s | -1.1 s | 1.7 s | 48% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 433 ms | 24 ms | 52 ms | 0 ms |
| en->pt | 0 ms | 422 ms | 26 ms | 78 ms | 0 ms |
| es->en | 0 ms | 405 ms | 28 ms | 38 ms | 0 ms |
| fr->en | 0 ms | 428 ms | 23 ms | 58 ms | 0 ms |
| de->en | 0 ms | 443 ms | 24 ms | 34 ms | 0 ms |
| it->en | 0 ms | 428 ms | 20 ms | 46 ms | 0 ms |
| ru->en | 0 ms | 451 ms | 21 ms | 42 ms | 0 ms |
| zh->en | 0 ms | 475 ms | 30 ms | 76 ms | 0 ms |
| nl->en | 0 ms | 419 ms | 20 ms | 39 ms | 0 ms |
| pl->en | 0 ms | 457 ms | 31 ms | 66 ms | 0 ms |
| uk->en | 0 ms | 470 ms | 21 ms | 49 ms | 372 ms |
| tr->en | 0 ms | 455 ms | 16 ms | 43 ms | 0 ms |
| ar->en | 0 ms | 472 ms | 19 ms | 46 ms | 0 ms |
| hi->en | 0 ms | 376 ms | 18 ms | 40 ms | 0 ms |
| ja->en | 0 ms | 473 ms | 23 ms | 68 ms | 0 ms |
| ko->en | 0 ms | 462 ms | 20 ms | 59 ms | 0 ms |

### Problemas encontrados

- **pt->en**: nenhum problema detectado
- **en->pt**: nenhum problema detectado
- **es->en**: transcrição ruim: 27% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **fr->en**: transcrição ruim: 25% das palavras erradas
- **de->en**: transcrição ruim: 79% das palavras erradas; inventou 4 palavras que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 3.1 s
- **it->en**: transcrição ruim: 65% das palavras erradas; inventou 6 palavras que não foram faladas
- **ru->en**: transcrição ruim: 24% das palavras erradas
- **zh->en**: transcrição ruim: 28% dos caracteres erradas
- **nl->en**: transcrição ruim: 44% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **pl->en**: transcrição ruim: 35% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **uk->en**: transcrição ruim: 38% das palavras erradas; não acompanha o falante: atraso típico 1.6 s, sobe +1.6 s da 1ª para a 2ª metade e sobram 2 s de tradução quando ele para; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **tr->en**: transcrição ruim: 24% das palavras erradas
- **ar->en**: transcrição ruim: 38% das palavras erradas
- **hi->en**: transcrição ruim: 100% das palavras erradas
- **ja->en**: transcrição ruim: 30% dos caracteres erradas
- **ko->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.3 s

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
