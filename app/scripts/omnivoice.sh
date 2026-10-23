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
cmake -S "$SRC" -B "$SRC/build" -DCMAKE_BUILD_TYPE=Release -DGGML_VULKAN=ON -DOMNIVOICE_SHARED=ON \
  -DBUILD_SHARED_LIBS=OFF -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DGGML_NATIVE=OFF "${extra[@]}" ${OMNIVOICE_CMAKE:-}
cmake --build "$SRC/build" --config Release --target omnivoice -j "$(getconf _NPROCESSORS_ONLN)"
mkdir -p target/release/omnivoice
if [ "$(uname)" = Darwin ]; then
  cp "$SRC/build/libomnivoice.dylib" target/release/omnivoice/
  install_name_tool -add_rpath @loader_path target/release/omnivoice/libomnivoice.dylib 2>/dev/null || true
else
  cp "$SRC/build/libomnivoice.so" target/release/omnivoice/
  patchelf --set-rpath '$ORIGIN' target/release/omnivoice/libomnivoice.so 2>/dev/null || true
fi
ls -la target/release/omnivoice
