#!/usr/bin/env bash
# Compila o motor do Praxis no macOS com OpenMP (todos os núcleos no CTranslate2).
# Precisa: brew install libomp   (só para compilar; vai estático dentro do executável)
set -euo pipefail
cd "$(dirname "$0")/.."
OMP="$(brew --prefix libomp)"
mkdir -p target/omp-link && ln -sf "$OMP/lib/libomp.a" target/omp-link/libgomp.a
export CC="$PWD/scripts/macos/cc.sh" CXX="$PWD/scripts/macos/cxx.sh"
export OpenMP_ROOT="$OMP" CMAKE_PREFIX_PATH="$OMP" CPATH="$OMP/include"
export RUSTFLAGS="${RUSTFLAGS:-} -L native=$PWD/target/omp-link"
exec cargo build --release "$@"
