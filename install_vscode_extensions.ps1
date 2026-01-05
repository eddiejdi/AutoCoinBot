#!/usr/bin/env powershell
<#!
  Instala extensões VSCode necessárias para Copilot remoto
#>

Write-Host "Instalando extensões VSCode para Copilot remoto..." -ForegroundColor Cyan

if (-not (Get-Command code -ErrorAction SilentlyContinue)) {
    Write-Host "VSCode não encontrado. Instale em https://code.visualstudio.com" -ForegroundColor Red
    exit 1
}

$extensions = @(
    "GitHub.copilot",
    "GitHub.copilot-chat",
    "ms-vscode-remote.remote-ssh",
    "ms-vscode-remote.remote-ssh-edit",
    "ms-vscode.remote-explorer"
)

Write-Host "Extensões a instalar:" -ForegroundColor Yellow
$extensions | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }

$failed = @()
$success = @()

foreach ($ext in $extensions) {
    Write-Host "Instalando $ext" -ForegroundColor Gray
    $output = code --install-extension $ext 2>&1
    if ($LASTEXITCODE -eq 0) {
        $success += $ext
    }
    else {
        $failed += $ext
        Write-Host "  Erro: $output" -ForegroundColor Red
    }
}

Write-Host "Resumo:" -ForegroundColor Cyan
Write-Host "  Sucesso: $($success.Count)" -ForegroundColor Green
if ($failed.Count -gt 0) {
    Write-Host "  Falha: $($failed.Count)" -ForegroundColor Red
    $failed | ForEach-Object { Write-Host "    - $_" -ForegroundColor Red }
}

Write-Host "Próximos passos: reinicie o VSCode e rode setup_copilot_models_ssh.ps1" -ForegroundColor Yellow
