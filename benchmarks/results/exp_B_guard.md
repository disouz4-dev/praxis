_Machine: macOS-26.6.2-x86_64-i386-64bit · i386 · 16 cores · Python 3.12.15 · CUDA False_

| Model | Lang | Clips | Speakers | Audio | WER full | WER live | CER live | RTF |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| small | pt | 10 | 10 | 111s | 15.5% | 24.0% | 8.5% | 0.17 |
| small | en | 12 | 12 | 83s | 3.9% | 7.3% | 5.6% | 0.23 |
| small | es | 12 | 12 | 130s | 11.0% | 14.1% | 7.6% | 0.19 |

WER full = whole utterance in one call · WER live = streamed through the engine's VAD (cuts at silence or every 4s) · RTF = ASR time / audio time (lower is faster).

### Worst live transcriptions

- `es_000135.wav` WER 70%
  - ref: vivía ya con ellos harville había alquilado aquella casa por medio año pues sus gustos su salud y sus medios
  - hyp: Vivía ya con ellos. Arvola vía al que yado aquella casa por medio...
- `en_000288.wav` WER 44%
  - ref: FOOTNOTE SUMNER TO SHANNON MAY TWELFTH EIGHTEEN FIFTY SIX
  - hyp: footnote. Sumner to Shannon. May 12, 1856.
- `pt_000701.wav` WER 42%
  - ref: uns aborrecem as laranjas outros aborrecem os amores agora se o aborrecimento vem por causa das cascas não sei o que é certo é que é assim é ferino disse emília olhando para adelaide ferino eu
  - hyp: aborrassem as laranas, outros aborrassem os amores. Agora é o seu aborrecimento. que vem por causa das claras coisas, não sei. O que é certo é que é assim. Ferino, de semilha olhando para de lá Ferino, é eu?
- `pt_000796.wav` WER 39%
  - ref: a soberba não perdoa a humildade não se vinga homens aprendei a vencer-vos e triunfareis de todos
  - hyp: a soberba não perdoa. humildade não se vinga. com os homens. aprendeu a vencer-vos. entre um fareis de todos.
- `en_000576.wav` WER 33%
  - ref: METER ROUGHLY ONE YARD THREE INCHES
  - hyp: meter roughly 1 yard 3 inches.
