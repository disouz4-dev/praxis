#!/bin/bash
# Praxis — remove o PraxisAudio.driver do macOS.
#
# Uso: sudo ./desinstalar.sh
#
# Apaga /Library/Audio/Plug-Ins/HAL/PraxisAudio.driver e reinicia o coreaudiod
# (o som de todos os apps para por 1 ou 2 segundos). Os apps que estavam usando
# "Praxis Mic" ou "Praxis Speaker" voltam para o dispositivo padrão.

set -euo pipefail

DESTINO="/Library/Audio/Plug-Ins/HAL/PraxisAudio.driver"

if [[ "$(uname)" != "Darwin" ]]; then
  echo "Este script só roda no macOS." >&2
  exit 1
fi

if [[ "$EUID" -ne 0 ]]; then
  echo "Precisa de administrador. Rode: sudo \"$0\"" >&2
  exit 1
fi

if [[ ! -e "$DESTINO" ]]; then
  echo "Nada a remover: $DESTINO não existe."
  exit 0
fi

echo "==> Removendo $DESTINO"
rm -rf "$DESTINO"

echo "==> Reiniciando o coreaudiod"
if ! launchctl kickstart -k system/com.apple.audio.coreaudiod 2>/dev/null; then
  killall coreaudiod 2>/dev/null || true
fi

sleep 2
if system_profiler SPAudioDataType 2>/dev/null | grep -q "Praxis"; then
  echo "Aviso: algum dispositivo Praxis ainda aparece; reinicie o Mac." >&2
  exit 1
fi
echo "Removido."
