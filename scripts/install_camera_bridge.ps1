# NEXUS RISK AI - Instalador local del puente de cámaras (Windows)
# Ejecutar desde la carpeta del repositorio: powershell -ExecutionPolicy Bypass -File .\scripts\install_camera_bridge.ps1
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..'))
Write-Host "NEXUS RISK AI | Instalacion de puente de camara" -ForegroundColor Cyan
$python = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 -c "import sys; assert sys.version_info >= (3, 10)" 2>$null
    if ($LASTEXITCODE -eq 0) { $python = @('py', '-3') }
}
if (-not $python -and (Get-Command python -ErrorAction SilentlyContinue)) {
    & python -c "import sys; assert sys.version_info >= (3, 10)" 2>$null
    if ($LASTEXITCODE -eq 0) { $python = @('python') }
}
if (-not $python) {
    Write-Host "Necesitas Python 3.10 o superior. Instala desde https://www.python.org/downloads/windows/ marcando Add Python to PATH." -ForegroundColor Yellow
    exit 1
}
$venv = Join-Path (Get-Location) '.venv-bridge'
if (-not (Test-Path $venv)) {
    if ($python.Count -eq 2) { & py -3 -m venv $venv }
    else { & python -m venv $venv }
    if ($LASTEXITCODE -ne 0) { throw "No se pudo crear el entorno virtual" }
}
$exe = Join-Path $venv 'Scripts\python.exe'
& $exe -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Error al actualizar pip" }
& $exe -m pip install "opencv-python-headless>=4.10,<5"
if ($LASTEXITCODE -ne 0) { throw "Error al instalar OpenCV" }
& $exe -c "import cv2; print('OpenCV listo:', cv2.__version__)"
if ($LASTEXITCODE -ne 0) { throw "OpenCV no funciona" }
Write-Host ""
Write-Host "Instalacion completa. Ejecuta scripts\start_camera_bridge.ps1 para conectar tu camara." -ForegroundColor Green
