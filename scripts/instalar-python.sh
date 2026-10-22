#!/usr/bin/env bash
# Instalador do Praxis — um comando só, no macOS e no Linux:
#
#   curl -fsSL https://raw.githubusercontent.com/disouz4-dev/praxis/main/install.sh | bash
#
# Não precisa ter Python, Homebrew nem o código baixado antes: o instalador baixa o
# Praxis, um Python próprio (pelo uv, só para o usuário), o microfone virtual, os
# modelos e as vozes para o idioma do sistema — e no fim o Praxis já abre funcionando.
# Windows: install.ps1 (o comando está no README).
#
# Opções (variáveis de ambiente):
#   PRAXIS_SEM_NLLB=1    não baixa o tradutor NLLB (licença de uso não comercial)
#   PRAXIS_WITH_CLONE=1  instala a clonagem de voz (OmniVoice + PyTorch, ~2 GB)
#   PRAXIS_GPU=vulkan    compila o whisper.cpp com Vulkan (placas AMD/Intel)
#   PRAXIS_REF=v0.2.0    versão do Praxis a instalar (padrão: main)
set -euo pipefail

REPO="disouz4-dev/praxis"
REF="${PRAXIS_REF:-main}"
OS="$(uname -s)"
ARCH="$(uname -m)"
PY_VERSION="3.12"

if [[ "$OS" == "Darwin" ]]; then
    INSTALL_DIR="$HOME/Library/Application Support/Praxis"
else
    INSTALL_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/praxis"
fi
BIN_DIR="$HOME/.local/bin"
VENV="$INSTALL_DIR/venv"
VOICES_DIR="$INSTALL_DIR/voices"

echo ""
echo "  ✦ Praxis — instalando em $INSTALL_DIR"
echo ""
mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$VOICES_DIR"

# ── 1. Código do Praxis ──────────────────────────────────────────────────────
# Rodando de dentro do repositório usa esse código; pelo comando de uma linha, baixa.
SCRIPT_DIR=""
if [[ -n "${BASH_SOURCE[0]:-}" && -f "${BASH_SOURCE[0]}" ]]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi
if [[ -z "$SCRIPT_DIR" || ! -f "$SCRIPT_DIR/praxis.py" ]]; then
    echo "==> Baixando o Praxis ($REF)..."
    SCRIPT_DIR="$(mktemp -d)"
    trap 'rm -rf "$SCRIPT_DIR"' EXIT
    curl -fsSL "https://codeload.github.com/$REPO/tar.gz/$REF" | tar xz -C "$SCRIPT_DIR" --strip-components=1
fi

# ── 2. Python próprio do Praxis (uv: sem administrador, sem Homebrew) ─────────
UV="$(command -v uv || true)"
if [[ -z "$UV" ]]; then
    echo "==> Instalando o uv (gerenciador de Python)..."
    curl -LsSf https://astral.sh/uv/install.sh | env UV_NO_MODIFY_PATH=1 sh >/dev/null
    UV="$HOME/.local/bin/uv"
fi
echo "==> Preparando o Python $PY_VERSION do Praxis..."
"$UV" python install "$PY_VERSION" >/dev/null
rm -rf "$VENV"
"$UV" venv --quiet --python "$PY_VERSION" "$VENV"
VPY="$VENV/bin/python3"
[[ -x "$VPY" ]] || VPY="$VENV/bin/python"
pipi() { "$UV" pip install --quiet --python "$VPY" "$@"; }

# ── 3. Peças do sistema: microfone virtual e áudio ───────────────────────────
if [[ "$OS" == "Darwin" ]]; then
    if ! system_profiler SPAudioDataType 2>/dev/null | grep -q "BlackHole"; then
        # Mesmo pacote e impressão digital que o Homebrew usa (cask blackhole-2ch)
        BH_URL="https://existential.audio/downloads/BlackHole2ch-0.7.1.pkg"
        BH_SHA="57b540f27a3e29c37e310e01bee0fdfab76733087e47f997ef9dccf851400dcf"
        echo "==> Instalando o BlackHole (microfone virtual) — o macOS vai pedir a sua senha..."
        BH_PKG="$(mktemp -d)/BlackHole2ch.pkg"
        if curl -fsSL "$BH_URL" -o "$BH_PKG" && \
                [[ "$(shasum -a 256 "$BH_PKG" | cut -d' ' -f1)" == "$BH_SHA" ]]; then
            sudo installer -pkg "$BH_PKG" -target / >/dev/null </dev/tty && echo "  BlackHole instalado." || \
                echo "  ! O BlackHole não foi instalado; o Praxis funciona, mas sem microfone virtual."
        else
            echo "  ! Não foi possível baixar e conferir o BlackHole."
        fi
        rm -f "$BH_PKG"
    fi
else
    # Linux: o PulseAudio/PipeWire já tem microfone virtual; faltam só utilitários
    pkgs=()
    command -v pactl &>/dev/null || pkgs+=(pulse)
    ldconfig -p 2>/dev/null | grep -q libportaudio || pkgs+=(portaudio)
    if [[ ${#pkgs[@]} -gt 0 ]]; then
        if command -v apt-get &>/dev/null; then
            map=(pulse:pulseaudio-utils portaudio:libportaudio2); inst=(sudo apt-get install -y)
        elif command -v dnf &>/dev/null; then
            map=(pulse:pulseaudio-utils portaudio:portaudio); inst=(sudo dnf install -y)
        elif command -v pacman &>/dev/null; then
            map=(pulse:libpulse portaudio:portaudio); inst=(sudo pacman -S --needed --noconfirm)
        elif command -v zypper &>/dev/null; then
            map=(pulse:pulseaudio-utils portaudio:portaudio); inst=(sudo zypper install -y)
        else
            map=(); inst=()
        fi
        real=()
        for p in "${pkgs[@]}"; do
            for m in ${map[@]+"${map[@]}"}; do [[ "${m%%:*}" == "$p" ]] && real+=("${m#*:}"); done
        done
        if [[ ${#real[@]} -gt 0 && ${#inst[@]} -gt 0 ]]; then
            echo "==> Instalando peças de áudio do sistema (${real[*]}) — pode pedir a sua senha..."
            "${inst[@]}" "${real[@]}" </dev/tty || echo "  ! Não foi possível instalar: ${real[*]}"
        else
            echo "  ! Instale manualmente: ${pkgs[*]}"
        fi
    fi
fi

# ── 4. Bibliotecas do Praxis ─────────────────────────────────────────────────
echo "==> Instalando as bibliotecas do Praxis..."
pipi -r "$SCRIPT_DIR/requirements.txt"
pipi --no-deps argostranslate
command -v ffmpeg &>/dev/null || pipi imageio-ffmpeg     # ffmpeg empacotado

# Aceleração pela placa de vídeo (veja praxis_accel.py; na primeira execução o Praxis
# compara a placa com o processador e só usa a placa se ela for melhor)
if command -v nvidia-smi &>/dev/null; then
    echo "==> Placa de vídeo NVIDIA detectada — instalando as bibliotecas CUDA..."
    pipi nvidia-cublas-cu12 "nvidia-cudnn-cu12>=9,<10" || \
        echo "  ! Bibliotecas CUDA não instaladas — o Whisper vai rodar no processador"
elif [[ "$OS" == "Darwin" && "$ARCH" == "arm64" ]]; then
    echo "==> Apple Silicon detectado — instalando o mlx-whisper (placa de vídeo)..."
    pipi mlx-whisper || echo "  ! mlx-whisper não instalado — o Whisper vai rodar no processador"
elif [[ "${PRAXIS_GPU:-}" == "vulkan" ]]; then
    echo "==> Compilando o whisper.cpp com Vulkan (placa de vídeo AMD/Intel)..."
    GGML_VULKAN=1 "$UV" pip install --quiet --python "$VPY" --no-binary pywhispercpp pywhispercpp || \
        echo "  ! A compilação com Vulkan falhou (instale o Vulkan SDK) — o Whisper vai rodar no processador"
fi
if [[ "${PRAXIS_WITH_CLONE:-0}" == "1" ]]; then
    echo "==> Instalando a clonagem de voz (OmniVoice + PyTorch)..."
    pipi -r "$SCRIPT_DIR/requirements-clone.txt"
fi

# ── 5. Arquivos do app ───────────────────────────────────────────────────────
echo "==> Copiando os arquivos do Praxis..."
cp "$SCRIPT_DIR"/praxis*.py "$INSTALL_DIR/"
rm -rf "$INSTALL_DIR/assets"
cp -R "$SCRIPT_DIR/assets" "$INSTALL_DIR/assets"

# ── 6. Atalhos ───────────────────────────────────────────────────────────────
cat > "$BIN_DIR/praxis" << LAUNCH
#!/usr/bin/env bash
exec "$VPY" "$INSTALL_DIR/praxis_config.py" "\$@"
LAUNCH
chmod +x "$BIN_DIR/praxis"

if [[ "$OS" == "Darwin" ]]; then
    # Pacote .app mínimo para o Dock mostrar o nome e o ícone do Praxis (e não os do Python)
    APP="$HOME/Applications/Praxis.app"
    rm -rf "$APP"
    mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
    cp "$INSTALL_DIR/assets/icon.icns" "$APP/Contents/Resources/Praxis.icns"
    cat > "$APP/Contents/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>Praxis</string>
  <key>CFBundleDisplayName</key><string>Praxis</string>
  <key>CFBundleIdentifier</key><string>dev.disouz4.praxis</string>
  <key>CFBundleExecutable</key><string>Praxis</string>
  <key>CFBundleIconFile</key><string>Praxis</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>0.2.0</string>
  <key>NSMicrophoneUsageDescription</key><string>O Praxis escuta o seu microfone para traduzir a sua fala.</string>
  <key>NSHighResolutionCapable</key><true/>
</dict></plist>
PLIST
    cat > "$APP/Contents/MacOS/Praxis" << RUN
#!/usr/bin/env bash
exec "$VPY" "$INSTALL_DIR/praxis_config.py" "\$@"
RUN
    chmod +x "$APP/Contents/MacOS/Praxis"
else
    DESK_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
    mkdir -p "$DESK_DIR"
    cat > "$DESK_DIR/praxis.desktop" << DESK
[Desktop Entry]
Type=Application
Name=Praxis
Comment=Tradutor de voz offline em tempo real
Exec=$BIN_DIR/praxis
Icon=$INSTALL_DIR/assets/icon.png
Terminal=false
Categories=AudioVideo;Audio;Utility;
StartupWMClass=Praxis
DESK
fi

# ── 7. Modelos e vozes para o idioma do sistema: o Praxis já abre funcionando ─
echo "==> Preparando vozes, reconhecimento de fala e tradução para o seu idioma..."
PREP_ARGS=()
[[ "${PRAXIS_SEM_NLLB:-0}" == "1" ]] && PREP_ARGS=(--sem-nllb)
"$VPY" "$INSTALL_DIR/praxis_preparar.py" ${PREP_ARGS[@]+"${PREP_ARGS[@]}"} || \
    echo "  ! O preparo não terminou — o Praxis baixa o que faltar na primeira vez em que for usado."

"$VPY" "$INSTALL_DIR/praxis.py" --check >/dev/null && CHECK="OK" || CHECK="falhou"

echo ""
echo "  ✦ Praxis instalado!  Autoteste: $CHECK"
if [[ "$OS" == "Darwin" ]]; then
    echo "  Abra pela pasta Aplicativos (Praxis) ou digite: praxis"
    echo "  No seu app de chamada, escolha 'BlackHole 2ch' como microfone."
else
    echo "  Abra pelo menu de aplicativos (Praxis) ou digite: praxis"
    echo "  No seu app de chamada, escolha 'Praxis_Microfone' como microfone."
fi
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "  (para o comando 'praxis' funcionar no terminal: export PATH=\"\$HOME/.local/bin:\$PATH\")"
fi
echo ""
