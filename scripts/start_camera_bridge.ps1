# NEXUS RISK AI - IP Webcam local bridge launcher
param(
  [string]$CameraUrl = "",
  [string]$Server = "https://nexus-production-6562.up.railway.app"
)
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..'))
$python = Join-Path (Get-Location) '.venv-bridge\Scripts\python.exe'
if (-not (Test-Path $python)) {
  Write-Host "Instalando OpenCV local automaticamente..." -ForegroundColor Cyan
  & (Join-Path $PSScriptRoot "install_camera_bridge.ps1")
  if (-not (Test-Path $python)) { throw "No se pudo instalar OpenCV. Ejecuta install_camera_bridge.ps1." }
}
$uri = [Uri]$Server
$localServer = ($uri.Host -in @('localhost', '127.0.0.1', '::1'))
if (-not $localServer -and $uri.Scheme -ne 'https') { throw "Servidor remoto requiere HTTPS." }
$headers = @{}
$cameras = @(Invoke-RestMethod -Uri "$Server/api/cameras" -Headers $headers -TimeoutSec 20)
if ($cameras.Count -eq 0) { throw "Registra una camara en el dashboard primero." }
for ($i = 0; $i -lt $cameras.Count; $i++) {
  Write-Host "[$i] $($cameras[$i].name) | $($cameras[$i].id)"
}
$selection = Read-Host "Numero de camara (Enter para 0)"
if ([string]::IsNullOrWhiteSpace($selection)) { $selection = "0" }
$index = 0
if (-not [int]::TryParse($selection, [ref]$index) -or $index -lt 0 -or $index -ge $cameras.Count) { throw "Seleccion invalida." }
$camera = $cameras[$index]
if (-not $CameraUrl) { $CameraUrl = $camera.url }
if ([string]::IsNullOrWhiteSpace($CameraUrl)) {
  $CameraUrl = Read-Host "Introduce URL de la camara seleccionada (ej. http://IP:PUERTO/video)"
} else {
  $override = Read-Host "URL actual de esta camara (Enter para usar la registrada)"
  if (-not [string]::IsNullOrWhiteSpace($override)) { $CameraUrl = $override.Trim() }
}
if ([string]::IsNullOrWhiteSpace($CameraUrl)) { throw "No se especifico URL para la camara seleccionada." }
$cameraUri = $null
if (-not [Uri]::TryCreate($CameraUrl, [UriKind]::Absolute, [ref]$cameraUri)) {
  throw "URL invalida. Indica la direccion de esta camara, incluyendo protocolo y puerto."
}
if ($cameraUri.AbsolutePath -eq '/') {
  $CameraUrl = $CameraUrl.TrimEnd('/') + '/video'
  $cameraUri = [Uri]$CameraUrl
}
Write-Host "Camara seleccionada: $($camera.name) | ID: $($camera.id)" -ForegroundColor Cyan
Write-Host "Destino LAN: $($cameraUri.Host):$($cameraUri.Port)$($cameraUri.AbsolutePath)" -ForegroundColor Cyan
try {
  $probe = Invoke-WebRequest -Uri $cameraUri.GetLeftPart([System.UriPartial]::Authority) -UseBasicParsing -TimeoutSec 5
  Write-Host "Servidor HTTP IP Webcam responde: $($probe.StatusCode)" -ForegroundColor Green
} catch {
  Write-Warning "No se pudo abrir la página IP Webcam: $($_.Exception.Message)"
}
if ($cameraUri.Scheme -notin @('http', 'https', 'rtsp')) { throw "URL de camara invalida." }
$port = $cameraUri.Port
Write-Host "Probando $($cameraUri.Host):$port ..."
$test = Test-NetConnection -ComputerName $cameraUri.Host -Port $port -WarningAction SilentlyContinue
if (-not $test.TcpTestSucceeded) {
  Write-Warning "SIN ACCESO AL TELEFONO: IP Webcam debe mostrar Start server activo. Verifica IP, puerto, Wi-Fi y aislamiento AP."
  Write-Host "No es un error de Railway: OpenCV no puede acceder al telefono desde esta laptop." -ForegroundColor Yellow
} else {
  Write-Host "Telefono accesible por TCP. Iniciando OpenCV..." -ForegroundColor Green
}
Write-Host "Iniciando puente OpenCV para $($camera.name) ..."

& $python scripts/camera_bridge.py --camera-url $CameraUrl --camera-id $camera.id --server $Server --fps 2
exit $LASTEXITCODE
