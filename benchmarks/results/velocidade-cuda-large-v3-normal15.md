_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `large-v3` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 14s | 18.2% palavras | 3.0% | 81.9 | 2.7 s | 4.0 s | +0.0 s | 4.7 s | 68% | ✅ |
| en->pt | 14s | 7.0% palavras | 8.5% | 81.1 | 2.3 s | 2.9 s | +1.1 s | 5.6 s | 91% | ✅ |
| es->en | 12s | 3.9% palavras | 1.0% | 81.5 | 1.1 s | 1.2 s | -0.2 s | 2.7 s | 57% | ✅ |
| fr->en | 14s | 10.0% palavras | 8.5% | 59.4 | 1.4 s | 2.8 s | +1.0 s | 3.7 s | 67% | ✅ |
| de->en | 14s | 12.5% palavras | 4.4% | 57.2 | 1.0 s | 1.2 s | +0.1 s | 3.8 s | 55% | ✅ |
| it->en | 16s | 13.5% palavras | 3.0% | 69.8 | 2.7 s | 4.3 s | +0.9 s | 5.1 s | 78% | ✅ |
| ru->en | 17s | 4.8% palavras | 1.5% | 56.0 | 1.9 s | 2.2 s | +0.0 s | 1.0 s | 51% | ✅ |
| zh->en | 15s | 12.0% caracteres | 12.0% | 56.3 | 2.1 s | 2.4 s | +0.3 s | 4.4 s | 79% | ✅ |
| nl->en | 15s | 11.1% palavras | 11.4% | 76.3 | 0.9 s | 1.0 s | +0.3 s | 4.1 s | 58% | ✅ |
| pl->en | 15s | 0.0% palavras | 0.0% | 63.4 | 1.8 s | 3.0 s | +0.4 s | 3.7 s | 80% | ✅ |
| uk->en | 15s | 4.2% palavras | 2.0% | 97.1 | 1.2 s | 1.2 s | -0.0 s | 3.4 s | 56% | ✅ |
| tr->en | 14s | 19.1% palavras | 9.6% | 57.4 | 1.8 s | 2.1 s | -0.2 s | 1.8 s | 47% | ✅ |
| ar->en | 15s | 6.9% palavras | 6.7% | 84.3 | 1.8 s | 4.2 s | +1.7 s | 4.2 s | 60% | ❌ |
| hi->en | 15s | 31.0% palavras | 13.3% | 33.9 | 1.4 s | 1.9 s | +0.2 s | 1.7 s | 54% | ✅ |
| ja->en | 14s | 0.0% caracteres | 0.0% | 71.4 | 3.0 s | 3.7 s | +0.8 s | 3.5 s | 53% | ✅ |
| ko->en | 12s | 26.0% caracteres | 26.0% | 55.6 | 2.7 s | 2.7 s | -0.0 s | 4.0 s | 63% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 597 ms | 20 ms | 55 ms | 1256 ms |
| en->pt | 0 ms | 726 ms | 26 ms | 56 ms | 168 ms |
| es->en | 0 ms | 576 ms | 25 ms | 36 ms | 0 ms |
| fr->en | 0 ms | 721 ms | 26 ms | 79 ms | 0 ms |
| de->en | 0 ms | 577 ms | 17 ms | 32 ms | 0 ms |
| it->en | 0 ms | 684 ms | 21 ms | 67 ms | 1138 ms |
| ru->en | 0 ms | 664 ms | 19 ms | 56 ms | 0 ms |
| zh->en | 0 ms | 897 ms | 33 ms | 78 ms | 336 ms |
| nl->en | 0 ms | 702 ms | 25 ms | 63 ms | 0 ms |
| pl->en | 0 ms | 684 ms | 28 ms | 65 ms | 469 ms |
| uk->en | 0 ms | 784 ms | 31 ms | 90 ms | 0 ms |
| tr->en | 0 ms | 713 ms | 26 ms | 80 ms | 236 ms |
| ar->en | 0 ms | 868 ms | 23 ms | 77 ms | 0 ms |
| hi->en | 0 ms | 709 ms | 10 ms | 24 ms | 299 ms |
| ja->en | 0 ms | 766 ms | 33 ms | 79 ms | 1313 ms |
| ko->en | 0 ms | 804 ms | 38 ms | 95 ms | 100 ms |

### Problemas encontrados

- **pt->en**: a tradução pronta espera 1256 ms a fala anterior terminar de tocar; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **en->pt**: nenhum problema detectado
- **es->en**: nenhum problema detectado
- **fr->en**: nenhum problema detectado
- **de->en**: nenhum problema detectado
- **it->en**: a tradução pronta espera 1138 ms a fala anterior terminar de tocar; picos de atraso: 1 em cada 20 trechos demora mais de 4.3 s
- **ru->en**: nenhum problema detectado
- **zh->en**: nenhum problema detectado
- **nl->en**: nenhum problema detectado
- **pl->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.0 s
- **uk->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **tr->en**: nenhum problema detectado
- **ar->en**: não acompanha o falante: atraso típico 1.8 s, sobe +1.7 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para
- **hi->en**: transcrição ruim: 31% das palavras erradas
- **ja->en**: a tradução pronta espera 1313 ms a fala anterior terminar de tocar; picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **ko->en**: transcrição ruim: 26% dos caracteres erradas; inventou 13 caracteres que não foram faladas

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
