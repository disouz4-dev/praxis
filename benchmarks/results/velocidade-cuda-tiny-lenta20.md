_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `tiny` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 36.4% palavras | 12.7% | 46.7 | 0.5 s | 0.8 s | +0.1 s | 2.4 s | 53% | ✅ |
| en->pt | 19s | 7.0% palavras | 5.3% | 64.1 | 1.4 s | 1.5 s | +1.0 s | 2.8 s | 66% | ✅ |
| es->en | 16s | 23.1% palavras | 10.6% | 48.2 | 0.5 s | 0.6 s | +0.1 s | 2.1 s | 43% | ✅ |
| fr->en | 19s | 57.5% palavras | 26.8% | 44.1 | 0.6 s | 0.7 s | +0.2 s | 3.6 s | 54% | ✅ |
| de->en | 19s | 87.5% palavras | 31.4% | 35.8 | 0.5 s | 0.8 s | +0.1 s | 2.3 s | 48% | ✅ |
| it->en | 21s | 56.8% palavras | 17.3% | 47.2 | 0.5 s | 0.5 s | -0.0 s | 1.6 s | 59% | ✅ |
| ru->en | 22s | 57.1% palavras | 14.9% | 45.2 | 1.5 s | 3.2 s | -1.5 s | 0.4 s | 46% | ✅ |
| zh->en | 20s | 31.3% caracteres | 31.3% | 42.1 | 1.1 s | 2.5 s | +0.6 s | 2.4 s | 61% | ✅ |
| nl->en | 20s | 63.0% palavras | 33.3% | 50.6 | 0.2 s | 0.4 s | -0.0 s | 4.0 s | 47% | ✅ |
| pl->en | 21s | 59.5% palavras | 24.3% | 38.0 | 0.5 s | 1.8 s | -1.0 s | 2.7 s | 50% | ✅ |
| uk->en | 20s | 66.7% palavras | 14.9% | 44.3 | 1.2 s | 2.7 s | +1.8 s | 1.5 s | 41% | ❌ |
| tr->en | 19s | 47.6% palavras | 22.3% | 44.3 | 0.7 s | 1.4 s | -0.9 s | 0.0 s | 36% | ✅ |
| ar->en | 20s | 69.0% palavras | 23.5% | 30.9 | 1.1 s | 2.7 s | -0.7 s | 1.4 s | 43% | ✅ |
| hi->en | 20s | 100.0% palavras | 100.8% | 16.5 | 0.5 s | 1.1 s | +0.1 s | 0.1 s | 51% | ✅ |
| ja->en | 19s | 39.1% caracteres | 39.1% | 40.9 | 0.6 s | 0.6 s | -0.1 s | 0.0 s | 37% | ✅ |
| ko->en | 17s | 34.0% caracteres | 34.0% | 40.7 | 2.3 s | 3.7 s | -0.9 s | 1.4 s | 47% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 51 ms | 47 ms | 48 ms | 0 ms |
| en->pt | 0 ms | 55 ms | 38 ms | 65 ms | 0 ms |
| es->en | 0 ms | 41 ms | 24 ms | 38 ms | 0 ms |
| fr->en | 0 ms | 56 ms | 37 ms | 54 ms | 0 ms |
| de->en | 0 ms | 40 ms | 40 ms | 38 ms | 0 ms |
| it->en | 0 ms | 45 ms | 27 ms | 46 ms | 0 ms |
| ru->en | 0 ms | 50 ms | 35 ms | 65 ms | 0 ms |
| zh->en | 0 ms | 65 ms | 36 ms | 74 ms | 0 ms |
| nl->en | 0 ms | 42 ms | 30 ms | 52 ms | 0 ms |
| pl->en | 0 ms | 62 ms | 41 ms | 45 ms | 0 ms |
| uk->en | 0 ms | 58 ms | 33 ms | 44 ms | 135 ms |
| tr->en | 0 ms | 49 ms | 29 ms | 53 ms | 0 ms |
| ar->en | 0 ms | 60 ms | 33 ms | 42 ms | 0 ms |
| hi->en | 0 ms | 34 ms | 15 ms | 45 ms | 0 ms |
| ja->en | 0 ms | 69 ms | 39 ms | 73 ms | 0 ms |
| ko->en | 0 ms | 58 ms | 32 ms | 62 ms | 0 ms |

### Problemas encontrados

- **pt->en**: transcrição ruim: 36% das palavras erradas
- **en->pt**: nenhum problema detectado
- **es->en**: transcrição ruim: 23% das palavras erradas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **fr->en**: transcrição ruim: 57% das palavras erradas; inventou 7 palavras que não foram faladas
- **de->en**: transcrição ruim: 88% das palavras erradas; inventou 6 palavras que não foram faladas; 1 trecho(s) com fala viraram texto vazio
- **it->en**: transcrição ruim: 57% das palavras erradas
- **ru->en**: transcrição ruim: 57% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.2 s
- **zh->en**: transcrição ruim: 31% dos caracteres erradas
- **nl->en**: transcrição ruim: 63% das palavras erradas; inventou 5 palavras que não foram faladas; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **pl->en**: transcrição ruim: 59% das palavras erradas; inventou 4 palavras que não foram faladas
- **uk->en**: transcrição ruim: 67% das palavras erradas; não acompanha o falante: atraso típico 1.2 s, sobe +1.8 s da 1ª para a 2ª metade e sobram 2 s de tradução quando ele para; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **tr->en**: transcrição ruim: 48% das palavras erradas
- **ar->en**: transcrição ruim: 69% das palavras erradas
- **hi->en**: transcrição ruim: 100% das palavras erradas
- **ja->en**: transcrição ruim: 39% dos caracteres erradas; inventou 8 caracteres que não foram faladas
- **ko->en**: transcrição ruim: 34% dos caracteres erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.7 s

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
