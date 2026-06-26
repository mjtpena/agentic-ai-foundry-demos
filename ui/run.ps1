<#
  Launch the Foundry Live Demo Console (Windows / PowerShell).
    ./ui/run.ps1                # http://127.0.0.1:8099
  Requires: az login + a populated ../.env (run infra/provision.ps1 first).
#>
[CmdletBinding()]
param([int]$Port = 8099)
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
Write-Host "Foundry Live Demo Console -> http://127.0.0.1:$Port" -ForegroundColor Cyan
Push-Location $root
try { & $py -m uvicorn ui.server.main:app --host 127.0.0.1 --port $Port }
finally { Pop-Location }
