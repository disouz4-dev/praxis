_Máquina: macOS-26.6.2-x86_64-i386-64bit · processador i386 · Python 3.12.15 · placa de vídeo CUDA: não_

Whisper `small` rodando em: processador — ~1 min de fala real contínua por par, entregue em tempo real

| Par | Fala | Taxa de erro | Erro por letra | Fidelidade da tradução (0–100) | Atraso típico | Pior caso comum (1 em 20) | Crescimento do atraso (2ª vs 1ª metade) | Tradução pendente quando o falante para | Fala traduzida / original | Acompanha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| pt->en | 19s | 39.5% palavras | 36.4% | 51.8 | 2.2 s | 2.2 s | +0.0 s | 3.5 s | 44% | ❌ |
| en->pt | 20s | 33.3% palavras | 27.3% | 61.3 | 2.7 s | 2.7 s | +0.0 s | 6.4 s | 58% | ❌ |
| es->en | 21s | 53.3% palavras | 48.4% | 30.2 | 2.0 s | 2.0 s | +0.0 s | 0.0 s | 37% | ❌ |
| fr->en | 21s | 62.5% palavras | 48.2% | 35.9 | 2.7 s | 2.7 s | +0.0 s | 1.3 s | 50% | ❌ |

### Eco (a tradução tocada volta pelo microfone)

| Par | Trechos traduzidos depois que o falante parou | Palavras nesses trechos |
|---|---:|---:|
| pt->en | 0 | 0 |
| en->pt | 0 | 0 |
| es->en | 0 | 0 |
| fr->en | 0 | 0 |

### Para onde vai o tempo (típico, por trecho)

| Par | Espera na fila | Transcrição | Tradução | Voz (1ª frase) | Espera pela fala anterior |
|---|---:|---:|---:|---:|---:|
| pt->en | 0 ms | 1365 ms | 40 ms | 95 ms | 514 ms |
| en->pt | 0 ms | 1512 ms | 83 ms | 193 ms | 1 ms |
| es->en | 0 ms | 1387 ms | 80 ms | 66 ms | 0 ms |
| fr->en | 0 ms | 1462 ms | 55 ms | 77 ms | 0 ms |

### Problemas encontrados

- **pt->en**: transcrição ruim: 40% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 8 palavras seguidas); não acompanha o falante: atraso típico 2.2 s, sobe +0.0 s da 1ª para a 2ª metade e sobram 4 s de tradução quando ele para; 1 trecho(s) com fala viraram texto vazio
- **en->pt**: transcrição ruim: 33% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 17 palavras seguidas); não acompanha o falante: atraso típico 2.7 s, sobe +0.0 s da 1ª para a 2ª metade e sobram 6 s de tradução quando ele para
- **es->en**: transcrição ruim: 53% das palavras erradas; pulou 2 trecho(s) inteiro(s) da fala (maior: 8 palavras seguidas); não acompanha o falante: atraso típico 2.0 s, sobe +0.0 s da 1ª para a 2ª metade e sobram 0 s de tradução quando ele para; 1 trecho(s) com fala viraram texto vazio
- **fr->en**: transcrição ruim: 62% das palavras erradas; pulou 1 trecho(s) inteiro(s) da fala (maior: 22 palavras seguidas); não acompanha o falante: atraso típico 2.7 s, sobe +0.0 s da 1ª para a 2ª metade e sobram 1 s de tradução quando ele para

Taxa de erro = parcela das palavras (caracteres em zh/ja) transcritas errado, puladas ou inventadas. Fidelidade da tradução (0–100) compara a tradução do que foi ouvido com a tradução do texto real; 100 = idênticas. Atraso = do fim de um trecho de fala até o primeiro áudio traduzido; atraso típico = mediana (metade dos trechos é mais rápida); pior caso comum = 1 em cada 20 trechos demora mais que isso. Crescimento do atraso ≈ 0 significa que acompanha o ritmo.
