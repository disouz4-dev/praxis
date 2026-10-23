# Compila o omnivoice.cpp (OmniVoice: a voz clonada fiel, MIT) como omnivoice.dll com o motor
# Vulkan (placas AMD, Intel e NVIDIA) e põe em target/release/omnivoice/. O vulkan-1.dll vem com o
# driver da placa; sem ele (ou sem placa), o Praxis usa a voz leve.
# Precisa do Vulkan SDK (VULKAN_SDK) e do SPIRV-Headers. Uso (em app/): scripts/omnivoice.ps1
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$commit = "1a468d8b9d65b3544ca1004d2d7c05dfc65d1f3e"
$src = "target/omnivoice-src"
# sem conversão de quebra de linha (senão o patch do Praxis não encaixa)
if (-not (Test-Path "$src/.git")) { git -c core.autocrlf=false clone -q https://github.com/ServeurpersoCom/omnivoice.cpp.git $src }
git -C $src config core.autocrlf false
git -C $src checkout -q -f $commit
git -C $src submodule update -q --init --recursive
git -C $src apply --whitespace=nowarn (Resolve-Path "pacotes/omnivoice-praxis.patch")
# OMNIVOICE_CMAKE traz várias opções separadas por espaço: cada uma vira um argumento
$extra = @(); if ($env:OMNIVOICE_CMAKE) { $extra = $env:OMNIVOICE_CMAKE -split ' ' | Where-Object { $_ } }
cmake -S $src -B "$src/build" -DCMAKE_BUILD_TYPE=Release -DGGML_VULKAN=ON -DOMNIVOICE_SHARED=ON `
  -DBUILD_SHARED_LIBS=OFF -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DGGML_NATIVE=OFF @extra
if ($LASTEXITCODE -ne 0) { exit 1 }
cmake --build "$src/build" --config Release --target omnivoice -j 4
if ($LASTEXITCODE -ne 0) { exit 1 }
New-Item -ItemType Directory -Force target/release/omnivoice | Out-Null
$dll = Get-ChildItem "$src/build" -Recurse -Filter omnivoice.dll | Select-Object -First 1
Copy-Item $dll.FullName target/release/omnivoice/
Get-ChildItem target/release/omnivoice
