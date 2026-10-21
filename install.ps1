# Instalador do Praxis para Windows (PowerShell 5+).
#   powershell -ExecutionPolicy Bypass -File install.ps1
$ErrorActionPreference = "Stop"

$InstallDir = Join-Path $env:LOCALAPPDATA "Praxis"
$Venv       = Join-Path $InstallDir "venv"
$VoicesDir  = Join-Path $InstallDir "voices"
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "  ✦ Praxis — instalando em $InstallDir"
Write-Host ""
New-Item -ItemType Directory -Force -Path $InstallDir, $VoicesDir | Out-Null

# Python 3.10+
$py = (Get-Command py -ErrorAction SilentlyContinue)
if ($py) { $Python = @("py", "-3") } else { $Python = @("python") }
& $Python[0] $Python[1..9] -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"
if ($LASTEXITCODE -ne 0) { throw "É necessário Python 3.10+: https://www.python.org/downloads/" }

Write-Host "==> Criando o ambiente virtual Python (venv)..."
& $Python[0] $Python[1..9] -m venv $Venv
$VPy = Join-Path $Venv "Scripts\python.exe"
& $VPy -m pip install --upgrade pip -q

Write-Host "==> Instalando dependências Python..."
& $VPy -m pip install -q -r (Join-Path $ScriptDir "requirements.txt")
& $VPy -m pip install -q --no-deps argostranslate
# Aceleração pela placa de vídeo (veja praxis_accel.py)
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    Write-Host "==> Placa de vídeo NVIDIA detectada — instalando as bibliotecas CUDA..."
    & $VPy -m pip install -q nvidia-cublas-cu12 "nvidia-cudnn-cu12>=9,<10"
} elseif ($env:PRAXIS_GPU -eq "vulkan") {
    Write-Host "==> Compilando o whisper.cpp com Vulkan (placa de vídeo AMD/Intel)..."
    $env:GGML_VULKAN = "1"
    & $VPy -m pip install -q --no-binary pywhispercpp pywhispercpp
    if ($LASTEXITCODE -ne 0) { Write-Host "  ! A compilação com Vulkan falhou (instale o Vulkan SDK + VS Build Tools) — o Whisper vai rodar na CPU" }
}

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "==> ffmpeg não encontrado — instalando o ffmpeg empacotado (imageio-ffmpeg)..."
    & $VPy -m pip install -q imageio-ffmpeg
}

Write-Host "==> Copiando arquivos..."
# motor, interface, plataforma, aceleração, eco e preparo
Copy-Item -Force (Join-Path $ScriptDir "praxis*.py") $InstallDir
Copy-Item -Recurse -Force (Join-Path $ScriptDir "assets") $InstallDir

$VoiceFile = Join-Path $VoicesDir "en_US-lessac-medium.onnx"
if (-not (Test-Path $VoiceFile)) {
    Write-Host "==> Baixando a voz padrão do Piper (en_US-lessac-medium)..."
    $base = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
    Invoke-WebRequest "$base.json" -OutFile "$VoiceFile.json"
    Invoke-WebRequest $base -OutFile "$VoiceFile.part"
    Move-Item -Force "$VoiceFile.part" $VoiceFile
}

# Atalhos no Menu Iniciar e na Área de Trabalho com o ícone do Praxis (pythonw = sem janela de console)
$Pyw = Join-Path $Venv "Scripts\pythonw.exe"
$Shell = New-Object -ComObject WScript.Shell
foreach ($dir in @([Environment]::GetFolderPath("Programs"), [Environment]::GetFolderPath("Desktop"))) {
    $lnk = $Shell.CreateShortcut((Join-Path $dir "Praxis.lnk"))
    $lnk.TargetPath = $Pyw
    $lnk.Arguments = "`"$(Join-Path $InstallDir 'praxis_config.py')`""
    $lnk.WorkingDirectory = $InstallDir
    $lnk.IconLocation = (Join-Path $InstallDir "assets\icon.ico")
    $lnk.Save()
}

$hasCable = Get-CimInstance Win32_SoundDevice | Where-Object { $_.Name -like "*VB-Audio*" }
Write-Host ""
Write-Host "  ✦ Praxis instalado! Abra pelo Menu Iniciar."
if (-not $hasCable) {
    Write-Host "  ! Instale o VB-Audio Virtual Cable (microfone virtual): https://vb-audio.com/Cable/"
}
Write-Host "  No seu app de chamada, escolha 'CABLE Output' como microfone."
& $VPy (Join-Path $InstallDir "praxis.py") --check | Out-Null
if ($LASTEXITCODE -eq 0) { Write-Host "  Autoteste: OK" } else { Write-Host "  ! O autoteste falhou" }

# Deixa tudo pronto para os idiomas do sistema: vozes, reconhecimento de fala, tradutores
Write-Host ""
Write-Host "==> Preparando o Praxis para já abrir funcionando (vozes, reconhecimento de fala, tradução)..."
$prepArgs = @()
if ($env:PRAXIS_SEM_NLLB -eq "1") { $prepArgs += "--sem-nllb" }
& $VPy (Join-Path $InstallDir "praxis_preparar.py") @prepArgs
if ($LASTEXITCODE -ne 0) { Write-Host "  ! O preparo não terminou — o Praxis baixa o que faltar na primeira vez em que for usado." }
