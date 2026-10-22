# Instalação do Praxis pelo PowerShell, no Windows 10/11 (64 bits):
#
#   irm https://disouz4-dev.github.io/praxis/install.ps1 | iex
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

# O Windows PowerShell lê este script na codificação antiga do Windows (pelo arquivo ou pelo
# "irm | iex"): as letras acentuadas chegam trocadas ("instalaÃ§Ã£o"). Say desfaz a troca.
function Say($t) {
    if ($t -match "[\u00C3\u00C2]") { $t = [Text.Encoding]::UTF8.GetString([Text.Encoding]::GetEncoding(1252).GetBytes($t)) }
    Write-Host "  $t"
}

try {
    Write-Host ""
    Say "✦ Praxis - instalação"
    Write-Host ""

    # -- 1. O Praxis (versão mais atual publicada) --
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

    # -- 2. Microfone virtual (VB-Audio Virtual Cable), com o nome "Praxis Mic" --
    # Instalar o driver e renomear os lados do cabo pedem administrador: tudo vai num passo só.
    $temCabo = [bool](Get-CimInstance Win32_SoundDevice | Where-Object { $_.Name -like "*VB-Audio Virtual Cable*" })
    $vb = ""
    if ($temCabo) {
        Say "Microfone virtual (VB-Cable) já instalado."
    } else {
        Say "Baixando o microfone virtual (VB-Audio Virtual Cable)…"
        $zip = Join-Path $Tmp "vbcable.zip"
        Invoke-WebRequest "https://download.vb-audio.com/Download_CABLE/VBCABLE_Driver_Pack45.zip" -OutFile $zip
        $sha = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
        if ($sha -ne "b950e39f01af1d04ea623c8f6d8eb9b6ea5c477c637295fabf20631c85116bfb") {
            throw "o arquivo do VB-Cable baixado não confere (impressão digital diferente)"
        }
        Expand-Archive $zip -DestinationPath (Join-Path $Tmp "vb")
        $vb = Join-Path $Tmp "vb\VBCABLE_Setup_x64.exe"
    }
    $passo = @'
param($vb)
if ($vb) { Start-Process -FilePath $vb -ArgumentList "-i", "-h" -Wait; Start-Sleep 3 }
# o mesmo que Painel de Som -> Propriedades -> nome: o app de chamada passa a mostrar "Praxis Mic"

Add-Type -IgnoreWarnings -TypeDefinition @"
using System; using System.Runtime.InteropServices;
[StructLayout(LayoutKind.Sequential)] public struct PROPERTYKEY { public Guid fmtid; public uint pid; }
[StructLayout(LayoutKind.Explicit)] public struct PROPVARIANT { [FieldOffset(0)] public ushort vt; [FieldOffset(8)] public IntPtr p; }
[Guid("886d8eeb-8cf2-4446-8d02-cdba1dbdcf99"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IPropertyStore { int GetCount(out uint c); int GetAt(uint i, out PROPERTYKEY k); int GetValue(ref PROPERTYKEY k, out PROPVARIANT v); int SetValue(ref PROPERTYKEY k, ref PROPVARIANT v); int Commit(); }
[Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice { int Activate(ref Guid iid, int ctx, IntPtr p, [MarshalAs(UnmanagedType.IUnknown)] out object o); int OpenPropertyStore(int access, out IPropertyStore ps); int GetId([MarshalAs(UnmanagedType.LPWStr)] out string id); int GetState(out int s); }
[Guid("0BD7A1BE-7A1A-44DB-8397-CC5392387B5E"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceCollection { int GetCount(out uint c); int Item(uint i, out IMMDevice d); }
[Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator { int EnumAudioEndpoints(int flow, int mask, out IMMDeviceCollection c); }
[ComImport, Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")] class MMDeviceEnumerator {}
public static class Nomes {
  static PROPERTYKEY Desc = new PROPERTYKEY { fmtid = new Guid("a45c254e-df1c-4efd-8020-67d146a850e0"), pid = 2 };
  static PROPERTYKEY Friendly = new PROPERTYKEY { fmtid = new Guid("a45c254e-df1c-4efd-8020-67d146a850e0"), pid = 14 };
  static string Ler(IPropertyStore ps, PROPERTYKEY k) { PROPVARIANT v; ps.GetValue(ref k, out v); return v.vt == 31 ? Marshal.PtrToStringUni(v.p) : ""; }
  // flow: 0 = reprodução, 1 = gravação. Troca o nome de quem hoje se chama 'de' (ou já 'para').
  public static string Renomear(int flow, string de, string para) {
    var en = (IMMDeviceEnumerator)new MMDeviceEnumerator(); IMMDeviceCollection col; en.EnumAudioEndpoints(flow, 0xF, out col);
    uint n; col.GetCount(out n); string r = "";
    for (uint i = 0; i < n; i++) {
      IMMDevice d; col.Item(i, out d); IPropertyStore ro; d.OpenPropertyStore(0, out ro);
      string nome = Ler(ro, Friendly);   // "CABLE Output (VB-Audio Virtual Cable)"
      if (!nome.EndsWith("(VB-Audio Virtual Cable)")) continue;
      if (nome.StartsWith(para + " (")) { r += "já se chama " + para + "; "; continue; }
      if (!nome.StartsWith(de + " (")) continue;
      IPropertyStore rw; int hr = d.OpenPropertyStore(1, out rw); if (hr != 0) { r += "sem permissão (" + hr.ToString("X") + "); "; continue; }
      var k = Desc; var v = new PROPVARIANT { vt = 31, p = Marshal.StringToCoTaskMemUni(para) };
      hr = rw.SetValue(ref k, ref v); if (hr == 0) hr = rw.Commit();
      r += (hr == 0 ? de + " -> " + para : "falhou " + hr.ToString("X")) + "; ";
    }
    return r == "" ? "não achei " + de : r;
  }
}
"@
[Nomes]::Renomear(1, "CABLE Output", "Praxis Mic") | Out-Null
[Nomes]::Renomear(0, "CABLE Input", "Praxis interno") | Out-Null
'@
    $arq = Join-Path $Tmp "microfone.ps1"
    Set-Content -Encoding UTF8 -Path $arq -Value $passo
    $admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)
    if ($admin) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $arq $vb
    } else {
        Say "(o Windows vai pedir permissão de administrador para o microfone virtual)"
        $pa = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "`"$arq`"")
        if ($vb) { $pa += "`"$vb`"" }
        Start-Process powershell -ArgumentList $pa -Verb RunAs -Wait
    }
    $nomes = (Get-CimInstance Win32_PnPEntity -Filter "PNPClass='AudioEndpoint'" | Select-Object -Expand Name) -join " | "
    if ($nomes -like "*Praxis Mic*") { Say "Microfone virtual pronto: no app de chamada, escolha `"Praxis Mic`"." }
    else { Say "Microfone virtual instalado (pode ser preciso reiniciar o Windows uma vez)." }

    Write-Host ""
    Say "OK: Praxis instalado. Abra pelo Menu Iniciar."
    Say "  Na primeira tradução ele baixa os modelos para os seus idiomas."
    Write-Host ""
} finally {
    Remove-Item -Recurse -Force $Tmp -ErrorAction SilentlyContinue
}
