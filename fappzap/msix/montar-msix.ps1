# Monta o .msix do FappZap Acesso a partir da pasta do programa compilado (a mesma que vira o MSI).
#   powershell -File fappzap\msix\montar-msix.ps1 -App <pasta> -Saida <arquivo.msix> -Versao 1.5.0.0
# Para a Store vai SEM assinatura (a Microsoft assina). Para testar fora da Store, passe -Publisher
# com o mesmo nome do certificado de teste e assine depois com o signtool.
param(
  [Parameter(Mandatory)] [string] $App,
  [Parameter(Mandatory)] [string] $Saida,
  [Parameter(Mandatory)] [string] $Versao,
  [string] $Identidade = 'FappSolutions.FappZapAcesso',
  # O Publisher da conta Fapp Solutions no Partner Center (o mesmo do FappZap Suporte).
  [string] $Publisher = 'CN=997374EF-248E-4CB5-BE11-B0218CDA905C'
)
$ErrorActionPreference = 'Stop'
$aqui = Split-Path -Parent $MyInvocation.MyCommand.Path
$raiz = Split-Path -Parent $aqui
$layout = Join-Path ([IO.Path]::GetTempPath()) ("fz-msix-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $layout | Out-Null

# Drivers (impressora e monitor virtual) não instalam de dentro de um pacote da Store: ficam fora.
Get-ChildItem $App | Where-Object { $_.Name -notin @('drivers', 'usbmmidd_v2') } |
  ForEach-Object { Copy-Item $_.FullName -Destination $layout -Recurse }
Copy-Item (Join-Path $raiz 'marca-msix') -Destination (Join-Path $layout 'Assets') -Recurse

$manifesto = Get-Content (Join-Path $aqui 'AppxManifest.xml') -Raw -Encoding UTF8
$manifesto = $manifesto.Replace('{VERSAO}', $Versao).Replace('{IDENTIDADE}', $Identidade).Replace('{PUBLISHER}', $Publisher)
[IO.File]::WriteAllText((Join-Path $layout 'AppxManifest.xml'), $manifesto, (New-Object Text.UTF8Encoding $false))

$sdk = Get-ChildItem 'C:\Program Files (x86)\Windows Kits\10\bin\*\x64\makeappx.exe' | Sort-Object FullName | Select-Object -Last 1
if (-not $sdk) { throw 'makeappx.exe não encontrado (Windows SDK).' }
& $sdk.FullName pack /o /d $layout /p $Saida | Out-Host
if ($LASTEXITCODE -ne 0) { throw "makeappx falhou ($LASTEXITCODE)" }
Remove-Item $layout -Recurse -Force
Write-Host "msix: $Saida"
