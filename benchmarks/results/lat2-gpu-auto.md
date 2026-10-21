_Máquina: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · processador x86_64 · 16 núcleos · Python 3.12.3 · placa de vídeo CUDA: sim_

Modelo Whisper: `auto` · roda em: placa de vídeo (CUDA)

| Par | Gravações | Espera pelo silêncio | Transcrição | Tradução | Voz (1ª frase) | **Total, atraso típico** | **Total, pior caso comum (1 em 20)** |
|---|---:|---:|---:|---:|---:|---:|---:|
| pt->en | 15 | 288 | 396 | 59 | 261 | **1003 ms** | **1166 ms** |
| en->pt | 15 | 288 | 327 | 132 | 306 | **1049 ms** | **1248 ms** |
| es->en | 15 | 256 | 396 | 71 | 265 | **1004 ms** | **1202 ms** |
| en->es | 15 | 288 | 311 | 138 | 296 | **1048 ms** | **1247 ms** |
| de->en | 15 | 288 | 414 | 95 | 296 | **1103 ms** | **1171 ms** |
| en->de | 15 | 288 | 308 | 139 | 411 | **1235 ms** | **1555 ms** |
| fr->en | 15 | 288 | 262 | 78 | 273 | **892 ms** | **1108 ms** |
| it->en | 15 | 288 | 416 | 88 | 293 | **1072 ms** | **1165 ms** |

Valores por etapa em ms, atraso típico (mediana: metade das gravações é mais rápida). Pior caso comum = 1 em cada 20 gravações demora mais que isso. Espera pelo silêncio = quanto o detector de fala aguarda para ter certeza de que a frase acabou. Total = do fim da fala até a primeira amostra de áudio traduzido pronta (início da reprodução).
