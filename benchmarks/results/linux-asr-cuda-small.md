_Machine: Linux-7.0.0-31-generic-x86_64-with-glibc2.39 · x86_64 · 16 cores · Python 3.12.3 · CUDA True_

| Model | Backend | Lang | Clips | Speakers | Audio | WER full | WER live | CER live | RTF |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| small | cuda | pt | 10 | 10 | 111s | 14.7% | 17.1% | 6.5% | 0.02 |
| small | cuda | en | 12 | 12 | 83s | 2.9% | 4.4% | 3.6% | 0.02 |
| small | cuda | es | 12 | 12 | 130s | 5.6% | 6.6% | 1.7% | 0.02 |

WER full = whole utterance in one call · WER live = streamed through the engine's VAD (cuts at silence or every 6s) · RTF = ASR time / audio time (lower is faster).

### Worst live transcriptions

- `pt_000701.wav` WER 44%
  - ref: uns aborrecem as laranjas outros aborrecem os amores agora se o aborrecimento vem por causa das cascas não sei o que é certo é que é assim é ferino disse emília olhando para adelaide ferino eu
  - hyp: OUCH Aborrassem as laranas Outros aborrassem os amores Agora, o aborrecimento vem por causa das coisas que eu não sei Ok certo, é que é assim. Ferino de semilha olhando para trás. Ferino é eu.
- `en_000288.wav` WER 44%
  - ref: FOOTNOTE SUMNER TO SHANNON MAY TWELFTH EIGHTEEN FIFTY SIX
  - hyp: footnote Sumner to Shannon May 12, 1856.
- `pt_000529.wav` WER 28%
  - ref: dentro da casa em que nasceste és tudo como tudo é feliz no fim do dia quando voltas das aulas e do estudo volta quando tu voltas a alegria
  - hyp: dentro da casa em que nasce este estudo. Como tudo é feliz no fim do dia. quando volta às 11 do estudo. Volta quando tu voltas à alegria.
- `pt_000345.wav` WER 18%
  - ref: e já os cigarros de ótimo bragança fumegavam enquanto ao arruído da palestra juntava-se à meia nau o ranger dos moitões e cabos do velame desfraldado
  - hyp: E já os cigarros de ótimo bragança fumegavam, enquanto ao arruído da palestra... juntávase a meia-nal. o ranger dos moitões e cabos do velame desfraudado.
- `en_000144.wav` WER 15%
  - ref: MEANWHILE RODOLFO HAD LEOCADIA SAFE IN HIS CUSTODY AND IN HIS OWN APARTMENT
  - hyp: Meanwhile, Rudolfo had Leuqueria safe in his custody. and in his own apartment.
