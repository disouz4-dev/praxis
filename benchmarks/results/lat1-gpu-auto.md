_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · 16 núcleos · Python 3.12.3 · placa de vídeo CUDA: sim_

Modelo Whisper: `auto` · roda em: placa de vídeo (CUDA)

| Par | Gravações | Espera pelo silêncio | Transcrição | Tradução | Voz (1ª frase) | **Total, atraso típico** | **Total, pior caso comum (1 em 20)** |
|---|---:|---:|---:|---:|---:|---:|---:|
| pt->en | 15 | 288 | 396 | 59 | 278 | **1001 ms** | **1195 ms** |
| en->pt | 15 | 288 | 311 | 132 | 341 | **1138 ms** | **1306 ms** |
| es->en | 15 | 256 | 400 | 72 | 276 | **1011 ms** | **1197 ms** |
| en->es | 15 | 288 | 305 | 136 | 344 | **1110 ms** | **1271 ms** |
| de->en | 15 | 288 | 412 | 94 | 290 | **1086 ms** | **1167 ms** |
| en->de | 15 | 288 | 303 | 149 | 952 | **1805 ms** | **2276 ms** |
| fr->en | 15 | 288 | 265 | 81 | 288 | **932 ms** | **1153 ms** |
| it->en | 15 | 288 | 417 | 88 | 292 | **1071 ms** | **1178 ms** |

Valores por etapa em ms, atraso típico (mediana: metade das gravações é mais rápida). Pior caso comum = 1 em cada 20 gravações demora mais que isso. Espera pelo silêncio = quanto o detector de fala aguarda para ter certeza de que a frase acabou. Total = do fim da fala até a primeira amostra de áudio traduzido pronta (início da reprodução).
