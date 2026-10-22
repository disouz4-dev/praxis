_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `large-v3` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 9.1% palavras | 5.2% | 78.5 | 1.0 s | 1.7 s | +0.2 s | 1.6 s | 55% | ✅ |
| en->pt | 19s | 4.7% palavras | 4.3% | 54.7 | 0.9 s | 1.7 s | +0.1 s | 2.1 s | 73% | ✅ |
| es->en | 16s | 11.5% palavras | 7.7% | 54.1 | 0.8 s | 1.5 s | -0.5 s | 1.6 s | 47% | ✅ |
| fr->en | 19s | 5.0% palavras | 3.7% | 76.9 | 1.4 s | 2.2 s | -0.6 s | 3.7 s | 51% | ✅ |
| de->en | 19s | 25.0% palavras | 7.3% | 49.3 | 0.9 s | 1.1 s | +0.2 s | 1.8 s | 45% | ✅ |
| it->en | 21s | 18.9% palavras | 4.2% | 57.6 | 1.1 s | 1.3 s | -0.1 s | 2.6 s | 64% | ✅ |
| ru->en | 22s | 4.8% palavras | 1.5% | 56.4 | 1.9 s | 1.9 s | -0.1 s | 0.0 s | 37% | ✅ |
| zh->en | 20s | 21.7% caracteres | 21.7% | 44.8 | 1.1 s | 2.2 s | +0.4 s | 3.0 s | 74% | ✅ |
| nl->en | 20s | 11.1% palavras | 11.4% | 74.7 | 0.8 s | 1.0 s | +0.3 s | 3.9 s | 38% | ✅ |
| pl->en | 21s | 2.7% palavras | 1.1% | 66.5 | 1.7 s | 2.4 s | -0.7 s | 3.0 s | 67% | ✅ |
| uk->en | 20s | 4.2% palavras | 2.0% | 60.7 | 1.1 s | 1.9 s | -0.1 s | 0.5 s | 53% | ✅ |
| tr->en | 19s | 19.1% palavras | 9.6% | 52.5 | 1.1 s | 2.8 s | +0.0 s | 0.0 s | 35% | ✅ |
| ar->en | 20s | 10.3% palavras | 3.4% | 65.9 | 1.1 s | 2.0 s | -0.8 s | 1.1 s | 44% | ✅ |
| hi->en | 20s | 31.0% palavras | 12.5% | 34.3 | 1.2 s | 2.2 s | -0.0 s | 0.3 s | 40% | ✅ |
| ja->en | 19s | 0.0% caracteres | 0.0% | 65.3 | 1.7 s | 2.2 s | +1.0 s | 0.0 s | 39% | ✅ |
| ko->en | 17s | 0.0% caracteres | 0.0% | 56.3 | 2.4 s | 4.7 s | -1.1 s | 0.8 s | 50% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 566 ms | 15 ms | 39 ms | 0 ms |
| en->pt | 0 ms | 502 ms | 11 ms | 32 ms | 0 ms |
| es->en | 0 ms | 522 ms | 14 ms | 21 ms | 0 ms |
| fr->en | 0 ms | 603 ms | 19 ms | 56 ms | 0 ms |
| de->en | 0 ms | 554 ms | 16 ms | 29 ms | 0 ms |
| it->en | 0 ms | 611 ms | 16 ms | 42 ms | 0 ms |
| ru->en | 0 ms | 661 ms | 20 ms | 53 ms | 0 ms |
| zh->en | 0 ms | 567 ms | 13 ms | 42 ms | 35 ms |
| nl->en | 0 ms | 591 ms | 15 ms | 36 ms | 0 ms |
| pl->en | 0 ms | 638 ms | 23 ms | 63 ms | 0 ms |
| uk->en | 0 ms | 546 ms | 14 ms | 30 ms | 0 ms |
| tr->en | 0 ms | 586 ms | 17 ms | 43 ms | 0 ms |
| ar->en | 0 ms | 602 ms | 10 ms | 35 ms | 0 ms |
| hi->en | 0 ms | 692 ms | 10 ms | 24 ms | 0 ms |
| ja->en | 0 ms | 600 ms | 15 ms | 37 ms | 657 ms |
| ko->en | 0 ms | 638 ms | 21 ms | 59 ms | 0 ms |

### Problemas encontrados

- **pt->en**: nenhum problema detectado
- **en->pt**: nenhum problema detectado
- **es->en**: nenhum problema detectado
- **fr->en**: nenhum problema detectado
- **de->en**: transcrição ruim: 25% das palavras erradas
- **it->en**: nenhum problema detectado
- **ru->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **zh->en**: transcrição ruim: 22% dos caracteres erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 6 caracteres seguidas); inventou 5 caracteres que não foram faladas
- **nl->en**: nenhum problema detectado
- **pl->en**: nenhum problema detectado
- **uk->en**: nenhum problema detectado
- **tr->en**: nenhum problema detectado
- **ar->en**: nenhum problema detectado
- **hi->en**: transcrição ruim: 31% das palavras erradas
- **ja->en**: nenhum problema detectado
- **ko->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.7 s

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
