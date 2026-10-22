# PraxisAudio.driver — microfone virtual do Praxis no macOS

Driver de áudio próprio do Praxis (licença MIT). É um "Audio Server Plug-in":
um plug-in que o servidor de áudio do macOS (o `coreaudiod`) carrega da pasta
`/Library/Audio/Plug-Ins/HAL`. Ele cria dois dispositivos virtuais, com os
mesmos nomes usados no Linux e no Windows:

| Nome visível     | Identificador único (UID)       | Para que serve |
|------------------|---------------------------------|----------------|
| `Praxis Mic`     | `dev.disouz4.praxis.mic`        | O Praxis toca a fala traduzida nele; o app de chamada (Zoom, Meet, Discord) escolhe "Praxis Mic" como microfone. |
| `Praxis Speaker` | `dev.disouz4.praxis.speaker`    | Modo bilateral manual: o app de chamada toca nele (escolhido como alto-falante) e o Praxis grava dele. |

Cada dispositivo tem uma saída **e** uma entrada ligadas em laço: o que é
tocado na saída sai na entrada do mesmo dispositivo. Os dois são separados
(tocar no Mic não aparece no Speaker).

- Formato: 2 canais, ponto flutuante de 32 bits, 48 kHz (também aceita 44,1 kHz;
  entrada e saída mudam juntas).
- Demora do laço: cerca de dois ciclos de áudio (poucos milissegundos); o laço
  é só memória.
- Silêncio quando ninguém está tocando; nunca reaparece áudio velho.
- Fabricante: `Praxis`. Identificador do pacote: `dev.disouz4.praxis.audio`.
- Não recebe os sons de alerta do sistema (para não vazarem na chamada).
- Não tem controle de volume: o volume é o de quem toca.

## Como é feito

- `fonte/AnelAmostras.hpp` — anel de amostras do laço, indexado pelo tempo em
  amostras que o coreaudiod informa (a saída escreve no tempo de saída, a
  entrada lê no tempo de entrada, que vem um pouco atrás). Sem alocação nem
  trava no caminho de tempo real.
- `fonte/DispositivoLaco.*` — os dispositivos, montados com a biblioteca
  [libASPL](https://github.com/gavv/libASPL) (MIT), versão fixa v3.1.2. A
  libASPL é baixada pelo CMake com `git` para `build/` (não fica no
  repositório).
- `fonte/PontoDeEntrada.cpp` — a função de fábrica `PraxisAudioFabrica`, que o
  `Info.plist` aponta em `CFPlugInFactories`. É o único símbolo exportado.
- `testes/` — testes que rodam sem instalar nada (veja abaixo).
- `AVISOS-DE-TERCEIROS.md` — origem e licenças do código de terceiros.

Nenhum código do BlackHole foi usado.

## Construir (não precisa de sudo)

Precisa das ferramentas do Xcode (`xcode-select --install`), `cmake` e `git`.

```sh
cd app/macos/driver
./construir.sh            # ou ./construir.sh --limpo para começar do zero
```

O script configura, compila um binário universal (Intel `x86_64` + Apple
Silicon `arm64`, macOS 10.15 ou mais novo), roda os testes, assina ad hoc
(`codesign -s -`) e confere o pacote (`plutil -lint`, `codesign --verify`,
função de fábrica exportada nas duas arquiteturas, carregamento do pacote
assinado). Resultado: `app/macos/driver/build/PraxisAudio.driver`.

Para depurar depois de instalado, `./construir.sh --diagnostico` liga o
registro detalhado da libASPL no registro do sistema.

### Testes que rodam sem instalar

`ctest` (chamado pelo `construir.sh`) roda três programas:

1. `anel_de_amostras` — escrita e leitura, volta do anel sem estalos (também
   com blocos de tamanhos aleatórios por muitas voltas), leitor mais rápido que
   o escritor, silêncio, buracos na escrita, relógio reiniciado, limpeza.
2. `dispositivos_de_laco` — o teste faz o papel do coreaudiod e chama as mesmas
   operações de entrada e saída: confere nomes, identificadores, fabricante,
   formato, o laço de ponta a ponta no Mic e no Speaker, a separação entre os
   dois e a troca de taxa para 44,1 kHz.
3. `carregar_driver` — carrega o `PraxisAudio.driver` construído pelo mesmo
   mecanismo de plug-ins que o coreaudiod usa (fábrica do `Info.plist`),
   inicializa com um hospedeiro falso e lê pela interface em C a lista de
   dispositivos, nomes, identificadores e fluxos.

Conferências manuais do pacote:

```sh
plutil -lint build/PraxisAudio.driver/Contents/Info.plist
codesign -dv build/PraxisAudio.driver
lipo -archs build/PraxisAudio.driver/Contents/MacOS/PraxisAudio   # x86_64 arm64
nm -gU build/PraxisAudio.driver/Contents/MacOS/PraxisAudio        # T _PraxisAudioFabrica
plutil -p build/PraxisAudio.driver/Contents/Info.plist | grep -A2 CFPlugInFactories
```

## Instalar (precisa de senha de administrador)

```sh
sudo ./instalar.sh
```

Copia para `/Library/Audio/Plug-Ins/HAL/PraxisAudio.driver`, acerta dono e
permissões, tira a marca de "baixado da internet" e reinicia o coreaudiod (o
som de todos os apps para por 1 ou 2 segundos). No fim espera "Praxis Mic"
aparecer em `system_profiler SPAudioDataType`.

## Desinstalar

```sh
sudo ./desinstalar.sh
```

## Testar depois de instalado (não precisa de sudo)

Automático (precisa do `sox`: `brew install sox`):

```sh
./testar-instalado.sh
```

Na primeira vez o macOS pede permissão de microfone para o Terminal (gravar de
"Praxis Mic" conta como usar um microfone). O script confere: os dois
dispositivos aparecem; tocar um tom em cada um e gravar dele dá som; sem nada
tocando a gravação é silêncio; tocar no Mic não vaza para o Speaker.

Manual, passo a passo:

```sh
# 1. Os dispositivos aparecem?
system_profiler SPAudioDataType | grep -A10 Praxis

# 2. Grava 4 s do Praxis Mic em segundo plano e toca um tom de 440 Hz nele.
sox -t coreaudio "Praxis Mic" -r 48000 -c 2 gravado.wav trim 0 4 &
sleep 0.5
sox -n -r 48000 -c 2 -t coreaudio "Praxis Mic" synth 2 sine 440 vol 0.5
wait

# 3. A gravação tem som? ("RMS amplitude" perto de 0,35; silêncio dá 0)
sox gravado.wav -n stat 2>&1 | grep -i "rms     amplitude"
afplay gravado.wav            # ouvir no alto-falante normal

# Mesmo teste com ffmpeg em vez de sox (gravação pelo AVFoundation):
ffmpeg -f avfoundation -list_devices true -i "" 2>&1 | grep -i praxis
ffmpeg -y -f avfoundation -i ":Praxis Mic" -t 4 gravado-ffmpeg.wav &
sleep 1
sox -n -r 48000 -c 2 -t coreaudio "Praxis Mic" synth 2 sine 440 vol 0.5
wait
ffmpeg -i gravado-ffmpeg.wav -af volumedetect -f null - 2>&1 | grep mean_volume
# perto de -9 dB = tem som; -91 dB = silêncio
```

Teste com app de chamada: no Zoom/Meet/Discord escolha **Praxis Mic** como
microfone; no Praxis escolha **Praxis Mic** como saída; fale e confira o
medidor de nível do microfone no app de chamada.

Se não aparecer nada, veja o registro do coreaudiod:

```sh
log show --last 5m --predicate 'process == "coreaudiod"' | grep -i praxis
```

## Riscos conhecidos

- **Assinatura ad hoc**: serve para uso local. O coreaudiod carrega plug-ins
  com assinatura ad hoc, mas o Gatekeeper (verificação de apps baixados) pode
  bloquear um driver baixado da internet com a marca de quarentena; o
  `instalar.sh` tira essa marca. Para distribuir para outras pessoas, o certo
  é assinar com um certificado "Developer ID" da Apple e notarizar (enviar à
  Apple para verificação automática), de preferência dentro de um instalador
  `.pkg`.
- **Apple Silicon**: o binário tem a fatia `arm64`, mas só foi compilado e
  testado neste Mac Intel. Precisa de um teste real num Mac M1/M2/M3.
- **Verificação sem instalar**: os testes chamam o código do jeito que o
  coreaudiod chama, mas o comportamento real do coreaudiod (relógio, tamanho
  dos ciclos, troca de taxa por apps) só se confirma depois de instalar.
