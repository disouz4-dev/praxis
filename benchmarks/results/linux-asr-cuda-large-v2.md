_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · 16 cores · Python 3.12.3 · CUDA True_

| Model | Backend | Lang | Clips | Speakers | Audio | WER full | WER live | CER live | RTF |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| large-v2 | cuda | pt | 10 | 10 | 111s | 2.7% | 10.1% | 4.0% | 0.09 |
| large-v2 | cuda | en | 12 | 12 | 83s | 4.4% | 4.9% | 4.6% | 0.10 |
| large-v2 | cuda | es | 12 | 12 | 130s | 2.2% | 4.7% | 2.7% | 0.09 |

WER full = whole utterance in one call · WER live = streamed through the engine's VAD (cuts at silence or every 6s) · RTF = ASR time / audio time (lower is faster).

### Worst live transcriptions

- `en_000288.wav` WER 44%
  - ref: FOOTNOTE SUMNER TO SHANNON MAY TWELFTH EIGHTEEN FIFTY SIX
  - hyp: footnote. Sumner to Shannon. May 12, 1856.
- `en_000576.wav` WER 33%
  - ref: METER ROUGHLY ONE YARD THREE INCHES
  - hyp: meter, roughly 1 yard 3 inches.
- `es_001194.wav` WER 25%
  - ref: y siendo esto ansí antes quedaremos confusos que informados puesto que podamos usar del mismo artificio que sospechamos dándola al religioso por tercera persona
  - hyp: Y siendo esto así, antes quedaremos confusos que informados. del mismo artificio que sospechamos, dándolo al religioso por tercera persona.
- `pt_000796.wav` WER 22%
  - ref: a soberba não perdoa a humildade não se vinga homens aprendei a vencer-vos e triunfareis de todos
  - hyp: A soberba não perdoa. A humildade não se minga. HOMENS Aprendem a vencermos! E triunfareis de todos!
- `pt_000600.wav` WER 17%
  - ref: continuamente vemos novidades diferentes em tudo da esperança do mal ficam as mágoas na lembrança e do bem se algum houve as saudades
  - hyp: Continuamente vemos novidades, diferentes em tudo da esperança. Do mal ficam as mágoas na lembrança. Se algum houve. Há saudades.
