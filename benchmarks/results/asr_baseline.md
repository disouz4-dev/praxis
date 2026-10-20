_Machine: macOS-26.6.2-x86_64-i386-64bit · i386 · 16 cores · Python 3.12.15 · CUDA False_

| Model | Lang | Clips | Speakers | Audio | WER full | WER live | CER live | RTF |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| base | pt | 10 | 10 | 111s | 28.7% | 120.9% | 55.9% | 0.06 |
| base | en | 12 | 12 | 83s | 5.8% | 10.7% | 8.4% | 0.08 |
| base | es | 12 | 12 | 130s | 11.0% | 93.4% | 49.6% | 0.06 |
| small | pt | 10 | 10 | 111s | 15.5% | 26.4% | 11.7% | 0.18 |
| small | en | 12 | 12 | 83s | 3.9% | 8.7% | 6.7% | 0.23 |
| small | es | 12 | 12 | 130s | 11.0% | 13.8% | 7.0% | 0.18 |

WER full = whole utterance in one call · WER live = streamed through the engine's VAD (cuts at silence or every 4s) · RTF = ASR time / audio time (lower is faster).

### Worst live transcriptions

- `pt_000600.wav` WER 991%
  - ref: continuamente vemos novidades diferentes em tudo da esperança do mal ficam as mágoas na lembrança e do bem se algum houve as saudades
  - hyp: Continuamente vemos novidades diferentes em tudo da esperança. do mal ficou as magas na lembrança. e do bem. O que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que é o que Assol d'AIDS
- `es_000925.wav` WER 706%
  - ref: luego roma fue dueña de todos los países que tenía alrededor hasta que tuvo tantos pueblos que no los pudo gobernar y cada pueblo se fue haciendo libre y nombrando su rey
  - hyp: Luego Roma fue dueña de todos los países que tenía alrededor. hasta que tuvo tantos pelos que no los pudo gornar. la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de la de
- `es_000135.wav` WER 85%
  - ref: vivía ya con ellos harville había alquilado aquella casa por medio año pues sus gustos su salud y sus medios
  - hyp: ¡Vive ya con ellos! Carvo la via alquiliado, a que ia caça por merio.
- `es_000135.wav` WER 70%
  - ref: vivía ya con ellos harville había alquilado aquella casa por medio año pues sus gustos su salud y sus medios
  - hyp: Vivía ya con ellos. Arvola vía al que yado aquella casa por medio...
- `pt_000701.wav` WER 64%
  - ref: uns aborrecem as laranjas outros aborrecem os amores agora se o aborrecimento vem por causa das cascas não sei o que é certo é que é assim é ferino disse emília olhando para adelaide ferino eu
  - hyp: Aborrece-nos as larantes. Outros aborrecemos amoros. Agora sou aborrecimento. E o que é certo é que é assim. de semia olhando para a deláida. Serrinho é eu.
