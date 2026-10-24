#!/bin/bash
# Praxis — instala o PraxisAudio.driver no macOS.
#
# Uso: sudo ./instalar.sh [caminho/para/PraxisAudio.driver]
#      (sem caminho, usa build/PraxisAudio.driver gerado pelo ./construir.sh)
#
# O que faz:
#   1. copia o driver para /Library/Audio/Plug-Ins/HAL/PraxisAudio.driver
#      (troca uma versão antiga, se houver);
#   2. acerta dono (root) e permissões, e tira a marca de "baixado da internet";
#   3. reinicia o coreaudiod (o servidor de áudio do macOS). O som de TODOS os
#      apps para por 1 ou 2 segundos e volta sozinho.
#
# Precisa de senha de administrador (sudo).

set -euo pipefail

PASTA="$(cd "$(dirname "$0")" && pwd)"
ORIGEM="${1:-$PASTA/build/PraxisAudio.driver}"
DESTINO_PASTA="/Library/Audio/Plug-Ins/HAL"
DESTINO="$DESTINO_PASTA/PraxisAudio.driver"

if [[ "$(uname)" != "Darwin" ]]; then
  echo "Este script só roda no macOS." >&2
  exit 1
fi

if [[ "$EUID" -ne 0 ]]; then
  echo "Precisa de administrador. Rode: sudo \"$0\" ${1:+\"$1\"}" >&2
  exit 1
fi

if [[ ! -f "$ORIGEM/Contents/Info.plist" || ! -f "$ORIGEM/Contents/MacOS/PraxisAudio" ]]; then
  echo "Driver não encontrado em: $ORIGEM" >&2
  echo "Construa antes com: \"$PASTA/construir.sh\"" >&2
  exit 1
fi

if ! codesign --verify --strict "$ORIGEM" 2>/dev/null; then
  echo "A assinatura do driver não confere: $ORIGEM" >&2
  echo "Construa de novo com: \"$PASTA/construir.sh\"" >&2
  exit 1
fi

echo "==> Copiando para $DESTINO"
mkdir -p "$DESTINO_PASTA"
rm -rf "$DESTINO"
ditto "$ORIGEM" "$DESTINO"
chown -R root:wheel "$DESTINO"
chmod -R u=rwX,go=rX "$DESTINO"
xattr -dr com.apple.quarantine "$DESTINO" 2>/dev/null || true

echo "==> Reiniciando o coreaudiod"
if ! launchctl kickstart -k system/com.apple.audio.coreaudiod 2>/dev/null; then
  killall coreaudiod 2>/dev/null || true
fi

echo "==> Esperando os dispositivos aparecerem"
for _ in $(seq 1 20); do
  sleep 1
  if system_profiler SPAudioDataType 2>/dev/null | grep -q "Praxis Mic"; then
    system_profiler SPAudioDataType 2>/dev/null | grep "Praxis"
    echo "Instalado."
    exit 0
  fi
done

echo "O driver foi copiado, mas \"Praxis Mic\" ainda não apareceu." >&2
echo "Veja o registro: log show --last 2m --predicate 'process == \"coreaudiod\"' | grep -i praxis" >&2
exit 1
