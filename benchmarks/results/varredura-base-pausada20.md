_Máquina: macOS-26.6.2-x86_64-i386-64bit · processador i386 · Python 3.12.15 · placa de vídeo CUDA: não_

Whisper `small` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 9.1% palavras | 1.5% | 65.9 | 2.9 s | 3.9 s | +0.1 s | 3.8 s | 56% | ✅ |
| en->pt | 19s | 9.3% palavras | 4.8% | 53.2 | 4.2 s | 5.8 s | +2.4 s | 5.6 s | 73% | ❌ |
| es->en | 16s | 11.5% palavras | 4.8% | 73.3 | 2.6 s | 3.4 s | -0.1 s | 3.4 s | 50% | ✅ |
| fr->en | 19s | 15.0% palavras | 9.8% | 61.3 | 3.4 s | 4.6 s | -0.8 s | 5.8 s | 56% | ✅ |
| de->en | 19s | 37.5% palavras | 13.9% | 38.8 | 2.6 s | 2.8 s | +0.2 s | 3.2 s | 42% | ✅ |
| it->en | 21s | 35.1% palavras | 8.3% | 44.6 | 2.7 s | 2.9 s | -0.1 s | 3.5 s | 60% | ✅ |
| ru->en | 22s | 19.1% palavras | 6.0% | 52.9 | 3.8 s | 3.9 s | +0.0 s | 0.2 s | 39% | ✅ |
| zh->en | 20s | 19.3% caracteres | 19.3% | 42.8 | 2.9 s | 4.4 s | +0.2 s | 4.8 s | 67% | ✅ |
| nl->en | 20s | 44.4% palavras | 19.3% | 58.1 | 2.5 s | 2.8 s | +0.4 s | 6.3 s | 44% | ✅ |
| pl->en | 21s | 21.6% palavras | 6.5% | 48.6 | 3.6 s | 4.6 s | -1.3 s | 4.6 s | 67% | ✅ |
| uk->en | 20s | 25.0% palavras | 7.4% | 37.5 | 3.1 s | 4.0 s | -0.1 s | 3.4 s | 46% | ✅ |
| tr->en | 19s | 23.8% palavras | 10.6% | 57.2 | 2.8 s | 4.5 s | +0.0 s | 0.4 s | 36% | ✅ |
| ar->en | 20s | 24.1% palavras | 7.6% | 67.1 | 3.4 s | 4.9 s | -1.7 s | 2.7 s | 47% | ✅ |
| hi->en | 20s | 55.2% palavras | 29.2% | 24.8 | 3.2 s | 4.4 s | +0.8 s | 3.6 s | 48% | ✅ |
| ja->en | 19s | 17.4% caracteres | 17.4% | 52.6 | 3.6 s | 4.0 s | +0.9 s | 0.0 s | 38% | ✅ |
| ko->en | 17s | 12.0% caracteres | 12.0% | 53.6 | 4.1 s | 6.4 s | -1.2 s | 2.6 s | 50% | ❌ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 1 ms | 2121 ms | 74 ms | 89 ms | 1 ms |
| en->pt | 2757 ms | 2034 ms | 43 ms | 84 ms | 1 ms |
| es->en | 172 ms | 2045 ms | 125 ms | 68 ms | 0 ms |
| fr->en | 0 ms | 2141 ms | 95 ms | 130 ms | 1 ms |
| de->en | 0 ms | 2073 ms | 66 ms | 71 ms | 0 ms |
| it->en | 1 ms | 2213 ms | 60 ms | 101 ms | 0 ms |
| ru->en | 0 ms | 2211 ms | 110 ms | 118 ms | 1 ms |
| zh->en | 140 ms | 2168 ms | 63 ms | 96 ms | 1 ms |
| nl->en | 0 ms | 2169 ms | 77 ms | 106 ms | 0 ms |
| pl->en | 0 ms | 2219 ms | 111 ms | 140 ms | 1 ms |
| uk->en | 382 ms | 2089 ms | 60 ms | 76 ms | 1 ms |
| tr->en | 0 ms | 2127 ms | 65 ms | 123 ms | 1 ms |
| ar->en | 525 ms | 2081 ms | 40 ms | 74 ms | 1 ms |
| hi->en | 113 ms | 2347 ms | 59 ms | 81 ms | 0 ms |
| ja->en | 937 ms | 2182 ms | 71 ms | 85 ms | 73 ms |
| ko->en | 0 ms | 2187 ms | 100 ms | 141 ms | 0 ms |

### Problemas encontrados

- **pt->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.9 s
- **en->pt**: não acompanha o falante: atraso típico 4.2 s, sobe +2.4 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para; trechos esperam 2757 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala)
- **es->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.4 s
- **fr->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.6 s
- **de->en**: transcrição ruim: 38% das palavras erradas
- **it->en**: transcrição ruim: 35% das palavras erradas
- **ru->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.9 s
- **zh->en**: pulou 1 trecho(s) inteiro(s) da fala (maior: 6 caracteres seguidas); picos de atraso: 1 em cada 20 trechos demora mais de 4.4 s
- **nl->en**: transcrição ruim: 44% das palavras erradas
- **pl->en**: transcrição ruim: 22% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.6 s
- **uk->en**: transcrição ruim: 25% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **tr->en**: transcrição ruim: 24% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.5 s
- **ar->en**: transcrição ruim: 24% das palavras erradas; trechos esperam 525 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); picos de atraso: 1 em cada 20 trechos demora mais de 4.9 s
- **hi->en**: transcrição ruim: 55% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.4 s
- **ja->en**: trechos esperam 937 ms na fila antes de serem transcritos (a transcrição é mais lenta que a fala); picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **ko->en**: não acompanha o falante: atraso típico 4.1 s, sobe -1.2 s da 1ª para a 2ª metade e sobram 3 s de tradução quando ele para

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
