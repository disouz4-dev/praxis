_Máquina: macOS-26.6.2-x86_64-i386-64bit · processador i386 · Python 3.12.15 · placa de vídeo CUDA: não_

Whisper `small` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 48.8% palavras | 47.5% | 43.8 | 3.9 s | 3.9 s | +0.0 s | 3.8 s | 36% | ❌ |
| en->pt | 20s | 38.9% palavras | 37.1% | 50.5 | 4.1 s | 4.1 s | +0.0 s | 5.0 s | 51% | ❌ |
| es->en | 21s | 51.1% palavras | 36.4% | 35.0 | 3.1 s | 3.1 s | +0.0 s | 3.0 s | 39% | ❌ |
| fr->en | 21s | 58.9% palavras | 45.0% | 41.8 | 4.4 s | 4.4 s | +0.0 s | 4.0 s | 49% | ❌ |
| de->en | 19s | 50.0% palavras | 36.4% | 42.5 | 6.1 s | 6.3 s | +0.0 s | 4.0 s | 42% | ❌ |
| it->en | 20s | 61.7% palavras | 43.6% | 36.6 | 4.9 s | 5.4 s | +0.6 s | 4.4 s | 46% | ❌ |
| ru->en | 19s | 46.2% palavras | 39.3% | 54.8 | 3.9 s | 3.9 s | +0.0 s | 0.0 s | 35% | ❌ |
| zh->en | 19s | 34.1% caracteres | 34.1% | 39.5 | 4.9 s | 5.0 s | +1.5 s | 4.9 s | 39% | ❌ |
| nl->en | 22s | 41.7% palavras | 30.0% | 39.8 | 4.3 s | 5.1 s | +1.8 s | 6.1 s | 51% | ❌ |
| pl->en | 18s | 48.7% palavras | 40.3% | 38.9 | 3.1 s | 3.1 s | +0.0 s | 6.4 s | 48% | ❌ |
| uk->en | 19s | 61.8% palavras | 47.9% | 38.2 | 6.7 s | 7.9 s | +1.3 s | 0.0 s | 38% | ❌ |
| tr->en | 17s | 33.3% palavras | 20.9% | 57.9 | 4.0 s | 4.0 s | +0.0 s | 4.0 s | 29% | ❌ |
| ar->en | 19s | 56.7% palavras | 37.3% | 38.1 | 4.8 s | 4.8 s | +0.0 s | 3.1 s | 40% | ❌ |
| hi->en | 20s | 73.2% palavras | 52.0% | 25.9 | 4.8 s | 5.2 s | +1.0 s | 8.0 s | 39% | ❌ |
| ja->en | 25s | 30.7% caracteres | 30.7% | 34.2 | 4.5 s | 4.5 s | -0.0 s | 3.5 s | 36% | ❌ |
| ko->en | 20s | 47.3% caracteres | 47.3% | 21.5 | 4.9 s | 5.1 s | +0.2 s | 0.0 s | 33% | ❌ |

### Eco (a tradução tocada volta pelo microfone)

| Par | Trechos traduzidos depois que o falante parou | Palavras nesses trechos |
|---|---:|---:|
| pt->en | 0 | 0 |
| en->pt | 0 | 0 |
| es->en | 0 | 0 |
| fr->en | 0 | 0 |
| de->en | 0 | 0 |
| it->en | 0 | 0 |
| ru->en | 0 | 0 |
| zh->en | 0 | 0 |
| nl->en | 0 | 0 |
| pl->en | 0 | 0 |
| uk->en | 0 | 0 |
| tr->en | 0 | 0 |
| ar->en | 0 | 0 |
| hi->en | 0 | 0 |
| ja->en | 0 | 0 |
| ko->en | 0 | 0 |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 1 ms | 2603 ms | 85 ms | 112 ms | 0 ms |
| en->pt | 0 ms | 2742 ms | 125 ms | 131 ms | 2 ms |
| es->en | 1 ms | 2497 ms | 143 ms | 81 ms | 0 ms |
| fr->en | 0 ms | 2918 ms | 169 ms | 147 ms | 2 ms |
| de->en | 0 ms | 2683 ms | 126 ms | 105 ms | 1 ms |
| it->en | 730 ms | 2729 ms | 91 ms | 153 ms | 263 ms |
| ru->en | 0 ms | 2861 ms | 161 ms | 213 ms | 284 ms |
| zh->en | 0 ms | 2566 ms | 103 ms | 103 ms | 0 ms |
| nl->en | 0 ms | 2873 ms | 138 ms | 158 ms | 154 ms |
| pl->en | 0 ms | 2727 ms | 129 ms | 146 ms | 1 ms |
| uk->en | 1255 ms | 2576 ms | 144 ms | 153 ms | 727 ms |
| tr->en | 0 ms | 5211 ms | 112 ms | 157 ms | 0 ms |
| ar->en | 0 ms | 3127 ms | 171 ms | 169 ms | 2 ms |
| hi->en | 1474 ms | 2904 ms | 78 ms | 127 ms | 1 ms |
| ja->en | 1 ms | 2896 ms | 161 ms | 207 ms | 0 ms |
| ko->en | 0 ms | 2667 ms | 299 ms | 206 ms | 1 ms |

### Problemas encontrados

- **pt->en**: transcrição ruim: 49% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 16 palavras seguidas); não acompanha o falante: atraso típico 3.9 s, sobe +0.0 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para; 2 trecho(s) com fala viraram texto vazio
- **en->pt**: transcrição ruim: 39% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 21 palavras seguidas); não acompanha o falante: atraso típico 4.1 s, sobe +0.0 s da 1ª para a 2ª metade e sobram 5 s de tradução quando ele para
- **es->en**: transcrição ruim: 51% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 6 palavras seguidas); não acompanha o falante: atraso típico 3.1 s, sobe +0.0 s da 1ª para a 2ª metade e sobram 3 s de tradução quando ele para
- **fr->en**: transcrição ruim: 59% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 23 palavras seguidas); não acompanha o falante: atraso típico 4.4 s, sobe +0.0 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para
- **de->en**: transcrição ruim: 50% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 8 palavras seguidas); não acompanha o falante: atraso típico 6.1 s, sobe +0.0 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para
- **it->en**: transcrição ruim: 62% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 19 palavras seguidas); não acompanha o falante: atraso típico 4.9 s, sobe +0.6 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para; trechos esperam 730 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **ru->en**: transcrição ruim: 46% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 10 palavras seguidas); não acompanha o falante: atraso típico 3.9 s, sobe +0.0 s da 1ª para a 2ª metade e sobram 0 s de tradução quando ele para
- **zh->en**: transcrição ruim: 34% dos caracteres erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 8 caracteres seguidas); não acompanha o falante: atraso típico 4.9 s, sobe +1.5 s da 1ª para a 2ª metade e sobram 5 s de tradução quando ele para
- **nl->en**: transcrição ruim: 42% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 13 palavras seguidas); não acompanha o falante: atraso típico 4.3 s, sobe +1.8 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para
- **pl->en**: transcrição ruim: 49% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 12 palavras seguidas); não acompanha o falante: atraso típico 3.1 s, sobe +0.0 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para
- **uk->en**: transcrição ruim: 62% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 17 palavras seguidas); não acompanha o falante: atraso típico 6.7 s, sobe +1.3 s da 1ª para a 2ª metade e sobram 0 s de tradução quando ele para; trechos esperam 1255 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 1 trecho(s) com fala viraram texto vazio
- **tr->en**: transcrição ruim: 33% das palavras erradas; não acompanha o falante: atraso típico 4.0 s, sobe +0.0 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para
- **ar->en**: transcrição ruim: 57% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 10 palavras seguidas); não acompanha o falante: atraso típico 4.8 s, sobe +0.0 s da 1ª para a 2ª metade e sobram 3 s de tradução quando ele para
- **hi->en**: transcrição ruim: 73% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 16 palavras seguidas); não acompanha o falante: atraso típico 4.8 s, sobe +1.0 s da 1ª para a 2ª metade e sobram 8 s de tradução quando ele para; trechos esperam 1474 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); 2 trecho(s) com fala viraram texto vazio
- **ja->en**: transcrição ruim: 31% dos caracteres erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 9 caracteres seguidas); não acompanha o falante: atraso típico 4.5 s, sobe -0.0 s da 1ª para a 2ª metade e sobram 3 s de tradução quando ele para
- **ko->en**: transcrição ruim: 47% dos caracteres erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 33 caracteres seguidas); não acompanha o falante: atraso típico 4.9 s, sobe +0.2 s da 1ª para a 2ª metade e sobram 0 s de tradução quando ele para; 1 trecho(s) com fala viraram texto vazio

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
