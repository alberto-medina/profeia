param(
    [Parameter(Mandatory = $true)]
    [string] $ApiUrl
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $projectRoot "frontend\api_config.json"

$url = $ApiUrl.Trim().TrimEnd("/")
if (-not ($url.StartsWith("http://") -or $url.StartsWith("https://"))) {
    throw "La URL debe empezar con http:// o https://"
}

$json = @{
    api_url = $url
} | ConvertTo-Json -Depth 2

Set-Content -LiteralPath $configPath -Value $json -Encoding UTF8
Write-Host "URL de API configurada para Android/demo:"
Write-Host $url
