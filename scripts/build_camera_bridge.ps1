# Build NEXUS-Camara-IP.exe locally on Windows (PyInstaller cannot cross-compile).
$ErrorActionPreference = 'Stop'
$root = Resolve-Path (Join-Path $PSScriptRoot '..')
Set-Location $root
$python = Join-Path $root '.venv-bridge\Scripts\python.exe'
if (-not (Test-Path $python)) {
  & (Join-Path $PSScriptRoot 'install_camera_bridge.ps1')
}
if (-not (Test-Path $python)) { throw 'No se encontro Python del entorno .venv-bridge' }
& $python -m pip install --upgrade pyinstaller
if ($LASTEXITCODE -ne 0) { throw 'No se pudo instalar PyInstaller' }
& $python -m PyInstaller --noconfirm --clean --onefile --console --name NEXUS-Camara-IP --paths scripts --collect-all cv2 scripts/nexus_camera_ip.py
if ($LASTEXITCODE -ne 0) { throw 'Falló la compilación del ejecutable' }
Write-Host "Ejecutable creado: $root\dist\NEXUS-Camara-IP.exe" -ForegroundColor Green
