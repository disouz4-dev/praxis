# Roda o cargo no Windows ligado à ctranslate2.dll do pacote oficial (mesma do Python).
# Ex.: scripts\cargo-windows.ps1 build --release
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$lib = Join-Path (Get-Location) "target\ct2-lib"
if (-not (Test-Path (Join-Path $lib "ctranslate2.lib"))) { & (Join-Path $PSScriptRoot "ct2-do-pacote-oficial.ps1") }
$env:CMAKE_LIBRARY_PATH = $lib
$env:RUSTFLAGS = "$env:RUSTFLAGS -L native=$lib"
cargo @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
