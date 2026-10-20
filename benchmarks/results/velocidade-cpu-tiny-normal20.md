_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `tiny` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 44.2% palavras | 12.1% | 65.2 | 1.4 s | 3.7 s | -0.9 s | 3.4 s | 76% | ✅ |
| en->pt | 20s | 7.4% palavras | 5.1% | 70.8 | 1.3 s | 1.7 s | +0.5 s | 4.6 s | 80% | ✅ |
| es->en | 21s | 6.7% palavras | 1.6% | 55.1 | 0.8 s | 1.5 s | +0.2 s | 1.8 s | 54% | ✅ |
| fr->en | 21s | 57.1% palavras | 28.3% | 50.5 | 2.1 s | 3.4 s | +0.2 s | 5.0 s | 79% | ✅ |
| de->en | 19s | 52.9% palavras | 17.4% | 49.8 | 1.3 s | 2.7 s | -0.7 s | 4.2 s | 62% | ✅ |
| it->en | 20s | 61.7% palavras | 13.3% | 38.4 | 1.1 s | 3.0 s | -1.6 s | 4.7 s | 70% | ✅ |
| ru->en | 19s | 26.9% palavras | 4.1% | 72.9 | 1.4 s | 3.5 s | +0.6 s | 3.1 s | 56% | ✅ |
| zh->en | 19s | 22.7% caracteres | 22.7% | 42.8 | 1.4 s | 2.8 s | -0.5 s | 0.0 s | 41% | ✅ |
| nl->en | 22s | 60.4% palavras | 22.0% | 37.0 | 1.5 s | 2.2 s | +1.2 s | 3.5 s | 64% | ✅ |
| pl->en | 18s | 53.8% palavras | 7.1% | 46.5 | 0.7 s | 1.1 s | +0.3 s | 3.1 s | 72% | ✅ |
| uk->en | 19s | 58.8% palavras | 20.7% | 44.6 | 1.5 s | 3.7 s | -2.2 s | 2.0 s | 73% | ✅ |
| tr->en | 17s | 41.7% palavras | 5.5% | 55.7 | 0.7 s | 1.1 s | -0.5 s | 0.0 s | 45% | ✅ |
| ar->en | 19s | 60.0% palavras | 19.0% | 40.2 | 1.5 s | 3.0 s | -0.2 s | 3.0 s | 66% | ✅ |
| hi->en | 20s | 109.8% palavras | 109.6% | 18.3 | 0.7 s | 1.1 s | -0.0 s | 1.9 s | 58% | ✅ |
| ja->en | 25s | 28.4% caracteres | 28.4% | 52.6 | 1.6 s | 4.8 s | -2.5 s | 2.0 s | 57% | ✅ |
| ko->en | 20s | 47.3% caracteres | 47.3% | 23.5 | 1.0 s | 1.0 s | +0.0 s | 2.8 s | 22% | ❌ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 258 ms | 27 ms | 75 ms | 618 ms |
| en->pt | 0 ms | 254 ms | 30 ms | 79 ms | 68 ms |
| es->en | 0 ms | 252 ms | 28 ms | 41 ms | 0 ms |
| fr->en | 0 ms | 269 ms | 37 ms | 52 ms | 1179 ms |
| de->en | 0 ms | 259 ms | 34 ms | 48 ms | 0 ms |
| it->en | 0 ms | 271 ms | 25 ms | 43 ms | 186 ms |
| ru->en | 0 ms | 274 ms | 31 ms | 67 ms | 3 ms |
| zh->en | 0 ms | 227 ms | 18 ms | 33 ms | 0 ms |
| nl->en | 0 ms | 237 ms | 24 ms | 28 ms | 1 ms |
| pl->en | 0 ms | 287 ms | 44 ms | 74 ms | 0 ms |
| uk->en | 0 ms | 275 ms | 28 ms | 60 ms | 385 ms |
| tr->en | 0 ms | 276 ms | 22 ms | 41 ms | 0 ms |
| ar->en | 0 ms | 291 ms | 36 ms | 77 ms | 0 ms |
| hi->en | 0 ms | 211 ms | 18 ms | 33 ms | 112 ms |
| ja->en | 0 ms | 292 ms | 48 ms | 99 ms | 0 ms |
| ko->en | 0 ms | 693 ms | 29 ms | 92 ms | 0 ms |

### Problemas encontrados

- **pt->en**: transcrição ruim: 44% das palavras erradas; inventou 6 palavras que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **en->pt**: nenhum problema detectado
- **es->en**: nenhum problema detectado
- **fr->en**: transcrição ruim: 57% das palavras erradas; inventou 7 palavras que não foram faladas; a tradução pronta espera 1179 ms a fala anterior terminar de tocar; picos de atraso: 1 em cada 20 trechos demora mais de 3.4 s
- **de->en**: transcrição ruim: 53% das palavras erradas
- **it->en**: transcrição ruim: 62% das palavras erradas; inventou 4 palavras que não foram faladas
- **ru->en**: transcrição ruim: 27% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.5 s
- **zh->en**: transcrição ruim: 23% dos caracteres erradas
- **nl->en**: transcrição ruim: 60% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **pl->en**: transcrição ruim: 54% das palavras erradas; inventou 4 palavras que não foram faladas
- **uk->en**: transcrição ruim: 59% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **tr->en**: transcrição ruim: 42% das palavras erradas
- **ar->en**: transcrição ruim: 60% das palavras erradas
- **hi->en**: transcrição ruim: 110% das palavras erradas; inventou 4 palavras que não foram faladas
- **ja->en**: transcrição ruim: 28% dos caracteres erradas; inventou 8 caracteres que não foram faladas; picos de atraso: 1 em cada 20 trechos demora mais de 4.8 s
- **ko->en**: transcrição ruim: 47% dos caracteres erradas; pulou 2 trecho(s) inteiro(s) da fala (maior: 21 caracteres seguidas); não acompanha o falante: atraso típico 1.0 s, sobe +0.0 s da 1ª para a 2ª metade e sobram 3 s de tradução quando ele para; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
