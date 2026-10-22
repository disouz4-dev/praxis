#!/bin/bash
# Praxis — confere o PraxisAudio.driver DEPOIS de instalado (não precisa de sudo).
#
# Uso: ./testar-instalado.sh
#
# Precisa do sox (brew install sox). Para cada dispositivo ("Praxis Mic" e
# "Praxis Speaker"): grava dele enquanto toca um tom de 440 Hz nele, e confere
# que a gravação tem som. Depois confere que, sem nada tocando, a gravação é
# silêncio, e que tocar num dispositivo não vaza para o outro.
# Os arquivos de teste ficam numa pasta temporária e são apagados no fim.

set -euo pipefail

if ! system_profiler SPAudioDataType 2>/dev/null | grep -q "Praxis Mic"; then
  echo "FALHOU: \"Praxis Mic\" não aparece. O driver está instalado? (sudo ./instalar.sh)" >&2
  exit 1
fi
if ! system_profiler SPAudioDataType 2>/dev/null | grep -q "Praxis Speaker"; then
  echo "FALHOU: \"Praxis Speaker\" não aparece." >&2
  exit 1
fi
echo "ok: os dois dispositivos aparecem no sistema"
system_profiler SPAudioDataType 2>/dev/null | grep -A12 "Praxis" || true

if ! command -v sox >/dev/null 2>&1; then
  echo "Para o teste de som, instale o sox: brew install sox" >&2
  exit 1
fi

TEMP="$(mktemp -d)"
trap 'rm -rf "$TEMP"' EXIT

# Volume médio (raiz da média dos quadrados) de um arquivo, entre 0 e 1.
volume() {
  sox "$1" -n stat 2>&1 | awk '/RMS     amplitude/ {print $3}'
}

# grava DE durante 3 s; se TOCAR_EM não for vazio, toca um tom de 440 Hz nele
# durante 2 s começando 0,5 s depois do início da gravação.
gravar() {
  local de="$1" tocar_em="$2" arquivo="$3"
  sox -q -t coreaudio "$de" -r 48000 -c 2 -b 32 -e floating-point "$arquivo" trim 0 3 &
  local pid=$!
  sleep 0.5
  if [[ -n "$tocar_em" ]]; then
    sox -q -n -r 48000 -c 2 -t coreaudio "$tocar_em" synth 2 sine 440 vol 0.5
  fi
  wait "$pid"
}

falhas=0
confere() {
  local descricao="$1" arquivo="$2" espera="$3"
  local v
  v="$(volume "$arquivo")"
  if [[ "$espera" == "som" ]]; then
    if awk -v v="$v" 'BEGIN { exit !(v > 0.1) }'; then
      echo "ok: $descricao (volume $v)"
    else
      echo "FALHOU: $descricao — esperava som, volume $v"; falhas=$((falhas + 1))
    fi
  else
    if awk -v v="$v" 'BEGIN { exit !(v < 0.0001) }'; then
      echo "ok: $descricao (volume $v)"
    else
      echo "FALHOU: $descricao — esperava silêncio, volume $v"; falhas=$((falhas + 1))
    fi
  fi
}

gravar "Praxis Mic" "Praxis Mic" "$TEMP/mic.wav"
confere "laço do Praxis Mic (toca nele e grava dele)" "$TEMP/mic.wav" som

gravar "Praxis Speaker" "Praxis Speaker" "$TEMP/speaker.wav"
confere "laço do Praxis Speaker" "$TEMP/speaker.wav" som

gravar "Praxis Mic" "" "$TEMP/silencio.wav"
confere "Praxis Mic sem nada tocando é silêncio" "$TEMP/silencio.wav" silencio

gravar "Praxis Speaker" "Praxis Mic" "$TEMP/vazamento.wav"
confere "tocar no Mic não vaza para o Speaker" "$TEMP/vazamento.wav" silencio

if [[ "$falhas" -gt 0 ]]; then
  echo "$falhas verificação(ões) falharam." >&2
  exit 1
fi
echo "Tudo certo."
