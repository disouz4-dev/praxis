# Instalação do Praxis pelo PowerShell, no Windows 10/11 (64 bits):
#
#   irm https://raw.githubusercontent.com/disouz4-dev/praxis/main/install.ps1 | iex
#
# Pergunta ao GitHub qual é a versão mais atual do Praxis, baixa o instalador dela e
# instala sem perguntas (na pasta do usuário, com atalho no Menu Iniciar). Instala também
# o VB-Audio Virtual Cable, o microfone virtual que leva a tradução ao app de chamada
# (gratuito, do site oficial do fabricante; pede permissão de administrador).
#
# Opção: $env:PRAXIS_SETUP = "C:\caminho\Praxis_x.y.z_x64-setup.exe" instala um já baixado.
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.Encoding]::UTF8   # acentos certos na janela do PowerShell
$ProgressPreference = "SilentlyContinue"   # o download fica muito mais rápido sem a barra
$Repo = "disouz4-dev/praxis"
$Tmp = Join-Path $env:TEMP ("praxis-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $Tmp | Out-Null

function Say($t) { Write-Host "  $t" }

try {
    Write-Host ""
    Say "✦ Praxis — instalação"
    Write-Host ""

    # ── 1. O Praxis (versão mais atual publicada) ──
    $Setup = $env:PRAXIS_SETUP
    if (-not $Setup) {
        $rel = Invoke-RestMethod "https://api.github.com/repos/$Repo/releases/latest" -Headers @{ "User-Agent" = "praxis" }
        $asset = $rel.assets | Where-Object { $_.name -like "*_x64-setup.exe" } | Select-Object -First 1
        if (-not $asset) { throw "não encontrei o instalador do Windows na versão $($rel.tag_name)" }
        Say "Baixando o Praxis $($rel.tag_name) (a versão mais atual)…"
        $Setup = Join-Path $Tmp $asset.name
        Invoke-WebRequest $asset.browser_download_url -OutFile $Setup
    }
    Say "Instalando o Praxis…"
    $p = Start-Process -FilePath $Setup -ArgumentList "/S" -Wait -PassThru
    if ($p.ExitCode -ne 0) { throw "o instalador do Praxis terminou com erro ($($p.ExitCode))" }

    # ── 2. Microfone virtual (VB-Audio Virtual Cable) ──
    $temCabo = Get-CimInstance Win32_SoundDevice | Where-Object { $_.Name -like "*VB-Audio Virtual Cable*" }
    if ($temCabo) {
        Say "Microfone virtual (VB-Cable) já instalado."
    } else {
        Say "Instalando o microfone virtual (VB-Audio Virtual Cable)…"
        $zip = Join-Path $Tmp "vbcable.zip"
        Invoke-WebRequest "https://download.vb-audio.com/Download_CABLE/VBCABLE_Driver_Pack45.zip" -OutFile $zip
        $sha = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
        if ($sha -ne "b950e39f01af1d04ea623c8f6d8eb9b6ea5c477c637295fabf20631c85116bfb") {
            throw "o arquivo do VB-Cable baixado não confere (impressão digital diferente)"
        }
        Expand-Archive $zip -DestinationPath (Join-Path $Tmp "vb")
        $vb = Join-Path $Tmp "vb\VBCABLE_Setup_x64.exe"
        $admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
            [Security.Principal.WindowsBuiltInRole]::Administrator)
        if ($admin) {
            Start-Process -FilePath $vb -ArgumentList "-i", "-h" -Wait
        } else {
            Say "(o Windows vai pedir permissão de administrador para o driver)"
            Start-Process -FilePath $vb -ArgumentList "-i", "-h" -Verb RunAs -Wait
        }
        Say "Microfone virtual instalado (pode ser preciso reiniciar o Windows uma vez)."
    }

    Write-Host ""
    Say "✓ Praxis instalado. Abra pelo Menu Iniciar."
    Say "  Na primeira tradução ele baixa os modelos para os seus idiomas."
    Write-Host ""
} finally {
    Remove-Item -Recurse -Force $Tmp -ErrorAction SilentlyContinue
}
