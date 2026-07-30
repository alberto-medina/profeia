Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$distRoot = Join-Path $projectRoot "dist"
$packageName = "ProfeIA-Demo"
$packageDir = Join-Path $distRoot $packageName
$zipPath = Join-Path $distRoot "$packageName.zip"

$resolvedProject = (Resolve-Path $projectRoot).Path

function Assert-InProject {
    param([string] $Path)
    $fullPath = [System.IO.Path]::GetFullPath($Path)
    if (-not $fullPath.StartsWith($resolvedProject, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Ruta fuera del proyecto: $fullPath"
    }
}

Assert-InProject $distRoot
Assert-InProject $packageDir
Assert-InProject $zipPath

if (Test-Path $packageDir) {
    Remove-Item -LiteralPath $packageDir -Recurse -Force
}
if (Test-Path $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}
New-Item -ItemType Directory -Force -Path $packageDir | Out-Null

New-Item -ItemType Directory -Force -Path (Join-Path $packageDir "backend") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $packageDir "frontend") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $packageDir "assets") | Out-Null

Copy-Item -LiteralPath (Join-Path $projectRoot "README.md") -Destination $packageDir -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "backend\app") -Destination (Join-Path $packageDir "backend") -Recurse -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "backend\requirements.txt") -Destination (Join-Path $packageDir "backend") -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "backend\.env.example") -Destination (Join-Path $packageDir "backend\.env.example") -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "frontend\main.py") -Destination (Join-Path $packageDir "frontend") -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "frontend\profeia.kv") -Destination (Join-Path $packageDir "frontend") -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "frontend\requirements.txt") -Destination (Join-Path $packageDir "frontend") -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "frontend\screens") -Destination (Join-Path $packageDir "frontend") -Recurse -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "frontend\utils") -Destination (Join-Path $packageDir "frontend") -Recurse -Force
Copy-Item -LiteralPath (Join-Path $projectRoot "frontend\widgets") -Destination (Join-Path $packageDir "frontend") -Recurse -Force

if (Test-Path (Join-Path $projectRoot "assets\icons")) {
    Copy-Item -LiteralPath (Join-Path $projectRoot "assets\icons") -Destination (Join-Path $packageDir "assets") -Recurse -Force
}
if (Test-Path (Join-Path $projectRoot "assets\images")) {
    Copy-Item -LiteralPath (Join-Path $projectRoot "assets\images") -Destination (Join-Path $packageDir "assets") -Recurse -Force
}

@'
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Creando entorno backend..."
Set-Location (Join-Path $root "backend")
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\pip.exe" install -r requirements.txt

Write-Host "Creando entorno frontend..."
Set-Location (Join-Path $root "frontend")
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\pip.exe" install -r requirements.txt

Write-Host ""
Write-Host "Dependencias instaladas. Ahora ejecuta: .\iniciar_demo.ps1"
'@ | Set-Content -LiteralPath (Join-Path $packageDir "instalar_dependencias.ps1") -Encoding ASCII

@'
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:KIVY_HOME = Join-Path $root ".kivy"

$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"

if (-not (Test-Path (Join-Path $backendDir ".venv\Scripts\python.exe"))) {
    throw "Falta instalar dependencias. Ejecuta primero: .\instalar_dependencias.ps1"
}
if (-not (Test-Path (Join-Path $frontendDir ".venv\Scripts\python.exe"))) {
    throw "Falta instalar dependencias. Ejecuta primero: .\instalar_dependencias.ps1"
}

Start-Process powershell -WindowStyle Normal -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command",
    "cd `"$backendDir`"; .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001"
)

Start-Sleep -Seconds 3

Start-Process powershell -WindowStyle Normal -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-Command",
    "cd `"$frontendDir`"; .\.venv\Scripts\python.exe main.py"
)
'@ | Set-Content -LiteralPath (Join-Path $packageDir "iniciar_demo.ps1") -Encoding ASCII

@'
# ProfeIA Demo para Windows

Requisitos:
- Windows 10/11
- Python 3.11 instalado y marcado en PATH
- Internet solo para instalar dependencias la primera vez

Como probar:

1. Descomprimir `ProfeIA-Demo.zip`.
2. Abrir PowerShell dentro de la carpeta descomprimida.
3. Ejecutar:

```powershell
powershell -ExecutionPolicy Bypass -File .\instalar_dependencias.ps1
powershell -ExecutionPolicy Bypass -File .\iniciar_demo.ps1
```

El demo abre dos ventanas:
- backend FastAPI en `http://127.0.0.1:8001`
- app ProfeIA Kivy

Notas:
- Es un demo local, sin IA paga obligatoria.
- No incluye `.env` privado ni claves.
- Los archivos generados quedan dentro de `backend\generated`.
- Para cerrar, cerrar la app y presionar `CTRL+C` en la ventana del backend.
'@ | Set-Content -LiteralPath (Join-Path $packageDir "LEEME_DEMO.md") -Encoding UTF8

Get-ChildItem -Path $packageDir -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Path $packageDir -Recurse -Include "*.pyc", "*.pyo" | Remove-Item -Force

Compress-Archive -LiteralPath $packageDir -DestinationPath $zipPath -Force

Write-Host "Demo generado:"
Write-Host $zipPath
