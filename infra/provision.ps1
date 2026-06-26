<#
.SYNOPSIS
  Accelerate Agentic AI — MASTER provisioning script (Azure CLI, PowerShell).
  Mirrors provision.sh for Windows / PowerShell users.

.DESCRIPTION
  Creates: resource group, Microsoft Foundry account + project, model
  deployments (gpt-4o, gpt-4.1, gpt-4.1-mini, gpt-5-mini, text-embedding-3-large),
  Azure AI Search, storage + container, RBAC, and a populated ..\.env.
  Idempotent — safe to re-run.

.EXAMPLE
  az login
  ./provision.ps1
#>
[CmdletBinding()]
param(
  [string]$Location       = $env:LOCATION       ?? "australiaeast",
  [string]$ResourceGroup  = $env:RESOURCE_GROUP ?? "rg-agentic-ai-demos",
  [string]$Suffix         = $env:SUFFIX,
  [string]$FoundryProject = $env:FOUNDRY_PROJECT ?? "agentic-demos",
  [string]$ProjectsApiVersion = "2025-06-01"
)
$ErrorActionPreference = "Stop"
function Say  ($m){ Write-Host "==> $m"  -ForegroundColor Blue }
function Ok   ($m){ Write-Host "  ✓ $m"  -ForegroundColor Green }
function Warn ($m){ Write-Host "  ! $m"  -ForegroundColor Yellow }
function Die  ($m){ Write-Host "  ✗ $m"  -ForegroundColor Red; exit 1 }

if (-not (Get-Command az -ErrorAction SilentlyContinue)) { Die "Azure CLI ('az') not found. Install: https://aka.ms/azcli" }
$Sub = az account show --query id -o tsv 2>$null
if (-not $Sub) { Die "Not logged in. Run 'az login' first." }
if (-not $Suffix) { $Suffix = (("{0}{1}" -f $env:USERNAME, (Get-Date -Format "yyMMdd")) -replace '[^a-z0-9]','').ToLower(); if ($Suffix.Length -gt 8){$Suffix=$Suffix.Substring(0,8)} }

$FoundryAccount = $env:FOUNDRY_ACCOUNT ?? "foundry-aa-$Suffix"
$SearchService  = $env:SEARCH_SERVICE  ?? "srch-aa-$Suffix"
$SearchSku      = $env:SEARCH_SKU      ?? "basic"
$StorageAccount = $env:STORAGE_ACCOUNT ?? "staa$Suffix"
$BlobContainer  = $env:BLOB_CONTAINER  ?? "earth-at-night-data"
$ProjectEndpoint = "https://$FoundryAccount.services.ai.azure.com/api/projects/$FoundryProject"
$FoundryEndpoint = "https://$FoundryAccount.services.ai.azure.com"
$SearchEndpoint  = "https://$SearchService.search.windows.net"

# name:format:version:sku:capacity  (empty version = let Azure pick the default)
$Models = @(
  "gpt-4o:OpenAI:2024-11-20:GlobalStandard:30",
  "gpt-4.1:OpenAI:2025-04-14:GlobalStandard:30",
  "gpt-4.1-mini:OpenAI:2025-04-14:GlobalStandard:30",
  "gpt-5-mini:OpenAI::GlobalStandard:30",
  "text-embedding-3-large:OpenAI:1:Standard:50"
)

Say "Subscription : $Sub";  Say "Location : $Location";  Say "Resource grp : $ResourceGroup"
Say "Foundry : $FoundryAccount (project $FoundryProject)";  Say "Search : $SearchService";  Say "Storage : $StorageAccount/$BlobContainer"
$ans = Read-Host "Proceed and create these resources? [y/N]"
if ($ans -notmatch '^[Yy]$') { Die "Aborted by user." }

foreach ($ns in "Microsoft.CognitiveServices","Microsoft.Search","Microsoft.Storage") { az provider register --namespace $ns 2>$null | Out-Null }

Say "Creating resource group"
az group create -n $ResourceGroup -l $Location -o none; Ok "Resource group $ResourceGroup"

Say "Creating Microsoft Foundry account"
az cognitiveservices account show -n $FoundryAccount -g $ResourceGroup -o none 2>$null
if ($LASTEXITCODE -ne 0) {
  az cognitiveservices account create -n $FoundryAccount -g $ResourceGroup -l $Location `
     --kind AIServices --sku S0 --custom-domain $FoundryAccount --assign-identity --yes -o none
}
Ok "Foundry account $FoundryAccount"
$FoundryId = az cognitiveservices account show -n $FoundryAccount -g $ResourceGroup --query id -o tsv

Say "Creating Foundry project '$FoundryProject'"
$projUrl = "https://management.azure.com$FoundryId/projects/$FoundryProject`?api-version=$ProjectsApiVersion"
$body = (@{ location=$Location; identity=@{type="SystemAssigned"}; properties=@{displayName=$FoundryProject; description="Accelerate Agentic AI demos"} } | ConvertTo-Json -Compress)
az rest --method put --url $projUrl --headers "Content-Type=application/json" --body $body -o none 2>$null
if ($LASTEXITCODE -eq 0) { Ok "Project $FoundryProject" } else {
  Warn "Project REST create failed (api-version $ProjectsApiVersion may be stale)."
  Warn "Create project '$FoundryProject' in the portal at $FoundryEndpoint and paste its endpoint into ..\.env"
}

Say "Deploying models"
foreach ($spec in $Models) {
  $p = $spec.Split(":"); $name=$p[0]; $fmt=$p[1]; $ver=$p[2]; $sku=$p[3]; $cap=$p[4]
  az cognitiveservices account deployment show -n $FoundryAccount -g $ResourceGroup --deployment-name $name -o none 2>$null
  if ($LASTEXITCODE -eq 0) { Ok "$name already deployed"; continue }
  $verArg = @(); if ($ver) { $verArg = @("--model-version", $ver) }
  az cognitiveservices account deployment create -n $FoundryAccount -g $ResourceGroup `
     --deployment-name $name --model-name $name --model-format $fmt @verArg `
     --sku-name $sku --sku-capacity $cap -o none 2>$null
  if ($LASTEXITCODE -eq 0) { Ok "Deployed $name ($sku, ${cap}k TPM)" }
  else { Warn "Could not deploy $name in $Location (quota/availability) — demos fall back to gpt-4o." }
}

Say "Creating Azure AI Search"
az extension add --name search --upgrade -y 2>$null | Out-Null
az search service show --name $SearchService -g $ResourceGroup -o none 2>$null
if ($LASTEXITCODE -ne 0) {
  az search service create --name $SearchService -g $ResourceGroup --sku $SearchSku --location $Location --identity-type SystemAssigned -o none
}
az search service update --name $SearchService -g $ResourceGroup --auth-options aadOrApiKey --aad-auth-failure-mode http403 -o none 2>$null
Ok "Search service $SearchService"
$SearchMi = az search service show --name $SearchService -g $ResourceGroup --query identity.principalId -o tsv 2>$null

Say "Creating storage + container"
az storage account show -n $StorageAccount -g $ResourceGroup -o none 2>$null
if ($LASTEXITCODE -ne 0) {
  az storage account create -n $StorageAccount -g $ResourceGroup -l $Location --sku Standard_LRS --kind StorageV2 --allow-blob-public-access false -o none
}
az storage container create --name $BlobContainer --account-name $StorageAccount --auth-mode login -o none 2>$null
Ok "Storage $StorageAccount / $BlobContainer"

Say "Assigning RBAC"
$UserOid   = az ad signed-in-user show --query id -o tsv 2>$null
$StorageId = az storage account show -n $StorageAccount -g $ResourceGroup --query id -o tsv
$SearchId  = az search service show --name $SearchService -g $ResourceGroup --query id -o tsv
function Assign($role,$oid,$scope,$ptype,$label){ if(-not $oid){return}; az role assignment create --role $role --assignee-object-id $oid --assignee-principal-type $ptype --scope $scope -o none 2>$null; if($LASTEXITCODE -eq 0){Ok "  $role -> $label"}else{Warn "  $role -> $label (exists or no perms)"} }
Assign "Cognitive Services User"        $UserOid $FoundryId "User" "you @ Foundry"
Assign "Cognitive Services OpenAI User" $UserOid $FoundryId "User" "you @ OpenAI"
Assign "Search Service Contributor"     $UserOid $SearchId  "User" "you @ Search(control)"
Assign "Search Index Data Contributor"  $UserOid $SearchId  "User" "you @ Search(data)"
Assign "Search Index Data Reader"       $UserOid $SearchId  "User" "you @ Search(read)"
Assign "Storage Blob Data Contributor"  $UserOid $StorageId "User" "you @ Storage"
Assign "Storage Blob Data Reader"       $SearchMi $StorageId "ServicePrincipal" "SearchMI @ Storage"
Assign "Cognitive Services User"        $SearchMi $FoundryId "ServicePrincipal" "SearchMI @ Foundry"

Say "Writing ..\.env"
$envText = @"
# Auto-generated by infra/provision.ps1 on $((Get-Date).ToUniversalTime().ToString("s"))Z
PROJECT_ENDPOINT=$ProjectEndpoint
FOUNDRY_PROJECT_ENDPOINT=$ProjectEndpoint
AZURE_AI_PROJECT_ENDPOINT=$ProjectEndpoint
FOUNDRY_ACCOUNT_ENDPOINT=$FoundryEndpoint
MODEL_DEPLOYMENT_NAME=gpt-4o
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4o
FOUNDRY_MODEL_DEPLOYMENT_NAME=gpt-4o
PROMPT_AGENT_MODEL=gpt-5-mini
HOSTED_AGENT_MODEL=gpt-4.1
EMBEDDING_DEPLOYMENT=text-embedding-3-large
SEARCH_ENDPOINT=$SearchEndpoint
AZURE_SEARCH_ENDPOINT=$SearchEndpoint
SEARCH_INDEX_NAME=earth-at-night
KNOWLEDGE_SOURCE_NAME=earth-at-night-ks
KNOWLEDGE_BASE_NAME=earth-at-night-kb
STORAGE_ACCOUNT=$StorageAccount
BLOB_CONTAINER=$BlobContainer
A2A_PROJECT_CONNECTION_ID=
MCP_SERVER_URL=https://learn.microsoft.com/api/mcp
MCP_SERVER_LABEL=mslearn
"@
Set-Content -Path (Join-Path $PSScriptRoot "..\.env") -Value $envText -Encoding utf8
Ok ".env written"
Ok "Provisioning complete."
Say "Next: cd ..; python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt"
