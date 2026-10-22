#!/usr/bin/env bash
# Monta o pacote do Praxis para Linux (x86-64): o aplicativo, o motor de linha de comando
# e todas as bibliotecas lado a lado (o programa procura as bibliotecas na própria pasta).
# As bibliotecas da placa de vídeo NVIDIA NÃO vão no pacote (são ~1,5 GB): o instalador
# baixa só quando encontra uma placa NVIDIA.
#
# Uso (em app/, depois de compilar com scripts/cargo-linux.sh build --release):
#   scripts/empacotar-linux.sh   → target/dist/praxis-linux-x64/ (base do .deb: scripts/empacotar-deb.sh)
set -euo pipefail
cd "$(dirname "$0")/.."
R=target/release
OUT=target/dist/praxis-linux-x64
rm -rf "$OUT"
mkdir -p "$OUT"
cp "$R/praxis" "$OUT/praxis"
[ -f "$R/praxis-cli" ] && cp "$R/praxis-cli" "$OUT/praxis-cli"
cp "$R"/libsherpa-onnx-c-api.so "$R"/libsherpa-onnx-cxx-api.so "$R"/libonnxruntime.so "$OUT/"
cp -P target/ct2-lib/*.so* "$OUT/"
cp desktop/icons/128x128.png "$OUT/praxis.png"
cat > "$OUT/praxis.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Praxis
Comment=Tradutor de voz em tempo real, sem internet
Exec=@DIR@/praxis
Icon=@DIR@/praxis.png
Categories=AudioVideo;Audio;Utility;
Terminal=false
EOF
# confere que o programa acha tudo na própria pasta
missing=$(cd "$OUT" && LD_LIBRARY_PATH= ldd ./praxis | grep "not found" || true)
if [ -n "$missing" ]; then
  echo "faltam bibliotecas no pacote:"; echo "$missing"; exit 1
fi
du -sh "$OUT"
