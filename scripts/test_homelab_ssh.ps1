$key = Join-Path $env:USERPROFILE '.ssh\id_rsa_homelab'
$cmd = 'echo ok'
ssh -i $key -o BatchMode=yes homelab@192.168.15.2 $cmd
