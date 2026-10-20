_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `large-v3-turbo` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 12.1% palavras | 2.2% | 69.0 | 6.0 s | 6.3 s | +0.4 s | 5.7 s | 44% | ❌ |
| en->pt | 19s | 0.0% palavras | 0.0% | 83.7 | 6.5 s | 7.0 s | +1.2 s | 7.0 s | 58% | ❌ |
| es->en | 16s | 3.9% palavras | 1.0% | 81.6 | 8.8 s | 11.4 s | +5.8 s | 8.1 s | 29% | ❌ |
| fr->en | 19s | 0.0% palavras | 0.0% | 71.2 | 8.3 s | 9.6 s | +2.8 s | 3.3 s | 31% | ❌ |
| de->en | 19s | 20.8% palavras | 6.6% | 49.2 | 9.4 s | 11.3 s | +4.2 s | 12.5 s | 37% | ❌ |
| it->en | 21s | 24.3% palavras | 4.8% | 51.3 | 7.3 s | 11.4 s | +3.2 s | 8.9 s | 51% | ❌ |
| ru->en | 22s | 4.8% palavras | 1.5% | 49.9 | 10.5 s | 10.6 s | +2.0 s | 4.8 s | 30% | ❌ |
| zh->en | 20s | 15.7% caracteres | 15.7% | 52.6 | 6.7 s | 8.9 s | +0.8 s | 9.2 s | 68% | ❌ |
| nl->en | 20s | 22.2% palavras | 14.0% | 62.4 | 6.6 s | 8.3 s | +0.5 s | 8.6 s | 45% | ❌ |
| pl->en | 21s | 8.1% palavras | 2.7% | 56.4 | 11.3 s | 13.2 s | +4.5 s | 10.4 s | 51% | ❌ |
| uk->en | 20s | 8.3% palavras | 2.0% | 64.6 | 7.8 s | 9.0 s | +1.3 s | 5.9 s | 38% | ❌ |
| tr->en | 19s | 19.1% palavras | 9.6% | 39.7 | 7.7 s | 8.5 s | +1.9 s | 2.9 s | 22% | ❌ |
| ar->en | 20s | 13.8% palavras | 13.5% | 74.3 | 9.4 s | 9.9 s | +2.3 s | 7.5 s | 39% | ❌ |
| hi->en | 20s | 58.6% palavras | 21.7% | 26.3 | 13.1 s | 17.9 s | +7.0 s | 17.0 s | 38% | ❌ |
| ja->en | 19s | 50.0% caracteres | 50.0% | 37.5 | 6.1 s | 6.2 s | +0.1 s | 2.7 s | 24% | ❌ |
| ko->en | 17s | 6.0% caracteres | 6.0% | 58.3 | 9.3 s | 10.8 s | +1.7 s | 4.2 s | 32% | ❌ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 17 ms | 5545 ms | 23 ms | 50 ms | 0 ms |
| en->pt | 249 ms | 5169 ms | 26 ms | 75 ms | 0 ms |
| es->en | 5110 ms | 5212 ms | 21 ms | 38 ms | 0 ms |
| fr->en | 2434 ms | 5171 ms | 21 ms | 52 ms | 0 ms |
| de->en | 4320 ms | 5238 ms | 16 ms | 26 ms | 0 ms |
| it->en | 2454 ms | 5212 ms | 18 ms | 41 ms | 0 ms |
| ru->en | 4452 ms | 5265 ms | 19 ms | 55 ms | 0 ms |
| zh->en | 309 ms | 5381 ms | 25 ms | 93 ms | 0 ms |
| nl->en | 2170 ms | 5220 ms | 19 ms | 43 ms | 0 ms |
| pl->en | 6524 ms | 5334 ms | 27 ms | 59 ms | 0 ms |
| uk->en | 1790 ms | 5324 ms | 21 ms | 44 ms | 0 ms |
| tr->en | 2775 ms | 5298 ms | 17 ms | 40 ms | 0 ms |
| ar->en | 3275 ms | 5353 ms | 18 ms | 55 ms | 0 ms |
| hi->en | 9154 ms | 5337 ms | 12 ms | 27 ms | 0 ms |
| ja->en | 324 ms | 5259 ms | 22 ms | 54 ms | 0 ms |
| ko->en | 1946 ms | 5220 ms | 22 ms | 60 ms | 0 ms |

### Problemas encontrados

- **pt->en**: não acompanha o falante: atraso típico 6.0 s, sobe +0.4 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para
- **en->pt**: não acompanha o falante: atraso típico 6.5 s, sobe +1.2 s da 1ª para a 2ª metade e sobram 7 s de tradução quando ele para
- **es->en**: não acompanha o falante: atraso típico 8.8 s, sobe +5.8 s da 1ª para a 2ª metade e sobram 8 s de tradução quando ele para; trechos esperam 5110 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **fr->en**: não acompanha o falante: atraso típico 8.3 s, sobe +2.8 s da 1ª para a 2ª metade e sobram 3 s de tradução quando ele para; trechos esperam 2434 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **de->en**: transcrição ruim: 21% das palavras erradas; não acompanha o falante: atraso típico 9.4 s, sobe +4.2 s da 1ª para a 2ª metade e sobram 12 s de tradução quando ele para; trechos esperam 4320 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **it->en**: transcrição ruim: 24% das palavras erradas; não acompanha o falante: atraso típico 7.3 s, sobe +3.2 s da 1ª para a 2ª metade e sobram 9 s de tradução quando ele para; trechos esperam 2454 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ru->en**: não acompanha o falante: atraso típico 10.5 s, sobe +2.0 s da 1ª para a 2ª metade e sobram 5 s de tradução quando ele para; trechos esperam 4452 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **zh->en**: não acompanha o falante: atraso típico 6.7 s, sobe +0.8 s da 1ª para a 2ª metade e sobram 9 s de tradução quando ele para
- **nl->en**: transcrição ruim: 22% das palavras erradas; não acompanha o falante: atraso típico 6.6 s, sobe +0.5 s da 1ª para a 2ª metade e sobram 9 s de tradução quando ele para; trechos esperam 2170 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **pl->en**: não acompanha o falante: atraso típico 11.3 s, sobe +4.5 s da 1ª para a 2ª metade e sobram 10 s de tradução quando ele para; trechos esperam 6524 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **uk->en**: não acompanha o falante: atraso típico 7.8 s, sobe +1.3 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para; trechos esperam 1790 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **tr->en**: não acompanha o falante: atraso típico 7.7 s, sobe +1.9 s da 1ª para a 2ª metade e sobram 3 s de tradução quando ele para; trechos esperam 2775 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ar->en**: não acompanha o falante: atraso típico 9.4 s, sobe +2.3 s da 1ª para a 2ª metade e sobram 8 s de tradução quando ele para; trechos esperam 3275 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **hi->en**: transcrição ruim: 59% das palavras erradas; não acompanha o falante: atraso típico 13.1 s, sobe +7.0 s da 1ª para a 2ª metade e sobram 17 s de tradução quando ele para; trechos esperam 9154 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ja->en**: transcrição ruim: 50% dos caracteres erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 19 caracteres seguidas); não acompanha o falante: atraso típico 6.1 s, sobe +0.1 s da 1ª para a 2ª metade e sobram 3 s de tradução quando ele para
- **ko->en**: não acompanha o falante: atraso típico 9.3 s, sobe +1.7 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para; trechos esperam 1946 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
