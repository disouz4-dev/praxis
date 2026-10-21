# Roda o cargo no Windows ligado à ctranslate2.dll do pacote oficial (mesma do Python).
# Ex.: scripts\cargo-windows.ps1 build --release
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$lib = Join-Path (Get-Location) "target\ct2-lib"
if (-not (Test-Path (Join-Path $lib "cublas.lib"))) { & (Join-Path $PSScriptRoot "ct2-do-pacote-oficial.ps1") }
# O sherpa-onnx-sys baixa as bibliotecas prontas para target\sherpa-onnx-prebuilt\ e copia
# as DLLs para target\<perfil>\, mas só quando o build.rs dele roda. O cache do GitHub
# Actions (Swatinem/rust-cache) guarda o "já compilado" do sherpa-onnx-sys e apaga essas
# pastas. Para cada compilação guardada, confere se a pasta que o build.rs indicou ainda
# tem a biblioteca; se não tem, apaga o registro de compilação para ele rodar de novo.
foreach ($saida in Get-ChildItem "target\*\build\sherpa-onnx-sys-*\output", "target\*\*\build\sherpa-onnx-sys-*\output" -File -Force -ErrorAction SilentlyContinue) {
    $linha = Select-String -Path $saida.FullName -Pattern '^cargo:rustc-link-search=native=(.+)$' | Select-Object -First 1
    if (-not $linha) { continue }
    $pasta = $linha.Matches[0].Groups[1].Value.Trim()
    if (-not (Get-ChildItem (Join-Path $pasta "*sherpa-onnx-c-api*") -ErrorAction SilentlyContinue)) {
        $perfil = $saida.Directory.Parent.Parent.FullName
        Write-Host "bibliotecas do sherpa-onnx ausentes em ${pasta}: o sherpa-onnx-sys será compilado de novo"
        Get-ChildItem (Join-Path $perfil "build\sherpa-onnx-sys-*"), (Join-Path $perfil ".fingerprint\sherpa-onnx-sys-*") -Directory -Force -ErrorAction SilentlyContinue |
            Remove-Item -Recurse -Force
        # uma pasta lib\ vazia que sobrou faria o build.rs achar que já baixou
        if ($pasta -match 'sherpa-onnx-prebuilt[\\/][^\\/]+[\\/]lib$') { Remove-Item -Recurse -Force (Split-Path $pasta) -ErrorAction SilentlyContinue }
    }
}
$env:CMAKE_LIBRARY_PATH = $lib
$env:RUSTFLAGS = "$env:RUSTFLAGS -L native=$lib"
cargo @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
