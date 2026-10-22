_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `large-v3-turbo` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 71s | 4.8% palavras | 1.6% | 77.5 | 25.7 s | 32.9 s | +12.3 s | 31.6 s | 65% | ❌ |
| en->pt | 72s | 2.1% palavras | 1.9% | 74.2 | 8.5 s | 11.1 s | +2.5 s | 10.6 s | 77% | ❌ |
| es->en | 73s | 2.6% palavras | 0.8% | 69.1 | 17.1 s | 31.8 s | +20.0 s | 31.0 s | 56% | ❌ |
| fr->en | 62s | 8.2% palavras | 5.7% | 68.6 | 14.6 s | 22.0 s | +6.4 s | 19.1 s | 66% | ❌ |
| de->en | 63s | 14.1% palavras | 4.2% | 65.5 | 18.8 s | 33.0 s | +15.8 s | 34.0 s | 55% | ❌ |
| it->en | 78s | 14.1% palavras | 4.8% | 62.8 | 18.9 s | 31.8 s | +10.9 s | 30.6 s | 64% | ❌ |
| ru->en | 66s | 5.7% palavras | 3.1% | 75.7 | 7.9 s | 10.8 s | +0.2 s | 9.4 s | 54% | ❌ |
| zh->en | 62s | 5.6% caracteres | 5.6% | 38.5 | 8.8 s | 11.8 s | -0.8 s | 2.6 s | 44% | ❌ |
| nl->en | 66s | 11.6% palavras | 3.4% | 63.4 | 11.3 s | 13.9 s | +4.3 s | 16.1 s | 61% | ❌ |
| pl->en | 69s | 2.5% palavras | 0.4% | 66.7 | 18.1 s | 26.5 s | +7.8 s | 27.4 s | 77% | ❌ |
| uk->en | 69s | 10.7% palavras | 4.5% | 71.6 | 15.1 s | 25.0 s | +14.1 s | 26.5 s | 59% | ❌ |
| tr->en | 72s | 11.3% palavras | 3.3% | 67.1 | 7.4 s | 11.1 s | +0.7 s | 8.2 s | 45% | ❌ |
| ar->en | 74s | 11.7% palavras | 4.6% | 68.7 | 11.2 s | 13.2 s | +1.8 s | 13.1 s | 62% | ❌ |
| hi->en | 69s | 31.5% palavras | 15.6% | 49.7 | 24.7 s | 44.0 s | +21.7 s | 42.0 s | 55% | ❌ |
| ja->en | 64s | 10.0% caracteres | 10.0% | 58.3 | 6.8 s | 9.9 s | -1.2 s | 7.5 s | 57% | ❌ |
| ko->en | 69s | 7.1% caracteres | 7.1% | 60.8 | 7.1 s | 9.6 s | +0.7 s | 9.0 s | 64% | ❌ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 19601 ms | 5510 ms | 24 ms | 65 ms | 0 ms |
| en->pt | 2951 ms | 5186 ms | 30 ms | 78 ms | 0 ms |
| es->en | 12993 ms | 5112 ms | 26 ms | 44 ms | 0 ms |
| fr->en | 8619 ms | 5242 ms | 25 ms | 60 ms | 0 ms |
| de->en | 14334 ms | 5152 ms | 19 ms | 29 ms | 0 ms |
| it->en | 12999 ms | 5262 ms | 22 ms | 61 ms | 0 ms |
| ru->en | 2187 ms | 5299 ms | 28 ms | 68 ms | 0 ms |
| zh->en | 2845 ms | 5266 ms | 24 ms | 52 ms | 0 ms |
| nl->en | 5708 ms | 5294 ms | 30 ms | 66 ms | 0 ms |
| pl->en | 12703 ms | 5280 ms | 31 ms | 71 ms | 0 ms |
| uk->en | 9517 ms | 5325 ms | 23 ms | 60 ms | 0 ms |
| tr->en | 2196 ms | 5269 ms | 21 ms | 63 ms | 0 ms |
| ar->en | 5103 ms | 5403 ms | 25 ms | 79 ms | 0 ms |
| hi->en | 20935 ms | 5435 ms | 19 ms | 37 ms | 0 ms |
| ja->en | 0 ms | 5397 ms | 37 ms | 100 ms | 0 ms |
| ko->en | 0 ms | 5331 ms | 28 ms | 83 ms | 0 ms |

### Problemas encontrados

- **pt->en**: não acompanha o falante: atraso típico 25.7 s, sobe +12.3 s da 1ª para a 2ª metade e sobram 32 s de tradução quando ele para; trechos esperam 19601 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **en->pt**: não acompanha o falante: atraso típico 8.5 s, sobe +2.5 s da 1ª para a 2ª metade e sobram 11 s de tradução quando ele para; trechos esperam 2951 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **es->en**: não acompanha o falante: atraso típico 17.1 s, sobe +20.0 s da 1ª para a 2ª metade e sobram 31 s de tradução quando ele para; trechos esperam 12993 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **fr->en**: não acompanha o falante: atraso típico 14.6 s, sobe +6.4 s da 1ª para a 2ª metade e sobram 19 s de tradução quando ele para; trechos esperam 8619 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **de->en**: não acompanha o falante: atraso típico 18.8 s, sobe +15.8 s da 1ª para a 2ª metade e sobram 34 s de tradução quando ele para; trechos esperam 14334 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **it->en**: não acompanha o falante: atraso típico 18.9 s, sobe +10.9 s da 1ª para a 2ª metade e sobram 31 s de tradução quando ele para; trechos esperam 12999 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **ru->en**: não acompanha o falante: atraso típico 7.9 s, sobe +0.2 s da 1ª para a 2ª metade e sobram 9 s de tradução quando ele para; trechos esperam 2187 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **zh->en**: não acompanha o falante: atraso típico 8.8 s, sobe -0.8 s da 1ª para a 2ª metade e sobram 3 s de tradução quando ele para; trechos esperam 2845 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **nl->en**: não acompanha o falante: atraso típico 11.3 s, sobe +4.3 s da 1ª para a 2ª metade e sobram 16 s de tradução quando ele para; trechos esperam 5708 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 2 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **pl->en**: não acompanha o falante: atraso típico 18.1 s, sobe +7.8 s da 1ª para a 2ª metade e sobram 27 s de tradução quando ele para; trechos esperam 12703 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **uk->en**: não acompanha o falante: atraso típico 15.1 s, sobe +14.1 s da 1ª para a 2ª metade e sobram 26 s de tradução quando ele para; trechos esperam 9517 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **tr->en**: não acompanha o falante: atraso típico 7.4 s, sobe +0.7 s da 1ª para a 2ª metade e sobram 8 s de tradução quando ele para; trechos esperam 2196 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ar->en**: não acompanha o falante: atraso típico 11.2 s, sobe +1.8 s da 1ª para a 2ª metade e sobram 13 s de tradução quando ele para; trechos esperam 5103 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **hi->en**: transcrição ruim: 32% das palavras erradas; não acompanha o falante: atraso típico 24.7 s, sobe +21.7 s da 1ª para a 2ª metade e sobram 42 s de tradução quando ele para; trechos esperam 20935 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ja->en**: não acompanha o falante: atraso típico 6.8 s, sobe -1.2 s da 1ª para a 2ª metade e sobram 8 s de tradução quando ele para
- **ko->en**: não acompanha o falante: atraso típico 7.1 s, sobe +0.7 s da 1ª para a 2ª metade e sobram 9 s de tradução quando ele para; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
