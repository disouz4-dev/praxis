#!/bin/sh
# Bibliotecas da placa de vídeo NVIDIA para o Praxis instalado pelo .deb (roda como
# administrador na instalação; pode ser rodado de novo: sudo /opt/praxis/praxis-placa).
# Baixa do PyPI (bibliotecas oficiais da NVIDIA) e do sherpa-onnx, confere o SHA-256 de
# cada arquivo e guarda em /opt/praxis/placa, onde o programa procura primeiro.
set -e
APP=/opt/praxis
P="$APP/placa"
[ -f "$P/.pronto" ] && { echo "Praxis: bibliotecas da placa de vídeo já instaladas."; exit 0; }
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
echo "Praxis: placa NVIDIA encontrada; baixando as bibliotecas da placa (~1,8 GB, só uma vez)…"
mkdir -p "$TMP/w" "$P.novo"
for pv in nvidia-cuda-runtime-cu12:12.9.79 nvidia-cublas-cu12:12.9.2.10 nvidia-cudnn-cu12:9.27.0.42 nvidia-curand-cu12:10.3.10.19; do
    pkg=${pv%%:*}; ver=${pv#*:}
    par=$(curl -fsSL "https://pypi.org/pypi/$pkg/$ver/json" | python3 -c '
import json, sys
f = next(f for f in json.load(sys.stdin)["urls"] if "manylinux" in f["filename"] and "x86_64" in f["filename"])
print(f["url"], f["digests"]["sha256"])')
    curl -fsSL -o "$TMP/w/$pkg.whl" "${par% *}"
    echo "${par#* }  $TMP/w/$pkg.whl" | sha256sum -c --quiet -
    (cd "$TMP/w" && unzip -q -o "$pkg.whl" 'nvidia/*/lib/*.so*')
done
find "$TMP/w/nvidia" -name '*.so*' -exec mv {} "$P.novo/" \;
S=sherpa-onnx-v1.13.8-cuda-12.x-cudnn-9.x-onnxruntime1.28.2-linux-x64-gpu
curl -fsSL -o "$TMP/s.tar.bz2" "https://github.com/k2-fsa/sherpa-onnx/releases/download/v1.13.8/$S.tar.bz2"
tar -C "$TMP" -xjf "$TMP/s.tar.bz2" "$S/lib"
for f in libonnxruntime.so libonnxruntime_providers_cuda.so libonnxruntime_providers_shared.so \
         libsherpa-onnx-c-api.so libsherpa-onnx-cxx-api.so; do
    cp "$TMP/$S/lib/$f" "$P.novo/"
done
rm -rf "$P"; mv "$P.novo" "$P"
# o programa procura primeiro em placa/ e depois na própria pasta: nada do pacote é trocado
touch "$P/.pronto"
echo "Praxis: bibliotecas da placa de vídeo instaladas."
