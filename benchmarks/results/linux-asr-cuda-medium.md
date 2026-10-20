_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · 16 cores · Python 3.12.3 · CUDA True_

| Model | Backend | Lang | Clips | Speakers | Audio | WER full | WER live | CER live | RTF |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| medium | cuda | pt | 10 | 10 | 111s | 10.8% | 12.8% | 4.6% | 0.05 |
| medium | cuda | en | 12 | 12 | 83s | 4.4% | 3.9% | 2.8% | 0.06 |
| medium | cuda | es | 12 | 12 | 130s | 2.8% | 6.0% | 1.8% | 0.05 |

WER full = whole utterance in one call · WER live = streamed through the engine's VAD (cuts at silence or every 6s) · RTF = ASR time / audio time (lower is faster).

### Worst live transcriptions

- `en_000288.wav` WER 44%
  - ref: FOOTNOTE SUMNER TO SHANNON MAY TWELFTH EIGHTEEN FIFTY SIX
  - hyp: Footnote Sumner to Shannon. May 12, 1856.
- `pt_000271.wav` WER 36%
  - ref: e todavia nada parece mais injustificado que uma tal apoteose lord beaconsfield por fim foi um homem de estado que fez romances
  - hyp: E, todavia... Nada parece mais injustificado que matar o proteose. Lá o Lá o Lá foi um homem de estado que fez romances.
- `pt_000529.wav` WER 17%
  - ref: dentro da casa em que nasceste és tudo como tudo é feliz no fim do dia quando voltas das aulas e do estudo volta quando tu voltas a alegria
  - hyp: dentro da casa em que nasce. É estudo. como tudo é feliz no fim do dia. quando volta das aulas e do estudo. Volta quando tu voltas à alegria.
- `es_000468.wav` WER 17%
  - ref: y en un instante quedaron enteradas de quiénes eran don quijote y su escudero de que no poco contento recibieron porque ya tenían de él noticia por su historia
  - hyp: Y en un instante quedaron enteradas de quienes eran Don Quijote y su escudero. de que no pocos contentos recibieron porque ya tenían del noticia por su historia.
- `pt_000796.wav` WER 17%
  - ref: a soberba não perdoa a humildade não se vinga homens aprendei a vencer-vos e triunfareis de todos
  - hyp: A soberba não perdoa. A humildade não se vinga. Omens. Aprendei a vencermos. e triunfareis de todos.
