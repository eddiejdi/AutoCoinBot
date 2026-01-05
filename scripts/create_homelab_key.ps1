$keyPath = Join-Path $env:USERPROFILE ".ssh\id_rsa_homelab"

if (Test-Path $keyPath) {
    Write-Host "Key already exists at $keyPath"
    exit 0
}

Write-Host "Generating SSH key at $keyPath"
ssh-keygen -t rsa -b 4096 -f $keyPath -N "" -q
