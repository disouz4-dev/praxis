#!/bin/sh
# Atualiza o Praxis pelo repositório apt do Praxis (chamado pelo botão "Atualizar", via
# pkexec). Só olha o repositório do Praxis: não atualiza o resto do sistema.
set -e
L=/etc/apt/sources.list.d/praxis.list
apt-get update -o Dir::Etc::sourcelist="$L" -o Dir::Etc::sourceparts=- -o APT::Get::List-Cleanup=0
apt-get install -y --only-upgrade praxis
