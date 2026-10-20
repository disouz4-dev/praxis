_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `small` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 9.1% palavras | 1.5% | 67.1 | 1.7 s | 2.2 s | +0.1 s | 2.2 s | 54% | ✅ |
| en->pt | 19s | 7.0% palavras | 5.3% | 46.2 | 1.5 s | 2.4 s | +0.1 s | 2.6 s | 70% | ✅ |
| es->en | 16s | 11.5% palavras | 4.8% | 73.3 | 1.4 s | 2.0 s | -0.5 s | 2.2 s | 49% | ✅ |
| fr->en | 19s | 15.0% palavras | 9.8% | 59.0 | 2.0 s | 3.3 s | -1.0 s | 4.4 s | 54% | ✅ |
| de->en | 19s | 37.5% palavras | 13.1% | 39.1 | 1.6 s | 1.7 s | +0.1 s | 1.9 s | 43% | ✅ |
| it->en | 21s | 35.1% palavras | 8.3% | 48.0 | 1.7 s | 1.8 s | -0.1 s | 2.6 s | 59% | ✅ |
| ru->en | 22s | 19.1% palavras | 6.0% | 53.4 | 2.6 s | 2.6 s | +0.0 s | 0.0 s | 39% | ✅ |
| zh->en | 20s | 19.3% caracteres | 19.3% | 47.5 | 1.7 s | 2.8 s | +0.6 s | 3.1 s | 66% | ✅ |
| nl->en | 20s | 44.4% palavras | 18.4% | 58.8 | 1.5 s | 1.7 s | +0.3 s | 4.9 s | 40% | ✅ |
| pl->en | 21s | 27.0% palavras | 6.5% | 44.8 | 2.4 s | 3.0 s | -1.0 s | 2.8 s | 62% | ✅ |
| uk->en | 20s | 16.7% palavras | 6.1% | 46.2 | 1.7 s | 2.5 s | -0.2 s | 1.1 s | 48% | ✅ |
| tr->en | 19s | 23.8% palavras | 10.6% | 63.9 | 1.8 s | 3.4 s | +0.0 s | 0.0 s | 34% | ✅ |
| ar->en | 20s | 24.1% palavras | 7.6% | 63.5 | 1.7 s | 2.5 s | -0.6 s | 1.8 s | 46% | ✅ |
| hi->en | 20s | 55.2% palavras | 30.0% | 22.9 | 2.0 s | 3.1 s | +0.4 s | 1.7 s | 46% | ✅ |
| ja->en | 19s | 17.4% caracteres | 17.4% | 50.1 | 2.3 s | 2.7 s | +0.8 s | 0.0 s | 36% | ✅ |
| ko->en | 17s | 10.0% caracteres | 10.0% | 48.4 | 3.0 s | 5.2 s | -1.1 s | 1.4 s | 49% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 1199 ms | 16 ms | 33 ms | 0 ms |
| en->pt | 0 ms | 1077 ms | 10 ms | 28 ms | 0 ms |
| es->en | 0 ms | 1096 ms | 18 ms | 29 ms | 0 ms |
| fr->en | 0 ms | 1193 ms | 20 ms | 43 ms | 0 ms |
| de->en | 0 ms | 1160 ms | 17 ms | 32 ms | 0 ms |
| it->en | 0 ms | 1253 ms | 17 ms | 46 ms | 0 ms |
| ru->en | 0 ms | 1321 ms | 26 ms | 57 ms | 0 ms |
| zh->en | 0 ms | 1162 ms | 14 ms | 38 ms | 0 ms |
| nl->en | 0 ms | 1227 ms | 16 ms | 36 ms | 0 ms |
| pl->en | 0 ms | 1266 ms | 26 ms | 48 ms | 0 ms |
| uk->en | 0 ms | 1156 ms | 13 ms | 30 ms | 0 ms |
| tr->en | 0 ms | 1232 ms | 16 ms | 44 ms | 0 ms |
| ar->en | 0 ms | 1238 ms | 12 ms | 31 ms | 0 ms |
| hi->en | 0 ms | 1327 ms | 15 ms | 31 ms | 0 ms |
| ja->en | 0 ms | 1201 ms | 17 ms | 38 ms | 596 ms |
| ko->en | 0 ms | 1248 ms | 22 ms | 54 ms | 0 ms |

### Problemas encontrados

- **pt->en**: nenhum problema detectado
- **en->pt**: nenhum problema detectado
- **es->en**: nenhum problema detectado
- **fr->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.3 s
- **de->en**: transcrição ruim: 38% das palavras erradas
- **it->en**: transcrição ruim: 35% das palavras erradas
- **ru->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **zh->en**: pulou 1 trecho(s) inteiro(s) da fala (maior: 6 caracteres seguidas)
- **nl->en**: transcrição ruim: 44% das palavras erradas
- **pl->en**: transcrição ruim: 27% das palavras erradas
- **uk->en**: nenhum problema detectado
- **tr->en**: transcrição ruim: 24% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.4 s
- **ar->en**: transcrição ruim: 24% das palavras erradas
- **hi->en**: transcrição ruim: 55% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.1 s
- **ja->en**: nenhum problema detectado
- **ko->en**: picos de atraso: 1 em cada 20 trechos demora mais de 5.2 s

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
