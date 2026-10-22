_Máquina: macOS-26.6.2-x86_64-i386-64bit · processador i386 · Python 3.12.15 · placa de vídeo CUDA: não_

Whisper `small` em processador · eco no alto-falante da pessoa A: sem eco · tratamento de eco: **nada** · sobreposição dos turnos: 0%

| Conversa | Erro A (fala da pessoa A) | Erro B | Fidelidade A→B | Fidelidade B→A | Espera do ouvinte A→B | Espera B→A | Eco: palavras falsas mandadas a B |
|---|---:|---:|---:|---:|---:|---:|---:|
| pt<->en | 11.0% | 0.8% | 66.9 | 72.0 | 0.11 s | 0.0 s | 0 |
| pt<->es | 11.0% | 2.2% | 70.0 | 58.1 | 0.13 s | 0.0 s | 0 |
| pt<->fr | 11.0% | 32.3% | 60.8 | 47.0 | 0.09 s | 0.29 s | 0 |
| pt<->de | 11.0% | 20.8% | 57.1 | 49.8 | 0.67 s | 1.84 s | 0 |
| pt<->it | 11.0% | 28.1% | 61.3 | 47.6 | 0.14 s | 0.18 s | 0 |
| pt<->ru | 11.0% | 17.1% | 47.0 | 63.0 | 0.17 s | 0.0 s | 0 |
| pt<->zh | 11.0% | 20.4% | 37.8 | 36.4 | 0.27 s | 0.0 s | 0 |
| pt<->nl | 11.0% | 20.8% | 57.5 | 45.2 | 0.41 s | 0.0 s | 0 |
| pt<->pl | 11.0% | 18.0% | 64.5 | 49.0 | 0.14 s | 0.0 s | 0 |
| pt<->uk | 11.0% | 11.6% | 45.1 | 76.7 | 0.74 s | 0.0 s | 0 |
| pt<->tr | 11.0% | 34.3% | 54.1 | 49.4 | 0.64 s | 0.0 s | 0 |
| pt<->ar | 11.0% | 44.4% | 56.7 | 53.9 | 0.0 s | 0.83 s | 0 |
| pt<->hi | 11.0% | 103.1% | 49.2 | 26.2 | 0.25 s | 2.2 s | 0 |
| pt<->ja | 11.0% | 16.5% | 35.3 | 44.4 | 0.0 s | 0.0 s | 0 |
| pt<->ko | 11.0% | 6.4% | 23.5 | 46.2 | 0.36 s | 0.0 s | 0 |
| **média** | 11.0% | 25.1% | | | | | 0 |

Erro = parcela das palavras (letras em zh/ja/ko) transcritas errado, puladas ou inventadas. Fidelidade (0–100) compara a tradução do que foi ouvido com a tradução do texto real. Espera do ouvinte = do fim da fala até o começo da tradução (mediana). Eco = palavras transcritas no microfone da pessoa A quando ela não estava falando.