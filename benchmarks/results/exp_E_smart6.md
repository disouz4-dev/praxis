_Machine: macOS-26.6.2-x86_64-i386-64bit · i386 · 16 cores · Python 3.12.15 · CUDA False_

| Model | Backend | Lang | Clips | Speakers | Audio | WER full | WER live | CER live | RTF |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| small | cpu | pt | 10 | 10 | 111s | 15.5% | 16.7% | 5.6% | 0.16 |
| small | cpu | en | 12 | 12 | 83s | 3.9% | 5.3% | 4.3% | 0.23 |
| small | cpu | es | 12 | 12 | 130s | 11.0% | 6.9% | 1.9% | 0.16 |

WER full = whole utterance in one call · WER live = streamed through the engine's VAD (cuts at silence or every 4s) · RTF = ASR time / audio time (lower is faster).

### Worst live transcriptions

- `en_000288.wav` WER 44%
  - ref: FOOTNOTE SUMNER TO SHANNON MAY TWELFTH EIGHTEEN FIFTY SIX
  - hyp: footnote Sumner to Shannon. May 12, 1856.
- `pt_000701.wav` WER 42%
  - ref: uns aborrecem as laranjas outros aborrecem os amores agora se o aborrecimento vem por causa das cascas não sei o que é certo é que é assim é ferino disse emília olhando para adelaide ferino eu
  - hyp: OUCH Aborrecem as laranas, outros aborrecem os amores. Agora, o seu aborrecimento vem por causa das cascas, não sei. Ok certo, é que é assim. De ferrino, de semilha olhando para the light Ferrino é eu?
- `en_000576.wav` WER 33%
  - ref: METER ROUGHLY ONE YARD THREE INCHES
  - hyp: meter, roughly 1 yard, 3 inches.
- `es_000007.wav` WER 30%
  - ref: tú has muerto en mansedumbre tú con dulzura entregándote á mí en la suprema sumisión de la vida pero él
  - hyp: Tú has muerto en mansedumbre. tu condulsora. entregándote a mí en la suprema sumisión de la vida. ¡Vidóen!
- `pt_000529.wav` WER 28%
  - ref: dentro da casa em que nasceste és tudo como tudo é feliz no fim do dia quando voltas das aulas e do estudo volta quando tu voltas a alegria
  - hyp: dentro da casa em que nasce este estudo. Como tudo é feliz no fim do dia. quando volta às 11 do estudo. volta quando tu voltas à alegria.
