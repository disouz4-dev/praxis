#!/bin/bash
# Praxis — constrói PraxisAudio.driver (binário universal Intel + Apple Silicon),
# roda os testes e assina ad hoc (assinatura local, sem certificado da Apple).
#
# Uso: ./construir.sh                 (construção normal)
#      ./construir.sh --limpo         (apaga a pasta de construção antes)
#      ./construir.sh --diagnostico   (liga o registro detalhado no registro
#                                      do sistema, só para depurar)
#
# Não precisa de sudo e não instala nada. Na primeira vez baixa a libASPL
# (https://github.com/gavv/libASPL, licença MIT) com git, dentro de build/.
# Resultado: app/macos/driver/build/PraxisAudio.driver

set -euo pipefail

PASTA="$(cd "$(dirname "$0")" && pwd)"
CONSTRUCAO="$PASTA/build"
DRIVER="$CONSTRUCAO/PraxisAudio.driver"
FUNCAO_FABRICA="PraxisAudioFabrica"

if [[ "$(uname)" != "Darwin" ]]; then
  echo "Este script só roda no macOS." >&2
  exit 1
fi

for programa in cmake git codesign plutil lipo nm; do
  if ! command -v "$programa" >/dev/null 2>&1; then
    echo "Falta o programa '$programa'. Instale as ferramentas do Xcode e o cmake." >&2
    exit 1
  fi
done

DIAGNOSTICO=OFF
for opcao in "$@"; do
  case "$opcao" in
    --limpo) rm -rf "$CONSTRUCAO" ;;
    --diagnostico) DIAGNOSTICO=ON ;;
    *) echo "Opção desconhecida: $opcao" >&2; exit 1 ;;
  esac
done

echo "==> Configurando"
cmake -S "$PASTA" -B "$CONSTRUCAO" -DCMAKE_BUILD_TYPE=Release -DPRAXIS_DIAGNOSTICO="$DIAGNOSTICO"

echo "==> Compilando"
cmake --build "$CONSTRUCAO" --parallel "$(sysctl -n hw.ncpu)"

echo "==> Testes"
(cd "$CONSTRUCAO" && ctest --output-on-failure)

echo "==> Assinando ad hoc"
codesign --force --sign - --timestamp=none "$DRIVER"

echo "==> Conferindo o pacote"
plutil -lint "$DRIVER/Contents/Info.plist"
codesign --verify --strict --verbose=2 "$DRIVER"
echo "Arquiteturas: $(lipo -archs "$DRIVER/Contents/MacOS/PraxisAudio")"

# A função que o Info.plist aponta em CFPlugInFactories tem que estar exportada.
FUNCAO_NO_PLIST="$(/usr/libexec/PlistBuddy -c 'Print :CFPlugInFactories' "$DRIVER/Contents/Info.plist" | awk -F' = ' '/=/{print $2}')"
if [[ "$FUNCAO_NO_PLIST" != "$FUNCAO_FABRICA" ]]; then
  echo "ERRO: o Info.plist aponta '$FUNCAO_NO_PLIST', esperado '$FUNCAO_FABRICA'." >&2
  exit 1
fi
for arq in $(lipo -archs "$DRIVER/Contents/MacOS/PraxisAudio"); do
  if ! nm -gU -arch "$arq" "$DRIVER/Contents/MacOS/PraxisAudio" | grep -q " T _$FUNCAO_FABRICA\$"; then
    echo "ERRO: a função de fábrica não está exportada na arquitetura $arq." >&2
    exit 1
  fi
done
echo "Função de fábrica exportada: _$FUNCAO_FABRICA"

# Carrega de novo o pacote já assinado, como o coreaudiod faria.
"$CONSTRUCAO/testes/teste_carregar" "$DRIVER"

echo
echo "Pronto: $DRIVER"
echo "Para instalar (pede a senha de administrador): sudo \"$PASTA/instalar.sh\""
