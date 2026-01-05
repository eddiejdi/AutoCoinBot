$configPath = Join-Path $env:USERPROFILE '.ssh\config'
$hostBlock = @"
# AutoCoinBot Models Server
Host homelab-models
    HostName 192.168.15.2
    User homelab
    Port 22
    IdentityFile ~/.ssh/id_rsa_homelab
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
"@

if (-not (Test-Path (Split-Path $configPath))) {
    New-Item -ItemType Directory -Path (Split-Path $configPath) -Force | Out-Null
}

if (-not (Test-Path $configPath)) {
    $hostBlock | Set-Content -Path $configPath -Encoding UTF8
    Write-Host "Created $configPath with homelab-models block"
    exit 0
}

$existing = Get-Content $configPath -Raw
if ($existing -notmatch 'Host homelab-models') {
    Add-Content -Path $configPath -Value "`n$hostBlock" -Encoding UTF8
    Write-Host "Appended homelab-models block to $configPath"
} else {
    $lines = $existing -split "`n"
    $newLines = @()
    $inBlock = $false
    foreach ($line in $lines) {
        if ($line -match '^Host homelab-models') { $inBlock = $true }
        if ($inBlock -and ($line -match '^Host ' -and $line -notmatch '^Host homelab-models')) { $inBlock = $false }
        if (-not $inBlock) { $newLines += $line }
    }
    $newContent = ($newLines -join "`n") + "`n$hostBlock"
    $newContent | Set-Content -Path $configPath -Encoding UTF8
    Write-Host "Replaced homelab-models block in $configPath"
}
