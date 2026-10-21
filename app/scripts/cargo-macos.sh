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
if [[ "$(uname -m)" == "x86_64" ]]; then
    # Mac Intel: liga na biblioteca do pacote oficial (scripts/ct2-do-pacote-oficial.sh)
    [[ -f target/ct2-lib/libctranslate2.dylib ]] || scripts/ct2-do-pacote-oficial.sh >/dev/null
    export CMAKE_LIBRARY_PATH="$PWD/target/ct2-lib"
    export RUSTFLAGS="$RUSTFLAGS -L native=$PWD/target/ct2-lib -C link-arg=-Wl,-rpath,@executable_path -C link-arg=-Wl,-rpath,@executable_path/../Frameworks -C link-arg=-Wl,-rpath,$PWD/target/ct2-lib"
fi
exec cargo "$@"
