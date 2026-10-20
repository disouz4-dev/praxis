# Tradução do Praxis comparada com tradução humana

Data: 2026-10-20 17:39 · Máquina: Linux x86_64 · x86_64 · só processador (sem placa de vídeo) · 60 frases do conjunto FLEURS/FLoRes, as mesmas nos 16 idiomas.

## Como ler as notas

- **Fidelidade da tradução (0–100)** — nome técnico chrF. Compara a tradução do Praxis com a de uma pessoa, em pedaços de poucas letras. Tolera pequenas diferenças de flexão. Como referência: acima de 60 costuma ser uma tradução boa e fácil de entender; entre 45 e 60, entende-se a ideia com erros; abaixo de 45, há perda séria de sentido.
- **Coincidência de trechos (0–100)** — nome técnico BLEU. Conta sequências de 1 a 4 palavras iguais às da tradução humana. É rígida (um sinônimo correto já tira pontos), então números de 30 a 40 já indicam boa tradução.
- **Saídas suspeitas** — traduções vazias; que repetem o mesmo trecho em laço; com comprimento muito diferente da humana (mais de 2,5 vezes maior ou menos de 30%); na escrita errada (ex.: saiu em inglês quando devia sair em árabe); com letras do idioma de origem no meio do inglês; ou com fidelidade da frase abaixo de 20, sinal de frase inventada sem relação com o original (este último pode acusar também uma tradução certa escrita de um jeito bem diferente da humana; confira o exemplo).
- **Chinês como destino (en→zh):** a fidelidade fica baixa por construção (um caractere chinês já é uma palavra inteira), então não dá para compará-la com a dos outros idiomas; para o chinês olhe a coincidência de trechos. Por isso o en→zh fica fora da lista de piores direções.
- O tempo é medido por frase, depois de o modelo já estar carregado.

## a) De cada idioma para o inglês

| Direção | Fidelidade da tradução (0–100) | Coincidência de trechos (0–100) | Tempo médio por frase | Saídas suspeitas |
|---|---:|---:|---:|---:|
| pt→en (português → inglês) | 68.8 | 45.6 | 173 ms | 0/60 |
| es→en (espanhol → inglês) | 59.1 | 32.4 | 178 ms | 0/60 |
| fr→en (francês → inglês) | 67.2 | 43.1 | 177 ms | 0/60 |
| de→en (alemão → inglês) | 66.1 | 41.7 | 171 ms | 0/60 |
| it→en (italiano → inglês) | 58.8 | 28.5 | 185 ms | 0/60 |
| ru→en (russo → inglês) | 59.6 | 32.9 | 182 ms | 0/60 |
| zh→en (chinês → inglês) | 56.9 | 28.5 | 186 ms | 0/60 |
| nl→en (holandês → inglês) | 59.6 | 34.4 | 172 ms | 0/60 |
| pl→en (polonês → inglês) | 56.0 | 26.0 | 181 ms | 0/60 |
| uk→en (ucraniano → inglês) | 64.2 | 39.8 | 184 ms | 1/60 |
| tr→en (turco → inglês) | 61.4 | 36.3 | 179 ms | 0/60 |
| ar→en (árabe → inglês) | 66.0 | 43.1 | 179 ms | 0/60 |
| hi→en (hindi → inglês) | 63.8 | 38.3 | 174 ms | 0/60 |
| ja→en (japonês → inglês) | 51.9 | 23.8 | 178 ms | 1/60 |
| ko→en (coreano → inglês) | 55.2 | 27.5 | 179 ms | 1/60 |

## b) Do inglês para cada idioma

| Direção | Fidelidade da tradução (0–100) | Coincidência de trechos (0–100) | Tempo médio por frase | Saídas suspeitas |
|---|---:|---:|---:|---:|
| en→pt (inglês → português) | 68.8 | 45.0 | 208 ms | 0/60 |
| en→es (inglês → espanhol) | 55.2 | 26.8 | 205 ms | 0/60 |
| en→fr (inglês → francês) | 69.6 | 48.8 | 237 ms | 0/60 |
| en→de (inglês → alemão) | 64.3 | 38.1 | 221 ms | 0/60 |
| en→it (inglês → italiano) | 55.9 | 26.8 | 210 ms | 0/60 |
| en→ru (inglês → russo) | 56.9 | 31.5 | 221 ms | 1/60 |
| en→zh (inglês → chinês) | 28.4 | 31.1 | 163 ms | 0/60 |
| en→nl (inglês → holandês) | 56.7 | 27.7 | 203 ms | 0/60 |
| en→pl (inglês → polonês) | 49.6 | 19.7 | 230 ms | 1/60 |
| en→uk (inglês → ucraniano) | 53.5 | 24.8 | 211 ms | 0/60 |
| en→tr (inglês → turco) | 58.1 | 24.2 | 188 ms | 0/60 |
| en→ar (inglês → árabe) | 56.6 | 23.7 | 231 ms | 0/60 |
| en→hi (inglês → hindi) | 55.9 | 30.4 | 203 ms | 0/60 |

## c) Pares sem inglês (passam pelo inglês: duas traduções seguidas)

| Direção | Fidelidade da tradução (0–100) | Coincidência de trechos (0–100) | Tempo médio por frase | Saídas suspeitas |
|---|---:|---:|---:|---:|
| pt→es (português → espanhol) | 53.1 | 23.8 | 200 ms | 0/60 |
| es→pt (espanhol → português) | 54.7 | 25.8 | 203 ms | 0/60 |
| pt→fr (português → francês) | 63.5 | 40.1 | 229 ms | 0/60 |
| fr→pt (francês → português) | 61.0 | 36.1 | 206 ms | 0/60 |
| de→pt (alemão → português) | 59.9 | 33.9 | 197 ms | 0/60 |
| pt→it (português → italiano) | 51.7 | 21.3 | 204 ms | 0/60 |
| it→pt (italiano → português) | 54.0 | 24.5 | 215 ms | 0/60 |
| ru→uk (russo → ucraniano) | 52.7 | 23.6 | 218 ms | 0/60 |

### Quanto se perde ao passar pelo inglês

Comparamos cada par sem inglês com a tradução de uma etapa só que chega no mesmo idioma (inglês → destino), porque as notas só são comparáveis quando a tradução humana de referência é a mesma. Também mostramos a primeira etapa (origem → inglês).

| Par | Fidelidade do par | inglês → destino | Diferença | origem → inglês | Diferença |
|---|---:|---:|---:|---:|---:|
| pt→es | 53.1 | 55.2 | -2.1 | 68.8 | -15.7 |
| es→pt | 54.7 | 68.8 | -14.1 | 59.1 | -4.4 |
| pt→fr | 63.5 | 69.6 | -6.1 | 68.8 | -5.3 |
| fr→pt | 61.0 | 68.8 | -7.8 | 67.2 | -6.2 |
| de→pt | 59.9 | 68.8 | -8.9 | 66.1 | -6.2 |
| pt→it | 51.7 | 55.9 | -4.2 | 68.8 | -17.1 |
| it→pt | 54.0 | 68.8 | -14.8 | 58.8 | -4.8 |
| ru→uk | 52.7 | 53.5 | -0.8 | 59.6 | -6.9 |

Perda média contra inglês → destino: **-7.3 pontos** de fidelidade.

## d) Português de Portugal ou do Brasil? (saídas inglês → português)

- Frases do Praxis com alguma marca de **português de Portugal**: **1 de 60 (2%)**.
- Frases do Praxis com alguma marca de **português do Brasil**: 6 de 60 (10%).
- Para comparar, a tradução humana brasileira das mesmas frases: 0 com marca de Portugal, 9 com marca do Brasil.
- Marcas de Portugal encontradas no Praxis: actual/acção (grafia antiga) (1).
- Marcas do Brasil encontradas no Praxis: você (3), equipe (1), estar + gerúndio (ex.: está fazendo) (2).

Exemplos:

- “O relatório é altamente crítico com quase todos os aspectos da atual política do Executivo em relação ao Iraque e insta a uma mudança imediata de direcção.” — marcas: actual/acção (grafia antiga)

## e) Tempo por frase

- Mais lentas: en→fr 237 ms (máx. 371 ms); en→ar 231 ms (máx. 404 ms); en→pl 230 ms (máx. 376 ms); pt→fr 229 ms (máx. 337 ms); en→de 221 ms (máx. 356 ms).
- Média geral: 197 ms por frase.

## Piores direções

1. en→pl — fidelidade 49.6, coincidência 19.7
2. pt→it — fidelidade 51.7, coincidência 21.3
3. ja→en — fidelidade 51.9, coincidência 23.8
4. ru→uk — fidelidade 52.7, coincidência 23.6
5. pt→es — fidelidade 53.1, coincidência 23.8

### Exemplos da pior direção (en→pl)

- **Original:** Fire rescue crews eventually doused the fire by 11:35 pm.
  - **Humano:** Załogi straży pożarnej ostatecznie ugasiły ogień przed godz. 23:35.
  - **Praxis:** Zespół ratowniczy nagle zamknął pożar o 11:35.

- **Original:** Today, the only insects that cannot fold back their wings are dragon flies and mayflies.
  - **Humano:** Dziś do jedynych owadów nieposiadających zdolności składania skrzydeł należą ważki i jętki.
  - **Praxis:** Dzisiaj jedynymi owadami, które nie potrafią złożyć skrzydła, są muchy smoka i muchy majów.

- **Original:** Plants make their food from the sun by photosynthesis. They also provide shade.
  - **Humano:** Fotosynteza to proces, w którym rośliny wykorzystują światło słoneczne do produkcji substancji odżywczych. Rośliny dają też cień.
  - **Praxis:** Rośliny wytwarzają swoje jedzenie ze słońca poprzez fotosyntezę. Zapewniają również cień.

- **Original:** So, it is likely that the notation was added simply as a label.
  - **Humano:** W związku z tym można założyć, że adnotację dodano w charakterze etykiety opisowej.
  - **Praxis:** Jest więc prawdopodobne, że notacja została dodana po prostu jako etykieta.

- **Original:** It is thinner under the maria and thicker under the highlands.
  - **Humano:** Jest cieńsza pod morzami księżycowymi i grubsza pod wyżynami.
  - **Praxis:** Jest cienkiej pod Mariami, a grubszej pod górami.

## Saídas suspeitas

Total: 5 saídas em 5 direções.

- uk→en: letras do idioma de origem vazaram — original “Спершу шоу транслювали виключно на давно працюючому Інтернет-радіо ТогіНет Радіо – сайті, присвяченому радіобесідам.” → Praxis “The show was originally broadcast exclusively on the long-running Internet radio station Toginet Radio  сай, a website dedicated to radio talk shows.”
- ja→en: quase nada em comum com a humana (possível frase inventada) — original “そのため、単にラベルとして表記が追加されがちです。” → Praxis “That's why we often just add labels.”
- ko→en: muito mais curta que a humana — original “원단이 너무 뜨거워지지 않도록 주의하세요(원단이 수축하거나 그을릴 수 있습니다).” → Praxis “Be careful not to get too hot.”
- en→ru: quase nada em comum com a humana (possível frase inventada) — original “Rip currents are the returning flow from waves breaking off the beach, often at a reef or similar.” → Praxis “Рип-потоки - это возвращающийся поток от волн, отрывающихся от пляжа, часто на рифе или аналогичном.”
- en→pl: quase nada em comum com a humana (possível frase inventada) — original “Fire rescue crews eventually doused the fire by 11:35 pm.” → Praxis “Zespół ratowniczy nagle zamknął pożar o 11:35.”

## O que isso significa

Das 27 direções de uma etapa só (sem contar o en→zh, medido à parte), 10 ficaram com fidelidade de 60 ou mais (tradução boa e fácil de entender); 1 ficaram abaixo de 50 (en→pl), faixa em que quem ouve entende a ideia geral mas perde detalhes e às vezes o sentido. Passar pelo inglês custa em média 7.3 pontos de fidelidade frente à tradução direta do inglês para o mesmo idioma: os erros das duas etapas se somam. No português, 2% das frases traduzidas do inglês têm alguma marca de português de Portugal — para quem ouve no Brasil isso soa estrangeiro, mas raramente atrapalha o entendimento. Lembre que estas frases são textos de notícia e enciclopédia, mais difíceis que conversa do dia a dia, e que aqui o texto entra perfeito: numa chamada real, os erros da transcrição da fala somam-se a estes.
