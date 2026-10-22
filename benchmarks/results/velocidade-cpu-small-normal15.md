_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `small` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 14s | 12.1% palavras | 2.2% | 73.5 | 3.7 s | 4.6 s | -0.3 s | 5.4 s | 71% | ✅ |
| en->pt | 14s | 0.0% palavras | 0.0% | 75.8 | 2.6 s | 3.1 s | +0.8 s | 5.8 s | 87% | ✅ |
| es->en | 12s | 0.0% palavras | 0.0% | 85.4 | 1.9 s | 3.3 s | +0.2 s | 3.3 s | 58% | ✅ |
| fr->en | 14s | 7.5% palavras | 7.3% | 55.6 | 2.1 s | 3.4 s | +1.1 s | 4.2 s | 69% | ✅ |
| de->en | 14s | 20.8% palavras | 7.3% | 55.5 | 1.6 s | 1.8 s | +0.1 s | 4.0 s | 55% | ✅ |
| it->en | 16s | 24.3% palavras | 4.8% | 54.0 | 4.0 s | 5.5 s | +0.2 s | 5.9 s | 88% | ❌ |
| ru->en | 17s | 19.1% palavras | 6.0% | 53.4 | 2.6 s | 3.1 s | +0.2 s | 1.6 s | 52% | ✅ |
| zh->en | 15s | 16.9% caracteres | 16.9% | 48.2 | 2.7 s | 3.0 s | +0.3 s | 3.3 s | 67% | ✅ |
| nl->en | 15s | 29.6% palavras | 14.0% | 66.1 | 1.6 s | 1.7 s | +0.4 s | 5.0 s | 59% | ✅ |
| pl->en | 15s | 18.9% palavras | 2.7% | 60.1 | 2.1 s | 3.3 s | -0.2 s | 4.8 s | 80% | ✅ |
| uk->en | 15s | 8.3% palavras | 2.7% | 84.4 | 1.9 s | 1.9 s | +0.0 s | 4.1 s | 59% | ✅ |
| tr->en | 14s | 23.8% palavras | 10.6% | 66.0 | 2.4 s | 2.7 s | -0.3 s | 2.2 s | 45% | ✅ |
| ar->en | 15s | 17.2% palavras | 4.2% | 82.2 | 2.4 s | 4.0 s | +1.1 s | 3.9 s | 53% | ✅ |
| hi->en | 15s | 65.5% palavras | 33.3% | 21.9 | 2.0 s | 2.6 s | +0.6 s | 2.6 s | 57% | ✅ |
| ja->en | 14s | 19.6% caracteres | 19.6% | 44.9 | 3.5 s | 4.2 s | +0.8 s | 3.0 s | 45% | ✅ |
| ko->en | 12s | 14.0% caracteres | 14.0% | 44.4 | 3.9 s | 4.5 s | +1.3 s | 5.3 s | 68% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 162 ms | 1238 ms | 23 ms | 55 ms | 1250 ms |
| en->pt | 0 ms | 1271 ms | 29 ms | 67 ms | 1 ms |
| es->en | 0 ms | 1157 ms | 25 ms | 37 ms | 234 ms |
| fr->en | 0 ms | 1306 ms | 29 ms | 70 ms | 0 ms |
| de->en | 0 ms | 1237 ms | 21 ms | 36 ms | 0 ms |
| it->en | 0 ms | 1320 ms | 23 ms | 72 ms | 1539 ms |
| ru->en | 0 ms | 1302 ms | 26 ms | 50 ms | 0 ms |
| zh->en | 0 ms | 1520 ms | 31 ms | 87 ms | 0 ms |
| nl->en | 0 ms | 1376 ms | 32 ms | 74 ms | 0 ms |
| pl->en | 0 ms | 1328 ms | 29 ms | 71 ms | 175 ms |
| uk->en | 0 ms | 1466 ms | 32 ms | 94 ms | 0 ms |
| tr->en | 0 ms | 1350 ms | 27 ms | 70 ms | 207 ms |
| ar->en | 0 ms | 1454 ms | 26 ms | 75 ms | 0 ms |
| hi->en | 36 ms | 1366 ms | 14 ms | 32 ms | 95 ms |
| ja->en | 0 ms | 1385 ms | 29 ms | 68 ms | 1254 ms |
| ko->en | 0 ms | 1407 ms | 35 ms | 92 ms | 760 ms |

### Problemas encontrados

- **pt->en**: a tradução pronta espera 1250 ms a fala anterior terminar de tocar; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 4.6 s
- **en->pt**: picos de atraso: 1 em cada 20 trechos demora mais de 3.1 s
- **es->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.3 s
- **fr->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.4 s
- **de->en**: transcrição ruim: 21% das palavras erradas
- **it->en**: transcrição ruim: 24% das palavras erradas; não acompanha o falante: atraso típico 4.0 s, sobe +0.2 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para; a tradução pronta espera 1539 ms a fala anterior terminar de tocar
- **ru->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.1 s
- **zh->en**: nenhum problema detectado
- **nl->en**: transcrição ruim: 30% das palavras erradas
- **pl->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.3 s
- **uk->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **tr->en**: transcrição ruim: 24% das palavras erradas
- **ar->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **hi->en**: transcrição ruim: 66% das palavras erradas
- **ja->en**: a tradução pronta espera 1254 ms a fala anterior terminar de tocar; picos de atraso: 1 em cada 20 trechos demora mais de 4.2 s
- **ko->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.5 s

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
