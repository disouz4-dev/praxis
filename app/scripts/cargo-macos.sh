#!/usr/bin/env bash
# Roda o cargo no macOS com o OpenMP do LLVM ligado (todos os núcleos no CTranslate2;
# sem ele o Whisper fica 2× mais lento que no Python). Ex.: scripts/cargo-macos.sh test
# Precisa: brew install libomp   (só para compilar; vai estático dentro do executável)
set -euo pipefail
cd "$(dirname "$0")/.."
OMP="$(brew --prefix libomp)"
mkdir -p target/omp-link && ln -sf "$OMP/lib/libomp.a" target/omp-link/libgomp.a
export CC="$PWD/scripts/macos/cc.sh" CXX="$PWD/scripts/macos/cxx.sh"
export OpenMP_ROOT="$OMP" CMAKE_PREFIX_PATH="$OMP" CPATH="$OMP/include"
export RUSTFLAGS="${RUSTFLAGS:-} -L native=$PWD/target/omp-link"
if true; then
    # liga na biblioteca do pacote oficial do CTranslate2 (scripts/ct2-do-pacote-oficial.sh)
    [[ -f target/ct2-lib/libctranslate2.dylib ]] || scripts/ct2-do-pacote-oficial.sh >/dev/null
    export CMAKE_LIBRARY_PATH="$PWD/target/ct2-lib"
    export RUSTFLAGS="$RUSTFLAGS -L native=$PWD/target/ct2-lib -C link-arg=-Wl,-rpath,@executable_path -C link-arg=-Wl,-rpath,@executable_path/../Frameworks -C link-arg=-Wl,-rpath,$PWD/target/ct2-lib"
fi
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
