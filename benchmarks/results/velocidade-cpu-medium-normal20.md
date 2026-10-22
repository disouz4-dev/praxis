_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `medium` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 7.0% palavras | 3.5% | 74.8 | 5.5 s | 6.8 s | -0.1 s | 7.0 s | 70% | ❌ |
| en->pt | 20s | 5.6% palavras | 6.2% | 78.6 | 4.7 s | 5.8 s | +0.5 s | 8.3 s | 89% | ❌ |
| es->en | 21s | 4.4% palavras | 1.1% | 61.6 | 4.4 s | 5.1 s | +0.4 s | 5.3 s | 54% | ❌ |
| fr->en | 21s | 19.6% palavras | 6.0% | 48.1 | 5.5 s | 8.7 s | +1.9 s | 6.5 s | 60% | ❌ |
| de->en | 19s | 11.8% palavras | 4.9% | 67.1 | 6.4 s | 7.3 s | -0.3 s | 3.4 s | 41% | ❌ |
| it->en | 20s | 19.1% palavras | 5.6% | 47.3 | 5.8 s | 6.9 s | +0.4 s | 2.4 s | 52% | ❌ |
| ru->en | 19s | 19.2% palavras | 6.1% | 72.9 | 5.1 s | 7.5 s | +1.0 s | 7.2 s | 57% | ❌ |
| zh->en | 19s | 11.4% caracteres | 11.4% | 56.0 | 5.8 s | 6.3 s | +0.7 s | 4.0 s | 40% | ❌ |
| nl->en | 22s | 18.8% palavras | 4.0% | 66.6 | 7.2 s | 8.8 s | +3.5 s | 9.3 s | 66% | ❌ |
| pl->en | 18s | 7.7% palavras | 0.9% | 49.3 | 4.5 s | 5.3 s | +0.5 s | 7.7 s | 76% | ❌ |
| uk->en | 19s | 2.9% palavras | 0.5% | 78.8 | 7.4 s | 9.1 s | -0.1 s | 5.8 s | 56% | ❌ |
| tr->en | 17s | 0.0% palavras | 0.0% | 56.5 | 4.8 s | 5.5 s | +0.1 s | 3.8 s | 33% | ❌ |
| ar->en | 19s | 13.3% palavras | 9.5% | 57.8 | 5.0 s | 5.2 s | -0.1 s | 4.9 s | 46% | ❌ |
| hi->en | 20s | 48.8% palavras | 19.8% | 26.1 | 9.2 s | 13.6 s | +5.0 s | 9.0 s | 48% | ❌ |
| ja->en | 25s | 15.9% caracteres | 15.9% | 62.6 | 5.3 s | 6.8 s | -1.5 s | 5.5 s | 47% | ❌ |
| ko->en | 20s | 5.4% caracteres | 5.4% | 49.5 | 5.4 s | 6.2 s | -0.9 s | 7.3 s | 53% | ❌ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 1489 ms | 3493 ms | 25 ms | 71 ms | 0 ms |
| en->pt | 0 ms | 3524 ms | 29 ms | 87 ms | 0 ms |
| es->en | 0 ms | 3363 ms | 27 ms | 44 ms | 0 ms |
| fr->en | 143 ms | 3846 ms | 33 ms | 56 ms | 633 ms |
| de->en | 2294 ms | 3583 ms | 33 ms | 55 ms | 0 ms |
| it->en | 1623 ms | 3698 ms | 21 ms | 52 ms | 0 ms |
| ru->en | 18 ms | 3694 ms | 29 ms | 75 ms | 53 ms |
| zh->en | 0 ms | 3323 ms | 17 ms | 33 ms | 0 ms |
| nl->en | 3010 ms | 3631 ms | 25 ms | 55 ms | 0 ms |
| pl->en | 0 ms | 3953 ms | 39 ms | 76 ms | 0 ms |
| uk->en | 3293 ms | 3879 ms | 26 ms | 61 ms | 0 ms |
| tr->en | 0 ms | 3815 ms | 17 ms | 38 ms | 0 ms |
| ar->en | 0 ms | 3926 ms | 22 ms | 52 ms | 0 ms |
| hi->en | 4757 ms | 3903 ms | 12 ms | 30 ms | 0 ms |
| ja->en | 0 ms | 4068 ms | 31 ms | 95 ms | 0 ms |
| ko->en | 0 ms | 3775 ms | 34 ms | 88 ms | 0 ms |

### Problemas encontrados

- **pt->en**: não acompanha o falante: atraso típico 5.5 s, sobe -0.1 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para; trechos esperam 1489 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **en->pt**: não acompanha o falante: atraso típico 4.7 s, sobe +0.5 s da 1ª para a 2ª metade e sobram 8 s de tradução quando ele para
- **es->en**: não acompanha o falante: atraso típico 4.4 s, sobe +0.4 s da 1ª para a 2ª metade e sobram 5 s de tradução quando ele para
- **fr->en**: não acompanha o falante: atraso típico 5.5 s, sobe +1.9 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para
- **de->en**: não acompanha o falante: atraso típico 6.4 s, sobe -0.3 s da 1ª para a 2ª metade e sobram 3 s de tradução quando ele para; trechos esperam 2294 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **it->en**: não acompanha o falante: atraso típico 5.8 s, sobe +0.4 s da 1ª para a 2ª metade e sobram 2 s de tradução quando ele para; trechos esperam 1623 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ru->en**: não acompanha o falante: atraso típico 5.1 s, sobe +1.0 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para
- **zh->en**: não acompanha o falante: atraso típico 5.8 s, sobe +0.7 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para
- **nl->en**: não acompanha o falante: atraso típico 7.2 s, sobe +3.5 s da 1ª para a 2ª metade e sobram 9 s de tradução quando ele para; trechos esperam 3010 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **pl->en**: não acompanha o falante: atraso típico 4.5 s, sobe +0.5 s da 1ª para a 2ª metade e sobram 8 s de tradução quando ele para
- **uk->en**: não acompanha o falante: atraso típico 7.4 s, sobe -0.1 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para; trechos esperam 3293 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **tr->en**: não acompanha o falante: atraso típico 4.8 s, sobe +0.1 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para
- **ar->en**: não acompanha o falante: atraso típico 5.0 s, sobe -0.1 s da 1ª para a 2ª metade e sobram 5 s de tradução quando ele para
- **hi->en**: transcrição ruim: 49% das palavras erradas; não acompanha o falante: atraso típico 9.2 s, sobe +5.0 s da 1ª para a 2ª metade e sobram 9 s de tradução quando ele para; trechos esperam 4757 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ja->en**: não acompanha o falante: atraso típico 5.3 s, sobe -1.5 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para
- **ko->en**: não acompanha o falante: atraso típico 5.4 s, sobe -0.9 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
