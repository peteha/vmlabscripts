param(
    [string]$vCenterServer,
    [string]$Username,
    [string]$Password,
    [string]$JsonFilePath
)
Import-Module VMware.VimAutomation.Core

# Connect to vCenter
$viserver = Connect-VIServer -Server $vCenterServer -User $Username -Password $Password

Write-Host "=== Connected to " $viserver " ==="

Write-Host "=== Updating HCL ===" -ForegroundColor green
Update-VsanHclDatabase -FilePath $JsonFilePath

# Disconnect from vCenter and remove the session
Disconnect-VIServer -Server $viserver -Confirm:$false