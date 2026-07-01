Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $projectRoot "frontend"
$env:KIVY_HOME = Join-Path $projectRoot ".kivy"

Set-Location $frontendDir
python main.py
