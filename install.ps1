# Praxis installer for Windows (PowerShell 5+).
#   powershell -ExecutionPolicy Bypass -File install.ps1
$ErrorActionPreference = "Stop"

$InstallDir = Join-Path $env:LOCALAPPDATA "Praxis"
$Venv       = Join-Path $InstallDir "venv"
$VoicesDir  = Join-Path $InstallDir "voices"
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "  ✦ Praxis — installing to $InstallDir"
Write-Host ""
New-Item -ItemType Directory -Force -Path $InstallDir, $VoicesDir | Out-Null

# Python 3.10+
$py = (Get-Command py -ErrorAction SilentlyContinue)
if ($py) { $Python = @("py", "-3") } else { $Python = @("python") }
& $Python[0] $Python[1..9] -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"
if ($LASTEXITCODE -ne 0) { throw "Python 3.10+ is required: https://www.python.org/downloads/" }

Write-Host "==> Creating Python venv..."
& $Python[0] $Python[1..9] -m venv $Venv
$VPy = Join-Path $Venv "Scripts\python.exe"
& $VPy -m pip install --upgrade pip -q

Write-Host "==> Installing Python dependencies..."
& $VPy -m pip install -q -r (Join-Path $ScriptDir "requirements.txt")
& $VPy -m pip install -q --no-deps argostranslate
# GPU acceleration (see praxis_accel.py)
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    Write-Host "==> NVIDIA GPU detected — installing CUDA runtime libraries..."
    & $VPy -m pip install -q nvidia-cublas-cu12 "nvidia-cudnn-cu12>=9,<10"
} elseif ($env:PRAXIS_GPU -eq "vulkan") {
    Write-Host "==> Building whisper.cpp with Vulkan (AMD/Intel GPU)..."
    $env:GGML_VULKAN = "1"
    & $VPy -m pip install -q --no-binary pywhispercpp pywhispercpp
    if ($LASTEXITCODE -ne 0) { Write-Host "  ! Vulkan build failed (install the Vulkan SDK + VS Build Tools) — CPU fallback" }
}

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "==> ffmpeg not found — installing bundled ffmpeg (imageio-ffmpeg)..."
    & $VPy -m pip install -q imageio-ffmpeg
}

Write-Host "==> Copying files..."
Copy-Item -Force (Join-Path $ScriptDir "praxis.py"), (Join-Path $ScriptDir "praxis_config.py"), (Join-Path $ScriptDir "praxis_platform.py") $InstallDir
Copy-Item -Recurse -Force (Join-Path $ScriptDir "assets") $InstallDir

$VoiceFile = Join-Path $VoicesDir "en_US-lessac-medium.onnx"
if (-not (Test-Path $VoiceFile)) {
    Write-Host "==> Downloading default Piper voice (en_US-lessac-medium)..."
    $base = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
    Invoke-WebRequest "$base.json" -OutFile "$VoiceFile.json"
    Invoke-WebRequest $base -OutFile "$VoiceFile.part"
    Move-Item -Force "$VoiceFile.part" $VoiceFile
}

# Start Menu + Desktop shortcuts with the Praxis icon (pythonw = no console window)
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
Write-Host "  ✦ Praxis installed! Open it from the Start Menu."
if (-not $hasCable) {
    Write-Host "  ! Install VB-Audio Virtual Cable (virtual microphone): https://vb-audio.com/Cable/"
}
Write-Host "  In your call app, select 'CABLE Output' as the microphone."
& $VPy (Join-Path $InstallDir "praxis.py") --check | Out-Null
if ($LASTEXITCODE -eq 0) { Write-Host "  Self-check: OK" } else { Write-Host "  ! Self-check failed" }
