$path = Join-Path $env:USERPROFILE '.ssh\id_rsa_homelab'
$acl = Get-Acl $path
$acl.SetAccessRuleProtection($true,$false)
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule($env:USERNAME,'FullControl','Allow')
$acl.SetAccessRule($rule)
Set-Acl -Path $path -AclObject $acl
Write-Host "Permissions tightened on $path"
