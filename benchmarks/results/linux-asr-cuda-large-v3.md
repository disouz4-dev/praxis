_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · 16 cores · Python 3.12.3 · CUDA True_

| Model | Backend | Lang | Clips | Speakers | Audio | WER full | WER live | CER live | RTF |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| large-v3 | cuda | pt | 10 | 10 | 111s | 4.3% | 8.9% | 4.9% | 0.08 |
| large-v3 | cuda | en | 12 | 12 | 83s | 1.5% | 6.8% | 5.3% | 0.10 |
| large-v3 | cuda | es | 12 | 12 | 130s | 3.1% | 3.8% | 1.3% | 0.08 |

WER full = whole utterance in one call · WER live = streamed through the engine's VAD (cuts at silence or every 6s) · RTF = ASR time / audio time (lower is faster).

### Worst live transcriptions

- `pt_000271.wav` WER 50%
  - ref: e todavia nada parece mais injustificado que uma tal apoteose lord beaconsfield por fim foi um homem de estado que fez romances
  - hyp: E, todavia, Nada parece mais injustificado que uma tal apoteose. Lord Beaconsfield, por fim, foi o primeiro a ser o primeiro a ser o primeiro Foi um homem de Estado que fez romances.
- `en_000288.wav` WER 44%
  - ref: FOOTNOTE SUMNER TO SHANNON MAY TWELFTH EIGHTEEN FIFTY SIX
  - hyp: Footnote. Sumner to Shannon. May 12, 1856.
- `en_000576.wav` WER 33%
  - ref: METER ROUGHLY ONE YARD THREE INCHES
  - hyp: meter roughly 1 yard 3 inches
- `en_000216.wav` WER 31%
  - ref: THESE THOUGHTS AGITATED ME ALL DAY AND MY IMAGINATION SCARCELY CALMED DOWN AFTER SEVERAL HOURS SLEEP
  - hyp: These thoughts agitated me all day, and my imagination scarcely calmed down after a few minutes of sleep. several hours sleep.
- `pt_000103.wav` WER 13%
  - ref: qual é a verdadeira moeda que nos domina onde o nosso ouro para que serve o nosso miserável papel senão para comprar a libra inglesa onde está a nossa fortuna pública
  - hyp: Qual é a verdadeira moeda que nos domina? Onde nosso louro? Para que serve o nosso miserável papel se não para comprar a Libra inglesa? Onde está a nossa fortuna pública?
