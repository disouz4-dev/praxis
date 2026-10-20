_Máquina: macOS-26.6.2-x86_64-i386-64bit · processador i386 · Python 3.12.15 · placa de vídeo CUDA: não_

Whisper `small` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 14.0% palavras | 7.6% | 74.6 | 2.6 s | 4.5 s | +0.1 s | 5.4 s | 65% | ✅ |
| en->pt | 20s | 0.0% palavras | 0.0% | 74.3 | 3.0 s | 3.7 s | +0.4 s | 6.7 s | 85% | ✅ |
| es->en | 21s | 2.2% palavras | 0.5% | 56.5 | 2.5 s | 3.3 s | -0.3 s | 3.3 s | 54% | ✅ |
| fr->en | 21s | 28.6% palavras | 10.4% | 62.1 | 3.8 s | 5.2 s | -0.0 s | 6.6 s | 79% | ✅ |
| de->en | 19s | 23.5% palavras | 7.6% | 61.3 | 1.9 s | 2.5 s | -0.3 s | 5.4 s | 58% | ✅ |
| it->en | 20s | 38.3% palavras | 10.8% | 51.1 | 2.9 s | 3.7 s | -1.3 s | 5.4 s | 70% | ✅ |
| ru->en | 19s | 15.4% palavras | 3.1% | 75.2 | 2.9 s | 4.9 s | +0.6 s | 4.5 s | 57% | ✅ |
| zh->en | 19s | 20.4% caracteres | 20.4% | 49.1 | 2.7 s | 4.1 s | -0.5 s | 1.4 s | 47% | ✅ |
| nl->en | 22s | 20.8% palavras | 5.7% | 62.4 | 3.0 s | 4.0 s | +1.4 s | 5.5 s | 71% | ✅ |
| pl->en | 18s | 10.3% palavras | 2.4% | 53.5 | 2.4 s | 2.7 s | +0.2 s | 5.3 s | 74% | ✅ |
| uk->en | 19s | 14.7% palavras | 3.2% | 75.6 | 2.5 s | 4.0 s | -2.0 s | 4.3 s | 71% | ✅ |
| tr->en | 17s | 4.2% palavras | 0.6% | 59.6 | 2.0 s | 2.5 s | -0.6 s | 0.7 s | 36% | ✅ |
| ar->en | 19s | 20.0% palavras | 7.6% | 54.8 | 3.0 s | 3.7 s | -0.2 s | 3.8 s | 64% | ✅ |
| hi->en | 20s | 61.0% palavras | 30.5% | 29.2 | 2.9 s | 3.0 s | -0.1 s | 5.6 s | 61% | ✅ |
| ja->en | 25s | 18.2% caracteres | 18.2% | 49.1 | 2.5 s | 2.9 s | -0.4 s | 3.4 s | 40% | ✅ |
| ko->en | 20s | 4.0% caracteres | 4.0% | 45.8 | 3.4 s | 3.7 s | -0.1 s | 6.0 s | 56% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 5 ms | 1707 ms | 85 ms | 179 ms | 2 ms |
| en->pt | 0 ms | 1735 ms | 92 ms | 188 ms | 3 ms |
| es->en | 0 ms | 1504 ms | 139 ms | 83 ms | 1 ms |
| fr->en | 0 ms | 1504 ms | 80 ms | 92 ms | 1272 ms |
| de->en | 0 ms | 1404 ms | 69 ms | 88 ms | 0 ms |
| it->en | 0 ms | 1497 ms | 59 ms | 120 ms | 3 ms |
| ru->en | 0 ms | 1507 ms | 75 ms | 142 ms | 113 ms |
| zh->en | 0 ms | 1432 ms | 45 ms | 71 ms | 1 ms |
| nl->en | 183 ms | 1473 ms | 71 ms | 108 ms | 1 ms |
| pl->en | 0 ms | 1707 ms | 124 ms | 159 ms | 1 ms |
| uk->en | 0 ms | 1564 ms | 71 ms | 137 ms | 1 ms |
| tr->en | 0 ms | 1585 ms | 52 ms | 84 ms | 0 ms |
| ar->en | 0 ms | 1666 ms | 83 ms | 112 ms | 1 ms |
| hi->en | 0 ms | 1756 ms | 52 ms | 71 ms | 0 ms |
| ja->en | 0 ms | 1627 ms | 92 ms | 119 ms | 1 ms |
| ko->en | 0 ms | 2284 ms | 139 ms | 176 ms | 2 ms |

### Problemas encontrados

- **pt->en**: 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 4.5 s
- **en->pt**: picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **es->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.3 s
- **fr->en**: transcrição ruim: 29% das palavras erradas; a tradução pronta espera 1272 ms a fala anterior terminar de tocar; picos de atraso: 1 em cada 20 trechos demora mais de 5.2 s
- **de->en**: transcrição ruim: 24% das palavras erradas
- **it->en**: transcrição ruim: 38% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **ru->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.9 s
- **zh->en**: transcrição ruim: 20% dos caracteres erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.1 s
- **nl->en**: transcrição ruim: 21% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **pl->en**: nenhum problema detectado
- **uk->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **tr->en**: nenhum problema detectado
- **ar->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **hi->en**: transcrição ruim: 61% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.0 s
- **ja->en**: nenhum problema detectado
- **ko->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
