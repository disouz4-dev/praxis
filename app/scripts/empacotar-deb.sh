#!/usr/bin/env bash
# Pacote .deb do Praxis (Debian, Ubuntu e derivados, x86-64). Instala com:
#   sudo apt install ./praxis_<versão>_amd64.deb
# O Praxis fica em /opt/praxis (programa e bibliotecas lado a lado); o comando `praxis` e o
# atalho do menu de aplicativos apontam para lá. Com placa de vídeo NVIDIA, a instalação
# baixa as bibliotecas oficiais da placa (~1,8 GB) para /opt/praxis/placa, conferindo a
# impressão digital; sem internet ou sem placa, o Praxis usa o processador.
#
# O pacote registra o repositório apt do Praxis: as versões novas chegam pela atualização
# do sistema, e o botão "Atualizar" do aplicativo chama /opt/praxis/praxis-atualizar.
#
# Uso (em app/, depois de scripts/empacotar-linux.sh): scripts/empacotar-deb.sh
set -euo pipefail
cd "$(dirname "$0")/.."
VER="$(grep -A3 '^\[workspace.package\]' Cargo.toml | grep -m1 '^version' | cut -d'"' -f2)"
SRC=target/dist/praxis-linux-x64
[ -x "$SRC/praxis" ] || { echo "rode antes: scripts/empacotar-linux.sh"; exit 1; }
D="target/dist/deb/praxis_${VER}_amd64"
rm -rf "$D"
mkdir -p "$D/DEBIAN" "$D/opt/praxis" "$D/usr/bin" "$D/usr/share/applications" "$D/usr/share/icons/hicolor/128x128/apps"
cp -a "$SRC/." "$D/opt/praxis/"
rm -f "$D/opt/praxis/praxis.desktop"
ln -s /opt/praxis/praxis "$D/usr/bin/praxis"
cp "$SRC/praxis.png" "$D/usr/share/icons/hicolor/128x128/apps/praxis.png"
cat > "$D/usr/share/applications/praxis.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Praxis
Comment=Tradutor de voz em tempo real, sem internet
Exec=/opt/praxis/praxis
Icon=praxis
Categories=AudioVideo;Audio;Utility;
Terminal=false
EOF
cp scripts/deb-placa.sh "$D/opt/praxis/praxis-placa"
cp scripts/deb-atualizar.sh "$D/opt/praxis/praxis-atualizar"
chmod 755 "$D/opt/praxis/praxis-placa" "$D/opt/praxis/praxis-atualizar"
# repositório apt do Praxis (GitHub Pages, assinado): as versões novas chegam pela
# atualização normal do sistema; a chave pública confere a assinatura
mkdir -p "$D/usr/share/keyrings" "$D/etc/apt/sources.list.d"
cp pacotes/praxis-archive-keyring.gpg "$D/usr/share/keyrings/praxis-archive-keyring.gpg"
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/praxis-archive-keyring.gpg] https://disouz4-dev.github.io/praxis/apt ./" \
    > "$D/etc/apt/sources.list.d/praxis.list"
echo /etc/apt/sources.list.d/praxis.list > "$D/DEBIAN/conffiles"
SIZE=$(du -sk "$D/opt" | cut -f1)
cat > "$D/DEBIAN/control" <<EOF
Package: praxis
Version: ${VER}
Section: sound
Priority: optional
Architecture: amd64
Installed-Size: ${SIZE}
Depends: libwebkit2gtk-4.1-0, libgtk-3-0 | libgtk-3-0t64, libasound2 | libasound2t64, pulseaudio-utils, curl, unzip, python3, bzip2
Maintainer: Praxis <noreply@users.noreply.github.com>
Homepage: https://github.com/disouz4-dev/praxis
Description: Tradutor de voz em tempo real, sem internet
 Você fala no seu idioma e a outra pessoa ouve a tradução, pelo microfone
 virtual do Praxis, em qualquer aplicativo de chamada. Tudo roda no
 computador: reconhecimento de fala, tradução e voz.
EOF
cat > "$D/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
# placa de vídeo NVIDIA: baixa as bibliotecas da placa (não impede a instalação se falhar)
if [ "$1" = "configure" ] && command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi -L >/dev/null 2>&1; then
    /opt/praxis/praxis-placa || echo "Praxis: não foi possível baixar as bibliotecas da placa de vídeo agora; ele vai usar o processador. Para tentar de novo: sudo /opt/praxis/praxis-placa"
fi
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database -q /usr/share/applications || true
exit 0
EOF
cat > "$D/DEBIAN/prerm" <<'EOF'
#!/bin/sh
set -e
# as bibliotecas da placa foram baixadas na instalação: saem junto
if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
    rm -rf /opt/praxis/placa
fi
exit 0
EOF
chmod 755 "$D/DEBIAN/postinst" "$D/DEBIAN/prerm"
dpkg-deb --root-owner-group --build "$D" "target/dist/praxis_${VER}_amd64.deb" >/dev/null
sha256sum "target/dist/praxis_${VER}_amd64.deb"
du -sh "target/dist/praxis_${VER}_amd64.deb"
