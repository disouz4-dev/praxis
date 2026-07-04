#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="$HOME/.local/share/praxis"
BIN_DIR="$HOME/.local/bin"
VOICES_DIR="$INSTALL_DIR/voices"
VENV="$INSTALL_DIR/venv"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "  ✦ Praxis — instalando em $INSTALL_DIR"
echo ""

mkdir -p "$INSTALL_DIR" "$BIN_DIR" "$VOICES_DIR"

# ── Dependências do sistema ───────────────────────────────────────────────────
echo "==> Verificando dependências do sistema..."
MISSING_PKGS=()
command -v pactl   &>/dev/null || MISSING_PKGS+=(pulseaudio-utils)
command -v parec   &>/dev/null || MISSING_PKGS+=(pulseaudio-utils)
command -v python3 &>/dev/null || MISSING_PKGS+=(python3 python3-venv)
python3 -c "import tkinter" 2>/dev/null || MISSING_PKGS+=(python3-tk)

if [[ ${#MISSING_PKGS[@]} -gt 0 ]]; then
    echo "  Instalando: ${MISSING_PKGS[*]}"
    sudo apt-get install -y "${MISSING_PKGS[@]}"
fi

# ── Ambiente virtual Python ───────────────────────────────────────────────────
echo "==> Criando venv Python..."
python3 -m venv "$VENV"
# shellcheck source=/dev/null
source "$VENV/bin/activate"
pip install --upgrade pip -q

# ── PyTorch (CUDA se disponível, senão CPU) ───────────────────────────────────
if command -v nvidia-smi &>/dev/null; then
    echo "==> GPU NVIDIA detectada — instalando PyTorch com CUDA 12.1..."
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121 -q
else
    echo "==> GPU não detectada — instalando PyTorch CPU..."
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu -q
fi

# ── Dependências Python ───────────────────────────────────────────────────────
echo "==> Instalando dependências Python..."
pip install \
    faster-whisper \
    argostranslate \
    piper-tts \
    sounddevice \
    numpy \
    rich \
    customtkinter \
    -q

# ── Copia o app ───────────────────────────────────────────────────────────────
echo "==> Copiando arquivos..."
cp "$SCRIPT_DIR/praxis.py"        "$INSTALL_DIR/"
cp "$SCRIPT_DIR/praxis_config.py" "$INSTALL_DIR/"

# ── Voz Piper padrão: en_US-lessac-medium ────────────────────────────────────
VOICE_BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium"
VOICE_FILE="$VOICES_DIR/en_US-lessac-medium.onnx"

if [[ ! -f "$VOICE_FILE" ]]; then
    echo "==> Baixando voz Piper padrão (en_US-lessac-medium)..."
    curl -L --progress-bar "$VOICE_BASE/en_US-lessac-medium.onnx"      -o "$VOICE_FILE"
    curl -L --progress-bar "$VOICE_BASE/en_US-lessac-medium.onnx.json" -o "${VOICE_FILE}.json"
else
    echo "==> Voz padrão já instalada."
fi

# ── Launcher ──────────────────────────────────────────────────────────────────
cat > "$BIN_DIR/praxis" << EOF
#!/usr/bin/env bash
source "$VENV/bin/activate"
exec python3 "$INSTALL_DIR/praxis_config.py" "\$@"
EOF
chmod +x "$BIN_DIR/praxis"

# ── PATH check ────────────────────────────────────────────────────────────────
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo "  AVISO: Adicione ao ~/.bashrc:"
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

# ── Resumo ────────────────────────────────────────────────────────────────────
echo ""
echo "  ✦ Praxis instalado!"
echo ""
echo "  Abrir janela de configuração:"
echo "    praxis"
echo ""
echo "  Vozes disponíveis em: $VOICES_DIR/"
echo "  Baixe mais em: https://huggingface.co/rhasspy/piper-voices"
echo ""
echo "  Depois de iniciar: selecione 'Praxis_Microfone' no Discord/Meet/OBS."
echo ""
