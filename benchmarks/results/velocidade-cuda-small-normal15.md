_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `small` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 14s | 9.1% palavras | 1.5% | 76.1 | 2.5 s | 3.6 s | -0.2 s | 4.2 s | 72% | ✅ |
| en->pt | 14s | 0.0% palavras | 0.0% | 75.8 | 1.5 s | 2.1 s | +0.9 s | 4.9 s | 88% | ✅ |
| es->en | 12s | 0.0% palavras | 0.0% | 85.4 | 0.8 s | 2.2 s | +0.2 s | 2.4 s | 60% | ✅ |
| fr->en | 14s | 7.5% palavras | 7.3% | 55.6 | 0.9 s | 2.2 s | +1.0 s | 3.4 s | 71% | ✅ |
| de->en | 14s | 20.8% palavras | 7.3% | 55.0 | 0.6 s | 0.6 s | +0.0 s | 2.9 s | 52% | ✅ |
| it->en | 16s | 27.0% palavras | 5.9% | 54.7 | 2.9 s | 4.4 s | +0.4 s | 5.1 s | 90% | ✅ |
| ru->en | 17s | 19.1% palavras | 6.0% | 53.4 | 1.4 s | 1.8 s | +0.1 s | 0.4 s | 52% | ✅ |
| zh->en | 15s | 15.7% caracteres | 15.7% | 48.2 | 1.4 s | 1.9 s | +0.4 s | 2.4 s | 69% | ✅ |
| nl->en | 15s | 29.6% palavras | 14.0% | 66.1 | 0.4 s | 0.5 s | +0.2 s | 4.0 s | 58% | ✅ |
| pl->en | 15s | 13.5% palavras | 2.7% | 61.7 | 1.0 s | 2.2 s | +0.1 s | 3.5 s | 81% | ✅ |
| uk->en | 15s | 8.3% palavras | 2.7% | 78.6 | 0.6 s | 0.7 s | +0.2 s | 2.9 s | 56% | ✅ |
| tr->en | 14s | 28.6% palavras | 13.8% | 53.3 | 1.3 s | 1.5 s | -0.3 s | 1.3 s | 47% | ✅ |
| ar->en | 15s | 17.2% palavras | 4.2% | 82.2 | 1.1 s | 3.0 s | +1.3 s | 2.9 s | 55% | ✅ |
| hi->en | 15s | 69.0% palavras | 34.2% | 24.7 | 0.9 s | 1.1 s | +0.2 s | 1.2 s | 59% | ✅ |
| ja->en | 14s | 17.4% caracteres | 17.4% | 45.1 | 2.2 s | 2.8 s | +0.7 s | 1.8 s | 45% | ✅ |
| ko->en | 12s | 14.0% caracteres | 14.0% | 54.1 | 2.4 s | 2.8 s | +0.9 s | 4.1 s | 69% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 150 ms | 22 ms | 57 ms | 1445 ms |
| en->pt | 0 ms | 167 ms | 28 ms | 64 ms | 1 ms |
| es->en | 0 ms | 141 ms | 24 ms | 45 ms | 188 ms |
| fr->en | 0 ms | 179 ms | 27 ms | 73 ms | 0 ms |
| de->en | 0 ms | 143 ms | 17 ms | 35 ms | 0 ms |
| it->en | 0 ms | 161 ms | 23 ms | 73 ms | 1870 ms |
| ru->en | 0 ms | 168 ms | 26 ms | 50 ms | 0 ms |
| zh->en | 0 ms | 221 ms | 31 ms | 100 ms | 0 ms |
| nl->en | 0 ms | 190 ms | 29 ms | 81 ms | 0 ms |
| pl->en | 0 ms | 176 ms | 28 ms | 74 ms | 241 ms |
| uk->en | 0 ms | 212 ms | 31 ms | 90 ms | 0 ms |
| tr->en | 0 ms | 181 ms | 26 ms | 78 ms | 219 ms |
| ar->en | 0 ms | 207 ms | 24 ms | 81 ms | 0 ms |
| hi->en | 0 ms | 164 ms | 14 ms | 29 ms | 366 ms |
| ja->en | 0 ms | 190 ms | 27 ms | 65 ms | 1162 ms |
| ko->en | 0 ms | 200 ms | 34 ms | 93 ms | 471 ms |

### Problemas encontrados

- **pt->en**: a tradução pronta espera 1445 ms a fala anterior terminar de tocar; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; picos de atraso: 1 em cada 20 trechos demora mais de 3.6 s
- **en->pt**: nenhum problema detectado
- **es->en**: nenhum problema detectado
- **fr->en**: nenhum problema detectado
- **de->en**: transcrição ruim: 21% das palavras erradas
- **it->en**: transcrição ruim: 27% das palavras erradas; a tradução pronta espera 1870 ms a fala anterior terminar de tocar; picos de atraso: 1 em cada 20 trechos demora mais de 4.4 s
- **ru->en**: nenhum problema detectado
- **zh->en**: nenhum problema detectado
- **nl->en**: transcrição ruim: 30% das palavras erradas
- **pl->en**: nenhum problema detectado
- **uk->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **tr->en**: transcrição ruim: 29% das palavras erradas
- **ar->en**: nenhum problema detectado
- **hi->en**: transcrição ruim: 69% das palavras erradas
- **ja->en**: a tradução pronta espera 1162 ms a fala anterior terminar de tocar
- **ko->en**: nenhum problema detectado

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
