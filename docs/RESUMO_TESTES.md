# Resumo dos testes do Praxis

_Atualizado em 21/10/2026. Máquinas: Mac Intel com AMD Radeon Pro 5500M (sem placa de vídeo compatível: tudo no processador) e lab2 (Linux, NVIDIA RTX 3050 6 GB)._

Meta de qualidade: **1% de erro, teto de 3%**. Idioma acima do teto num computador não é oferecido nele.

## 1. Os melhores modelos, segundo os testes

| Etapa | Com placa de vídeo | Sem placa de vídeo | Por quê |
|---|---|---|---|
| Reconhecer a fala | o melhor medido por idioma: **Whisper large-v3-turbo** em pt/es/de/it, **Parakeet** em en/fr, **Whisper large-v3** nos outros | **Parakeet-ultra** (Moondream, set/2026) nos europeus, **Parakeet v2** no inglês, **Parakeet v3** em russo e ucraniano, **Parakeet japonês**, **Whisper small** nos outros | O Parakeet erra 2 a 4 vezes menos que o Whisper small no processador e leva 0,3 s por trecho (lab2 livre). Comparar 4 caminhos antes de decidir cada palavra tira mais 0,2 a 0,4 ponto por +0,04 s. O large-v3 completo ganha do turbo fora dos idiomas principais (0,8 a 0,9 s por trecho). |
| Traduzir | **NLLB-200 (Meta)** | **NLLB** nos idiomas fracos do Argos, **Argos** no resto | O NLLB ganhou em 149 dos 210 sentidos e quebrou metade das frases que o Argos quebra. No processador ele é ~8× mais lento, então só vale onde o Argos é fraco. |
| Falar | **Piper**, uma voz por idioma | igual | Roda em tempo real em qualquer máquina. |

O NLLB tem licença **CC BY-NC 4.0**: uso não comercial. O Praxis é aberto (MIT); quem usar o Praxis comercialmente precisa usar o Argos.

Descartados depois de medir: **MADLAD-400** (Google), com nota 41,8 contra 58,3 do NLLB, 222 de 720 frases quebradas e 2,8 s por frase; os modelos tiny, base e medium; **Qwen3-ASR 0.6B** (pior em quase tudo e 3 a 9 s por trecho no processador); **Cohere Transcribe** (erra pouco: francês 2,9%, português 2,3%, árabe 6,5%; mas leva 4 s por trecho no processador e 1,4 a 1,8 s na placa de vídeo, porque só existe a versão comprimida para processador; candidato quando houver versão para placa de vídeo); **Fun-ASR Nano** (não transcreveu japonês e a licença não está clara).

## 2. Qualidade por idioma: erro real no uso ao vivo

40 frases de pessoas diferentes por idioma (Google FLEURS). "Erro real" = palavras trocadas, faltando ou inventadas. Não contam: diferença de escrita ("e-mail" × "email"), número escrito de outro jeito ("3" × "três") e nome próprio estrangeiro. Em chinês e japonês a conta é por letra.

| Idioma | Com placa de vídeo | Sem placa de vídeo |
|---|---:|---:|
| Espanhol | **1,6%** ✅ | **2,0%** ✅ |
| Italiano | **1,7%** ✅ | **1,8%** ✅ |
| Alemão | **2,0%** ✅ | **2,7%** ✅ |
| Português | **2,2%** ✅ | **2,9%** ✅ |
| Inglês (100 frases) | **2,0%** ✅ | **2,0%** ✅ |
| Ucraniano | 3,2% | 5,8% |
| Holandês | 3,6% | 4,9% |
| Russo | 3,6% | 5,0% |
| Turco | 4,1% | 16,6% |
| Francês | 4,3% | 4,3% |
| Japonês | 4,5% | 4,7% |
| Polonês | 4,7% | 6,4% |
| Árabe | 7,6% | 29% |
| Chinês | 9,3% | 17,3% |
| Coreano | 13,8% | 25% |
| Hindi | 20% | 75% |

✅ = abaixo do teto de 3%. **Cinco idiomas passam com e sem placa de vídeo: inglês, espanhol, italiano, alemão e português.** De manhã, sem placa de vídeo, nenhum passava (o Whisper small errava 6 a 9%). Ucraniano, holandês e russo ficam a menos de 1 ponto do teto com placa de vídeo.

## 3. Rapidez (o Praxis acompanha quem fala?)

| Situação | Resultado |
|---|---|
| Fala contínua de 1 minuto, com placa de vídeo | atraso típico de 0,8 a 2,3 s; acompanha nos 16 idiomas |
| Fala contínua de 1 minuto, sem placa de vídeo | atraso típico de 2,7 s; pior caso comum de 5 s; acompanha em 14 de 16 |
| Conversa com turnos, sem placa de vídeo | quem escuta espera menos de 1 s pela tradução na maioria dos idiomas |

## 4. Condições difíceis

| Situação | Resultado |
|---|---|
| Sem fone, a tradução sai na caixa de som e volta pelo microfone (eco) | sem tratamento: **130** palavras falsas por conversa; com a trava (padrão): **0**; com o cancelador experimental: 2 a 4 |
| Silêncio ou chiado ambiente | 0 palavras inventadas |
| Ruído de fundo forte | o erro sobe de 18,5% para 26% (ruído fraco), 39% (médio) e 61% (forte) |
| Conversa de outras pessoas ao fundo, em outro idioma | 25 palavras inventadas em 20 s (recomenda-se fone) |
| Fala lenta ou com pausas longas | piorou o erro em quase todos os modelos e máquinas: não ajuda |

## 5. O que mudou por causa dos testes

- No processador, o Parakeet substitui o Whisper small nos idiomas europeus. Duas correções foram necessárias: ajustar o volume (gravações baixas perdiam o fim da frase) e pôr meio segundo de silêncio em volta de cada trecho (trecho cortado no meio da fala voltava vazio). Só com elas o inglês caiu de 10% para 2%.
- Com placa de vídeo ou Parakeet, o trecho de fala vai até 15 s em vez de 6 s. Pedaços de 6 s pioram qualquer modelo (o turbo vai de 2,4% para 4,1% em português). O corte no meio da fala era a maior fonte de erro e, com a mudança, todos os 16 idiomas melhoraram (alemão de 4,8% para 2,0%).
- A placa de vídeo só é usada se não for mais fraca que o processador. Isso é medido na primeira execução: neste Mac a placa perdeu, no lab2 ganhou.
- Idioma acima do teto de 3% não é oferecido naquele computador.
- Tradução automática: NLLB onde ele é melhor, Argos no resto.

- Whisper large-v3 comparando 5 caminhos: só ajuda no árabe (7,6% → 5,6%); nos outros idiomas fica igual e mais lento.

- Removedor de ruído (sherpa-onnx, GTCRN e DPDFNet): **piora** o reconhecimento de fala em todos os casos de ruído (português com conversa de fundo: 5,2% sem → 14,4% e 21,2% com). O Whisper lida melhor com o ruído do que com o áudio "limpo" artificialmente. Descartado.
- Vozes (o Whisper ouve e transcreve; erro menor = voz mais clara; 20 frases por idioma):

  | Idioma | Piper (atual) | Supertonic 3 | Kokoro |
  |---|---:|---:|---:|
  | Português | 4,0% | 3,6% | **2,0%** |
  | Inglês | 3,9% | 3,4% | **2,7%** |
  | Espanhol | 1,3% | 1,5% | **0,6%** |
  | Francês | 3,8% | 5,7% | **3,4%** |
  | Alemão | **3,8%** | 5,0% | — |
  | Italiano | 5,6% | 1,8% | **1,0%** |
  | Tempo por segundo de fala | **0,05 s** | 0,17 s | 0,09 s na placa de vídeo; 0,22 s no processador (4 núcleos) |

  O Kokoro é o mais claro; a versão comprimida dele não acelera na placa de vídeo, a completa sim.

**Testados e descartados:** esperar mais silêncio antes de cortar; comparar 5 caminhos na transcrição; repetir o fim do trecho anterior (o Whisper passou a inventar "E aí" e "Obrigado"); velocidade de voz "prevista"; usar o contexto da frase anterior.

## 6. Em aberto

- Rodar a instalação completa e verificar num computador limpo que tudo já começa funcionando.
- Testes em Windows e em placas AMD, Intel e Apple Silicon reais (não há essas máquinas aqui).
- Filtro de vozes de fundo (o removedor de ruído testado piorou o reconhecimento).
- Vozes: adotar o Kokoro com placa de vídeo e o Supertonic no italiano sem placa.
- Coreano, árabe, chinês e hindi continuam longe do teto mesmo com placa de vídeo. Candidatos: Qwen3-ASR 1.7B e Cohere na placa de vídeo.
- Converter o Parakeet-ultra nós mesmos e publicar no Praxis (hoje vem de uma conversão da comunidade, com impressão digital conferida).
- Tradução para uso comercial: o **Hy-MT2 1.8B** (Tencent, Apache 2.0) empata com o NLLB em qualidade (125 sentidos, −0,1 ponto; quebra 1 frase contra 5), mas é 2 a 3× mais lento (0,4 a 0,6 s por frase na placa de vídeo). O **TranslateGemma 4B** (Google) perdeu 2 a 3 pontos e foi 4× mais lento: descartado. Falta decidir se o Praxis troca o NLLB pelo Hy-MT2.
- Voz: medir Supertonic 3 e Kokoro contra o Piper (que passou para licença GPL).

Dados brutos em `benchmarks/results/`. Detalhes de cada rodada em `docs/QA_REPORT.md`.
