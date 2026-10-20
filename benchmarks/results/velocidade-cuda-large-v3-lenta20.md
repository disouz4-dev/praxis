_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · Python 3.12.3 · placa de vídeo CUDA: sim_

Whisper `large-v3` rodando em: placa de vídeo (CUDA) — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 9.1% palavras | 1.5% | 72.9 | 1.1 s | 1.4 s | +0.2 s | 2.3 s | 51% | ✅ |
| en->pt | 19s | 0.0% palavras | 0.0% | 90.5 | 2.0 s | 2.1 s | +0.9 s | 3.4 s | 66% | ✅ |
| es->en | 16s | 3.9% palavras | 1.0% | 81.5 | 1.1 s | 1.2 s | -0.1 s | 2.8 s | 46% | ✅ |
| fr->en | 19s | 2.5% palavras | 1.2% | 70.5 | 1.1 s | 1.3 s | +0.2 s | 3.5 s | 49% | ✅ |
| de->en | 19s | 12.5% palavras | 8.0% | 53.1 | 1.0 s | 3.0 s | +0.4 s | 2.9 s | 39% | ✅ |
| it->en | 21s | 13.5% palavras | 3.0% | 61.1 | 1.1 s | 1.5 s | +0.2 s | 2.2 s | 62% | ✅ |
| ru->en | 22s | 4.8% palavras | 1.5% | 54.6 | 2.1 s | 4.0 s | -1.7 s | 0.1 s | 44% | ✅ |
| zh->en | 20s | 12.0% caracteres | 12.0% | 49.0 | 1.8 s | 2.8 s | +0.6 s | 3.7 s | 70% | ✅ |
| nl->en | 20s | 11.1% palavras | 11.4% | 72.2 | 0.8 s | 1.0 s | +0.0 s | 4.3 s | 44% | ✅ |
| pl->en | 21s | 13.5% palavras | 4.3% | 52.6 | 1.4 s | 1.6 s | -0.4 s | 3.4 s | 64% | ✅ |
| uk->en | 20s | 8.3% palavras | 2.7% | 63.5 | 1.9 s | 3.1 s | +1.6 s | 1.6 s | 39% | ❌ |
| tr->en | 19s | 19.1% palavras | 9.6% | 45.2 | 1.3 s | 2.0 s | -0.9 s | 0.0 s | 36% | ✅ |
| ar->en | 20s | 6.9% palavras | 10.9% | 75.3 | 2.1 s | 2.5 s | +0.2 s | 2.1 s | 50% | ✅ |
| hi->en | 20s | 55.2% palavras | 20.0% | 15.9 | 1.1 s | 1.5 s | +0.3 s | 0.6 s | 38% | ✅ |
| ja->en | 19s | 30.4% caracteres | 30.4% | 43.1 | 1.1 s | 1.3 s | -0.2 s | 0.0 s | 28% | ✅ |
| ko->en | 17s | 0.0% caracteres | 0.0% | 49.9 | 3.0 s | 4.3 s | -1.0 s | 1.9 s | 42% | ✅ |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 632 ms | 22 ms | 50 ms | 0 ms |
| en->pt | 0 ms | 611 ms | 22 ms | 86 ms | 0 ms |
| es->en | 0 ms | 573 ms | 21 ms | 38 ms | 0 ms |
| fr->en | 0 ms | 635 ms | 18 ms | 49 ms | 0 ms |
| de->en | 0 ms | 568 ms | 17 ms | 25 ms | 0 ms |
| it->en | 0 ms | 616 ms | 17 ms | 46 ms | 0 ms |
| ru->en | 0 ms | 662 ms | 18 ms | 59 ms | 0 ms |
| zh->en | 0 ms | 781 ms | 25 ms | 92 ms | 0 ms |
| nl->en | 0 ms | 589 ms | 15 ms | 45 ms | 0 ms |
| pl->en | 0 ms | 659 ms | 25 ms | 67 ms | 0 ms |
| uk->en | 0 ms | 708 ms | 19 ms | 47 ms | 128 ms |
| tr->en | 0 ms | 629 ms | 18 ms | 54 ms | 0 ms |
| ar->en | 0 ms | 745 ms | 17 ms | 53 ms | 324 ms |
| hi->en | 0 ms | 636 ms | 9 ms | 26 ms | 0 ms |
| ja->en | 0 ms | 643 ms | 22 ms | 54 ms | 0 ms |
| ko->en | 0 ms | 635 ms | 22 ms | 56 ms | 0 ms |

### Problemas encontrados

- **pt->en**: nenhum problema detectado
- **en->pt**: nenhum problema detectado
- **es->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **fr->en**: nenhum problema detectado
- **de->en**: nenhum problema detectado
- **it->en**: nenhum problema detectado
- **ru->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.0 s
- **zh->en**: nenhum problema detectado
- **nl->en**: 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa; 1 trecho(s) com fala viraram texto vazio
- **pl->en**: nenhum problema detectado
- **uk->en**: não acompanha o falante: atraso típico 1.9 s, sobe +1.6 s da 1ª para a 2ª metade e sobram 2 s de tradução quando ele para; 1 trecho(s) cortado(s) no meio por excesso de duração sem pausa
- **tr->en**: nenhum problema detectado
- **ar->en**: nenhum problema detectado
- **hi->en**: transcrição ruim: 55% das palavras erradas
- **ja->en**: transcrição ruim: 30% dos caracteres erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 14 caracteres seguidas)
- **ko->en**: picos de atraso: 1 em cada 20 trechos demora mais de 4.3 s

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
