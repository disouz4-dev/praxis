_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `large-v3` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 9.3% palavras | 5.6% | 75.2 | 1.3 s | 3.8 s | -1.2 s | 4.3 s | 67% | ✅ |
| en->pt | 20s | 5.6% palavras | 6.2% | 83.7 | 1.9 s | 3.0 s | +0.8 s | 5.5 s | 90% | ✅ |
| es->en | 21s | 4.4% palavras | 1.1% | 55.3 | 1.3 s | 2.1 s | +0.3 s | 2.4 s | 54% | ✅ |
| fr->en | 21s | 16.1% palavras | 7.2% | 52.1 | 2.3 s | 3.2 s | -0.1 s | 4.4 s | 71% | ✅ |
| de->en | 19s | 8.8% palavras | 2.7% | 67.7 | 1.4 s | 2.7 s | -0.6 s | 4.2 s | 57% | ✅ |
| it->en | 20s | 10.6% palavras | 3.6% | 51.4 | 2.0 s | 3.2 s | -1.5 s | 4.2 s | 70% | ✅ |
| ru->en | 19s | 11.5% palavras | 7.1% | 67.2 | 2.0 s | 4.3 s | +0.6 s | 3.8 s | 58% | ✅ |
| zh->en | 19s | 0.0% caracteres | 0.0% | 71.8 | 2.2 s | 3.2 s | -0.1 s | 0.8 s | 48% | ✅ |
| nl->en | 22s | 8.3% palavras | 4.0% | 76.8 | 2.5 s | 3.3 s | +1.8 s | 3.3 s | 77% | ❌ |
| pl->en | 18s | 5.1% palavras | 0.0% | 49.2 | 1.3 s | 2.0 s | +0.5 s | 4.0 s | 75% | ✅ |
| uk->en | 19s | 2.9% palavras | 0.5% | 78.8 | 1.6 s | 3.2 s | -2.0 s | 3.4 s | 73% | ✅ |
| tr->en | 17s | 0.0% palavras | 0.0% | 56.5 | 1.1 s | 1.6 s | -0.6 s | 0.0 s | 35% | ✅ |
| ar->en | 19s | 6.7% palavras | 3.2% | 58.7 | 2.1 s | 2.8 s | -0.2 s | 2.9 s | 56% | ✅ |
| hi->en | 20s | 26.8% palavras | 11.3% | 31.1 | 1.6 s | 2.0 s | +0.5 s | 4.2 s | 54% | ✅ |
| ja->en | 25s | 10.2% caracteres | 10.2% | 60.4 | 1.7 s | 2.0 s | -0.5 s | 3.0 s | 45% | ✅ |
| ko->en | 20s | 2.7% caracteres | 2.7% | 56.4 | 2.4 s | 3.3 s | -1.3 s | 4.2 s | 60% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 658 ms | 19 ms | 65 ms | 0 ms |
| en->pt | 0 ms | 668 ms | 27 ms | 82 ms | 138 ms |
| es->en | 0 ms | 614 ms | 26 ms | 42 ms | 0 ms |
| fr->en | 0 ms | 714 ms | 27 ms | 65 ms | 986 ms |
| de->en | 0 ms | 651 ms | 29 ms | 46 ms | 0 ms |
| it->en | 0 ms | 698 ms | 23 ms | 52 ms | 128 ms |
| ru->en | 0 ms | 715 ms | 27 ms | 71 ms | 136 ms |
| zh->en | 0 ms | 532 ms | 16 ms | 36 ms | 0 ms |
| nl->en | 0 ms | 627 ms | 23 ms | 58 ms | 914 ms |
| pl->en | 0 ms | 789 ms | 33 ms | 81 ms | 0 ms |
| uk->en | 0 ms | 746 ms | 24 ms | 73 ms | 0 ms |
| tr->en | 0 ms | 722 ms | 16 ms | 44 ms | 0 ms |
| ar->en | 0 ms | 808 ms | 26 ms | 75 ms | 0 ms |
| hi->en | 0 ms | 705 ms | 12 ms | 23 ms | 0 ms |
| ja->en | 0 ms | 829 ms | 34 ms | 75 ms | 0 ms |
| ko->en | 0 ms | 724 ms | 32 ms | 102 ms | 0 ms |

### Problemas encontrados

- **pt->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.8 s
- **en->pt**: nenhum problema detectado
- **es->en**: nenhum problema detectado
- **fr->en**: a tradução pronta espera 986 ms a fala anterior terminar de tocar; picos de atraso: 1 em cada 20 trechos demora mais de 3.2 s
- **de->en**: nenhum problema detectado
- **it->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.2 s
- **ru->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.3 s
- **zh->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.2 s
- **nl->en**: não acompanha o falante: atraso típico 2.5 s, sobe +1.8 s da 1ª para a 2ª metade e sobram 3 s de tradução quando ele para; a tradução pronta espera 914 ms a fala anterior terminar de tocar; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **pl->en**: nenhum problema detectado
- **uk->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.2 s
- **tr->en**: nenhum problema detectado
- **ar->en**: nenhum problema detectado
- **hi->en**: transcrição ruim: 27% das palavras erradas
- **ja->en**: nenhum problema detectado
- **ko->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.3 s

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
