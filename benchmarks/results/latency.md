_Máquina: macOS-26.6.2-x86_64-i386-64bit · processador i386 · 16 núcleos · Python 3.12.15 · placa de vídeo CUDA: não_

Modelo Whisper: `small` · roda em: processador

| Par | Gravações | Espera pelo silêncio | Transcrição | Tradução | Voz (1ª frase) | **Total, atraso típico** | **Total, pior caso comum (1 em 20)** |
|---|---:|---:|---:|---:|---:|---:|---:|
| pt->en | 10 | 288 | 1666 | 56 | 110 | **2112 ms** | **2595 ms** |
| en->pt | 10 | 272 | 1392 | 48 | 92 | **1841 ms** | **1921 ms** |
| es->en | 10 | 256 | 1467 | 135 | 108 | **1962 ms** | **2182 ms** |

Valores por etapa em ms, atraso típico (mediana: metade das gravações é mais rápida). Pior caso comum = 1 em cada 20 gravações demora mais que isso. Espera pelo silêncio = quanto o detector de fala aguarda para ter certeza de que a frase acabou. Total = do fim da fala até a primeira amostra de áudio traduzido pronta (início da reprodução).
