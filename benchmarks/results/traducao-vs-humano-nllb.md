# Tradução do Praxis comparada com tradução humana

Data: 2026-10-20 15:14 · Máquina: Darwin x86_64 · i386 · só processador (sem placa de vídeo) · 60 frases do conjunto FLEURS/FLoRes, as mesmas nos 16 idiomas.

## Como ler as notas

- **Fidelidade da tradução (0–100)** — nome técnico chrF. Compara a tradução do Praxis com a de uma pessoa, em pedaços de poucas letras. Tolera pequenas diferenças de flexão. Como referência: acima de 60 costuma ser uma tradução boa e fácil de entender; entre 45 e 60, entende-se a ideia com erros; abaixo de 45, há perda séria de sentido.
- **Coincidência de trechos (0–100)** — nome técnico BLEU. Conta sequências de 1 a 4 palavras iguais às da tradução humana. É rígida (um sinônimo correto já tira pontos), então números de 30 a 40 já indicam boa tradução.
- **Saídas suspeitas** — traduções vazias; que repetem o mesmo trecho em laço; com comprimento muito diferente da humana (mais de 2,5 vezes maior ou menos de 30%); na escrita errada (ex.: saiu em inglês quando devia sair em árabe); com letras do idioma de origem no meio do inglês; ou com fidelidade da frase abaixo de 20, sinal de frase inventada sem relação com o original (este último pode acusar também uma tradução certa escrita de um jeito bem diferente da humana; confira o exemplo).
- **Chinês como destino (en→zh):** a fidelidade fica baixa por construção (um caractere chinês já é uma palavra inteira), então não dá para compará-la com a dos outros idiomas; para o chinês olhe a coincidência de trechos. Por isso o en→zh fica fora da lista de piores direções.
- O tempo é medido por frase, depois de o modelo já estar carregado.

## a) De cada idioma para o inglês

| Direção | Fidelidade da tradução (0–100) | Coincidência de trechos (0–100) | Tempo médio por frase | Saídas suspeitas |
|---|---:|---:|---:|---:|
| pt→en (português → inglês) | 68.5 | 45.7 | 1115 ms | 0/60 |
| es→en (espanhol → inglês) | 59.1 | 32.7 | 1159 ms | 0/60 |
| fr→en (francês → inglês) | 68.0 | 44.9 | 1146 ms | 0/60 |
| de→en (alemão → inglês) | 65.8 | 39.9 | 1100 ms | 1/60 |
| it→en (italiano → inglês) | 59.0 | 29.0 | 1137 ms | 0/60 |
| ru→en (russo → inglês) | 60.0 | 33.2 | 1100 ms | 0/60 |
| zh→en (chinês → inglês) | 57.8 | 29.8 | 1147 ms | 0/60 |
| nl→en (holandês → inglês) | 59.1 | 33.6 | 1076 ms | 0/60 |
| pl→en (polonês → inglês) | 56.2 | 26.3 | 1132 ms | 0/60 |
| uk→en (ucraniano → inglês) | 64.8 | 39.8 | 1119 ms | 1/60 |
| tr→en (turco → inglês) | 62.3 | 37.2 | 1076 ms | 0/60 |
| ar→en (árabe → inglês) | 65.9 | 43.0 | 1092 ms | 0/60 |
| hi→en (hindi → inglês) | 62.6 | 36.4 | 1068 ms | 0/60 |
| ja→en (japonês → inglês) | 52.5 | 24.4 | 1027 ms | 1/60 |
| ko→en (coreano → inglês) | 55.1 | 26.4 | 1502 ms | 0/60 |

## b) Do inglês para cada idioma

| Direção | Fidelidade da tradução (0–100) | Coincidência de trechos (0–100) | Tempo médio por frase | Saídas suspeitas |
|---|---:|---:|---:|---:|
| en→pt (inglês → português) | 69.2 | 45.8 | 1605 ms | 0/60 |
| en→es (inglês → espanhol) | 55.2 | 27.4 | 1585 ms | 0/60 |
| en→fr (inglês → francês) | 69.2 | 48.1 | 1873 ms | 0/60 |
| en→de (inglês → alemão) | 64.2 | 37.8 | 1618 ms | 0/60 |
| en→it (inglês → italiano) | 55.9 | 26.6 | 1383 ms | 0/60 |
| en→ru (inglês → russo) | 57.5 | 31.5 | 1492 ms | 0/60 |
| en→zh (inglês → chinês) | 27.8 | 30.5 | 1213 ms | 0/60 |
| en→nl (inglês → holandês) | 56.3 | 27.1 | 1558 ms | 0/60 |
| en→pl (inglês → polonês) | 49.6 | 19.6 | 1716 ms | 0/60 |
| en→uk (inglês → ucraniano) | 53.1 | 24.5 | 1525 ms | 0/60 |
| en→tr (inglês → turco) | 58.0 | 24.3 | 1451 ms | 0/60 |
| en→ar (inglês → árabe) | 56.1 | 22.6 | 1718 ms | 0/60 |
| en→hi (inglês → hindi) | 55.6 | 29.8 | 1616 ms | 0/60 |

## c) Pares sem inglês (passam pelo inglês: duas traduções seguidas)

| Direção | Fidelidade da tradução (0–100) | Coincidência de trechos (0–100) | Tempo médio por frase | Saídas suspeitas |
|---|---:|---:|---:|---:|
| pt→es (português → espanhol) | 53.1 | 24.2 | 1553 ms | 0/60 |
| es→pt (espanhol → português) | 55.2 | 26.2 | 1622 ms | 0/60 |
| pt→fr (português → francês) | 63.8 | 40.6 | 1868 ms | 0/60 |
| fr→pt (francês → português) | 61.3 | 35.6 | 1717 ms | 0/60 |
| de→pt (alemão → português) | 59.8 | 34.2 | 1406 ms | 0/60 |
| pt→it (português → italiano) | 51.7 | 21.6 | 1350 ms | 0/60 |
| it→pt (italiano → português) | 54.5 | 25.7 | 1424 ms | 0/60 |
| ru→uk (russo → ucraniano) | 53.2 | 24.8 | 1441 ms | 0/60 |

### Quanto se perde ao passar pelo inglês

Comparamos cada par sem inglês com a tradução de uma etapa só que chega no mesmo idioma (inglês → destino), porque as notas só são comparáveis quando a tradução humana de referência é a mesma. Também mostramos a primeira etapa (origem → inglês).

| Par | Fidelidade do par | inglês → destino | Diferença | origem → inglês | Diferença |
|---|---:|---:|---:|---:|---:|
| pt→es | 53.1 | 55.2 | -2.1 | 68.5 | -15.4 |
| es→pt | 55.2 | 69.2 | -14.0 | 59.1 | -3.9 |
| pt→fr | 63.8 | 69.2 | -5.4 | 68.5 | -4.7 |
| fr→pt | 61.3 | 69.2 | -7.9 | 68.0 | -6.7 |
| de→pt | 59.8 | 69.2 | -9.4 | 65.8 | -6.0 |
| pt→it | 51.7 | 55.9 | -4.2 | 68.5 | -16.8 |
| it→pt | 54.5 | 69.2 | -14.7 | 59.0 | -4.5 |
| ru→uk | 53.2 | 53.1 | +0.1 | 60.0 | -6.8 |

Perda média contra inglês → destino: **-7.2 pontos** de fidelidade.

## d) Português de Portugal ou do Brasil? (saídas inglês → português)

- Frases do Praxis com alguma marca de **português de Portugal**: **1 de 60 (2%)**.
- Frases do Praxis com alguma marca de **português do Brasil**: 6 de 60 (10%).
- Para comparar, a tradução humana brasileira das mesmas frases: 0 com marca de Portugal, 9 com marca do Brasil.
- Marcas de Portugal encontradas no Praxis: actual/acção (grafia antiga) (1).
- Marcas do Brasil encontradas no Praxis: você (3), equipe (1), estar + gerúndio (ex.: está fazendo) (2).

Exemplos:

- “O relatório é altamente crítico com quase todos os aspectos da atual política do Executivo em relação ao Iraque e insta a uma mudança imediata de direcção.” — marcas: actual/acção (grafia antiga)

## e) Tempo por frase

- Mais lentas: en→fr 1873 ms (máx. 3340 ms); pt→fr 1868 ms (máx. 3422 ms); en→ar 1718 ms (máx. 3020 ms); fr→pt 1717 ms (máx. 2906 ms); en→pl 1716 ms (máx. 2926 ms).
- Média geral: 1381 ms por frase.

## Piores direções

1. en→pl — fidelidade 49.6, coincidência 19.6
2. pt→it — fidelidade 51.7, coincidência 21.6
3. ja→en — fidelidade 52.5, coincidência 24.4
4. en→uk — fidelidade 53.1, coincidência 24.5
5. pt→es — fidelidade 53.1, coincidência 24.2

### Exemplos da pior direção (en→pl)

- **Original:** So, it is likely that the notation was added simply as a label.
  - **Humano:** W związku z tym można założyć, że adnotację dodano w charakterze etykiety opisowej.
  - **Praxis:** Jest więc prawdopodobne, że notatę dodano po prostu jako etykietę.

- **Original:** Today, the only insects that cannot fold back their wings are dragon flies and mayflies.
  - **Humano:** Dziś do jedynych owadów nieposiadających zdolności składania skrzydeł należą ważki i jętki.
  - **Praxis:** Dzisiaj jedynymi owadami, które nie potrafią złożyć skrzydła, są muchy smoka i muchy majów.

- **Original:** Plants make their food from the sun by photosynthesis. They also provide shade.
  - **Humano:** Fotosynteza to proces, w którym rośliny wykorzystują światło słoneczne do produkcji substancji odżywczych. Rośliny dają też cień.
  - **Praxis:** Rośliny wytwarzają swoje jedzenie ze słońca przez fotosyntezę. Zapewniają też cień.

- **Original:** It is thinner under the maria and thicker under the highlands.
  - **Humano:** Jest cieńsza pod morzami księżycowymi i grubsza pod wyżynami.
  - **Praxis:** Jest cienkiej pod Mariami, a grubszy pod górami.

- **Original:** Fire rescue crews eventually doused the fire by 11:35 pm.
  - **Humano:** Załogi straży pożarnej ostatecznie ugasiły ogień przed godz. 23:35.
  - **Praxis:** Zespół ratowniczy ostatecznie zamknął pożar o 11:35.

## Saídas suspeitas

Total: 3 saídas em 3 direções.

- de→en: repetição em laço, muito mais longa que a humana — original “NextGen ist ein System, von dem die FAA behauptet, dass es Flugzeugen erlauben würde, kürzere Strecken zu fliegen und jedes Jahr Millionen Gallonen an Treibstof” → Praxis “NextGen is a system, of which the FAA claims, that it would allow aircraft, It is also important to note that the Commission's proposals for a directive on the protection of workers' rights and the pr”
- uk→en: letras do idioma de origem vazaram — original “Спершу шоу транслювали виключно на давно працюючому Інтернет-радіо ТогіНет Радіо – сайті, присвяченому радіобесідам.” → Praxis “The show was originally broadcast exclusively on the long-running Internet radio station Toginet Radio  сай, a website dedicated to radio talk shows.”
- ja→en: quase nada em comum com a humana (possível frase inventada) — original “そのため、単にラベルとして表記が追加されがちです。” → Praxis “That's why we often just add labels.”

## O que isso significa

Das 27 direções de uma etapa só (sem contar o en→zh, medido à parte), 11 ficaram com fidelidade de 60 ou mais (tradução boa e fácil de entender); 1 ficaram abaixo de 50 (en→pl), faixa em que quem ouve entende a ideia geral mas perde detalhes e às vezes o sentido. Passar pelo inglês custa em média 7.2 pontos de fidelidade frente à tradução direta do inglês para o mesmo idioma: os erros das duas etapas se somam. No português, 2% das frases traduzidas do inglês têm alguma marca de português de Portugal — para quem ouve no Brasil isso soa estrangeiro, mas raramente atrapalha o entendimento. Lembre que estas frases são textos de notícia e enciclopédia, mais difíceis que conversa do dia a dia, e que aqui o texto entra perfeito: numa chamada real, os erros da transcrição da fala somam-se a estes.
