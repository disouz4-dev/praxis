_Máquina: macOS-26.6.2-x86_64-i386-64bit · processador i386 · Python 3.12.15 · placa de vídeo CUDA: não_

Whisper `small` em processador · eco no alto-falante da pessoa A: -12 dB · tratamento de eco: **cancelar** · sobreposição dos turnos: 50%

| Conversa | Erro A (fala da pessoa A) | Erro B | Fidelidade A→B | Fidelidade B→A | Espera do ouvinte A→B | Espera B→A | Eco: palavras falsas mandadas a B |
|---|---:|---:|---:|---:|---:|---:|---:|
| pt<->en | 21.9% | 0.8% | 63.4 | 72.0 | 0.12 s | 0.0 s | 3 |
| pt<->es | 11.0% | 2.2% | 70.0 | 58.1 | 0.19 s | 0.0 s | 2 |
| pt<->fr | 11.0% | 32.3% | 60.8 | 47.0 | 0.17 s | 0.36 s | 3 |
| pt<->de | 11.0% | 20.8% | 57.1 | 49.8 | 0.66 s | 1.82 s | 4 |
| pt<->it | 15.1% | 28.1% | 60.9 | 47.6 | 0.21 s | 0.28 s | 0 |
| pt<->ru | 11.0% | 22.9% | 47.0 | 63.0 | 0.2 s | 0.08 s | 2 |
| pt<->zh | 11.0% | 20.4% | 37.8 | 36.4 | 0.14 s | 0.0 s | 2 |
| pt<->nl | 11.0% | 20.8% | 57.5 | 45.2 | 0.28 s | 0.0 s | 3 |
| pt<->pl | 12.3% | 18.0% | 64.6 | 49.0 | 0.14 s | 0.0 s | 3 |
| pt<->uk | 11.0% | 14.0% | 45.1 | 76.7 | 0.73 s | 0.0 s | 0 |
| **média** | 12.6% | 18.0% | | | | | 22 |

Erro = parcela das palavras (letras em zh/ja/ko) transcritas errado, puladas ou inventadas. Fidelidade (0–100) compara a tradução do que foi ouvido com a tradução do texto real. Espera do ouvinte = do fim da fala até o começo da tradução (mediana). Eco = palavras transcritas no microfone da pessoa A quando ela não estava falando.