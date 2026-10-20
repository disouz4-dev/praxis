#!/usr/bin/env bash
# Instalador do Praxis — Linux (apt/dnf/pacman/zypper) e macOS (Homebrew).
# Windows: use o install.ps1
set -euo pipefail

OS="$(uname -s)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-python3}"

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

# ── Dependências do sistema ───────────────────────────────────────────────────
echo "==> Verificando dependências do sistema..."
if [[ "$OS" == "Darwin" ]]; then
    if ! command -v brew &>/dev/null; then
        echo "  O Homebrew é necessário: https://brew.sh" >&2
        exit 1
    fi
    need=()
    "$PY" -c "import tkinter" 2>/dev/null || need+=("python-tk@$("$PY" -c 'import sys; print(f"{sys.version_info[0]}.{sys.version_info[1]}")')")
    command -v ffmpeg &>/dev/null || need+=(ffmpeg)
    brew list portaudio &>/dev/null || need+=(portaudio)
    if [[ ${#need[@]} -gt 0 ]]; then
        echo "  brew install ${need[*]}"
        brew install "${need[@]}"
    fi
    if ! system_profiler SPAudioDataType 2>/dev/null | grep -q "BlackHole"; then
        echo "==> Instalando o BlackHole (driver de microfone virtual)..."
        brew install --cask blackhole-2ch || echo "  ! Instale o BlackHole manualmente: brew install --cask blackhole-2ch"
    fi
else
    pkgs=()
    command -v pactl  &>/dev/null || pkgs+=(pulse)
    command -v ffmpeg &>/dev/null || pkgs+=(ffmpeg)
    "$PY" -c "import tkinter" 2>/dev/null || pkgs+=(tk)
    "$PY" -c "import venv, ensurepip" 2>/dev/null || pkgs+=(venv)
    pkgs+=(portaudio)
    if command -v apt-get &>/dev/null; then
        map=(pulse:pulseaudio-utils ffmpeg:ffmpeg tk:python3-tk venv:python3-venv portaudio:libportaudio2)
        inst=sudo\ apt-get\ install\ -y
    elif command -v dnf &>/dev/null; then
        map=(pulse:pulseaudio-utils ffmpeg:ffmpeg tk:python3-tkinter venv:python3 portaudio:portaudio)
        inst=sudo\ dnf\ install\ -y
    elif command -v pacman &>/dev/null; then
        map=(pulse:libpulse ffmpeg:ffmpeg tk:tk venv:python portaudio:portaudio)
        inst=sudo\ pacman\ -S\ --needed\ --noconfirm
    elif command -v zypper &>/dev/null; then
        map=(pulse:pulseaudio-utils ffmpeg:ffmpeg tk:python3-tk venv:python3 portaudio:portaudio)
        inst=sudo\ zypper\ install\ -y
    else
        map=(); inst=""
    fi
    real=()
    for p in "${pkgs[@]}"; do
        for m in "${map[@]}"; do [[ "${m%%:*}" == "$p" ]] && real+=("${m#*:}"); done
    done
    if [[ ${#real[@]} -gt 0 && -n "$inst" ]]; then
        echo "  Instalando: ${real[*]}"
        # shellcheck disable=SC2086
        $inst "${real[@]}" || echo "  ! Não foi possível instalar alguns pacotes: ${real[*]}"
    elif [[ ${#real[@]} -gt 0 ]]; then
        echo "  ! Gerenciador de pacotes desconhecido — instale manualmente: ${pkgs[*]}"
    fi
fi

"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' || {
    echo "  É necessário Python 3.10+ (encontrado: $("$PY" --version))" >&2; exit 1; }

# ── Ambiente Python ───────────────────────────────────────────────────────────
echo "==> Criando o ambiente virtual Python (venv)..."
"$PY" -m venv "$VENV"
VPY="$VENV/bin/python3"
"$VPY" -m pip install --upgrade pip -q

echo "==> Instalando dependências Python..."
"$VPY" -m pip install -q -r "$SCRIPT_DIR/requirements.txt"
"$VPY" -m pip install -q --no-deps argostranslate

# ── Aceleração pela placa de vídeo (detectada sozinha; veja praxis_accel.py) ──
#   NVIDIA          → bibliotecas CUDA para o faster-whisper / CTranslate2
#   Apple Silicon   → mlx-whisper (Whisper na placa de vídeo da Apple via MLX)
#   GPU AMD/Intel   → whisper.cpp compilado com Vulkan (só se pedir:
#                     PRAXIS_GPU=vulkan; precisa do Vulkan SDK + compilador C++)
#   Macs Intel      → CPU (whisper.cpp com Metal errou/foi mais lento em Macs AMD)
if command -v nvidia-smi &>/dev/null; then
    echo "==> Placa de vídeo NVIDIA detectada — instalando as bibliotecas CUDA..."
    "$VPY" -m pip install -q nvidia-cublas-cu12 "nvidia-cudnn-cu12>=9,<10" || \
        echo "  ! Bibliotecas CUDA não instaladas — o Whisper vai rodar na CPU"
elif [[ "$OS" == "Darwin" && "$(uname -m)" == "arm64" ]]; then
    echo "==> Apple Silicon detectado — instalando o mlx-whisper (placa de vídeo)..."
    "$VPY" -m pip install -q mlx-whisper || echo "  ! mlx-whisper não instalado — o Whisper vai rodar na CPU"
elif [[ "${PRAXIS_GPU:-}" == "vulkan" ]]; then
    echo "==> Compilando o whisper.cpp com Vulkan (placa de vídeo AMD/Intel)..."
    GGML_VULKAN=1 "$VPY" -m pip install -q --no-binary pywhispercpp pywhispercpp || \
        echo "  ! A compilação com Vulkan falhou (instale o Vulkan SDK) — o Whisper vai rodar na CPU"
fi

if [[ "${PRAXIS_WITH_CLONE:-0}" == "1" ]]; then
    echo "==> Instalando a clonagem de voz (OmniVoice + PyTorch)..."
    "$VPY" -m pip install -q -r "$SCRIPT_DIR/requirements-clone.txt"
fi

# ── Arquivos do app ───────────────────────────────────────────────────────────
echo "==> Copiando arquivos..."
cp "$SCRIPT_DIR/praxis.py" "$SCRIPT_DIR/praxis_config.py" "$SCRIPT_DIR/praxis_platform.py" "$INSTALL_DIR/"
rm -rf "$INSTALL_DIR/assets"
cp -R "$SCRIPT_DIR/assets" "$INSTALL_DIR/assets"

# ── Voz padrão do Piper: en_US-lessac-medium ─────────────────────────────────
VOICE_BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium"
VOICE_FILE="$VOICES_DIR/en_US-lessac-medium.onnx"
if [[ ! -f "$VOICE_FILE" ]]; then
    echo "==> Baixando a voz padrão do Piper (en_US-lessac-medium)..."
    curl -fL --progress-bar "$VOICE_BASE/en_US-lessac-medium.onnx.json" -o "${VOICE_FILE}.json.part"
    curl -fL --progress-bar "$VOICE_BASE/en_US-lessac-medium.onnx"      -o "${VOICE_FILE}.part"
    mv "${VOICE_FILE}.json.part" "${VOICE_FILE}.json"
    mv "${VOICE_FILE}.part" "$VOICE_FILE"
else
    echo "==> A voz padrão já está instalada."
fi

# ── Atalho de abertura ───────────────────────────────────────────────────────
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
    echo "==> Pacote do app: $APP"
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

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo "  OBS.: adicione ao perfil do seu terminal (shell):"
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo ""
echo "  ✦ Praxis instalado!  Para abrir: praxis"
if [[ "$OS" == "Darwin" ]]; then
    echo "  No seu app de chamada, escolha 'BlackHole 2ch' como microfone."
else
    echo "  No seu app de chamada, escolha 'Praxis_Microfone' como microfone."
fi
echo ""
"$VPY" "$INSTALL_DIR/praxis.py" --check >/dev/null && echo "  Autoteste: OK" || echo "  ! O autoteste falhou: $VPY $INSTALL_DIR/praxis.py --check"
