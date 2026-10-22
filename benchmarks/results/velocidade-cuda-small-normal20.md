_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `small` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 14.0% palavras | 5.1% | 71.4 | 0.8 s | 3.6 s | -1.4 s | 3.6 s | 69% | ✅ |
| en->pt | 20s | 0.0% palavras | 0.0% | 79.6 | 1.2 s | 2.0 s | +0.6 s | 5.1 s | 87% | ✅ |
| es->en | 21s | 2.2% palavras | 0.5% | 56.5 | 0.9 s | 1.6 s | +0.3 s | 2.0 s | 55% | ✅ |
| fr->en | 21s | 28.6% palavras | 10.4% | 60.5 | 2.0 s | 3.3 s | -0.0 s | 4.7 s | 78% | ✅ |
| de->en | 19s | 23.5% palavras | 7.6% | 63.7 | 1.0 s | 2.4 s | -0.6 s | 4.1 s | 59% | ✅ |
| it->en | 20s | 38.3% palavras | 10.8% | 46.7 | 1.4 s | 2.3 s | -1.3 s | 4.0 s | 71% | ✅ |
| ru->en | 19s | 23.1% palavras | 5.1% | 74.2 | 1.4 s | 3.4 s | +0.6 s | 3.3 s | 59% | ✅ |
| zh->en | 19s | 20.4% caracteres | 20.4% | 48.9 | 1.3 s | 2.7 s | -0.6 s | 0.0 s | 43% | ✅ |
| nl->en | 22s | 18.8% palavras | 5.7% | 68.6 | 1.4 s | 2.4 s | +1.5 s | 3.9 s | 71% | ❌ |
| pl->en | 18s | 15.4% palavras | 3.3% | 50.7 | 0.7 s | 1.3 s | +0.5 s | 3.3 s | 76% | ✅ |
| uk->en | 19s | 14.7% palavras | 3.2% | 71.1 | 1.0 s | 2.5 s | -2.0 s | 2.6 s | 70% | ✅ |
| tr->en | 17s | 8.3% palavras | 1.2% | 61.3 | 0.6 s | 1.0 s | -0.5 s | 0.0 s | 34% | ✅ |
| ar->en | 19s | 20.0% palavras | 7.6% | 60.0 | 1.4 s | 2.2 s | -0.2 s | 2.4 s | 61% | ✅ |
| hi->en | 20s | 65.8% palavras | 29.4% | 28.9 | 0.9 s | 1.3 s | +0.1 s | 3.2 s | 58% | ✅ |
| ja->en | 25s | 18.2% caracteres | 18.2% | 55.6 | 1.4 s | 3.1 s | -1.6 s | 2.2 s | 51% | ✅ |
| ko->en | 20s | 5.4% caracteres | 5.4% | 48.2 | 1.5 s | 1.8 s | -0.7 s | 3.5 s | 54% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 167 ms | 21 ms | 63 ms | 0 ms |
| en->pt | 0 ms | 166 ms | 27 ms | 90 ms | 1 ms |
| es->en | 0 ms | 148 ms | 26 ms | 39 ms | 0 ms |
| fr->en | 0 ms | 178 ms | 29 ms | 46 ms | 1289 ms |
| de->en | 0 ms | 159 ms | 28 ms | 49 ms | 0 ms |
| it->en | 0 ms | 173 ms | 20 ms | 57 ms | 0 ms |
| ru->en | 0 ms | 179 ms | 26 ms | 69 ms | 110 ms |
| zh->en | 0 ms | 142 ms | 14 ms | 31 ms | 0 ms |
| nl->en | 0 ms | 163 ms | 24 ms | 55 ms | 1 ms |
| pl->en | 0 ms | 215 ms | 38 ms | 85 ms | 59 ms |
| uk->en | 0 ms | 191 ms | 24 ms | 63 ms | 0 ms |
| tr->en | 0 ms | 183 ms | 22 ms | 46 ms | 0 ms |
| ar->en | 0 ms | 220 ms | 27 ms | 48 ms | 58 ms |
| hi->en | 0 ms | 187 ms | 16 ms | 36 ms | 465 ms |
| ja->en | 0 ms | 205 ms | 36 ms | 97 ms | 0 ms |
| ko->en | 0 ms | 201 ms | 29 ms | 64 ms | 0 ms |

### Problemas encontrados

- **pt->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.6 s
- **en->pt**: nenhum problema detectado
- **es->en**: nenhum problema detectado
- **fr->en**: transcrição ruim: 29% das palavras erradas; a tradução pronta espera 1289 ms a fala anterior terminar de tocar; picos de atraso: 1 em cada 20 trechos demora mais de 3.3 s
- **de->en**: transcrição ruim: 24% das palavras erradas
- **it->en**: transcrição ruim: 38% das palavras erradas
- **ru->en**: transcrição ruim: 23% das palavras erradas; picos de atraso: 1 em cada 20 trechos demora mais de 3.4 s
- **zh->en**: transcrição ruim: 20% dos caracteres erradas
- **nl->en**: não acompanha o falante: atraso típico 1.4 s, sobe +1.5 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **pl->en**: nenhum problema detectado
- **uk->en**: nenhum problema detectado
- **tr->en**: nenhum problema detectado
- **ar->en**: nenhum problema detectado
- **hi->en**: transcrição ruim: 66% das palavras erradas
- **ja->en**: picos de atraso: 1 em cada 20 trechos demora mais de 3.1 s
- **ko->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
