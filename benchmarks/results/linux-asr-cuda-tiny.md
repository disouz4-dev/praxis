_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · 16 cores · Python 3.12.3 · CUDA True_

| Model | Backend | Lang | Clips | Speakers | Audio | WER full | WER live | CER live | RTF |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| tiny | cuda | pt | 10 | 10 | 111s | 32.6% | 41.9% | 16.4% | 0.01 |
| tiny | cuda | en | 12 | 12 | 83s | 5.8% | 8.2% | 4.5% | 0.01 |
| tiny | cuda | es | 12 | 12 | 130s | 20.7% | 23.5% | 7.0% | 0.02 |

WER full = whole utterance in one call · WER live = streamed through the engine's VAD (cuts at silence or every 6s) · RTF = ASR time / audio time (lower is faster).

### Worst live transcriptions

- `pt_000701.wav` WER 78%
  - ref: uns aborrecem as laranjas outros aborrecem os amores agora se o aborrecimento vem por causa das cascas não sei o que é certo é que é assim é ferino disse emília olhando para adelaide ferino eu
  - hyp: A borxasinas larantes. Ou que o borxas não é morto? Agora, sua borxas se mantivem por causa das cascas, você? ok certo, aqui é assim E é ferino! Decebinha olhando para a deláctea. Ferino é o!
- `es_000135.wav` WER 65%
  - ref: vivía ya con ellos harville había alquilado aquella casa por medio año pues sus gustos su salud y sus medios
  - hyp: Vivía ya con ellos. Harvard lo había al que ya ado a que ella casa por medio año. pues esos gustos sus salud, esos medios.
- `pt_000103.wav` WER 58%
  - ref: qual é a verdadeira moeda que nos domina onde o nosso ouro para que serve o nosso miserável papel senão para comprar a libra inglesa onde está a nossa fortuna pública
  - hyp: com o evo de adilamo é daquilo domina onde nosso nome. Para que serve nosso miserável papel, se não para comprar ali brimbleza. onde está nosso portula pública.
- `pt_000796.wav` WER 56%
  - ref: a soberba não perdoa a humildade não se vinga homens aprendei a vencer-vos e triunfareis de todos
  - hyp: A soberba não perdova. A Unmildade não se vingue. Ormens. Aprendeia-vincernos. E treinho faria isso de todos.
- `es_000007.wav` WER 45%
  - ref: tú has muerto en mansedumbre tú con dulzura entregándote á mí en la suprema sumisión de la vida pero él
  - hyp: Tu asmarto en manse dumbre. tú conduzuras. entregándote a mí en la supremas sumisión de la vida. Pero él?
