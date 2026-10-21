#!/usr/bin/env bash
# Usa no motor em Rust a MESMA biblioteca CTranslate2 do pacote oficial do Python
# (PyPI, OpenNMT): ela vem com a MKL da Intel e o OpenMP da Intel embutidos, então a
# velocidade é idêntica à do Praxis em Python (medido: compilando o CTranslate2 com
# oneDNN, o NLLB ficou 1,7× mais lento). A versão precisa ser a do ct2rs (4.8.3).
# Saída: target/ct2-lib/ (biblioteca + OpenMP), pronta para o cargo.
set -euo pipefail
cd "$(dirname "$0")/.."
VER="4.8.3"
OUT="$PWD/target/ct2-lib"
TMP="$(mktemp -d)"
case "$(uname -s)-$(uname -m)" in
    Darwin-x86_64) PLAT="macosx_11_0_x86_64" ;;
    Darwin-arm64)  PLAT="macosx_11_0_arm64" ;;
    Linux-x86_64)  PLAT="manylinux_2_28_x86_64" ;;
    *) echo "sistema sem pacote oficial do CTranslate2" >&2; exit 1 ;;
esac
"${PYTHON:-python3}" -m pip download --quiet --no-deps --only-binary :all: --python-version 3.12 \
    --platform "$PLAT" --platform manylinux_2_17_x86_64 "ctranslate2==$VER" -d "$TMP"
mkdir -p "$OUT"
( cd "$TMP" && unzip -q -o ./*.whl 'ctranslate2/.dylibs/*' 'ctranslate2.libs/*' 2>/dev/null || true )
if [[ -d "$TMP/ctranslate2/.dylibs" ]]; then           # macOS
    cp "$TMP"/ctranslate2/.dylibs/*.dylib "$OUT/"
    LIB="$(ls "$OUT"/libctranslate2.*.dylib | head -1)"
    ln -sf "$(basename "$LIB")" "$OUT/libctranslate2.dylib"
    install_name_tool -id "@rpath/$(basename "$LIB")" "$LIB"
    install_name_tool -id "@rpath/libiomp5.dylib" "$OUT/libiomp5.dylib"
    codesign -f -s - "$LIB" "$OUT/libiomp5.dylib" 2>/dev/null   # a alteração invalida a assinatura
else                                                    # Linux
    cp "$TMP"/ctranslate2.libs/* "$OUT/"
    LIB="$(ls "$OUT"/libctranslate2*.so* | head -1)"
    ln -sf "$(basename "$LIB")" "$OUT/libctranslate2.so"
fi
# o ct2rs pede bibliotecas que, no pacote oficial, já estão dentro do CTranslate2 ou são
# carregadas por ele na hora de rodar (cpu_features; cuBLAS da NVIDIA no Linux):
# arquivos vazios só para a ligação passar
echo "" | cc -x c -c -o "$TMP/vazio.o" -
for lib in cpu_features cublas_static cublasLt_static culibos; do
    ar rcs "$OUT/lib$lib.a" "$TMP/vazio.o"
done
rm -rf "$TMP"
ls -la "$OUT"
