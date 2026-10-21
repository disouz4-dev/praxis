# Roda o cargo no Windows ligado à ctranslate2.dll do pacote oficial (mesma do Python).
# Ex.: scripts\cargo-windows.ps1 build --release
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$lib = Join-Path (Get-Location) "target\ct2-lib"
if (-not (Test-Path (Join-Path $lib "cublas.lib"))) { & (Join-Path $PSScriptRoot "ct2-do-pacote-oficial.ps1") }
# O sherpa-onnx-sys baixa as bibliotecas prontas para target\sherpa-onnx-prebuilt\ e copia
# as DLLs para target\<perfil>\, mas só quando o build.rs dele roda. O cache do GitHub
# Actions (Swatinem/rust-cache) guarda o "já compilado" do sherpa-onnx-sys e apaga essas
# pastas; se elas sumiram, apaga o registro de compilação dele para o build.rs rodar de novo.
if (-not (Get-ChildItem "target\sherpa-onnx-prebuilt\*\lib" -Directory -ErrorAction SilentlyContinue)) {
    Get-ChildItem "target\*\build\sherpa-onnx-sys-*", "target\*\.fingerprint\sherpa-onnx-sys-*" -Directory -Force -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force
}
$env:CMAKE_LIBRARY_PATH = $lib
$env:RUSTFLAGS = "$env:RUSTFLAGS -L native=$lib"
cargo @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
