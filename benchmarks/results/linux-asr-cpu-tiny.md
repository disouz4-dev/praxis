_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · 16 cores · Python 3.12.3 · CUDA True_

| Model | Backend | Lang | Clips | Speakers | Audio | WER full | WER live | CER live | RTF |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| tiny | cpu | pt | 10 | 10 | 111s | 34.9% | 44.2% | 16.9% | 0.03 |
| tiny | cpu | en | 12 | 12 | 83s | 8.2% | 7.8% | 4.2% | 0.04 |
| tiny | cpu | es | 12 | 12 | 130s | 21.3% | 23.2% | 6.8% | 0.03 |

WER full = whole utterance in one call · WER live = streamed through the engine's VAD (cuts at silence or every 6s) · RTF = ASR time / audio time (lower is faster).

### Worst live transcriptions

- `pt_000701.wav` WER 89%
  - ref: uns aborrecem as laranjas outros aborrecem os amores agora se o aborrecimento vem por causa das cascas não sei o que é certo é que é assim é ferino disse emília olhando para adelaide ferino eu
  - hyp: Ust! A borxasinas larantes. Ou que o borxas não é um bordo. Agora, sua borxas se mantivem por causa das cascas, você. Ok, certo. Aqui é assim. Descerindo de sebinha olhando para a deláter. Serindo é o.
- `es_000135.wav` WER 65%
  - ref: vivía ya con ellos harville había alquilado aquella casa por medio año pues sus gustos su salud y sus medios
  - hyp: Vivía ya con ellos. Harvard lo había al que he dado a que ella casa por medio año. pues esos gustos sus salud, esos medios.
- `pt_000796.wav` WER 61%
  - ref: a soberba não perdoa a humildade não se vinga homens aprendei a vencer-vos e triunfareis de todos
  - hyp: A soberbana perdova. A Unmildade não se vinga. Ormes. Aprendeia-vincervos. E treinho faria isso de todos.
- `pt_000271.wav` WER 59%
  - ref: e todavia nada parece mais injustificado que uma tal apoteose lord beaconsfield por fim foi um homem de estado que fez romances
  - hyp: E toda a viê! Nada parece mais injustificado que uma tal poteosa. Lá de beconjude por fim. e não é uma menistadra que fez româncias.
- `es_000007.wav` WER 45%
  - ref: tú has muerto en mansedumbre tú con dulzura entregándote á mí en la suprema sumisión de la vida pero él
  - hyp: Tu asmarto en manse dumbre. tú conduzuras. entregándote a mí en la supremas sumisión de la vida. Pero él?
