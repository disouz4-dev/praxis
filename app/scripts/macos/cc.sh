#!/bin/sh
exec "$(dirname "$0")/clang-omp.sh" "$(xcrun -f clang)" "$@"
