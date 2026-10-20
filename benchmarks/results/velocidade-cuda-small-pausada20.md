_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `small` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 9.1% palavras | 1.5% | 67.1 | 0.6 s | 1.2 s | +0.1 s | 1.2 s | 55% | ✅ |
| en->pt | 19s | 11.6% palavras | 9.6% | 48.2 | 0.5 s | 1.4 s | +0.0 s | 1.7 s | 73% | ✅ |
| es->en | 16s | 11.5% palavras | 5.8% | 66.6 | 0.4 s | 1.0 s | -0.5 s | 1.0 s | 45% | ✅ |
| fr->en | 19s | 15.0% palavras | 9.8% | 59.0 | 0.9 s | 2.3 s | -1.1 s | 3.3 s | 56% | ✅ |
| de->en | 19s | 33.3% palavras | 11.7% | 36.1 | 0.5 s | 0.6 s | +0.0 s | 0.8 s | 43% | ✅ |
| it->en | 21s | 35.1% palavras | 8.3% | 48.0 | 0.6 s | 0.6 s | -0.0 s | 1.4 s | 60% | ✅ |
| ru->en | 22s | 19.1% palavras | 6.0% | 53.4 | 1.3 s | 1.4 s | +0.0 s | 0.0 s | 39% | ✅ |
| zh->en | 20s | 19.3% caracteres | 19.3% | 47.6 | 0.5 s | 1.9 s | +0.8 s | 2.2 s | 68% | ✅ |
| nl->en | 20s | 44.4% palavras | 17.5% | 59.8 | 0.4 s | 0.5 s | +0.2 s | 3.9 s | 41% | ✅ |
| pl->en | 21s | 27.0% palavras | 8.6% | 43.2 | 1.1 s | 1.7 s | -0.8 s | 1.6 s | 62% | ✅ |
| uk->en | 20s | 25.0% palavras | 7.4% | 47.0 | 0.6 s | 1.4 s | -0.1 s | 0.0 s | 48% | ✅ |
| tr->en | 19s | 23.8% palavras | 10.6% | 63.9 | 0.6 s | 2.0 s | +0.0 s | 0.0 s | 33% | ✅ |
| ar->en | 20s | 24.1% palavras | 8.4% | 55.9 | 0.6 s | 1.4 s | -0.6 s | 0.7 s | 45% | ✅ |
| hi->en | 20s | 55.2% palavras | 30.8% | 21.7 | 0.6 s | 2.1 s | +0.2 s | 0.4 s | 46% | ✅ |
| ja->en | 19s | 17.4% caracteres | 17.4% | 48.5 | 1.1 s | 1.5 s | +0.9 s | 0.0 s | 36% | ✅ |
| ko->en | 17s | 10.0% caracteres | 10.0% | 48.4 | 2.0 s | 4.2 s | -1.1 s | 0.4 s | 50% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 147 ms | 16 ms | 34 ms | 0 ms |
| en->pt | 0 ms | 121 ms | 9 ms | 27 ms | 0 ms |
| es->en | 0 ms | 119 ms | 17 ms | 23 ms | 0 ms |
| fr->en | 0 ms | 147 ms | 20 ms | 53 ms | 0 ms |
| de->en | 0 ms | 140 ms | 17 ms | 24 ms | 0 ms |
| it->en | 0 ms | 157 ms | 16 ms | 45 ms | 0 ms |
| ru->en | 0 ms | 168 ms | 26 ms | 56 ms | 0 ms |
| zh->en | 0 ms | 139 ms | 13 ms | 32 ms | 0 ms |
| nl->en | 0 ms | 148 ms | 17 ms | 38 ms | 0 ms |
| pl->en | 0 ms | 163 ms | 25 ms | 54 ms | 0 ms |
| uk->en | 0 ms | 129 ms | 12 ms | 30 ms | 0 ms |
| tr->en | 0 ms | 148 ms | 15 ms | 46 ms | 0 ms |
| ar->en | 0 ms | 155 ms | 11 ms | 31 ms | 0 ms |
| hi->en | 0 ms | 174 ms | 13 ms | 29 ms | 0 ms |
| ja->en | 0 ms | 124 ms | 12 ms | 27 ms | 533 ms |
| ko->en | 0 ms | 156 ms | 21 ms | 52 ms | 0 ms |

### Problemas encontrados

- **pt->en**: nenhum problema detectado
- **en->pt**: nenhum problema detectado
- **es->en**: nenhum problema detectado
- **fr->en**: nenhum problema detectado
- **de->en**: transcrição ruim: 33% das palavras erradas
- **it->en**: transcrição ruim: 35% das palavras erradas
- **ru->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **zh->en**: pulou 1 trecho(s) inteiro(s) da fala (maior: 6 caracteres seguidas)
- **nl->en**: transcrição ruim: 44% das palavras erradas
- **pl->en**: transcrição ruim: 27% das palavras erradas
- **uk->en**: transcrição ruim: 25% das palavras erradas
- **tr->en**: transcrição ruim: 24% das palavras erradas
- **ar->en**: transcrição ruim: 24% das palavras erradas
- **hi->en**: transcrição ruim: 55% das palavras erradas
- **ja->en**: nenhum problema detectado
- **ko->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.2 s

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
