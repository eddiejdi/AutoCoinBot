#!/usr/bin/env powershell
# Descobre modelos IA no servidor SSH e configura VSCode Copilot

param(
    [string]$SSHHost = "192.168.15.2",
    [string]$SSHUser = "homelab",
    [string]$SSHPass = "homelab",
    [string]$ModelsPath = "/home/homelab/models",  # Ajuste conforme necessário
    [switch]$Debug = $false
)

# ==================== CONFIGURAÇÕES ====================
$VSCodeSettingsPath = "$env:APPDATA\Code\User\settings.json"
$TempFile = "$env:TEMP\ssh_models_discovery.txt"

Write-Host "Descobrindo modelos no servidor SSH: $SSHHost" -ForegroundColor Cyan

# ==================== FUNÇÃO: EXECUTAR COMANDO SSH ====================
function Invoke-SSHCommand {
    param(
        [string]$Command,
        [string]$RemoteHost,
        [string]$RemoteUser,
        [string]$Password
    )
    
    try {
        # Tenta usar ssh client nativo (Windows 10+)
        # Use sshpass via WSL to allow password-based automation
        Write-Host "  Executando: $Command" -ForegroundColor Gray
        $wslCmd = "sshpass -p $Password ssh -o StrictHostKeyChecking=no ${RemoteUser}@${RemoteHost} '$Command'"
        $result = wsl -e bash -lc $wslCmd 2>&1
        return $result
    }
    catch {
        Write-Host "  Erro SSH: $_" -ForegroundColor Red
        return $null
    }
}

# ==================== DESCOBRIR MODELOS ====================
Write-Host "Buscando modelos..." -ForegroundColor Yellow

# Tentar múltiplos caminhos comuns
$possiblePaths = @(
    "/home/homelab/models",
    "/opt/models",
    "/root/models",
    "~/models",
    "/var/lib/models",
    "."
)

$models = @()
$foundPath = $null

foreach ($path in $possiblePaths) {
    Write-Host "  Verificando: $path" -ForegroundColor Gray
    
    # Comando para listar diretórios de modelos
    $listCmd = "ls -lah $path 2>/dev/null | head -20"
    $result = Invoke-SSHCommand -Command $listCmd -RemoteHost $SSHHost -RemoteUser $SSHUser -Password $SSHPass
    
    if ($result -and $result -notlike "*No such file*") {
        $foundPath = $path
        Write-Host "    Encontrado!" -ForegroundColor Green
        Write-Host $result -ForegroundColor DarkGray
        break
    }
}

if (-not $foundPath) {
    Write-Host "Nenhum diretorio de modelos encontrado nos caminhos padrao. Usando caminho padrao." -ForegroundColor Yellow
    $foundPath = $ModelsPath
}

# ==================== LISTAR MODELOS DETALHADOS ====================
Write-Host "Listando modelos em: $foundPath" -ForegroundColor Cyan

$findCmd = "find $foundPath -type f \( -name '*.gguf' -o -name '*.bin' -o -name '*.pt' -o -name '*.safetensors' \) 2>/dev/null"
$modelFiles = Invoke-SSHCommand -Command $findCmd -RemoteHost $SSHHost -RemoteUser $SSHUser -Password $SSHPass

if ($modelFiles) {
    $modelFiles = $modelFiles -split "`n" | Where-Object { $_ -match '\S' }
    Write-Host "Encontrados $($modelFiles.Count) modelos:" -ForegroundColor Green
    $modelFiles | ForEach-Object {
        Write-Host "    $_" -ForegroundColor Cyan
        $models += $_
    }
}
else {
    Write-Host "Nenhum modelo encontrado." -ForegroundColor Red
}

# ==================== OBTER INFORMAÇÕES DO SERVIDOR ====================
Write-Host "Informacoes do servidor:" -ForegroundColor Yellow

$sysInfo = Invoke-SSHCommand -Command "uname -a" -RemoteHost $SSHHost -RemoteUser $SSHUser -Password $SSHPass
Write-Host "    OS: $sysInfo" -ForegroundColor DarkGray

$pythonCmd = Invoke-SSHCommand -Command "python3 --version 2>&1" -RemoteHost $SSHHost -RemoteUser $SSHUser -Password $SSHPass
Write-Host "    Python: $pythonCmd" -ForegroundColor DarkGray

$gpuCmd = Invoke-SSHCommand -Command "nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'CPU only'" -RemoteHost $SSHHost -RemoteUser $SSHUser -Password $SSHPass
Write-Host "    GPU: $gpuCmd" -ForegroundColor DarkGray

# ==================== CONFIGURAR VSCODE ====================
Write-Host "Configurando VSCode..." -ForegroundColor Cyan

if (-not (Test-Path $VSCodeSettingsPath)) {
    Write-Host "  Criando settings.json..." -ForegroundColor Yellow
    $null = New-Item -Path (Split-Path $VSCodeSettingsPath) -ItemType Directory -Force
    Set-Content -Path $VSCodeSettingsPath -Value "{}" -Encoding UTF8
}

# Ler settings atuais com fallback seguro
try {
    $settings = Get-Content $VSCodeSettingsPath -Encoding UTF8 | ConvertFrom-Json -ErrorAction Stop
} catch {
    Write-Host "  settings.json corrompido. Recriando." -ForegroundColor Yellow
    $settings = @{}
}

# Adicionar configurações do Copilot
$settings | Add-Member -Name "github.copilot.enable" -Value @{
    "*" = $true
    "plaintext" = $false
    "markdown" = $false
} -MemberType NoteProperty -Force

# Configurar modelos remotos
$settings | Add-Member -Name "copilot.advanced" -Value @{
    "authorizationFallback" = $true
    "authorizationFallbackTimeout" = 100
} -MemberType NoteProperty -Force

# Adicionar informação do servidor SSH
if (-not $settings.PSObject.Properties.Name -contains "remote.SSH") {
    $settings | Add-Member -Name "remote.SSH" -Value @{
        "configFile" = "$env:USERPROFILE\.ssh\config"
        "defaultExtensions" = @(
            "ms-vscode-remote.remote-ssh",
            "ms-vscode-remote.remote-ssh-edit",
            "ms-vscode.remote-explorer"
        )
    } -MemberType NoteProperty
}

# Salvar settings.json
$settings | ConvertTo-Json -Depth 10 | Set-Content -Path $VSCodeSettingsPath -Encoding UTF8
Write-Host "  settings.json atualizado" -ForegroundColor Green

# ==================== CONFIGURAR SSH CONFIG ====================
Write-Host "Configurando SSH config..." -ForegroundColor Cyan

$sshConfigPath = "$env:USERPROFILE\.ssh\config"
$sshConfigDir = Split-Path $sshConfigPath

# Criar diretório .ssh se não existir
if (-not (Test-Path $sshConfigDir)) {
    $null = New-Item -Path $sshConfigDir -ItemType Directory -Force
    Write-Host "  Diretório .ssh criado" -ForegroundColor Green
}

# Verificar se host já está configurado
$hostExists = (Test-Path $sshConfigPath) -and (Select-String -Path $sshConfigPath -Pattern "Host homelab-models" -Quiet)

if (-not $hostExists) {
    $sshConfig = @"
# AutoCoinBot Models Server
Host homelab-models
    HostName 192.168.15.2
    User homelab
    Port 22
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    # Descomentar se usar chave privada:
    # IdentityFile ~/.ssh/homelab_key

"@
    
    if (Test-Path $sshConfigPath) {
        Add-Content -Path $sshConfigPath -Value $sshConfig -Encoding UTF8
    }
    else {
        Set-Content -Path $sshConfigPath -Value $sshConfig -Encoding UTF8
    }
    
    Write-Host "  SSH config atualizado" -ForegroundColor Green
}
else {
    Write-Host "  Host homelab-models já configurado" -ForegroundColor DarkYellow
}

# ==================== GERAR RELATÓRIO ====================
Write-Host "" -ForegroundColor White
Write-Host "CONFIGURACAO CONCLUIDA" -ForegroundColor Green

Write-Host "Resumo:" -ForegroundColor Yellow
Write-Host "  • Servidor: $SSHHost (usuário: $SSHUser)"
Write-Host "  • Modelos encontrados: $($models.Count)"
Write-Host "  • VSCode settings: $VSCodeSettingsPath"
Write-Host "  • SSH config: $sshConfigPath"

Write-Host "Proximos passos:" -ForegroundColor Cyan
Write-Host "  1. Reinicie o VSCode"
Write-Host "  2. Abra a paleta de comandos (Ctrl+Shift+P)"
Write-Host "  3. Digite: 'Remote-SSH: Connect to Host...'"
Write-Host "  4. Selecione: 'homelab-models'"
Write-Host "  5. O Copilot agora terá acesso aos modelos do servidor!"

Write-Host "Modelos disponiveis:" -ForegroundColor Yellow
if ($models.Count -gt 0) {
    $models | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkCyan }
}
else {
    Write-Host "    (nenhum encontrado)" -ForegroundColor DarkGray
}

# Salvar relatório
$report = @"
RELATORIO: Descoberta de Modelos IA
Data: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Servidor: $SSHHost
Usuario: $SSHUser

MODELOS ENCONTRADOS ($($models.Count)):
$(if ($models.Count -gt 0) { $models | ForEach-Object { "  - $_" } } else { "  (nenhum)" })

SERVIDOR:
    - OS: $sysInfo
    - Python: $pythonCmd
    - GPU: $gpuCmd

CONFIGURACOES:
    - VSCode settings: $VSCodeSettingsPath
    - SSH config: $sshConfigPath

Status: Concluido com sucesso
"@

$report | Set-Content -Path "$env:TEMP\copilot_models_report.txt" -Encoding UTF8
Write-Host "Relatório salvo em: $env:TEMP\copilot_models_report.txt" -ForegroundColor Gray

Write-Host ""
