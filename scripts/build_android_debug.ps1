Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $projectRoot "frontend"

Set-Location $frontendDir
buildozer -v android debug

Write-Host ""
Write-Host "Si la compilacion termino OK, el APK queda en:"
Write-Host (Join-Path $frontendDir "bin")
