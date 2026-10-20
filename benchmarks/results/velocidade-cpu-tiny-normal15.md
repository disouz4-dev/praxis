_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `tiny` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 14s | 27.3% palavras | 6.7% | 50.4 | 2.3 s | 3.7 s | +0.1 s | 4.3 s | 69% | ✅ |
| en->pt | 14s | 4.7% palavras | 4.3% | 75.1 | 1.5 s | 1.7 s | +0.6 s | 4.2 s | 84% | ✅ |
| es->en | 12s | 19.2% palavras | 10.6% | 62.8 | 0.8 s | 2.0 s | +0.0 s | 2.3 s | 57% | ✅ |
| fr->en | 14s | 30.0% palavras | 16.5% | 54.5 | 1.0 s | 1.8 s | +0.7 s | 3.4 s | 66% | ✅ |
| de->en | 14s | 87.5% palavras | 29.9% | 31.1 | 0.7 s | 0.8 s | +0.0 s | 3.9 s | 68% | ✅ |
| it->en | 16s | 64.9% palavras | 16.7% | 36.0 | 2.8 s | 4.1 s | +0.2 s | 4.3 s | 78% | ✅ |
| ru->en | 17s | 42.9% palavras | 9.7% | 55.1 | 1.5 s | 1.5 s | -0.0 s | 0.3 s | 50% | ✅ |
| zh->en | 15s | 25.3% caracteres | 25.3% | 44.9 | 1.3 s | 1.6 s | -0.1 s | 4.4 s | 83% | ✅ |
| nl->en | 15s | 55.6% palavras | 28.9% | 40.7 | 0.4 s | 0.6 s | +0.2 s | 4.2 s | 51% | ✅ |
| pl->en | 15s | 51.3% palavras | 17.3% | 43.6 | 0.8 s | 1.3 s | -0.3 s | 3.2 s | 70% | ✅ |
| uk->en | 15s | 75.0% palavras | 14.9% | 48.8 | 0.8 s | 2.3 s | -0.8 s | 2.9 s | 54% | ✅ |
| tr->en | 14s | 33.3% palavras | 17.0% | 54.8 | 1.1 s | 1.6 s | -0.5 s | 1.3 s | 45% | ✅ |
| ar->en | 15s | 55.2% palavras | 16.0% | 26.1 | 1.2 s | 1.8 s | +0.6 s | 1.8 s | 50% | ✅ |
| hi->en | 15s | 103.5% palavras | 110.0% | 20.8 | 0.8 s | 1.1 s | -0.1 s | 2.5 s | 69% | ✅ |
| ja->en | 14s | 30.4% caracteres | 30.4% | 39.4 | 2.1 s | 2.5 s | +0.5 s | 1.5 s | 43% | ✅ |
| ko->en | 12s | 70.0% caracteres | 70.0% | 0.2 | 0.0 s | 0.0 s | +0.0 s | 3.4 s | 0% | ❌ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 230 ms | 26 ms | 48 ms | 1178 ms |
| en->pt | 0 ms | 251 ms | 32 ms | 75 ms | 155 ms |
| es->en | 0 ms | 221 ms | 23 ms | 29 ms | 69 ms |
| fr->en | 0 ms | 255 ms | 33 ms | 80 ms | 0 ms |
| de->en | 0 ms | 255 ms | 32 ms | 48 ms | 0 ms |
| it->en | 0 ms | 262 ms | 30 ms | 68 ms | 1641 ms |
| ru->en | 0 ms | 261 ms | 31 ms | 43 ms | 0 ms |
| zh->en | 0 ms | 293 ms | 35 ms | 98 ms | 157 ms |
| nl->en | 0 ms | 258 ms | 34 ms | 71 ms | 0 ms |
| pl->en | 0 ms | 277 ms | 30 ms | 71 ms | 0 ms |
| uk->en | 0 ms | 280 ms | 30 ms | 72 ms | 0 ms |
| tr->en | 0 ms | 285 ms | 31 ms | 41 ms | 0 ms |
| ar->en | 0 ms | 300 ms | 36 ms | 50 ms | 0 ms |
| hi->en | 0 ms | 201 ms | 18 ms | 29 ms | 239 ms |
| ja->en | 0 ms | 285 ms | 32 ms | 59 ms | 927 ms |
| ko->en | 0 ms | 683 ms | 28 ms | — | — |

### Problemas encontrados

- **pt->en**: transcrição ruim: 27% das palavras erradas; a tradução pronta espera 1178 ms a fala anterior terminar de tocar; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s
- **en->pt**: nenhum problema detectado
- **es->en**: nenhum problema detectado
- **fr->en**: transcrição ruim: 30% das palavras erradas
- **de->en**: transcrição ruim: 88% das palavras erradas; inventou 7 palavras que não foram faladas
- **it->en**: transcrição ruim: 65% das palavras erradas; a tradução pronta espera 1641 ms a fala anterior terminar de tocar; picos de atraso: 1 em cada 20 trechos demora mais de 4.1 s
- **ru->en**: transcrição ruim: 43% das palavras erradas
- **zh->en**: transcrição ruim: 25% dos caracteres erradas
- **nl->en**: transcrição ruim: 56% das palavras erradas
- **pl->en**: transcrição ruim: 51% das palavras erradas
- **uk->en**: transcrição ruim: 75% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **tr->en**: transcrição ruim: 33% das palavras erradas
- **ar->en**: transcrição ruim: 55% das palavras erradas
- **hi->en**: transcrição ruim: 103% das palavras erradas
- **ja->en**: transcrição ruim: 30% dos caracteres erradas; a tradução pronta espera 927 ms a fala anterior terminar de tocar
- **ko->en**: transcrição ruim: 70% dos caracteres erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 22 caracteres seguidas); não acompanha o falante: atraso típico 0.0 s, sobe +0.0 s da 1ª para a 2ª metade e sobram 3 s de tradução quando ele para

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
