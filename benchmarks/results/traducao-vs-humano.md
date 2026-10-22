# Tradução do Praxis comparada com tradução humana

Data: 2026-10-20 14:53 · Máquina: Darwin x86_64 · i386 · só processador (sem placa de vídeo) · 60 frases do conjunto FLEURS/FLoRes, as mesmas nos 16 idiomas.

## Como ler as notas

- **Fidelidade da tradução (0–100)** — nome técnico chrF. Compara a tradução do Praxis com a de uma pessoa, em pedaços de poucas letras. Tolera pequenas diferenças de flexão. Como referência: acima de 60 costuma ser uma tradução boa e fácil de entender; entre 45 e 60, entende-se a ideia com erros; abaixo de 45, há perda séria de sentido.
- **Coincidência de trechos (0–100)** — nome técnico BLEU. Conta sequências de 1 a 4 palavras iguais às da tradução humana. É rígida (um sinônimo correto já tira pontos), então números de 30 a 40 já indicam boa tradução.
- **Saídas suspeitas** — traduções vazias; que repetem o mesmo trecho em laço; com comprimento muito diferente da humana (mais de 2,5 vezes maior ou menos de 30%); na escrita errada (ex.: saiu em inglês quando devia sair em árabe); com letras do idioma de origem no meio do inglês; ou com fidelidade da frase abaixo de 20, sinal de frase inventada sem relação com o original (este último pode acusar também uma tradução certa escrita de um jeito bem diferente da humana; confira o exemplo).
- **Chinês como destino (en→zh):** a fidelidade fica baixa por construção (um caractere chinês já é uma palavra inteira), então não dá para compará-la com a dos outros idiomas; para o chinês olhe a coincidência de trechos. Por isso o en→zh fica fora da lista de piores direções.
- O tempo é medido por frase, depois de o modelo já estar carregado.

## a) De cada idioma para o inglês

| Direção | Fidelidade da tradução (0–100) | Coincidência de trechos (0–100) | Tempo médio por frase | Saídas suspeitas |
|---|---:|---:|---:|---:|
| pt→en (português → inglês) | 66.4 | 43.2 | 140 ms | 0/60 |
| es→en (espanhol → inglês) | 55.4 | 26.6 | 325 ms | 0/60 |
| fr→en (francês → inglês) | 67.1 | 44.7 | 139 ms | 0/60 |
| de→en (alemão → inglês) | 68.6 | 43.6 | 145 ms | 0/60 |
| it→en (italiano → inglês) | 56.2 | 26.9 | 114 ms | 0/60 |
| ru→en (russo → inglês) | 61.5 | 36.0 | 167 ms | 0/60 |
| zh→en (chinês → inglês) | 54.7 | 25.7 | 150 ms | 0/60 |
| nl→en (holandês → inglês) | 57.3 | 29.4 | 153 ms | 0/60 |
| pl→en (polonês → inglês) | 56.1 | 26.7 | 188 ms | 0/60 |
| uk→en (ucraniano → inglês) | 57.0 | 30.2 | 164 ms | 0/60 |
| tr→en (turco → inglês) | 52.5 | 24.8 | 179 ms | 0/60 |
| ar→en (árabe → inglês) | 57.8 | 30.6 | 127 ms | 0/60 |
| hi→en (hindi → inglês) | 55.9 | 27.7 | 136 ms | 0/60 |
| ja→en (japonês → inglês) | 45.8 | 16.0 | 200 ms | 6/60 |
| ko→en (coreano → inglês) | 45.8 | 15.3 | 154 ms | 1/60 |

## b) Do inglês para cada idioma

| Direção | Fidelidade da tradução (0–100) | Coincidência de trechos (0–100) | Tempo médio por frase | Saídas suspeitas |
|---|---:|---:|---:|---:|
| en→pt (inglês → português) | 66.6 | 42.5 | 205 ms | 0/60 |
| en→es (inglês → espanhol) | 53.7 | 24.4 | 155 ms | 0/60 |
| en→fr (inglês → francês) | 67.1 | 44.5 | 208 ms | 0/60 |
| en→de (inglês → alemão) | 67.3 | 43.1 | 256 ms | 0/60 |
| en→it (inglês → italiano) | 52.3 | 21.7 | 156 ms | 0/60 |
| en→ru (inglês → russo) | 58.8 | 33.5 | 377 ms | 1/60 |
| en→zh (inglês → chinês) | 28.9 | 32.3 | 159 ms | 0/60 |
| en→nl (inglês → holandês) | 56.3 | 27.3 | 229 ms | 0/60 |
| en→pl (inglês → polonês) | 49.7 | 18.0 | 197 ms | 0/60 |
| en→uk (inglês → ucraniano) | 46.7 | 18.8 | 177 ms | 0/60 |
| en→tr (inglês → turco) | 51.4 | 16.0 | 132 ms | 0/60 |
| en→ar (inglês → árabe) | 46.2 | 16.2 | 164 ms | 6/60 |
| en→hi (inglês → hindi) | 53.5 | 27.5 | 205 ms | 0/60 |

## c) Pares sem inglês (passam pelo inglês: duas traduções seguidas)

| Direção | Fidelidade da tradução (0–100) | Coincidência de trechos (0–100) | Tempo médio por frase | Saídas suspeitas |
|---|---:|---:|---:|---:|
| pt→es (português → espanhol) | 51.0 | 21.6 | 327 ms | 0/60 |
| es→pt (espanhol → português) | 55.4 | 26.5 | 687 ms | 0/60 |
| pt→fr (português → francês) | 62.8 | 38.2 | 408 ms | 0/60 |
| fr→pt (francês → português) | 60.8 | 36.4 | 414 ms | 0/60 |
| de→pt (alemão → português) | 60.6 | 33.9 | 352 ms | 0/60 |
| pt→it (português → italiano) | 50.4 | 20.9 | 372 ms | 0/60 |
| it→pt (italiano → português) | 54.0 | 24.5 | 349 ms | 0/60 |
| ru→uk (russo → ucraniano) | 44.5 | 14.0 | 362 ms | 1/60 |

### Quanto se perde ao passar pelo inglês

Comparamos cada par sem inglês com a tradução de uma etapa só que chega no mesmo idioma (inglês → destino), porque as notas só são comparáveis quando a tradução humana de referência é a mesma. Também mostramos a primeira etapa (origem → inglês).

| Par | Fidelidade do par | inglês → destino | Diferença | origem → inglês | Diferença |
|---|---:|---:|---:|---:|---:|
| pt→es | 51.0 | 53.7 | -2.7 | 66.4 | -15.4 |
| es→pt | 55.4 | 66.6 | -11.2 | 55.4 | +0.0 |
| pt→fr | 62.8 | 67.1 | -4.3 | 66.4 | -3.6 |
| fr→pt | 60.8 | 66.6 | -5.8 | 67.1 | -6.3 |
| de→pt | 60.6 | 66.6 | -6.0 | 68.6 | -8.0 |
| pt→it | 50.4 | 52.3 | -1.9 | 66.4 | -16.0 |
| it→pt | 54.0 | 66.6 | -12.6 | 56.2 | -2.2 |
| ru→uk | 44.5 | 46.7 | -2.2 | 61.5 | -17.0 |

Perda média contra inglês → destino: **-5.8 pontos** de fidelidade.

## d) Português de Portugal ou do Brasil? (saídas inglês → português)

- Frases do Praxis com alguma marca de **português de Portugal**: **1 de 60 (2%)**.
- Frases do Praxis com alguma marca de **português do Brasil**: 7 de 60 (12%).
- Para comparar, a tradução humana brasileira das mesmas frases: 0 com marca de Portugal, 9 com marca do Brasil.
- Marcas de Portugal encontradas no Praxis: actual/acção (grafia antiga) (1).
- Marcas do Brasil encontradas no Praxis: você (4), equipe (1), estar + gerúndio (ex.: está fazendo) (3).

Exemplos:

- “O relatório é altamente crítico em relação a quase todos os aspectos da actual política do Executivo em relação ao Iraque e insta a uma mudança de direcção imediata.” — marcas: actual/acção (grafia antiga)

## e) Tempo por frase

- Mais lentas: es→pt 687 ms (máx. 1314 ms); fr→pt 414 ms (máx. 792 ms); pt→fr 408 ms (máx. 938 ms); en→ru 377 ms (máx. 716 ms); pt→it 372 ms (máx. 646 ms).
- Média geral: 233 ms por frase.

## Piores direções

1. ru→uk — fidelidade 44.5, coincidência 14.0
2. ja→en — fidelidade 45.8, coincidência 16.0
3. ko→en — fidelidade 45.8, coincidência 15.3
4. en→ar — fidelidade 46.2, coincidência 16.2
5. en→uk — fidelidade 46.7, coincidência 18.8

### Exemplos da pior direção (ru→uk)

- **Original:** Выкладывание экскурсии в виртуальное пространство для всеобщего обозрения — это также отличный способ освежить в памяти экскурсию и поделиться своим полученными знаниями с будущими классами.
  - **Humano:** Віртуальна екскурсія — також чудовий спосіб поміркувати про подорож і поділитися досвідом з майбутніми класами.
  - **Praxis:** Ми можемо самі зателефонувати одержувачу і узгодити зручний час і місце вручення квітів, а якщо необхідно, то збережемо сюрприз.

- **Original:** Слава о нем как о центре роскоши пошла около 400 г. н. э. и продолжалась примерно до 1100 г. н. э.
  - **Humano:** Він відомий тим, що був епіцентром розкоші, початок якого датується приблизно в 400 роком н. е., та який та проіснував приблизно до 1100 року н. е.
  - **Praxis:** Його популярність як центр розкоші почав близько 400. п. eh Він тривав до 1100. п. й

- **Original:** В начальный период своего существования это шоу транслировалось только на сайте давно существующего онлайн-радио TogiNet Radio, посвященного радиобеседам.
  - **Humano:** Спершу шоу транслювали виключно на давно працюючому Інтернет-радіо ТогіНет Радіо – сайті, присвяченому радіобесідам.
  - **Praxis:** На початку свого існування шоу транслювалося тільки на довгоочікуваний онлайн радіостанцію TogiNet Radio.

- **Original:** Не подвергайте ткань воздействию слишком высокой температуры (что может привести к усадке или в очень редких случаях к ожогу).
  - **Humano:** Будьте обережними, щоб тканина не стала занадто гарячою (що може спричинити зсідання, або в крайньому разі пропалину).
  - **Praxis:** Не піддавати тканині занадто високу температуру (який може призвести до усадки або, в дуже рідкісних випадках, опіку).

- **Original:** Отбойное течение — течение, создаваемое волнами, которые разбиваются о берег, или иногда об риф или что-то подобное.
  - **Humano:** Відбійні течії — це зворотні потоки від хвиль, які розбиваються на березі, часто на рифі або подібному.
  - **Praxis:** Стрижка струму - це струм, створений хвилями, які перервуться на берег, або іноді в риф або щось схоже.

## Saídas suspeitas

Total: 15 saídas em 5 direções.

- ja→en: letras do idioma de origem vazaram — original “現在、翅を折り返すことができない昆虫はトンボとカゲロウのみです。” → Praxis “At present,ボs that can not fold wings are only tombs and maggots.”
- ja→en: letras do idioma de origem vazaram — original “これらの理論では、ある種の人々が日常的に特定のことをしたがる動機について、そして彼らに特定のことをさせる、あるいはさせない環境要因について考察します。” → Praxis “In these theory, Theるs that some people have done on a daily basis and make them specific, Consider the environmental factors that are not allowed.”
- ja→en: letras do idioma de origem vazaram — original “田舎道の運転に慣れていない方は、急勾配、狭い車線、急カーブに注意し、気を抜かないでください。” → Praxis “If you are unfamiliar with the driving of the country road, please do not worry about勾, narrow lanes, andカーブ.”
- ja→en: letras do idioma de origem vazaram — original “離岸流とは、砕けて浜辺に戻ってくる引き波のことで、多くの場合、岩礁やそれに似た場所で発生します。” → Praxis “The shore flow is a 波 wave that is crushed and returned to the beach, which often occurs in rocks and similar places.”
- ja→en: letras do idioma de origem vazaram, quase nada em comum com a humana (possível frase inventada) — original “男性の誘いを断るときには、臆することなく毅然とした態度で自分の立場を貫きましょう（文化の違いがあろうがなかろうが、強引な誘いになびく必要はありません！）。” → Praxis “When you cut off male in , Keep your own position in a resolute attitude without timidity. You don’t have to be びed!”
- ja→en: letras do idioma de origem vazaram — original “このように、世に出てきた当時の鉛筆は多くの人にとって良き友人でした。” → Praxis “In this way, the世 of the time that came out to the world was a good friend for many.”
- ko→en: quase nada em comum com a humana (possível frase inventada) — original “사치의 진원지라는 명성은 서기 400년경에 시작하여 서기 1100년경까지 이어졌습니다.” → Praxis “The temple of Sachi started around 400 years in the west and began to reach around 1100 years.”
- en→ru: quase nada em comum com a humana (possível frase inventada) — original “Fire rescue crews eventually doused the fire by 11:35 pm.” → Praxis “Пожарные спасатели в конечном итоге облили огонь к 11:35 вечера.”
- en→ar: escrita errada (não traduziu), quase nada em comum com a humana (possível frase inventada) — original “Children are placed in Foster Care for a wide variety of reasons that range from neglect, to abuse, and even to extortion.” → Praxis “Children are placed in Foster Care for a wide variety of reasons that range from neglect, to abuse, and even to extortion.”
- en→ar: escrita errada (não traduziu), quase nada em comum com a humana (possível frase inventada) — original “A simple popular dinner, especially during the summer, is the Pa amb Oli: Bread with olive oil, tomato, and any available condiments such as cheese, tunafish, e” → Praxis “A simple popular dinner, especially during the summer, is the Pa amb Oli: Bread with olive oil, tomato, and any available condiments such as wound, tunafish, etc.”
- en→ar: escrita errada (não traduziu), quase nada em comum com a humana (possível frase inventada) — original “The harbor was the site of an infamous naval standoff in 1889 when seven ships from Germany, the US, and Britain refused to leave the harbor.” → Praxis “The harbor was the site of an infamous naval standoff in 1889 when seven ships from Germany, the US, and Britain refused to leave the harbor.”
- en→ar: escrita errada (não traduziu), quase nada em comum com a humana (possível frase inventada) — original “The crust is about 70 km thick on the near side and 100 km thick on the far side.” → Praxis “The crust is about 70 km fish on the near side and 100 km fish on the far side.”
- en→ar: escrita errada (não traduziu), quase nada em comum com a humana (possível frase inventada) — original “He added that "they should not, however, be asked to take on obligations that go beyond their development stage, responsibility and capabilities."” → Praxis “He added that "they should not, however, be asked to take on obligations that go beyond their development stage, responsibility and capabilities."”
- en→ar: escrita errada (não traduziu), quase nada em comum com a humana (possível frase inventada) — original “As a result, the performers smoke cannabis joints on stage, and the theatre itself is encouraging the audience to join in.” → Praxis “As a result, the performers smoke cannabis joints on stage, and the scene itself is encouraging the audience to join in.”
- ru→uk: quase nada em comum com a humana (possível frase inventada) — original “Выкладывание экскурсии в виртуальное пространство для всеобщего обозрения — это также отличный способ освежить в памяти экскурсию и поделиться своим полученными” → Praxis “Ми можемо самі зателефонувати одержувачу і узгодити зручний час і місце вручення квітів, а якщо необхідно, то збережемо сюрприз.”

## O que isso significa

Das 27 direções de uma etapa só (sem contar o en→zh, medido à parte), 7 ficaram com fidelidade de 60 ou mais (tradução boa e fácil de entender); 5 ficaram abaixo de 50 (ja→en, ko→en, en→pl, en→uk, en→ar), faixa em que quem ouve entende a ideia geral mas perde detalhes e às vezes o sentido. Passar pelo inglês custa em média 5.8 pontos de fidelidade frente à tradução direta do inglês para o mesmo idioma: os erros das duas etapas se somam. No português, 2% das frases traduzidas do inglês têm alguma marca de português de Portugal — para quem ouve no Brasil isso soa estrangeiro, mas raramente atrapalha o entendimento. Lembre que estas frases são textos de notícia e enciclopédia, mais difíceis que conversa do dia a dia, e que aqui o texto entra perfeito: numa chamada real, os erros da transcrição da fala somam-se a estes.
