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
# Para cada compilação guardada, confere se a pasta que o build.rs indicou ainda tem a
# biblioteca; se não tem, apaga o registro de compilação para o build.rs rodar de novo.
for saida in target/*/build/sherpa-onnx-sys-*/output target/*/*/build/sherpa-onnx-sys-*/output; do
    [[ -f "$saida" ]] || continue
    pasta="$(sed -n 's/^cargo:rustc-link-search=native=//p' "$saida" | head -1)"
    if ! compgen -G "$pasta/*sherpa-onnx-c-api*" >/dev/null; then
        perfil="${saida%/build/*}"
        echo "bibliotecas do sherpa-onnx ausentes em $pasta: o sherpa-onnx-sys será compilado de novo" >&2
        rm -rf "$perfil"/build/sherpa-onnx-sys-* "$perfil"/.fingerprint/sherpa-onnx-sys-*
        # uma pasta lib/ vazia que sobrou faria o build.rs achar que já baixou
        [[ "$pasta" == */sherpa-onnx-prebuilt/*/lib ]] && rm -rf "$(dirname "$pasta")"
    fi
done
exec cargo "$@"
