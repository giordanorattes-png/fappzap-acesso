# Teste do FappZap Acesso numa máquina de teste (rode no PowerShell COMO ADMINISTRADOR):
#   irm https://raw.githubusercontent.com/giordanorattes-png/fappzap-acesso/fappzap/fappzap/testar-vm.ps1 | iex
# Baixa o MSI do release mais novo, instala sem perguntas e mostra um resumo para colar na conversa.
# Não muda nenhuma configuração de segurança da máquina.
$ErrorActionPreference = 'Continue'
$repo = 'giordanorattes-png/fappzap-acesso'
$tmp = Join-Path $env:TEMP 'fappzap-acesso-teste'
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
$r = @()
# Não chamar de R: no PowerShell "r" é o atalho do Invoke-History e ganha da função.
function Linha($t) { $script:r += $t; Write-Host $t }

# Entre parênteses: no Windows PowerShell 5.1 a lista do JSON chega como um objeto só.
$rel = (Invoke-RestMethod "https://api.github.com/repos/$repo/releases?per_page=10") | Where-Object { $_.assets.name -match '\.msi$' } | Select-Object -First 1
$msi = $rel.assets | Where-Object name -match '\.msi$' | Select-Object -First 1
Linha "release: $($rel.tag_name) / $($msi.name)"
$arq = Join-Path $tmp $msi.name
Invoke-WebRequest $msi.browser_download_url -OutFile $arq -UseBasicParsing
Linha ("Smart App Control: " + @('desligado', 'ligado', 'avaliando')[[int](Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy' -ErrorAction SilentlyContinue).VerifiedAndReputablePolicyState])

$p = Start-Process msiexec.exe -ArgumentList '/i', "`"$arq`"", '/qn', '/l*v', "`"$tmp\msi.log`"" -Wait -PassThru
Linha "instalador: saída $($p.ExitCode) (0 = ok)"
Start-Sleep 30
$svc = Get-Service FappZap-Acesso -ErrorAction SilentlyContinue
Linha ("serviço: " + $(if ($svc) { "$($svc.Status) / $($svc.StartType)" } else { 'NÃO EXISTE' }))
$exe = 'C:\Program Files\FappZap-Acesso\FappZap-Acesso.exe'
if (Test-Path $exe) {
  $v = Join-Path $tmp 'versao.txt'
  Start-Process $exe -ArgumentList '--version' -Wait -NoNewWindow -RedirectStandardOutput $v
  Linha ("versão: " + (Get-Content $v -Raw).Trim())
  Linha ("ID: " + ((& $exe --get-id 2>&1) | Out-String).Trim())
} else { Linha 'programa: NÃO INSTALADO' }
$c = Get-NetTCPConnection -RemoteAddress 187.127.51.232 -ErrorAction SilentlyContinue
$u = Get-NetUDPEndpoint -ErrorAction SilentlyContinue | Where-Object { (Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).Name -eq 'FappZap-Acesso' }
Linha ("servidor acesso.fappsolutions.com: " + $(if ($c -or $u) { 'conectado' } else { 'sem conexão vista' }))
$bloq = Get-WinEvent -LogName 'Microsoft-Windows-CodeIntegrity/Operational' -MaxEvents 30 -ErrorAction SilentlyContinue | Where-Object { $_.Message -match 'FappZap' } | Select-Object -First 1
if ($bloq) { Linha "BLOQUEIO do Windows: $(($bloq.Message -split "`n")[0])" }
Write-Host ''
Write-Host '==== copie o bloco abaixo e cole na conversa ===='
$r -join "`n" | Write-Host
Set-Clipboard -Value ($r -join "`n") -ErrorAction SilentlyContinue
Write-Host '(o resumo também foi copiado para a área de transferência)'
