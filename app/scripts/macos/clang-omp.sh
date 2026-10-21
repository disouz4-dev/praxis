#!/bin/sh
# Intermediário do compilador da Apple para compilar o CTranslate2 com OpenMP: o CMake
# do CTranslate2 passa "-Xclang -fopenmp" como UM argumento, que o clang da Apple
# rejeita. Aqui ele vira dois. Todo o resto passa intacto.
real="$1"; shift
for a in "$@"; do
    case "$a" in
        "-Xclang -fopenmp") set -- "$@" -Xclang -fopenmp ;;
        *) set -- "$@" "$a" ;;
    esac
    shift
done
exec "$real" -isysroot "$(xcrun --show-sdk-path)" "$@"
