# Deletes the entire resource group (the slides' "Clean up resources" step).
param([string]$ResourceGroup = $env:RESOURCE_GROUP ?? "rg-agentic-ai-demos")
Write-Host "This will DELETE resource group '$ResourceGroup' and everything in it." -ForegroundColor Yellow
$confirm = Read-Host "Type the resource group name to confirm"
if ($confirm -ne $ResourceGroup) { Write-Host "Name mismatch — aborted." -ForegroundColor Red; exit 1 }
az group delete -n $ResourceGroup --yes --no-wait
Write-Host "  ✓ Deletion started (background)." -ForegroundColor Green
