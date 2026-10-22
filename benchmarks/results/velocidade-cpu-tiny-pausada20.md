_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `tiny` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 30.3% palavras | 7.5% | 55.3 | 0.8 s | 1.3 s | +0.1 s | 1.6 s | 55% | ✅ |
| en->pt | 19s | 18.6% palavras | 14.9% | 46.8 | 0.9 s | 1.8 s | +0.1 s | 1.8 s | 82% | ✅ |
| es->en | 16s | 23.1% palavras | 13.5% | 61.6 | 0.4 s | 0.9 s | -0.5 s | 1.1 s | 44% | ✅ |
| fr->en | 19s | 37.5% palavras | 20.1% | 48.3 | 0.9 s | 1.4 s | +0.0 s | 3.9 s | 48% | ✅ |
| de->en | 19s | 87.5% palavras | 27.7% | 31.7 | 0.6 s | 1.0 s | +0.1 s | 1.4 s | 47% | ✅ |
| it->en | 21s | 62.2% palavras | 19.1% | 47.5 | 0.7 s | 0.8 s | +0.0 s | 2.1 s | 67% | ✅ |
| ru->en | 22s | 66.7% palavras | 20.2% | 45.8 | 1.4 s | 1.5 s | +0.0 s | 0.0 s | 44% | ✅ |
| zh->en | 20s | 33.7% caracteres | 33.7% | 33.2 | 0.6 s | 2.1 s | +0.7 s | 2.1 s | 65% | ✅ |
| nl->en | 20s | 51.8% palavras | 28.1% | 44.1 | 0.5 s | 0.6 s | +0.2 s | 4.2 s | 41% | ✅ |
| pl->en | 21s | 78.4% palavras | 24.9% | 29.9 | 0.8 s | 1.2 s | -0.3 s | 1.5 s | 57% | ✅ |
| uk->en | 20s | 75.0% palavras | 30.4% | 34.2 | 0.7 s | 2.1 s | -0.1 s | 1.4 s | 56% | ✅ |
| tr->en | 19s | 33.3% palavras | 14.9% | 58.9 | 1.0 s | 2.9 s | +0.3 s | 0.0 s | 39% | ✅ |
| ar->en | 20s | 55.2% palavras | 25.2% | 30.8 | 0.8 s | 1.7 s | -0.7 s | 1.5 s | 50% | ✅ |
| hi->en | 20s | 100.0% palavras | 114.2% | 19.5 | 0.6 s | 1.0 s | -0.0 s | 0.7 s | 49% | ✅ |
| ja->en | 19s | 41.3% caracteres | 41.3% | 36.5 | 1.0 s | 1.1 s | +0.3 s | 0.0 s | 29% | ✅ |
| ko->en | 17s | 30.0% caracteres | 30.0% | 49.2 | 2.3 s | 4.2 s | -0.8 s | 1.0 s | 55% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 241 ms | 17 ms | 39 ms | 0 ms |
| en->pt | 0 ms | 185 ms | 12 ms | 30 ms | 0 ms |
| es->en | 0 ms | 191 ms | 17 ms | 24 ms | 0 ms |
| fr->en | 0 ms | 255 ms | 23 ms | 42 ms | 0 ms |
| de->en | 0 ms | 205 ms | 20 ms | 29 ms | 0 ms |
| it->en | 0 ms | 253 ms | 21 ms | 55 ms | 0 ms |
| ru->en | 0 ms | 269 ms | 33 ms | 75 ms | 0 ms |
| zh->en | 0 ms | 197 ms | 20 ms | 29 ms | 0 ms |
| nl->en | 0 ms | 242 ms | 22 ms | 35 ms | 0 ms |
| pl->en | 0 ms | 254 ms | 29 ms | 49 ms | 0 ms |
| uk->en | 0 ms | 202 ms | 16 ms | 39 ms | 0 ms |
| tr->en | 0 ms | 263 ms | 18 ms | 44 ms | 311 ms |
| ar->en | 0 ms | 263 ms | 19 ms | 39 ms | 0 ms |
| hi->en | 0 ms | 205 ms | 16 ms | 34 ms | 0 ms |
| ja->en | 0 ms | 205 ms | 20 ms | 24 ms | 269 ms |
| ko->en | 0 ms | 255 ms | 25 ms | 58 ms | 228 ms |

### Problemas encontrados

- **pt->en**: transcrição ruim: 30% das palavras erradas
- **en->pt**: nenhum problema detectado
- **es->en**: transcrição ruim: 23% das palavras erradas
- **fr->en**: transcrição ruim: 38% das palavras erradas
- **de->en**: transcrição ruim: 88% das palavras erradas; inventou 7 palavras que não foram faladas
- **it->en**: transcrição ruim: 62% das palavras erradas
- **ru->en**: transcrição ruim: 67% das palavras erradas; inventou 4 palavras que não foram faladas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **zh->en**: transcrição ruim: 34% dos caracteres erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 8 caracteres seguidas)
- **nl->en**: transcrição ruim: 52% das palavras erradas
- **pl->en**: transcrição ruim: 78% das palavras erradas
- **uk->en**: transcrição ruim: 75% das palavras erradas
- **tr->en**: transcrição ruim: 33% das palavras erradas
- **ar->en**: transcrição ruim: 55% das palavras erradas
- **hi->en**: transcrição ruim: 100% das palavras erradas
- **ja->en**: transcrição ruim: 41% dos caracteres erradas; inventou 4 caracteres que não foram faladas
- **ko->en**: transcrição ruim: 30% dos caracteres erradas; picos de atraso: 1 em cada 20 trechos demora mais de 4.2 s

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
