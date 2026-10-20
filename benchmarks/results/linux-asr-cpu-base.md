_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · 16 cores · Python 3.12.3 · CUDA True_

| Model | Backend | Lang | Clips | Speakers | Audio | WER full | WER live | CER live | RTF |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| base | cpu | pt | 10 | 10 | 111s | 29.5% | 27.5% | 9.4% | 0.05 |
| base | cpu | en | 12 | 12 | 83s | 5.8% | 6.3% | 4.0% | 0.07 |
| base | cpu | es | 12 | 12 | 130s | 11.6% | 15.7% | 4.4% | 0.05 |

WER full = whole utterance in one call · WER live = streamed through the engine's VAD (cuts at silence or every 6s) · RTF = ASR time / audio time (lower is faster).

### Worst live transcriptions

- `es_000135.wav` WER 65%
  - ref: vivía ya con ellos harville había alquilado aquella casa por medio año pues sus gustos su salud y sus medios
  - hyp: ¡Ve vi a ya con ellos! Harvo Lavia, alquiliado, a que ia caça por medio año. Pues sus gustos, sus salud, esos medios.
- `en_000288.wav` WER 56%
  - ref: FOOTNOTE SUMNER TO SHANNON MAY TWELFTH EIGHTEEN FIFTY SIX
  - hyp: Footnote Summary to Shannon. May 12, 1856.
- `pt_000701.wav` WER 53%
  - ref: uns aborrecem as laranjas outros aborrecem os amores agora se o aborrecimento vem por causa das cascas não sei o que é certo é que é assim é ferino disse emília olhando para adelaide ferino eu
  - hyp: Aborrecem as larantes, outros aborrecemos amores. Agora sua aborrecimento vem por causa das cascas não sei. ok, certo? aqui é assim Diferindo, disse a filha olhando para a delácia. Ferenino é eu.
- `pt_000600.wav` WER 48%
  - ref: continuamente vemos novidades diferentes em tudo da esperança do mal ficam as mágoas na lembrança e do bem se algum houve as saudades
  - hyp: Continuamente vemos novidades diferentes em tudo da esperança. do mal ficou as mágmas na lembrança. e do bem. O que é o que é o que assoludes.
- `pt_000529.wav` WER 38%
  - ref: dentro da casa em que nasceste és tudo como tudo é feliz no fim do dia quando voltas das aulas e do estudo volta quando tu voltas a alegria
  - hyp: dentro da casa em que nasce, é estudo! com toda feliz no fim do dia. quando volta da exámasa do estudo. volta quando tu volta a alegria
