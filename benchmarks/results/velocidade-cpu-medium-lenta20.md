_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `medium` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 9.1% palavras | 2.2% | 71.4 | 4.1 s | 4.3 s | +0.2 s | 2.8 s | 41% | ❌ |
| en->pt | 19s | 0.0% palavras | 0.0% | 77.9 | 4.9 s | 5.1 s | +1.0 s | 6.5 s | 67% | ❌ |
| es->en | 16s | 3.9% palavras | 1.9% | 77.2 | 4.9 s | 5.8 s | +1.9 s | 2.5 s | 31% | ❌ |
| fr->en | 19s | 7.5% palavras | 1.8% | 67.5 | 4.5 s | 4.8 s | +0.1 s | 6.4 s | 50% | ❌ |
| de->en | 19s | 29.2% palavras | 9.5% | 47.8 | 4.3 s | 4.6 s | +0.7 s | 6.7 s | 43% | ❌ |
| it->en | 21s | 24.3% palavras | 7.1% | 53.7 | 4.1 s | 5.2 s | +0.9 s | 2.3 s | 53% | ❌ |
| ru->en | 22s | 14.3% palavras | 7.5% | 54.6 | 5.4 s | 7.1 s | -0.9 s | 3.2 s | 43% | ❌ |
| zh->en | 20s | 18.1% caracteres | 18.1% | 54.4 | 5.3 s | 5.8 s | +0.9 s | 6.7 s | 70% | ❌ |
| nl->en | 20s | 22.2% palavras | 14.0% | 67.4 | 3.8 s | 4.0 s | +0.0 s | 7.0 s | 45% | ✅ |
| pl->en | 21s | 16.2% palavras | 4.3% | 59.7 | 7.1 s | 7.5 s | +0.9 s | 3.8 s | 42% | ❌ |
| uk->en | 20s | 8.3% palavras | 3.4% | 68.6 | 6.1 s | 6.7 s | +1.2 s | 5.2 s | 46% | ❌ |
| tr->en | 19s | 19.1% palavras | 9.6% | 49.1 | 5.1 s | 5.2 s | +0.1 s | 3.8 s | 36% | ❌ |
| ar->en | 20s | 17.2% palavras | 12.6% | 67.6 | 4.6 s | 5.3 s | +0.4 s | 5.0 s | 39% | ❌ |
| hi->en | 20s | 58.6% palavras | 23.3% | 26.5 | 7.3 s | 9.2 s | +2.6 s | 7.4 s | 36% | ❌ |
| ja->en | 19s | 15.2% caracteres | 15.2% | 54.0 | 4.4 s | 4.5 s | -0.1 s | 3.1 s | 36% | ❌ |
| ko->en | 17s | 8.0% caracteres | 8.0% | 56.6 | 6.2 s | 7.6 s | -0.7 s | 5.3 s | 45% | ❌ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 3510 ms | 26 ms | 50 ms | 0 ms |
| en->pt | 0 ms | 3460 ms | 26 ms | 90 ms | 0 ms |
| es->en | 1716 ms | 3316 ms | 28 ms | 42 ms | 0 ms |
| fr->en | 250 ms | 3502 ms | 21 ms | 47 ms | 0 ms |
| de->en | 194 ms | 3393 ms | 18 ms | 31 ms | 0 ms |
| it->en | 89 ms | 3486 ms | 18 ms | 46 ms | 0 ms |
| ru->en | 872 ms | 3576 ms | 20 ms | 57 ms | 0 ms |
| zh->en | 0 ms | 3932 ms | 28 ms | 87 ms | 223 ms |
| nl->en | 0 ms | 3428 ms | 19 ms | 44 ms | 0 ms |
| pl->en | 2926 ms | 3613 ms | 24 ms | 56 ms | 0 ms |
| uk->en | 972 ms | 3757 ms | 21 ms | 58 ms | 0 ms |
| tr->en | 1099 ms | 3611 ms | 17 ms | 51 ms | 0 ms |
| ar->en | 188 ms | 3764 ms | 22 ms | 58 ms | 0 ms |
| hi->en | 2961 ms | 3728 ms | 10 ms | 26 ms | 0 ms |
| ja->en | 0 ms | 3861 ms | 30 ms | 70 ms | 0 ms |
| ko->en | 351 ms | 3561 ms | 22 ms | 50 ms | 0 ms |

### Problemas encontrados

- **pt->en**: não acompanha o falante: atraso típico 4.1 s, sobe +0.2 s da 1ª para a 2ª metade e sobram 3 s de tradução quando ele para
- **en->pt**: não acompanha o falante: atraso típico 4.9 s, sobe +1.0 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para
- **es->en**: não acompanha o falante: atraso típico 4.9 s, sobe +1.9 s da 1ª para a 2ª metade e sobram 3 s de tradução quando ele para; trechos esperam 1716 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **fr->en**: não acompanha o falante: atraso típico 4.5 s, sobe +0.1 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para
- **de->en**: transcrição ruim: 29% das palavras erradas; não acompanha o falante: atraso típico 4.3 s, sobe +0.7 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para; 1 trecho(s) com fala viraram texto vazio
- **it->en**: transcrição ruim: 24% das palavras erradas; não acompanha o falante: atraso típico 4.1 s, sobe +0.9 s da 1ª para a 2ª metade e sobram 2 s de tradução quando ele para
- **ru->en**: não acompanha o falante: atraso típico 5.4 s, sobe -0.9 s da 1ª para a 2ª metade e sobram 3 s de tradução quando ele para; trechos esperam 872 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **zh->en**: inventou 6 caracteres que não foram faladas; não acompanha o falante: atraso típico 5.3 s, sobe +0.9 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para
- **nl->en**: transcrição ruim: 22% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio; picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **pl->en**: não acompanha o falante: atraso típico 7.1 s, sobe +0.9 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para; trechos esperam 2926 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **uk->en**: não acompanha o falante: atraso típico 6.1 s, sobe +1.2 s da 1ª para a 2ª metade e sobram 5 s de tradução quando ele para; trechos esperam 972 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **tr->en**: não acompanha o falante: atraso típico 5.1 s, sobe +0.1 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para; trechos esperam 1099 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ar->en**: não acompanha o falante: atraso típico 4.6 s, sobe +0.4 s da 1ª para a 2ª metade e sobram 5 s de tradução quando ele para; 1 trecho(s) com fala viraram texto vazio
- **hi->en**: transcrição ruim: 59% das palavras erradas; não acompanha o falante: atraso típico 7.3 s, sobe +2.6 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para; trechos esperam 2961 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ja->en**: não acompanha o falante: atraso típico 4.4 s, sobe -0.1 s da 1ª para a 2ª metade e sobram 3 s de tradução quando ele para
- **ko->en**: não acompanha o falante: atraso típico 6.2 s, sobe -0.7 s da 1ª para a 2ª metade e sobram 5 s de tradução quando ele para

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
