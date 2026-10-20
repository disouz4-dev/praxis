#!/usr/bin/env bash
# Praxis installer — Linux (apt/dnf/pacman/zypper) and macOS (Homebrew).
# Windows: use install.ps1
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
echo "  ✦ Praxis — installing to $INSTALL_DIR"
echo ""
mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$VOICES_DIR"

# ── System dependencies ───────────────────────────────────────────────────────
echo "==> Checking system dependencies..."
if [[ "$OS" == "Darwin" ]]; then
    if ! command -v brew &>/dev/null; then
        echo "  Homebrew is required: https://brew.sh" >&2
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
        echo "==> Installing BlackHole (virtual microphone driver)..."
        brew install --cask blackhole-2ch || echo "  ! Install BlackHole manually: brew install --cask blackhole-2ch"
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
        echo "  Installing: ${real[*]}"
        # shellcheck disable=SC2086
        $inst "${real[@]}" || echo "  ! Could not install some packages: ${real[*]}"
    elif [[ ${#real[@]} -gt 0 ]]; then
        echo "  ! Unknown package manager — install manually: ${pkgs[*]}"
    fi
fi

"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' || {
    echo "  Python 3.10+ is required (found $("$PY" --version))" >&2; exit 1; }

# ── Python environment ────────────────────────────────────────────────────────
echo "==> Creating Python venv..."
"$PY" -m venv "$VENV"
VPY="$VENV/bin/python3"
"$VPY" -m pip install --upgrade pip -q

echo "==> Installing Python dependencies..."
"$VPY" -m pip install -q -r "$SCRIPT_DIR/requirements.txt"
"$VPY" -m pip install -q --no-deps argostranslate

# ── GPU acceleration (auto-detected; see praxis_accel.py) ───────────────────
#   NVIDIA          → CUDA libraries for faster-whisper / CTranslate2
#   Apple Silicon   → mlx-whisper (Whisper on the Apple GPU via MLX)
#   AMD/Intel GPU   → whisper.cpp built with Vulkan (opt-in: PRAXIS_GPU=vulkan,
#                     needs the Vulkan SDK + a C++ compiler)
#   Intel Macs      → CPU (Metal whisper.cpp measured wrong/slower on AMD Macs)
if command -v nvidia-smi &>/dev/null; then
    echo "==> NVIDIA GPU detected — installing CUDA runtime libraries..."
    "$VPY" -m pip install -q nvidia-cublas-cu12 "nvidia-cudnn-cu12>=9,<10" || \
        echo "  ! CUDA libraries not installed — Whisper will run on CPU"
elif [[ "$OS" == "Darwin" && "$(uname -m)" == "arm64" ]]; then
    echo "==> Apple Silicon detected — installing mlx-whisper (GPU)..."
    "$VPY" -m pip install -q mlx-whisper || echo "  ! mlx-whisper not installed — Whisper will run on CPU"
elif [[ "${PRAXIS_GPU:-}" == "vulkan" ]]; then
    echo "==> Building whisper.cpp with Vulkan (AMD/Intel GPU)..."
    GGML_VULKAN=1 "$VPY" -m pip install -q --no-binary pywhispercpp pywhispercpp || \
        echo "  ! Vulkan build failed (install the Vulkan SDK) — Whisper will run on CPU"
fi

if [[ "${PRAXIS_WITH_CLONE:-0}" == "1" ]]; then
    echo "==> Installing voice cloning (OmniVoice + PyTorch)..."
    "$VPY" -m pip install -q -r "$SCRIPT_DIR/requirements-clone.txt"
fi

# ── App files ─────────────────────────────────────────────────────────────────
echo "==> Copying files..."
cp "$SCRIPT_DIR/praxis.py" "$SCRIPT_DIR/praxis_config.py" "$SCRIPT_DIR/praxis_platform.py" "$INSTALL_DIR/"
rm -rf "$INSTALL_DIR/assets"
cp -R "$SCRIPT_DIR/assets" "$INSTALL_DIR/assets"

# ── Default Piper voice: en_US-lessac-medium ─────────────────────────────────
VOICE_BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium"
VOICE_FILE="$VOICES_DIR/en_US-lessac-medium.onnx"
if [[ ! -f "$VOICE_FILE" ]]; then
    echo "==> Downloading default Piper voice (en_US-lessac-medium)..."
    curl -fL --progress-bar "$VOICE_BASE/en_US-lessac-medium.onnx.json" -o "${VOICE_FILE}.json.part"
    curl -fL --progress-bar "$VOICE_BASE/en_US-lessac-medium.onnx"      -o "${VOICE_FILE}.part"
    mv "${VOICE_FILE}.json.part" "${VOICE_FILE}.json"
    mv "${VOICE_FILE}.part" "$VOICE_FILE"
else
    echo "==> Default voice already installed."
fi

# ── Launcher ──────────────────────────────────────────────────────────────────
cat > "$BIN_DIR/praxis" << LAUNCH
#!/usr/bin/env bash
exec "$VPY" "$INSTALL_DIR/praxis_config.py" "\$@"
LAUNCH
chmod +x "$BIN_DIR/praxis"

if [[ "$OS" == "Darwin" ]]; then
    # Minimal .app bundle so the Dock shows the Praxis name + icon (not Python's)
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
  <key>NSMicrophoneUsageDescription</key><string>Praxis listens to your microphone to translate your speech.</string>
  <key>NSHighResolutionCapable</key><true/>
</dict></plist>
PLIST
    cat > "$APP/Contents/MacOS/Praxis" << RUN
#!/usr/bin/env bash
exec "$VPY" "$INSTALL_DIR/praxis_config.py" "\$@"
RUN
    chmod +x "$APP/Contents/MacOS/Praxis"
    echo "==> App bundle: $APP"
else
    DESK_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
    mkdir -p "$DESK_DIR"
    cat > "$DESK_DIR/praxis.desktop" << DESK
[Desktop Entry]
Type=Application
Name=Praxis
Comment=Real-time offline voice translator
Exec=$BIN_DIR/praxis
Icon=$INSTALL_DIR/assets/icon.png
Terminal=false
Categories=AudioVideo;Audio;Utility;
StartupWMClass=Praxis
DESK
fi

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo "  NOTE: add to your shell profile:"
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo ""
echo "  ✦ Praxis installed!  Run: praxis"
if [[ "$OS" == "Darwin" ]]; then
    echo "  In your call app, select 'BlackHole 2ch' as the microphone."
else
    echo "  In your call app, select 'Praxis_Microfone' as the microphone."
fi
echo ""
"$VPY" "$INSTALL_DIR/praxis.py" --check >/dev/null && echo "  Self-check: OK" || echo "  ! Self-check failed: $VPY $INSTALL_DIR/praxis.py --check"
