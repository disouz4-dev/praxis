_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `large-v3-turbo` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 9.1% palavras | 5.2% | 79.2 | 15.0 s | 20.4 s | +9.3 s | 20.8 s | 53% | ❌ |
| en->pt | 19s | 4.7% palavras | 5.3% | 57.1 | 22.9 s | 39.8 s | +18.9 s | 42.8 s | 74% | ❌ |
| es->en | 16s | 7.7% palavras | 6.7% | 64.7 | 13.8 s | 19.8 s | +9.7 s | 22.3 s | 41% | ❌ |
| fr->en | 19s | 2.5% palavras | 0.6% | 75.5 | 13.3 s | 17.3 s | +6.8 s | 10.4 s | 36% | ❌ |
| de->en | 19s | 16.7% palavras | 5.1% | 47.5 | 15.2 s | 20.7 s | +8.3 s | 20.4 s | 38% | ❌ |
| it->en | 21s | 16.2% palavras | 4.2% | 57.5 | 9.5 s | 14.6 s | +4.8 s | 12.7 s | 49% | ❌ |
| ru->en | 22s | 4.8% palavras | 1.5% | 56.4 | 8.1 s | 8.9 s | +1.7 s | 2.2 s | 31% | ❌ |
| zh->en | 20s | 13.2% caracteres | 13.2% | 48.4 | 15.7 s | 25.7 s | +11.5 s | 27.0 s | 67% | ❌ |
| nl->en | 20s | 25.9% palavras | 13.2% | 68.4 | 10.0 s | 12.1 s | +2.3 s | 2.7 s | 29% | ❌ |
| pl->en | 21s | 2.7% palavras | 1.1% | 63.8 | 9.4 s | 12.4 s | +3.5 s | 13.2 s | 59% | ❌ |
| uk->en | 20s | 4.2% palavras | 2.0% | 59.8 | 14.5 s | 21.7 s | +7.5 s | 21.4 s | 50% | ❌ |
| tr->en | 19s | 19.1% palavras | 9.6% | 55.2 | 8.8 s | 10.8 s | +2.2 s | 4.2 s | 24% | ❌ |
| ar->en | 20s | 17.2% palavras | 4.2% | 64.4 | 16.4 s | 21.0 s | +8.8 s | 19.0 s | 40% | ❌ |
| hi->en | 20s | 51.7% palavras | 19.2% | 27.8 | 13.4 s | 19.0 s | +7.2 s | 17.5 s | 40% | ❌ |
| ja->en | 19s | 0.0% caracteres | 0.0% | 71.0 | 8.8 s | 10.7 s | +4.1 s | 4.3 s | 37% | ❌ |
| ko->en | 17s | 4.0% caracteres | 4.0% | 56.6 | 9.8 s | 11.9 s | +2.3 s | 5.4 s | 30% | ❌ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 10368 ms | 5849 ms | 15 ms | 42 ms | 0 ms |
| en->pt | 21723 ms | 5903 ms | 11 ms | 31 ms | 0 ms |
| es->en | 11460 ms | 5943 ms | 15 ms | 28 ms | 0 ms |
| fr->en | 8697 ms | 5990 ms | 18 ms | 45 ms | 0 ms |
| de->en | 10017 ms | 5972 ms | 16 ms | 31 ms | 0 ms |
| it->en | 4105 ms | 6032 ms | 15 ms | 48 ms | 0 ms |
| ru->en | 2486 ms | 6063 ms | 22 ms | 49 ms | 0 ms |
| zh->en | 11110 ms | 6029 ms | 14 ms | 40 ms | 0 ms |
| nl->en | 1963 ms | 6063 ms | 19 ms | 42 ms | 0 ms |
| pl->en | 3646 ms | 6072 ms | 25 ms | 49 ms | 0 ms |
| uk->en | 8080 ms | 5954 ms | 14 ms | 34 ms | 0 ms |
| tr->en | 4401 ms | 6115 ms | 16 ms | 48 ms | 0 ms |
| ar->en | 11262 ms | 6028 ms | 12 ms | 32 ms | 0 ms |
| hi->en | 7726 ms | 6140 ms | 14 ms | 24 ms | 0 ms |
| ja->en | 4493 ms | 6053 ms | 23 ms | 48 ms | 0 ms |
| ko->en | 2936 ms | 6039 ms | 22 ms | 56 ms | 0 ms |

### Problemas encontrados

- **pt->en**: não acompanha o falante: atraso típico 15.0 s, sobe +9.3 s da 1ª para a 2ª metade e sobram 21 s de tradução quando ele para; trechos esperam 10368 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **en->pt**: não acompanha o falante: atraso típico 22.9 s, sobe +18.9 s da 1ª para a 2ª metade e sobram 43 s de tradução quando ele para; trechos esperam 21723 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **es->en**: não acompanha o falante: atraso típico 13.8 s, sobe +9.7 s da 1ª para a 2ª metade e sobram 22 s de tradução quando ele para; trechos esperam 11460 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **fr->en**: não acompanha o falante: atraso típico 13.3 s, sobe +6.8 s da 1ª para a 2ª metade e sobram 10 s de tradução quando ele para; trechos esperam 8697 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **de->en**: não acompanha o falante: atraso típico 15.2 s, sobe +8.3 s da 1ª para a 2ª metade e sobram 20 s de tradução quando ele para; trechos esperam 10017 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **it->en**: não acompanha o falante: atraso típico 9.5 s, sobe +4.8 s da 1ª para a 2ª metade e sobram 13 s de tradução quando ele para; trechos esperam 4105 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ru->en**: não acompanha o falante: atraso típico 8.1 s, sobe +1.7 s da 1ª para a 2ª metade e sobram 2 s de tradução quando ele para; trechos esperam 2486 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **zh->en**: pulou 1 trecho(s) inteiro(s) da fala (maior: 6 caracteres seguidas); não acompanha o falante: atraso típico 15.7 s, sobe +11.5 s da 1ª para a 2ª metade e sobram 27 s de tradução quando ele para; trechos esperam 11110 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **nl->en**: transcrição ruim: 26% das palavras erradas; não acompanha o falante: atraso típico 10.0 s, sobe +2.3 s da 1ª para a 2ª metade e sobram 3 s de tradução quando ele para; trechos esperam 1963 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **pl->en**: não acompanha o falante: atraso típico 9.4 s, sobe +3.5 s da 1ª para a 2ª metade e sobram 13 s de tradução quando ele para; trechos esperam 3646 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **uk->en**: não acompanha o falante: atraso típico 14.5 s, sobe +7.5 s da 1ª para a 2ª metade e sobram 21 s de tradução quando ele para; trechos esperam 8080 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **tr->en**: não acompanha o falante: atraso típico 8.8 s, sobe +2.2 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para; trechos esperam 4401 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ar->en**: não acompanha o falante: atraso típico 16.4 s, sobe +8.8 s da 1ª para a 2ª metade e sobram 19 s de tradução quando ele para; trechos esperam 11262 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **hi->en**: transcrição ruim: 52% das palavras erradas; não acompanha o falante: atraso típico 13.4 s, sobe +7.2 s da 1ª para a 2ª metade e sobram 18 s de tradução quando ele para; trechos esperam 7726 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ja->en**: não acompanha o falante: atraso típico 8.8 s, sobe +4.1 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para; trechos esperam 4493 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ko->en**: não acompanha o falante: atraso típico 9.8 s, sobe +2.3 s da 1ª para a 2ª metade e sobram 5 s de tradução quando ele para; trechos esperam 2936 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
