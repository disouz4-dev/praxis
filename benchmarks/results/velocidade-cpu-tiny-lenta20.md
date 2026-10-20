_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `tiny` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 36.4% palavras | 12.7% | 48.0 | 0.7 s | 1.0 s | +0.2 s | 2.5 s | 53% | ✅ |
| en->pt | 19s | 7.0% palavras | 5.3% | 64.1 | 1.6 s | 1.7 s | +1.0 s | 3.1 s | 67% | ✅ |
| es->en | 16s | 23.1% palavras | 11.5% | 45.9 | 0.7 s | 0.8 s | +0.1 s | 2.3 s | 44% | ✅ |
| fr->en | 19s | 45.0% palavras | 23.2% | 47.2 | 0.7 s | 0.9 s | +0.2 s | 3.1 s | 49% | ✅ |
| de->en | 19s | 83.3% palavras | 28.5% | 38.2 | 0.6 s | 1.0 s | +0.2 s | 2.6 s | 46% | ✅ |
| it->en | 21s | 56.8% palavras | 17.3% | 45.1 | 0.7 s | 0.7 s | -0.0 s | 1.7 s | 57% | ✅ |
| ru->en | 22s | 61.9% palavras | 24.6% | 42.1 | 1.6 s | 3.5 s | -1.6 s | 0.0 s | 40% | ✅ |
| zh->en | 20s | 33.7% caracteres | 33.7% | 33.1 | 1.3 s | 2.1 s | +0.6 s | 2.0 s | 53% | ✅ |
| nl->en | 20s | 59.3% palavras | 32.5% | 51.6 | 0.4 s | 0.6 s | -0.0 s | 4.1 s | 45% | ✅ |
| pl->en | 21s | 56.8% palavras | 31.4% | 35.5 | 0.9 s | 1.5 s | -0.4 s | 2.9 s | 52% | ✅ |
| uk->en | 20s | 66.7% palavras | 13.5% | 44.7 | 1.5 s | 3.0 s | +1.9 s | 2.1 s | 44% | ❌ |
| tr->en | 19s | 38.1% palavras | 19.1% | 42.2 | 0.8 s | 1.6 s | -1.0 s | 0.0 s | 35% | ✅ |
| ar->en | 20s | 69.0% palavras | 21.9% | 29.3 | 1.4 s | 2.9 s | -0.7 s | 1.9 s | 49% | ✅ |
| hi->en | 20s | 106.9% palavras | 102.5% | 17.0 | 0.6 s | 1.7 s | +0.5 s | 1.4 s | 58% | ✅ |
| ja->en | 19s | 37.0% caracteres | 37.0% | 38.9 | 0.8 s | 0.9 s | -0.1 s | 0.0 s | 30% | ✅ |
| ko->en | 17s | 50.0% caracteres | 50.0% | 32.3 | 2.4 s | 2.5 s | -0.2 s | 0.8 s | 36% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 256 ms | 28 ms | 55 ms | 0 ms |
| en->pt | 0 ms | 256 ms | 25 ms | 69 ms | 0 ms |
| es->en | 0 ms | 248 ms | 21 ms | 25 ms | 0 ms |
| fr->en | 0 ms | 246 ms | 24 ms | 47 ms | 0 ms |
| de->en | 0 ms | 256 ms | 28 ms | 36 ms | 0 ms |
| it->en | 0 ms | 255 ms | 17 ms | 37 ms | 0 ms |
| ru->en | 0 ms | 253 ms | 21 ms | 48 ms | 0 ms |
| zh->en | 0 ms | 278 ms | 30 ms | 64 ms | 0 ms |
| nl->en | 0 ms | 256 ms | 25 ms | 46 ms | 0 ms |
| pl->en | 0 ms | 255 ms | 30 ms | 32 ms | 0 ms |
| uk->en | 0 ms | 274 ms | 24 ms | 52 ms | 224 ms |
| tr->en | 0 ms | 260 ms | 19 ms | 40 ms | 0 ms |
| ar->en | 0 ms | 278 ms | 22 ms | 52 ms | 0 ms |
| hi->en | 0 ms | 207 ms | 17 ms | 31 ms | 0 ms |
| ja->en | 0 ms | 281 ms | 27 ms | 62 ms | 0 ms |
| ko->en | 0 ms | 272 ms | 23 ms | 66 ms | 0 ms |

### Problemas encontrados

- **pt->en**: transcrição ruim: 36% das palavras erradas
- **en->pt**: nenhum problema detectado
- **es->en**: transcrição ruim: 23% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **fr->en**: transcrição ruim: 45% das palavras erradas; inventou 4 palavras que não foram faladas
- **de->en**: transcrição ruim: 83% das palavras erradas; inventou 5 palavras que não foram faladas; 1 trecho(s) com fala viraram texto vazio
- **it->en**: transcrição ruim: 57% das palavras erradas
- **ru->en**: transcrição ruim: 62% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.5 s
- **zh->en**: transcrição ruim: 34% dos caracteres erradas
- **nl->en**: transcrição ruim: 59% das palavras erradas; inventou 4 palavras que não foram faladas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **pl->en**: transcrição ruim: 57% das palavras erradas
- **uk->en**: transcrição ruim: 67% das palavras erradas; não acompanha o falante: atraso típico 1.5 s, sobe +1.9 s da 1ª para a 2ª metade e sobram 2 s de tradução quando ele para; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **tr->en**: transcrição ruim: 38% das palavras erradas
- **ar->en**: transcrição ruim: 69% das palavras erradas
- **hi->en**: transcrição ruim: 107% das palavras erradas
- **ja->en**: transcrição ruim: 37% dos caracteres erradas
- **ko->en**: transcrição ruim: 50% dos caracteres erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 14 caracteres seguidas)

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
