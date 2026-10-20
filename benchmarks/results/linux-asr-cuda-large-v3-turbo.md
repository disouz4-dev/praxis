_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · 16 cores · Python 3.12.3 · CUDA True_

| Model | Backend | Lang | Clips | Speakers | Audio | WER full | WER live | CER live | RTF |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| large-v3-turbo | cuda | pt | 10 | 10 | 111s | 3.9% | 4.7% | 1.1% | 0.04 |
| large-v3-turbo | cuda | en | 12 | 12 | 83s | 3.9% | 5.3% | 4.8% | 0.06 |
| large-v3-turbo | cuda | es | 12 | 12 | 130s | 3.1% | 4.4% | 1.3% | 0.04 |

WER full = whole utterance in one call · WER live = streamed through the engine's VAD (cuts at silence or every 6s) · RTF = ASR time / audio time (lower is faster).

### Worst live transcriptions

- `en_000288.wav` WER 44%
  - ref: FOOTNOTE SUMNER TO SHANNON MAY TWELFTH EIGHTEEN FIFTY SIX
  - hyp: footnote. Sumner to Shannon May 12, 1856
- `en_000576.wav` WER 33%
  - ref: METER ROUGHLY ONE YARD THREE INCHES
  - hyp: meter roughly 1 yard 3 inches
- `en_000144.wav` WER 15%
  - ref: MEANWHILE RODOLFO HAD LEOCADIA SAFE IN HIS CUSTODY AND IN HIS OWN APARTMENT
  - hyp: Meanwhile, Rudolfo had Leuchedia safe in his custody. and in his own apartment.
- `pt_000103.wav` WER 13%
  - ref: qual é a verdadeira moeda que nos domina onde o nosso ouro para que serve o nosso miserável papel senão para comprar a libra inglesa onde está a nossa fortuna pública
  - hyp: Qual é a verdadeira moeda que nos domina? onde nosso ouro. Para que serve o nosso miserável papel se não para comprar a Libra Inglesa? Onde está nossa fortuna pública?
- `es_001194.wav` WER 12%
  - ref: y siendo esto ansí antes quedaremos confusos que informados puesto que podamos usar del mismo artificio que sospechamos dándola al religioso por tercera persona
  - hyp: Y siendo esto en sí, antes quedaremos confusos que informados. Puesto que podamos usar... del mismo artificio que sospechamos, dándolo al religioso por tercera persona.
