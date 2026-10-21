#!/usr/bin/env bash
# Roda o cargo no Linux x86-64 ligado à biblioteca do pacote oficial do CTranslate2
# (scripts/ct2-do-pacote-oficial.sh): mesma velocidade do Python e placa NVIDIA.
# Ex.: scripts/cargo-linux.sh build --release
set -euo pipefail
cd "$(dirname "$0")/.."
[[ -f target/ct2-lib/libctranslate2.so ]] || scripts/ct2-do-pacote-oficial.sh >/dev/null
export CMAKE_LIBRARY_PATH="$PWD/target/ct2-lib"
export RUSTFLAGS="${RUSTFLAGS:-} -L native=$PWD/target/ct2-lib -C link-arg=-Wl,--disable-new-dtags -C link-arg=-Wl,-rpath,\$ORIGIN -C link-arg=-Wl,-rpath,$PWD/target/ct2-lib"
# O sherpa-onnx-sys baixa as bibliotecas prontas para target/sherpa-onnx-prebuilt/ e as
# copia para target/<perfil>/, mas só quando o build.rs dele roda. O cache do GitHub
# Actions (Swatinem/rust-cache) guarda o "já compilado" do sherpa-onnx-sys e apaga essas
# pastas; sem elas, a ligação falha ("unable to find library -lsherpa-onnx-c-api").
# Se as bibliotecas sumiram, apaga o registro de compilação dele para o build.rs rodar de novo.
if ! compgen -G "target/sherpa-onnx-prebuilt/*/lib" >/dev/null; then
    find target -maxdepth 4 -type d \( -path '*/build/sherpa-onnx-sys-*' -o -path '*/.fingerprint/sherpa-onnx-sys-*' \) \
        -prune -exec rm -rf {} + 2>/dev/null || true
fi
exec cargo "$@"
