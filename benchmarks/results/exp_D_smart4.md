_Machine: macOS-26.6.2-x86_64-i386-64bit · i386 · 16 cores · Python 3.12.15 · CUDA False_

| Model | Lang | Clips | Speakers | Audio | WER full | WER live | CER live | RTF |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| small | pt | 10 | 10 | 111s | 15.5% | 20.5% | 9.4% | 0.17 |
| small | en | 12 | 12 | 83s | 3.9% | 7.8% | 5.2% | 0.24 |
| small | es | 12 | 12 | 130s | 11.0% | 12.8% | 7.8% | 0.17 |

WER full = whole utterance in one call · WER live = streamed through the engine's VAD (cuts at silence or every 4s) · RTF = ASR time / audio time (lower is faster).

### Worst live transcriptions

- `es_000135.wav` WER 80%
  - ref: vivía ya con ellos harville había alquilado aquella casa por medio año pues sus gustos su salud y sus medios
  - hyp: vivía ya con ellos. ¡Hárvola vía al que ya doa queia!
- `pt_000701.wav` WER 58%
  - ref: uns aborrecem as laranjas outros aborrecem os amores agora se o aborrecimento vem por causa das cascas não sei o que é certo é que é assim é ferino disse emília olhando para adelaide ferino eu
  - hyp: OUCH Aborrassem as laranas, outros aborrassem os amores. Agora, o seu aburrecimento vem por causa das claras que eu não sei. Ok certo, é que é assim. De ferrino, de semilha olhando para the light Ferrino é eu?
- `en_000288.wav` WER 44%
  - ref: FOOTNOTE SUMNER TO SHANNON MAY TWELFTH EIGHTEEN FIFTY SIX
  - hyp: footnote Sumner to Shannon. May 12, 1856.
- `en_000576.wav` WER 33%
  - ref: METER ROUGHLY ONE YARD THREE INCHES
  - hyp: meter, roughly 1 yard, 3 inches.
- `pt_000600.wav` WER 30%
  - ref: continuamente vemos novidades diferentes em tudo da esperança do mal ficam as mágoas na lembrança e do bem se algum houve as saudades
  - hyp: Continuamente vemos novidades diferentes em tudo da esp... até a próxima. do mal ficou as mágoas na lembrança. E do bem! Se algum ouve? A saudades.
