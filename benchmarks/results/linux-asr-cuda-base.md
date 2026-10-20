_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · 16 cores · Python 3.12.3 · CUDA True_

| Model | Backend | Lang | Clips | Speakers | Audio | WER full | WER live | CER live | RTF |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| base | cuda | pt | 10 | 10 | 111s | 30.2% | 26.7% | 8.8% | 0.01 |
| base | cuda | en | 12 | 12 | 83s | 5.8% | 5.8% | 3.7% | 0.01 |
| base | cuda | es | 12 | 12 | 130s | 10.7% | 16.6% | 4.8% | 0.01 |

WER full = whole utterance in one call · WER live = streamed through the engine's VAD (cuts at silence or every 6s) · RTF = ASR time / audio time (lower is faster).

### Worst live transcriptions

- `es_000135.wav` WER 65%
  - ref: vivía ya con ellos harville había alquilado aquella casa por medio año pues sus gustos su salud y sus medios
  - hyp: ¡Ve vi a ya con ellos! Harvo Lavia, alquiliado, a que ia caça por medio año. Pues sus gustos, sus salud, esos medios.
- `pt_000701.wav` WER 53%
  - ref: uns aborrecem as laranjas outros aborrecem os amores agora se o aborrecimento vem por causa das cascas não sei o que é certo é que é assim é ferino disse emília olhando para adelaide ferino eu
  - hyp: O que? Aborrecem as larantes. Outros aborrecemos amores. Agora, seu aborrecimento vem por causa das cascas não sei. Ok, certo? É que é assim. Diferindo, de semia, olhando para a deláida. Ferenino é o...
- `pt_000600.wav` WER 48%
  - ref: continuamente vemos novidades diferentes em tudo da esperança do mal ficam as mágoas na lembrança e do bem se algum houve as saudades
  - hyp: Continuamente vemos novidades diferentes em tudo da esperança. do mal ficou as mágmas na lembrança. E do bem. o que é o que é o que assoludes.
- `en_000288.wav` WER 44%
  - ref: FOOTNOTE SUMNER TO SHANNON MAY TWELFTH EIGHTEEN FIFTY SIX
  - hyp: Footnote Sumner to Shannon. May 12, 1856.
- `pt_000271.wav` WER 36%
  - ref: e todavia nada parece mais injustificado que uma tal apoteose lord beaconsfield por fim foi um homem de estado que fez romances
  - hyp: e toda vez... Nada parece mais injustificado que o Matal Poteuase. Lord Beconsfield, por fim... foi o homem de estado que fez româncias.
