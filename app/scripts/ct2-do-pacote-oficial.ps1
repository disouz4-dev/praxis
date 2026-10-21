# Windows: usa no motor em Rust a MESMA ctranslate2.dll do pacote oficial do Python (MKL
# da Intel + placa NVIDIA), como no Linux e no macOS. O pacote não traz o índice de
# ligação (.lib): ele é gerado a partir das funções exportadas pela própria DLL.
# Precisa das ferramentas do Visual Studio no PATH (dumpbin, lib, cl).
# Saída: target\ct2-lib\ (DLLs + .lib), pronta para o cargo (veja scripts\cargo-windows.ps1).
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$ver = "4.8.3"
$out = Join-Path (Get-Location) "target\ct2-lib"
$tmp = Join-Path $env:TEMP ("ct2-" + [guid]::NewGuid())
New-Item -ItemType Directory -Force -Path $out, $tmp | Out-Null
python -m pip download --quiet --no-deps --only-binary :all: --python-version 3.12 --platform win_amd64 "ctranslate2==$ver" -d $tmp
$whl = Get-ChildItem $tmp -Filter *.whl | Select-Object -First 1
Expand-Archive -Path $whl.FullName -DestinationPath (Join-Path $tmp "x") -Force
Copy-Item (Join-Path $tmp "x\ctranslate2\*.dll") $out -Force

# índice de ligação a partir das exportações da DLL
$exports = dumpbin /exports (Join-Path $out "ctranslate2.dll")
$names = $exports | ForEach-Object { if ($_ -match '^\s+\d+\s+[0-9A-F]+\s+[0-9A-F]+\s+(\S+)') { $Matches[1] } }
@("LIBRARY ctranslate2", "EXPORTS") + $names | Set-Content -Encoding ascii (Join-Path $tmp "ctranslate2.def")
lib /nologo /def:(Join-Path $tmp "ctranslate2.def") /machine:x64 /out:(Join-Path $out "ctranslate2.lib") | Out-Null

# o ct2rs pede bibliotecas que, no pacote oficial, já estão dentro da DLL (cpu_features)
# ou são carregadas por ela na hora de rodar (cuBLAS): índices vazios só para a ligação
Set-Content -Encoding ascii (Join-Path $tmp "vazio.c") "void praxis_vazio(void) {}"
cl /nologo /c (Join-Path $tmp "vazio.c") /Fo(Join-Path $tmp "vazio.obj") | Out-Null
foreach ($l in "cpu_features", "cublas", "cublasLt") {
    lib /nologo (Join-Path $tmp "vazio.obj") /out:(Join-Path $out "$l.lib") | Out-Null
}
Remove-Item -Recurse -Force $tmp
Get-ChildItem $out | Format-Table Name, Length
