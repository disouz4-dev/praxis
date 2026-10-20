_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · 16 núcleos · Python 3.12.3 · placa de vídeo CUDA: sim_

Modelo Whisper: `small` · roda em: processador

| Par | Gravações | Espera pelo silêncio | Transcrição | Tradução | Voz (1ª frase) | **Total, atraso típico** | **Total, pior caso comum (1 em 20)** |
|---|---:|---:|---:|---:|---:|---:|---:|
| pt->en | 10 | 288 | 1206 | 21 | 42 | **1532 ms** | **1778 ms** |
| en->pt | 10 | 272 | 1182 | 18 | 60 | **1553 ms** | **1607 ms** |
| es->en | 10 | 256 | 1252 | 31 | 52 | **1601 ms** | **1747 ms** |

Valores por etapa em ms, atraso típico (mediana: metade das gravações é mais rápida). Pior caso comum = 1 em cada 20 gravações demora mais que isso. Espera pelo silêncio = quanto o detector de fala aguarda para ter certeza de que a frase acabou. Total = do fim da fala até a primeira amostra de áudio traduzido pronta (início da reprodução).
