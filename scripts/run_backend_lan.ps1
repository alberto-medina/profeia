Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot "backend"

Set-Location $backendDir
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
