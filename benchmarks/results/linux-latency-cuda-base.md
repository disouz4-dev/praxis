_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · 16 núcleos · Python 3.12.3 · placa de vídeo CUDA: sim_

Modelo Whisper: `base` · roda em: placa de vídeo (CUDA)

| Par | Gravações | Espera pelo silêncio | Transcrição | Tradução | Voz (1ª frase) | **Total, atraso típico** | **Total, pior caso comum (1 em 20)** |
|---|---:|---:|---:|---:|---:|---:|---:|
| pt->en | 10 | 288 | 56 | 27 | 47 | **399 ms** | **494 ms** |
| en->pt | 10 | 272 | 56 | 23 | 56 | **402 ms** | **484 ms** |
| es->en | 10 | 256 | 64 | 32 | 57 | **413 ms** | **487 ms** |

Valores por etapa em ms, atraso típico (mediana: metade das gravações é mais rápida). Pior caso comum = 1 em cada 20 gravações demora mais que isso. Espera pelo silêncio = quanto o detector de fala aguarda para ter certeza de que a frase acabou. Total = do fim da fala até a primeira amostra de áudio traduzido pronta (início da reprodução).
