#!/usr/bin/env bash
# Compila o omnivoice.cpp (OmniVoice: a voz clonada fiel, MIT) como biblioteca com o motor Vulkan
# — placas AMD, Intel e NVIDIA no Linux; AMD nos Macs Intel pelo MoltenVK — e põe em
# target/release/omnivoice/. O Praxis carrega essa biblioteca na hora; sem ela (ou sem placa),
# usa a voz leve.
# Precisa do Vulkan (cabeçalhos, carregador, glslc e SPIRV-Headers). Uso (em app/): scripts/omnivoice.sh
set -euo pipefail
cd "$(dirname "$0")/.."
COMMIT=1a468d8b9d65b3544ca1004d2d7c05dfc65d1f3e
SRC=target/omnivoice-src
if [ ! -d "$SRC/.git" ]; then
  rm -rf "$SRC"   # cópia incompleta (ex.: restaurada pelo cache do GitHub)
  git clone -q https://github.com/ServeurpersoCom/omnivoice.cpp.git "$SRC"
fi
git -C "$SRC" fetch -q origin "$COMMIT" 2>/dev/null || true
git -C "$SRC" checkout -q -f "$COMMIT"
git -C "$SRC" submodule update -q --init --recursive
git -C "$SRC" apply --whitespace=nowarn "$PWD/pacotes/omnivoice-praxis.patch"
extra=()
[ "$(uname)" = Darwin ] && extra+=(-DGGML_METAL=OFF)
# OMNIVOICE_CUDA=1: a versão para placas NVIDIA (CUDA 12; as bibliotecas da NVIDIA vêm na pasta
# placa/ do Praxis), para as placas de uso pessoal: GeForce 16 e RTX 20 (75), RTX 30 (86), RTX 40 (89) e RTX 50 (120)
if [ "${OMNIVOICE_CUDA:-0}" = 1 ]; then
  B="$SRC/build-cuda"; NOME=libomnivoice-cuda.so
  extra+=(-DGGML_CUDA=ON -DGGML_VULKAN=OFF "-DCMAKE_CUDA_ARCHITECTURES=${OMNIVOICE_CUDA_ARCH:-75;86;89;120}")
else
  B="$SRC/build"; NOME=libomnivoice.so
  extra+=(-DGGML_VULKAN=ON)
fi
cmake -S "$SRC" -B "$B" -DCMAKE_BUILD_TYPE=Release -DOMNIVOICE_SHARED=ON \
  -DBUILD_SHARED_LIBS=OFF -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DGGML_NATIVE=OFF "${extra[@]}" ${OMNIVOICE_CMAKE:-}
cmake --build "$B" --config Release --target omnivoice -j "$(getconf _NPROCESSORS_ONLN)"
mkdir -p target/release/omnivoice
if [ "$(uname)" = Darwin ]; then
  cp "$B/libomnivoice.dylib" target/release/omnivoice/
  install_name_tool -add_rpath @loader_path target/release/omnivoice/libomnivoice.dylib 2>/dev/null || true
else
  cp "$B/libomnivoice.so" "target/release/omnivoice/$NOME"
  # acha as bibliotecas da NVIDIA na pasta placa/ do Praxis (/opt/praxis/placa)
  patchelf --set-rpath '$ORIGIN:$ORIGIN/../placa' "target/release/omnivoice/$NOME"
fi
ls -la target/release/omnivoice
