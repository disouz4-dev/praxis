#!/usr/bin/env bash
# Roda o cargo no Linux x86-64 ligado à biblioteca do pacote oficial do CTranslate2
# (scripts/ct2-do-pacote-oficial.sh): mesma velocidade do Python e placa NVIDIA.
# Ex.: scripts/cargo-linux.sh build --release
set -euo pipefail
cd "$(dirname "$0")/.."
[[ -f target/ct2-lib/libctranslate2.so ]] || scripts/ct2-do-pacote-oficial.sh >/dev/null
export CMAKE_LIBRARY_PATH="$PWD/target/ct2-lib"
export RUSTFLAGS="${RUSTFLAGS:-} -L native=$PWD/target/ct2-lib -C link-arg=-Wl,--disable-new-dtags -C link-arg=-Wl,-rpath,\$ORIGIN -C link-arg=-Wl,-rpath,$PWD/target/ct2-lib"
exec cargo "$@"
