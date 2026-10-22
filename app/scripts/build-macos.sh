#!/usr/bin/env bash
# Compila o motor do Praxis no macOS (versão final). Veja scripts/cargo-macos.sh.
exec "$(dirname "$0")/cargo-macos.sh" build --release "$@"
