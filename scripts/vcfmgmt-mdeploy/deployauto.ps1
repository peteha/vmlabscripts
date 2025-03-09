## Updated from William Lam's script

$vCenterServerFQDN = "vc.pggb.local"
$vCenterUsername = "administrator@pggb.local"
$vCenterPassword = "pggbLabVMware1~~"

$VMFolder = "pg-workloads"
$VMCluster = "pg-cl-1"
$VMNetwork = "pg-vds-VM-Management"
$VMDatastore = "vsanDatastore"

# VCFA Config
$vcfa_hostname = "pgvmaa2"
$vcfa_IP = "10.200.2.23"
$vcfa_netmask = "255.255.255.0"
$vcfa_gateway = "10.200.2.1"
$vcfa_domain = "pggb.local"
$vcfa_searchpath = "pggb.local"
$vcfa_dns = "10.1.100.128"
$vcfa_ntp = "10.1.100.128"
$vcfa_rootpwd = "VMware1@@VMware1@@"
$vcfa_k8_cluster_cidr = "10.127.0.0/23"
$vcfa_k8_service_cidr = "10.127.16.0/23"
$vcfa_deploymentoption = "medium"
$vcfa_ovaloc = "C:\Users\peteha\Downloads\Prelude_VA-8.18.1.36791-24282366_OVF10.ova"


### DO NOT EDIT BEYOND HERE ###

$vcfa_fqdn = "${vcfa_hostname}.${vcfa_domain}"

Write-Host "=== Building VM App ${vcfa_fqdn} ===" -ForegroundColor Green

Write-Host "Connecting to vCenter Server ..."
Connect-VIServer -Server $vCenterServerFQDN -User $vCenterUsername -Password $vCenterPassword | Out-Null

$ovfconfig = Get-OvfConfiguration $vcfa_ovaloc

$networkMapLabel = ($ovfconfig.ToHashTable().keys | where {$_ -Match "NetworkMapping"}).replace("NetworkMapping.","").replace("-","_").replace(" ","_")
$ovfconfig.NetworkMapping.$networkMapLabel.value = $VMNetwork
$ovfconfig.common.vami.hostname.value = $vcfa_hostname
$ovfconfig.vami.vRealize_Automation.ip0.value = $vcfa_IP
$ovfconfig.vami.vRealize_Automation.netmask0.value = $vcfa_netmask
$ovfconfig.vami.vRealize_Automation.gateway.value = $vcfa_gateway
$ovfconfig.vami.vRealize_Automation.DNS.value = $vcfa_dns
$ovfconfig.vami.vRealize_Automation.searchpath.value = $vcfa_searchpath

$ovfconfig.common.varoot_password.value = $vcfa_rootpwd
$ovfconfig.common.va_ssh_enabled.value = "True"
$ovfconfig.common.fips_mode.value = "False"
$ovfconfig.common.ntp_servers.value = $vcfa_ntp
$ovfconfig.common.k8s_cluster_cidr.value = $vcfa_k8_cluster_cidr
$ovfconfig.common.k8s_service_cidr.value = $vcfa_k8_service_cidr
$ovfconfig.DeploymentOption.value = $vcfa_deploymentoption


$datastore = Get-Datastore -Server $viConnection -Name $VMDatastore | Select -First 1
$cluster = Get-Cluster -Server $viConnection -Name $VMCluster
$vmhost = $cluster | Get-VMHost | Get-Random -Count 1
$vmfolder = Get-Folder -Name $VMFolder

Write-Host "Deploying VCFA ..."
$vm = Import-VApp -Source $vcfa_ovaloc  -OvfConfiguration $ovfconfig -Name $vcfa_hostname -Location $VMCluster -VMHost $vmhost -Datastore $datastore -DiskStorageFormat thin -InventoryLocation (Get-Folder $VMFolder)
$vm | Start-Vm -RunAsync | Out-Null

Disconnect-VIServer * -Confirm:$false | Out-Null
