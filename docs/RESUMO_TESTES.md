# Resumo dos testes do Praxis

_Atualizado em 20/10/2026. Máquinas: Mac Intel com AMD Radeon Pro 5500M (sem placa de vídeo compatível: tudo no processador) e lab2 (Linux, NVIDIA RTX 3050 6 GB)._

Meta de qualidade: **1% de erro, teto de 3%**. Idioma acima do teto num computador não é oferecido nele.

## 1. Os melhores modelos, segundo os testes

| Etapa | Com placa de vídeo | Sem placa de vídeo | Por quê |
|---|---|---|---|
| Reconhecer a fala | **Whisper large-v3-turbo** | **Whisper small** | O turbo erra tão pouco quanto o large-v3 completo e é 2× mais rápido. No processador, só o small acompanha quem fala; medium e turbo ficam 4 a 26 s atrasados. |
| Traduzir | **NLLB-200 (Meta)** | **NLLB** nos idiomas fracos do Argos, **Argos** no resto | O NLLB ganhou em 149 dos 210 sentidos e quebrou metade das frases que o Argos quebra. No processador ele é ~8× mais lento, então só vale onde o Argos é fraco. |
| Falar | **Piper**, uma voz por idioma | igual | Roda em tempo real em qualquer máquina. |

O NLLB tem licença **CC BY-NC 4.0**: uso não comercial. O Praxis é aberto (MIT); quem usar o Praxis comercialmente precisa usar o Argos.

Descartados depois de medir: **MADLAD-400** (Google), com nota 41,8 contra 58,3 do NLLB, 222 de 720 frases quebradas e 2,8 s por frase; e os modelos tiny, base e medium.

## 2. Qualidade por idioma: erro real no uso ao vivo

40 frases de pessoas diferentes por idioma (Google FLEURS). "Erro real" = palavras trocadas, faltando ou inventadas. Não contam: diferença de escrita ("e-mail" × "email"), número escrito de outro jeito ("3" × "três") e nome próprio estrangeiro. Em chinês e japonês a conta é por letra.

| Idioma | Com placa de vídeo | Sem placa de vídeo |
|---|---:|---:|
| Espanhol | **1,6%** ✅ | 6,0% |
| Italiano | **1,7%** ✅ | 8,6% |
| Alemão | **2,0%** ✅ | 9,1% |
| Português | **2,2%** ✅ | 7,8% |
| Inglês | 3,2% | 7,5% |
| Russo | 3,8% | 10,6% |
| Ucraniano | 4,7% | 21% |
| Holandês, polonês, japonês | 5,4 a 5,5% | 17 a 23% |
| Turco | 5,8% | 16,6% |
| Francês | 6,4% | 15,9% |
| Árabe | 9,2% | 29% |
| Chinês | 11,3% | 17,3% |
| Coreano | 15,1% | 25% |
| Hindi | 30% | 75% |

✅ = abaixo do teto de 3%. **Sem placa de vídeo, nenhum idioma passa do teto.** Com placa de vídeo passam 4 idiomas, e o inglês fica perto.

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

- Com placa de vídeo, o trecho de fala vai até 15 s em vez de 6 s. O corte no meio da fala era a maior fonte de erro e, com a mudança, todos os 16 idiomas melhoraram (alemão de 4,8% para 2,0%).
- A placa de vídeo só é usada se não for mais fraca que o processador. Isso é medido na primeira execução: neste Mac a placa perdeu, no lab2 ganhou.
- Idioma acima do teto de 3% não é oferecido naquele computador.
- Tradução automática: NLLB onde ele é melhor, Argos no resto.

**Testados e descartados:** esperar mais silêncio antes de cortar; comparar 5 caminhos na transcrição; repetir o fim do trecho anterior (o Whisper passou a inventar "E aí" e "Obrigado"); velocidade de voz "prevista"; usar o contexto da frase anterior.

## 6. Em aberto

- Rodar a instalação completa e verificar num computador limpo que tudo já começa funcionando.
- Testes em Windows e em placas AMD, Intel e Apple Silicon reais (não há essas máquinas aqui).
- Redução de ruído e filtro de vozes de fundo.
- Coreano, árabe, chinês e hindi continuam longe do teto mesmo com placa de vídeo.

Dados brutos em `benchmarks/results/`. Detalhes de cada rodada em `docs/QA_REPORT.md`.
