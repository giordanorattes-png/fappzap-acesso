# Teste da variante da Microsoft Store do FappZap Acesso, DENTRO da Windows Sandbox (nunca na máquina de uso).
# Roda pelo LogonCommand do loja.wsb, com a pasta de teste mapeada em C:\teste. Resultado em C:\teste\resultado.txt
# e capturas em C:\teste\tela-*.png (a Sandbox é descartada ao fechar).
#
# Passos: (1) liga a confiança do certificado de TESTE e desliga o Smart App Control SÓ dentro da Sandbox (a Store
# assina de verdade; aqui o pacote leva um certificado de teste); (2) instala o .msix; (3) abre o app pelo atalho
# do pacote; (4) confere processo, rede para o nosso servidor e os registros; (5) captura a tela.
$ErrorActionPreference = 'Continue'
$pasta = 'C:\teste'
$saida = Join-Path $pasta 'resultado.txt'
function L($t) { $t | Out-File -FilePath $saida -Append -Encoding utf8; Write-Host $t }
Remove-Item $saida -ErrorAction SilentlyContinue
L "inicio: $(Get-Date -Format s)"

# 1) confiança do certificado de teste + SAC desligado (só nesta Sandbox)
$cer = Get-ChildItem $pasta -Filter *.cer | Select-Object -First 1
Import-Certificate -FilePath $cer.FullName -CertStoreLocation Cert:\LocalMachine\Root | Out-Null
Import-Certificate -FilePath $cer.FullName -CertStoreLocation Cert:\LocalMachine\TrustedPeople | Out-Null
reg add 'HKLM\SYSTEM\CurrentControlSet\Control\CI\Policy' /v VerifiedAndReputablePolicyState /t REG_DWORD /d 0 /f | Out-Null
CiTool --refresh 2>&1 | Out-Null
Start-Sleep 3
L ("SAC: " + @('desligado', 'ligado', 'avaliando')[[int](Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy').VerifiedAndReputablePolicyState])

# 2) instala o pacote
$msix = Get-ChildItem $pasta -Filter *.msix | Select-Object -First 1
L "pacote: $($msix.Name)"
try { Add-AppxPackage -Path $msix.FullName -ErrorAction Stop; L 'instalacao: OK' } catch { L "instalacao: FALHOU -> $($_.Exception.Message)" }
$pkg = Get-AppxPackage | Where-Object { $_.Name -like '*FappZapAcesso*' } | Select-Object -First 1
if (-not $pkg) { L 'pacote nao aparece em Get-AppxPackage'; exit 1 }
L "pacote instalado: $($pkg.PackageFullName)"
L "PFN: $($pkg.PackageFamilyName)"
$srv = Get-Service -Name 'FappZap-Acesso' -ErrorAction SilentlyContinue
L ("servico do Windows (esperado: NAO EXISTE): " + $(if ($srv) { "EXISTE ($($srv.Status))" } else { 'NAO EXISTE' }))

# 3) abre o app pelo atalho do pacote
Start-Process explorer.exe "shell:AppsFolder\$($pkg.PackageFamilyName)!FappZapAcesso"
Start-Sleep 25

# 4) processo, rede e registros
$proc = Get-Process -Name 'FappZap-Acesso' -ErrorAction SilentlyContinue
L ("processos FappZap-Acesso: " + $(if ($proc) { ($proc | ForEach-Object { "$($_.Id)" }) -join ',' } else { 'NENHUM (o app fechou)' }))
$c = Get-NetTCPConnection -RemoteAddress 187.127.51.232 -ErrorAction SilentlyContinue
$u = Get-NetUDPEndpoint -ErrorAction SilentlyContinue | Where-Object { (Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).Name -eq 'FappZap-Acesso' }
L ("servidor acesso.fappsolutions.com: " + $(if ($c -or $u) { 'conectado' } else { 'sem conexao vista' }))
$base = Join-Path $env:LOCALAPPDATA "Packages\$($pkg.PackageFamilyName)"
$logs = Get-ChildItem $base -Recurse -Include *.log -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 3
foreach ($lg in $logs) { L "--- $($lg.FullName.Replace($base, '...'))"; Get-Content $lg.FullName -Tail 25 -ErrorAction SilentlyContinue | ForEach-Object { L $_ } }
$bloq = Get-WinEvent -LogName 'Microsoft-Windows-CodeIntegrity/Operational' -MaxEvents 30 -ErrorAction SilentlyContinue | Where-Object { $_.Message -match 'FappZap' } | Select-Object -First 1
if ($bloq) { L "BLOQUEIO do Windows: $(($bloq.Message -split "`n")[0])" }

# 5) capturas da tela (1ª logo; 2ª depois de mais um tempo)
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
function Tela($nome) {
  $b = [System.Windows.Forms.SystemInformation]::VirtualScreen
  $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.CopyFromScreen($b.Left, $b.Top, 0, 0, $bmp.Size)
  $bmp.Save((Join-Path $pasta $nome), [System.Drawing.Imaging.ImageFormat]::Png)
  $g.Dispose(); $bmp.Dispose()
  L "captura: $nome ($($b.Width)x$($b.Height))"
}
Tela 'tela-1.png'
Start-Sleep 20
Tela 'tela-2.png'
L "fim: $(Get-Date -Format s)"
