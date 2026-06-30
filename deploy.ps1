<#
  Foundry Live Demo Console -> Azure Container Apps deployment.
  Works around the Windows az-CLI cp1252/colorama crash that aborted the
  Jun 28 attempts, pulls app settings from .env, and deploys the current
  source (so today's UI fixes are included).
#>
$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

# --- Fix the 'charmap'/cp1252 UnicodeEncodeError that crashed prior deploys ---
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
try { $OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
cmd /c "chcp 65001" | Out-Null

$logPath    = Join-Path $PSScriptRoot "ui\deploy3.log"
$resultPath = Join-Path $PSScriptRoot "ui\deploy_result.txt"
Remove-Item $resultPath -ErrorAction SilentlyContinue
try { Start-Transcript -Path $logPath -Force | Out-Null } catch {}

$APP  = "foundry-demo-console"
$RG   = "rg-agentic-ai-demos"
$ENVN = "agentic-demos-env"
$LOC  = "australiaeast"

function Finish($msg) {
  $msg | Out-File -FilePath $resultPath -Encoding utf8
  Write-Host ""
  Write-Host "RESULT: $msg"
  try { Stop-Transcript | Out-Null } catch {}
}

Write-Host "=== [1/4] Verifying az login ==="
az config set extension.use_dynamic_install=yes_without_prompt --only-show-errors 2>$null | Out-Null
$acctJson = az account show -o json 2>$null
if (-not $acctJson) { Finish "NOT_LOGGED_IN - run 'az login' in this window, then re-run deploy.bat"; exit 1 }
$acct = $acctJson | ConvertFrom-Json
Write-Host ("Subscription: {0} ({1})" -f $acct.name, $acct.id)

Write-Host "=== [2/4] Loading app settings from .env ==="
$envMap = @{}
$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $envFile) {
  Get-Content $envFile | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
      $parts = $line.Split("=", 2)
      $envMap[$parts[0].Trim()] = $parts[1].Trim().Trim('"')
    }
  }
}
$wanted = @(
  "PROJECT_ENDPOINT","FOUNDRY_ACCOUNT_ENDPOINT","SEARCH_ENDPOINT",
  "ENV_SUBSCRIPTION_NAME","ENV_REGION","ENV_RESOURCE_GROUP","FOUNDRY_MODELS",
  "A2A_PROJECT_CONNECTION_ID","MODEL_DEPLOYMENT_NAME","PROMPT_AGENT_MODEL",
  "HOSTED_AGENT_MODEL","EMBEDDING_DEPLOYMENT","MCP_SERVER_URL","MCP_SERVER_LABEL",
  "STORAGE_ACCOUNT","BLOB_CONTAINER"
)
$envArgs = @()
foreach ($k in $wanted) { if ($envMap.ContainsKey($k) -and $envMap[$k]) { $envArgs += ("{0}={1}" -f $k, $envMap[$k]) } }
if (-not ($envArgs -match "^ENV_REGION="))         { $envArgs += "ENV_REGION=$LOC" }
if (-not ($envArgs -match "^ENV_RESOURCE_GROUP=")) { $envArgs += "ENV_RESOURCE_GROUP=$RG" }
if (-not ($envArgs -match "^ENV_SUBSCRIPTION_NAME=")) { $envArgs += ("ENV_SUBSCRIPTION_NAME={0}" -f $acct.name) }
Write-Host ("Passing {0} app settings (values hidden)." -f $envArgs.Count)

$ACR    = "ca56e9198667acr"
$IMG    = "$ACR.azurecr.io/foundry-demo-console:latest"

Write-Host "=== [3a/4] Building image in ACR (explicit :latest tag) ==="
Write-Host "Server-side ACR build; ~3-6 min."
# NOTE on the cp1252 crash: `az acr build` streams the build log through colorama,
# which on a non-UTF-8 Windows console re-encodes via cp1252 and throws
# UnicodeEncodeError. The az CLI runs its bundled Python in ISOLATED mode, so it
# IGNORES $env:PYTHONUTF8 / PYTHONIOENCODING -- only the live console code page
# (chcp 65001) matters, and that's absent in non-interactive runs. The KEY fact:
# the build runs server-side in ACR and finishes regardless of any local stream
# crash. So we fire the build, swallow any local crash, and POLL the run status
# via the control plane (plain JSON, no colorama) to learn the real outcome.
$buildLog = Join-Path $PSScriptRoot "ui\acr-build.log"
try { az acr build -r $ACR -t "foundry-demo-console:latest" -f Dockerfile . *> $buildLog } catch {}

Write-Host "Build queued; polling ACR run status (server-side build continues even if the local log stream crashed)..."
$runId = $null; $status = $null
for ($i = 0; $i -lt 60; $i++) {
  Start-Sleep -Seconds 15
  $runs = az acr task list-runs -r $ACR --top 5 -o json --only-show-errors 2>$null | ConvertFrom-Json
  # Newest manual run is our build (no task name on quick builds).
  $run = $runs | Where-Object { -not $_.task } | Select-Object -First 1
  if (-not $run) { $run = $runs | Select-Object -First 1 }
  $runId = $run.runId; $status = $run.status
  Write-Host ("  [{0}] run={1} status={2}" -f $i, $runId, $status)
  if ($status -and $status -notin @("Running","Queued","Started")) { break }
}
if ($status -ne "Succeeded") { Finish "BUILD_FAILED run=$runId status=$status - see ui\acr-build.log"; exit 1 }
Write-Host "Build $runId Succeeded."

Write-Host "=== [3b/4] Updating Container App image + app settings ==="
# Use a unique --revision-suffix every deploy. Without it, `update --image ...:latest`
# with unchanged env vars is a no-op (ACA won't make a new revision for an identical
# tag string), so a freshly-built :latest image would NOT roll out. The suffix forces
# a new revision, which re-resolves :latest to the just-built digest.
$suffix = "r" + (Get-Date -Format "MMddHHmmss")
az containerapp update `
  -n $APP -g $RG `
  --image $IMG `
  --revision-suffix $suffix `
  --set-env-vars $envArgs `
  --only-show-errors
$code = $LASTEXITCODE
if ($code -ne 0) { Finish "DEPLOY_FAILED exit=$code - see ui\deploy3.log"; exit $code }

# Ensure external ingress on port 8000 (idempotent).
az containerapp ingress enable -n $APP -g $RG --type external --target-port 8000 --transport auto --only-show-errors 2>$null | Out-Null

Write-Host "=== [4/4] Reading live URL ==="
$fqdn = az containerapp show -n $APP -g $RG --query "properties.configuration.ingress.fqdn" -o tsv --only-show-errors 2>$null
$rev  = az containerapp show -n $APP -g $RG --query "properties.latestReadyRevisionName" -o tsv --only-show-errors 2>$null
if ($fqdn) { Finish "SUCCESS https://$fqdn revision=$rev $(Get-Date -Format s)" }
else       { Finish "DEPLOY_DONE_BUT_NO_FQDN - check 'az containerapp show -n $APP -g $RG'" }
