# Praxis — Relatório de Qualidade (v0.1.0 → v0.2.0)

_Data: 2026-10-20 · Escopo: auditoria completa do código, testes rápidos de funcionamento, testes unitários e de interface,
portabilidade entre sistemas, benchmarks de qualidade da transcrição e de atraso com fala humana real._

**Termos usados neste relatório** (explicados uma vez aqui):

- **Taxa de erro de palavras** — parcela das palavras transcritas errado, puladas ou inventadas em relação ao texto
  real (em inglês, WER). **Taxa de erro de caracteres** é o mesmo, contado por letra (usada em chinês, japonês e coreano,
  idiomas em que o limite das palavras é ambíguo).
- **Fidelidade da tradução (0–100)** — compara a tradução do que foi ouvido com a tradução do texto real; 100 =
  idênticas (métrica chrF).
- **Atraso típico** — a mediana: metade dos casos é mais rápida que isso (p50). **Pior caso comum (1 em 20)** —
  só 1 em cada 20 casos é mais lento que isso (p95).
- **Velocidade de transcrição** — tempo gasto transcrevendo ÷ duração do áudio; menor = mais rápido (RTF).
- **Detector de fala** — o componente que decide quando alguém está falando e onde cortar os trechos (VAD).
- **Transcrição / tradução / voz** — as três etapas do motor: fala → texto (Whisper), texto → outro idioma
  (Argos), texto → fala sintetizada (Piper).
- **Placa de vídeo** (GPU) e **processador** (CPU).

## Resumo

| Área | v0.1.0 | v0.2.0 |
|---|---|---|
| Sistemas | Só Linux (PulseAudio/PipeWire) | Linux · macOS · Windows |
| Fala contínua em tempo real, todos os 16 idiomas (rodada 2) | não testado | Placa de vídeo, `large-v3-turbo`: 12% de erro em média, 0.8–2.3 s, acompanha 16/16 · processador, `small`: 24%, 1.8–3.0 s, 16/16 |
| Placa de vídeo | Só NVIDIA CUDA | NVIDIA CUDA · Apple Silicon (MLX) · AMD/Intel (whisper.cpp Vulkan, opcional) · detectada automaticamente |
| Testes automáticos | nenhum | 115 testes rápidos (unitários, de funcionamento, de interface) + verificações lentas de qualidade/atraso |
| Integração contínua | nenhuma | GitHub Actions: Linux/macOS/Windows × Python 3.10/3.12 + benchmarks |
| Taxa de erro de palavras na transcrição ao vivo (pt, Whisper `small`, rodada 1) | **26.4%** | **16.7%** |
| Taxa de erro de palavras na transcrição ao vivo (en / es) | 8.7% / 13.8% | 5.3% / 6.9% |
| Atraso de ponta a ponta (fim da fala → primeiro áudio, atraso típico, processador) | — | **1.8–2.1 s** (processador Intel i9, `small`) |
| PyTorch obrigatório | sim (~550 MB) | não (só para a clonagem de voz opcional) |

## Como foi testado

* **Auditoria estática** de todas as 5,8 mil linhas (motor, interface, instalador) — cada problema abaixo tem
  arquivo/linha, um cenário de falha e (quando possível) um teste de regressão.
* **Funcionamento básico**: `praxis.py --check` / `--list-devices` em todos os sistemas na integração contínua; a
  interface real é montada, troca de abas em vários idiomas de interface, alterna o tema, salva e fecha
  (`tests/test_gui_smoke.py`).
* **Unitários**: interpretadores de saída (pactl, xrandr), reamostragem, detecção do driver de loopback, segmentação
  pelo detector de fala, divisão de frases, tradução via idioma intermediário, persistência da configuração,
  downloads atômicos, pipeline completo com substitutos falsos.
* **Fala real**: 34 gravações de 34 falantes voluntários diferentes em pt / en / es
  (Multilingual LibriSpeech + LibriSpeech, CC BY 4.0) com transcrições de referência feitas por pessoas.
  A qualidade é medida como taxa de erro de palavras/caracteres em dois modos: a frase inteira (melhor resultado
  possível) e **ao vivo** — o áudio passa bloco a bloco pelo `vad_worker` real do motor, exatamente como numa
  chamada.
* **Atraso**: por etapa (espera pelo silêncio, transcrição, tradução, voz da primeira frase) com a mesma fala real.

## Bugs críticos encontrados e corrigidos

| # | Onde | Bug | Impacto | Correção |
|---|---|---|---|---|
| 1 | motor | PyTorch (detector de fala Silero, Argos→stanza) e CTranslate2 (Whisper) carregam **dois runtimes OpenMP** | **Falha fatal (segfault) na primeira transcrição no macOS** | O motor não usa mais o torch: detector de fala Silero no ONNX Runtime, modelos do Argos rodando direto no CTranslate2 |
| 2 | motor | Argos/CTranslate2 com `compute_type="auto"` escolhe int8 em muitos processadores | **es→en (e toda tradução es→X via intermediário) sai como lixo** ("mainstremainstre…") — também afeta a v0.1.0 | `compute_type="default"`; verificação de sanidade da tradução na integração contínua |
| 3 | motor | Fala cortada a cada 4 s no meio da palavra, com o estado do detector de fala zerado a cada corte | Taxa de erro de palavras ao vivo em pt de 26.4% vs 15.5% para o mesmo áudio inteiro | Corte no ponto mais silencioso dos últimos 1.5 s sem zerar o detector de fala; limite aumentado para 6 s (medido abaixo) |
| 4 | motor | Sem pré-gravação: o buffer só começa *depois* que o detector de fala dispara | Primeira sílaba de toda frase perdida ("a soberba" → "sobre a") | 250 ms de pré-gravação |
| 5 | motor | Loops de alucinação do Whisper em trechos curtos cortados | Até 991% de erro de palavras numa única gravação ("o que é o que é …" ×100), traduzido e falado em voz alta | Proteção contra repetição em toda transcrição |
| 6 | interface | `pw-metadata` chamado sem proteção na abertura e no fechamento | **O app não abre** sem PipeWire (qualquer macOS/Windows, Linux só com PulseAudio); não fecha se ele travar | Camada de plataforma, sem efeito nos outros sistemas |
| 7 | interface | Pillow importado sem proteção na tela de abertura, mas ausente das dependências do instalador | **O app não abre** numa instalação limpa (reproduzido no macOS) | Pillow opcional, PNG nativo do Tk; Pillow incluído nos requisitos |
| 8 | interface | A função de áudio da aba Clonar chama o Tk ~350×/s a partir da thread do PortAudio | Travamento ao fechar / "main thread is not in main loop" (reproduzido) | Consulta periódica na thread principal a 30 Hz |
| 9 | motor | Dispositivos virtuais só removidos ao sair normalmente | Cada falha ao iniciar deixa módulos do PulseAudio para trás (dispositivos "Praxis_Microfone" duplicados) | Limpeza com `try/finally` |
| 10 | motor | Uma exceção na transcrição/tradução mata a thread de trabalho daquela direção | A tradução para em silêncio pelo resto da chamada | Tratamento de erro por trecho + evento `error` |

## Outros bugs corrigidos

**Motor (`praxis.py`)**
- `tempfile.mktemp`: um WAV gravado por trecho e nunca apagado (vazamento de disco, inseguro); referência do
  OmniVoice compartilhada pelas duas direções via variáveis globais (condição de corrida) → arquivo por voz e por
  direção.
- Bilateral + aperte-para-falar: o áudio do interlocutor era controlado pela *sua* tecla de aperte-para-falar, e
  soltá-la pausava as duas direções → o interlocutor sempre usa o detector de fala; pausar/retomar afeta as duas.
- `reload_voice` com um caminho inexistente era ignorado em silêncio (interface presa em "Aplicando…") → evento de
  erro.
- Validação de `--voice-out`, verificação de faixa de `--gate-threshold`, comandos `--check` e `--list-devices`.

**Interface (`praxis_config.py`)**
- A troca de abas usava `"Config" in label` → a aba Config nunca voltava em de/ru/zh/pl/uk/tr/ar/hi.
- O idioma da interface nunca era salvo; `_save()` não atualizava a configuração em memória, então alternar o tema
  depois sobrescrevia as configurações salvas com as da abertura.
- A voz "Tugão (PT)" nunca podia ser baixada (URL com caracteres fora do ASCII). Downloads interrompidos deixavam
  um `.onnx` parcial que aparecia como instalado → `.part` atômico + renomear, URL codificada.
- `_toggle_monitor` definido duas vezes: o botão de monitoramento da aba Clonar alternava o monitoramento do
  *motor* e o monitoramento do microfone nunca funcionou.
- As mensagens de status do teste de clonagem eram todas descartadas (`after(0, configure, kw)` passava um
  dicionário como argumento posicional).
- O recorte gravava toda referência no mesmo `/tmp/ov_ref_trim.wav` → importar um WAV longo e gerar salvava um
  clone de 5 s. Todos os caminhos fixos `/tmp/...` → pasta temporária privada por usuário.
- ffmpeg ausente / tempo esgotado / WAV inválido derrubavam a importação; erros ao salvar a gravação deixavam
  "Salvando…" para sempre.
- Reinício do motor: a thread de leitura antiga postava eventos velhos na nova sessão; `terminate()` sem `wait()`
  deixava processos zumbis; arquivos de log ficavam abertos; um motor que travava deixava a interface presa em
  "Rodando…" sem mensagem → parada elegante (comando `stop` → SIGTERM → SIGKILL), janela de falha com o fim do log.
- Transcrições bilaterais da outra pessoa apareciam como suas (`dir` ignorado) → marcadas com "←".
- `pactl set-default-source/sink` mudava para sempre os padrões do sistema → restaurados ao fechar (Linux),
  índices de dispositivo explícitos nos outros sistemas.
- Configuração corrompida/editada à mão derrubava a abertura (`None`/texto onde se esperava um número);
  gravação não atômica → conversão de tipos + gravação atômica.
- Janela mais alta que telas de 768 px; a thread de progresso da tela de abertura mexia no Tk fora da thread
  principal; saída mono rejeitada pelo CoreAudio (`AUHAL -50`); classe morta `MonitorWindow` removida.
- Ícone do app: o Dock/barra de tarefas mostrava o foguete do Python → ícone do Praxis (PNG/ICO/ICNS), nome do
  processo no macOS, pacote `Praxis.app`, `.desktop` no Linux, atalhos no Windows.

**Instalador**
- Só `apt-get`; não copiava `assets/` (sem logo/ícone depois de instalar); dependências faltando (`soundfile`,
  `pynput`, `pillow`, `requests`); instalava o PyTorch sempre → `install.sh` para
  apt/dnf/pacman/zypper/Homebrew, `install.ps1` para Windows, autoverificação no final.

## Qualidade da transcrição (fala real, Whisper `small`, processador)

| Modelo | Idioma | Gravações | Erro de palavras, frase inteira | Erro de palavras ao vivo (motor v0.1.0) | Velocidade de transcrição |
|---|---|---:|---:|---:|---:|
| base | pt | 10 | 28.7% | 120.9% | 0.06 |
| base | en | 12 | 5.8% | 10.7% | 0.08 |
| base | es | 12 | 11.0% | 93.4% | 0.06 |
| small | pt | 10 | 15.5% | 26.4% | 0.18 |
| small | en | 12 | 3.9% | 8.7% | 0.23 |
| small | es | 12 | 11.0% | 13.8% | 0.18 |

_Máquina: Intel Core i9-9980HK (MacBook Pro 2019), processador com int8, Python 3.12. Velocidade de transcrição = tempo transcrevendo ÷ duração do áudio._ A taxa de erro de palavras ao vivo acima de 100% do modelo `base` vem de loops de alucinação nos cortes de 4 s (uma gravação: 991%).

### O que cada mudança rendeu (taxa de erro de palavras ao vivo)

| Variante | pt | en | es |
|---|---:|---:|---:|
| A — segmentação da v0.1.0 (corte seco a cada 4 s), detector de fala no ONNX | 24.0% | 7.3% | 14.1% |
| B — + proteção contra repetição | 24.0% | 7.3% | 14.1% |
| C — + 250 ms de pré-gravação | 19.4% | 7.8% | 11.6% |
| D — + corte inteligente, limite de 4 s | 20.5% | 7.8% | 12.8% |
| **E — corte inteligente, limite de 6 s (novo padrão)** | **16.7%** | **5.3%** | **6.9%** |
| F — corte inteligente, limite de 8 s | 14.3% | 5.3% | 6.6% |
| G — D sem o filtro de detecção de fala interno do Whisper | 20.5% | 7.8% | 12.8% |

Taxa de erro de palavras com a frase inteira (melhor resultado possível): pt 15.5% · en 3.9% · es 11.0%. A pré-gravação recupera a primeira sílaba (−4.6 pontos em pt). O corte inteligente só compensa com um limite maior: com 4 s ele ainda divide a maioria das frases; com 6 s a taxa de erro ao vivo cai 30% (pt), 27% (en), 51% (es) em relação à v0.1.0. Com 8 s fica ~2 pontos melhor em pt, mas acrescenta até 2 s de espera durante fala sem pausa, por isso 6 s é o padrão (`--max-segment` para mudar). A proteção contra repetição não muda nada para o `small`, mas elimina os loops catastróficos do `base`; desligar o filtro de detecção de fala interno do Whisper não tem efeito.

## Atraso

_Máquina: macOS-26.6.2-x86_64-i386-64bit · processador i386 · 16 núcleos · Python 3.12.15 · placa de vídeo CUDA: não_

Modelo Whisper: `small` · roda em: processador

| Par | Gravações | Espera pelo silêncio | Transcrição | Tradução | Voz (1ª frase) | **Total, atraso típico** | **Total, pior caso comum (1 em 20)** |
|---|---:|---:|---:|---:|---:|---:|---:|
| pt->en | 10 | 288 | 1666 | 56 | 110 | **2112 ms** | **2595 ms** |
| en->pt | 10 | 272 | 1392 | 48 | 92 | **1841 ms** | **1921 ms** |
| es->en | 10 | 256 | 1467 | 135 | 108 | **1962 ms** | **2182 ms** |

Valores por etapa em ms, atraso típico (mediana). Total = do fim da fala até a primeira amostra de áudio traduzido pronta (início da reprodução).

Do fim da fala ao primeiro áudio traduzido, medido no último trecho ao vivo de 10 frases reais por par. A
transcrição é ~80% do total neste processador; espera-se que as opções com placa de vídeo (CUDA / MLX) reduzam
essa etapa várias vezes, mas elas não foram medidas aqui. A espera pelo silêncio (256–288 ms) é o silêncio de
200 ms que o detector de fala aguarda mais a granularidade de blocos de 32 ms. O custo de orquestração (filas,
threads, divisão de frases) é verificado como < 50 ms em `test_pipeline_overhead_latency`. Todas as verificações
lentas passam (`pytest -m slow`: 10 aprovadas — limites de taxa de erro ao vivo, nenhum loop de alucinação,
sanidade da tradução em 4 pares, atraso).

## Rodada 2 — fala contínua em tempo real, todos os 16 idiomas

_Máquina: lab2 — Linux Mint 22.3, placa de vídeo NVIDIA RTX 3050 6 GB, processador de 16 threads. Ferramenta: `benchmarks/stream_test.py`._

**Método.** Para cada idioma que o Praxis entende (14 idiomas de saída + ja, ko só como entrada), uma gravação
de ~60–75 s de fala real contínua é entregue aos workers reais do motor em tempo real, 32 ms por vez, exatamente
como um microfone. pt/es/fr/de/it/nl/pl usam um único leitor de audiolivro com as pausas originais
(Multilingual LibriSpeech), en um capítulo do LibriSpeech, e ru/zh/uk/tr/ar/hi/ja/ko frases consecutivas do FLEURS
(os falantes se alternam). O teste conhece o texto de antemão e acompanha cada trecho: erros de transcrição
(trocados / pulados / inventados), quanto os erros de transcrição mudam a tradução, o atraso do fim de cada trecho
de fala até o primeiro áudio traduzido, para onde vai esse tempo (fila, transcrição, tradução, voz, espera pela fala
anterior) e se o motor acompanha: atraso típico ≤ 4 s, sem crescimento entre a primeira e a segunda metade, ≤ 8 s
de tradução pendente quando o falante para. A fala traduzida é "tocada" pela sua duração real, então vozes lentas e
traduções longas aparecem como atraso.
Depois, `en →` cada um dos outros 13 idiomas de saída testa a tradução + voz de todos os idiomas.

| Equipamento | Modelo | Erro médio, 16 idiomas | pt | en | es | Atraso típico | Acompanha |
|---|---|---:|---:|---:|---:|---:|---:|
| Placa de vídeo (RTX 3050) | tiny | 47% | 29% | 6% | 19% | 0,4–1,6 s | 16/16 |
| Placa de vídeo (RTX 3050) | base | 36% | 16% | 3% | 11% | 0,4–1,7 s | 15/16 |
| Placa de vídeo (RTX 3050) | small | 22% | 8% | 2% | 3% | 0,5–2,0 s | 16/16 |
| Placa de vídeo (RTX 3050) | medium | 15% | 5% | 4% | 5% | 0,8–2,3 s | 16/16 |
| Placa de vídeo (RTX 3050) | large-v3 | 11% | 6% | 3% | 3% | 1,1–2,7 s | 16/16 |
| Placa de vídeo (RTX 3050) | **large-v3-turbo** | 10% | 5% | 1% | 3% | 0,8–2,3 s | 16/16 |
| Processador (lab2) | tiny | 52% | 32% | 7% | 18% | 0,6–1,6 s | 16/16 |
| Processador (lab2) | base | 38% | 14% | 6% | 12% | 0,8–2,2 s | 15/16 |
| Processador (lab2) | **small** | 22% | 8% | 3% | 3% | 1,8–3,0 s | 16/16 |
| Processador (lab2) | medium | 15% | 5% | 5% | 5% | 4,2–16,0 s | 0/16 |
| Processador (lab2) | large-v3-turbo | 10% | 5% | 2% | 3% | 6,8–25,7 s | 0/16 |

### Resultado por idioma (o que o modo automático usa)

| Idioma | Placa de vídeo: erro | erro por letra | atraso | Processador: erro | erro por letra | atraso |
|---|---:|---:|---:|---:|---:|---:|
| Português | 5% | 1% | 1,1 s | 8% | 3% | 2,0 s |
| Inglês | 1% | 1% | 1,1 s | 3% | 1% | 1,9 s |
| Espanhol | 3% | 1% | 0,9 s | 3% | 1% | 1,9 s |
| Francês | 8% | 6% | 1,3 s | 25% | 13% | 2,6 s |
| Alemão | 18% | 5% | 0,9 s | 29% | 10% | 1,8 s |
| Italiano | 14% | 5% | 1,5 s | 32% | 9% | 2,3 s |
| Russo | 7% | 4% | 1,8 s | 16% | 5% | 2,7 s |
| Chinês (por letra) | 6% | 6% | 1,4 s | 29% | 29% | 2,3 s |
| Holandês | 12% | 4% | 0,9 s | 21% | 9% | 1,8 s |
| Polonês | 3% | 1% | 0,9 s | 16% | 3% | 2,1 s |
| Ucraniano | 8% | 4% | 0,8 s | 19% | 5% | 1,9 s |
| Turco | 12% | 4% | 1,4 s | 24% | 6% | 2,0 s |
| Árabe | 13% | 6% | 1,6 s | 31% | 10% | 2,7 s |
| Híndi | 34% | 15% | 0,9 s | 70% | 37% | 2,2 s |
| Japonês (por letra) | 11% | 11% | 1,8 s | 20% | 20% | 2,7 s |
| Coreano (por letra) | 7% | 7% | 2,3 s | 8% | 8% | 3,0 s |

Placa de vídeo = `large-v3-turbo` na RTX 3050; processador = `small`. Erro = palavras erradas, puladas ou inventadas (chinês, japonês e coreano medidos por letra, porque nesses idiomas o limite das palavras é ambíguo). Erro por letra = o mesmo contado letra a letra: mostra quando o erro é de grafia (ex.: híndi), não de palavra perdida.

Erro = parcela das palavras transcritas errado, puladas ou inventadas, média dos 16 idiomas (chinês, japonês e coreano medidos por letra).
**Negrito** = o que `--model auto` escolhe agora: `large-v3-turbo` com placa de vídeo, `small` no processador.

### Problemas que o teste revelou — e o que foi feito

| # | Problema (como apareceu) | Correção | Antes → depois |
|---|---|---|---|
| 1 | O motor esperava cada tradução terminar de **tocar** antes de transcrever o trecho seguinte (processador, `small`: 4–6 s de atraso, crescendo +38…+94 ms por segundo) | Thread de reprodução ordenada: a transcrição do próximo trecho acontece durante a reprodução | atraso 5.1 → 2.0 s (pt), acompanha 0/3 → 16/16 |
| 2 | Passagens longas sem pontuação faziam a **tradução** entrar em loop ("I have not been able to do so…") | Frases com > 30 palavras (60 caracteres em zh/ja) divididas nas vírgulas, depois pelo tamanho | fidelidade da tradução it→en 8.5 → 54.9 |
| 3 | Um filtro descartava **fala real** sempre que a nota de "não é fala" do Whisper era ≥ 0.5 (0.53–0.59 em frases reais) | A própria regra do Whisper: descartar só se não for fala **e** a confiança for baixa | frases perdidas recuperadas (pt, it, uk) |
| 4 | Sobras de 0.1–0.8 s depois de um corte voltavam **vazias**, perdendo sílabas ("Professor" → "ofessor") | Sobras grudadas no trecho seguinte (ou enviadas após 1 s de silêncio) | trechos vazios 10 → 3 |
| 5 | Tradução para **alemão** falada com 146% da duração original → 38 s de tradução pendente | Voz alemã padrão "MLS" (10.8 letras/s) → "Thorsten" (19.9); vozes lentas calibradas automaticamente para ≥ 15 letras/s | 146% → 82%, acompanha |
| 6 | Traduções para **árabe / hindi / holandês** mais longas que a fala, ficando para trás | Velocidade de fala adaptativa: a voz acelera (×1.15 → ×1.4) conforme a reprodução se acumula | en→ar 121% → 102%, en→nl 111% → 92%, todos os 13 acompanham |
| 7 | Caracteres quebrados "�" vindos do Whisper chegavam à tradução e à fala (hindi) | Removidos antes da tradução | — |
| 8 | Nossa própria métrica separava palavras em hindi/árabe nos sinais vocálicos (escondia erros reais) | A normalização mantém os sinais combinantes; resultados recalculados | hi 46% → 70% (valor real) |
| 9 | `medium` pulava frases inteiras em espanhol | Resolvido pelos itens 3 e 4 | 0 frases puladas em qualquer idioma |

### Ainda limitado (qualidade do modelo, não bugs do motor)

- No processador, o modelo mais preciso que roda em tempo real é o `small`: bom para pt/en/es (3–8% de erro), mas
  16–37% em fr, de, it, zh, nl, tr, ar, ja, ko e ~70% em hindi. O app agora avisa sobre isso e aponta os números
  com placa de vídeo (ex.: fr 25% no processador vs 8% com placa de vídeo).
- Mesmo o `large-v3-turbo` numa placa de vídeo erra 27% em coreano e 34% em hindi (`large-v3`: 24% / 26%).
- Um único trecho ainda pode ter um pico de 4–7 s quando uma frase longa é seguida de mais fala.
- Corpus: ~1 min por idioma, fala lida. Áudio espontâneo e com ruído de chamadas terá resultado pior.

## Rodada 3 — varredura geral dos pontos fracos

Cada fragilidade prevista virou um teste com números. Processador = `small`, placa de vídeo = RTX 3050.

| Fragilidade | Como foi testada | Resultado | O que foi feito |
|---|---|---|---|
| Qualidade real da tradução | 60 frases × 36 direções contra traduções **humanas** (FLEURS) | Argos: fidelidade 55,4 (46–69); en→ar deixa 10% em inglês; ja→en mistura caracteres japoneses em 10%; ru→uk inventou uma frase; passar pelo inglês custa −5,8 | Tradutor **NLLB-200 (Meta)** opcional e automático: fidelidade 58,2, melhor em 22 de 36 direções (+6 a +10 em ar, tr, ko, ja, uk, hi), saídas erradas 14 → 2; 0,2 s/frase na placa de vídeo, ~1,4 s no processador. **Licença não comercial.** |
| Português de Portugal | marcas de pt-PT em en→pt | 1 frase em 60 (Argos), 0 (NLLB) | não é problema |
| Silêncio e ruído de ambiente | 20 s sem fala | 0 palavras inventadas | — |
| Falatório de fundo | 6 vozes em outros idiomas, sem fala do usuário | 25 palavras inventadas (modo pt) | pendente: descartar trecho em outro idioma; recomendar fone |
| Fala com ruído | 16 idiomas com ruído fraco/médio/forte | erro 18,5% → 26% → 39% → 61% | pendente: filtro de redução de ruído |
| Eco (alto-falante → microfone) | tradução vazando a −12 dB | sem proteção: erro 78%, 25 trechos de eco, laços sem fim | **trava de eco**: 0 trechos de eco, erro 49%; guarda de laços sem espaço. Pendente: cancelamento de eco |
| Contexto entre trechos | com e sem, fala normal e pausada | piorou (18,5% → 20,2%) | mantido desligado |
| Velocidade da fala | normal 20 s / 15 s, lenta e pausada; 11 combinações de modelo e computador | a lenta piorou em 11 de 11; a pausada em 10 de 11 | conclusão: falar devagar não ajuda; o problema é cortar a fala |
| Primeiro uso sem internet | sem nada baixado e sem rede | recursão infinita / travado para sempre | mensagem clara em até 22 s |
| Japonês/coreano na 1ª vez | instalação do pacote | quebrava ("No module named 'stanza'") | instalação própria do pacote |
| Clonagem de voz no Mac | PyTorch junto com o Whisper | abortava/travava | modo de compatibilidade medido como estável |
| Picos de atraso | análise de ~1.000 trechos | ~80% vêm de esperar a tradução longa anterior terminar de tocar | pendente: gerar a voz na hora de tocar |
| Interface | varredura automática + defeitos conhecidos | 7 defeitos | corrigidos (tecla de letra no aperte-para-falar, cronômetro, clonagem carregando 2×, apagar clone, widgets fora da thread principal, pasta de clones) |
| Idioma do sistema | — | o app abria sempre em português | herda o idioma do sistema na 1ª execução |

**Pendências que continuam (por gravidade):** cancelamento de eco; redução de ruído; voz de fundo; picos de atraso; Windows nunca testado em máquina real; MLX e Vulkan sem hardware real.

## Suporte a placa de vídeo

`praxis_accel.py` escolhe o backend de cada máquina (para forçar: `--device` / `PRAXIS_DEVICE`):
CUDA → faster-whisper/CTranslate2; Apple Silicon → mlx-whisper; placa de vídeo AMD/Intel → whisper.cpp compilado
com Vulkan (compilação opcional); caso contrário, processador. O Piper usa os provedores CUDA / DirectML / CoreML
quando disponíveis; o OmniVoice usa CUDA ou MPS.

Medido nesta máquina (Intel i9 + AMD Radeon Pro 5500M): o whisper.cpp com **Metal** devolveu `","` para uma frase
de 4 s em português e levou 2.85 s vs 2.10 s no processador — por isso Macs Intel ficam fixos no processador.
A integração contínua não tem placas de vídeo: a lógica de escolha é testada para cada família de equipamento com
simulações (`tests/test_accel.py`). **O CUDA foi verificado em equipamento real** (lab2, RTX 3050) — o que revelou
que as bibliotecas cuBLAS/cuDNN instaladas via pip não eram encontradas sem `LD_LIBRARY_PATH` (o Whisper voltava em
silêncio para o processador; corrigido por `ensure_cuda_libs()`). MLX e Vulkan continuam sem verificação em
equipamento real.

## Problemas conhecidos (não corrigidos nesta rodada)

- Alguns textos da interface ainda estão fixos em português no código (janela de download, painel de
  monitoramento, tela de abertura).
- `ja`/`ko` não têm nomes traduzidos nos menus de idioma.
- Uma gravação reiniciada em menos de 1 s roda duas cadeias de temporizador (para sozinha em ~7 s).
- Capturar uma tecla de *letra* como tecla de aperte-para-falar falha (`KeyCode` do pynput não tem `.name`); os
  atalhos globais do pynput não funcionam no Wayland.
- OmniVoice: "Gerar"/"Testar" em paralelo podem carregar o modelo duas vezes (falta de memória na placa de vídeo);
  a aba Clonar recarrega um modelo Whisper a cada transcrição; apagar um clone não pede confirmação.
- O OmniVoice (opcional) ainda precisa do PyTorch, então no macOS ele pode cair no conflito de OpenMP (#1) quando
  usado junto com o Whisper no mesmo processo.
- O Argos `en→pt` produz português europeu ("estás", "a testar").
