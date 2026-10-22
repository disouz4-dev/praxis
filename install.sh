#!/usr/bin/env bash
# Instalação do Praxis pelo terminal, no Linux (Debian, Ubuntu e derivados):
#
#   curl -fsSL https://raw.githubusercontent.com/disouz4-dev/praxis/main/install.sh | bash
#
# Baixa o pacote .deb da última versão publicada e instala com o apt (pede a sua senha de
# administrador). É o mesmo que baixar o .deb da página de versões e abrir com dois
# cliques. Com placa de vídeo NVIDIA, a instalação baixa as bibliotecas da placa.
#
# A versão não fica escrita aqui: o instalador pergunta ao GitHub qual é a mais atual.
# Opção (variável de ambiente): PRAXIS_DEB=arquivo.deb instala um .deb já baixado.
# Windows: install.ps1 (PowerShell) · macOS: por enquanto, scripts/instalar-python.sh
set -euo pipefail

REPO="disouz4-dev/praxis"
if [[ "$(uname -s)" != "Linux" || "$(uname -m)" != "x86_64" ]]; then
    echo "Este instalador é para Linux x86-64. No macOS, use por enquanto: scripts/instalar-python.sh"
    exit 1
fi
command -v apt >/dev/null || { echo "Este instalador usa o apt (Debian, Ubuntu e derivados)."; exit 1; }

DEB="${PRAXIS_DEB:-}"
if [[ -z "$DEB" ]]; then
    TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
    # pergunta ao GitHub qual é a versão mais atual e o endereço do .deb dela
    INFO="$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest")"
    VER="$(grep -m1 '"tag_name"' <<<"$INFO" | cut -d'"' -f4)"
    URL="$(grep -o '"browser_download_url": *"[^"]*_amd64\.deb"' <<<"$INFO" | grep -v '/praxis_amd64.deb' | head -1 | cut -d'"' -f4)"
    [[ -n "$VER" && -n "$URL" ]] || { echo "Não encontrei a versão mais atual no GitHub (sem internet?)."; exit 1; }
    echo "  Baixando o Praxis $VER (a versão mais atual)…"
    curl -fL --progress-bar -o "$TMP/praxis_amd64.deb" "$URL"
    DEB="$TMP/praxis_amd64.deb"
fi
echo "  Instalando (o apt vai pedir a sua senha)…"
sudo apt install -y "$(realpath "$DEB")"
echo ""
echo "  ✓ Praxis instalado. Abra pelo menu de aplicativos ou com o comando: praxis"
