# NEXUS RISK AI - Conectar cámara IP local a Railway.
param(
  [string]$CameraUrl = "",
  [string]$Server = "https://nexus-production-6562.up.railway.app"
)
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..'))
$python = Join-Path (Get-Location) '.venv-bridge\Scripts\python.exe'
if (-not (Test-Path $python)) { throw "Primero ejecuta scripts\install_camera_bridge.ps1" }
if (-not $env:NEXUS_API_KEY) {
  $secret = Read-Host "Introduce tu API Key de NEXUS (no se guardara en disco)" -AsSecureString
  $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
  try { $env:NEXUS_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
  finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}
if (-not $env:NEXUS_API_KEY) { throw "La API Key es obligatoria" }
$headers = @{ "X-API-Key" = $env:NEXUS_API_KEY }
$cameras = Invoke-RestMethod -Uri "$Server/api/cameras" -Headers $headers -TimeoutSec 20
if (-not $cameras -or $cameras.Count -eq 0) { throw "No hay camaras registradas. Registra tu camara en el dashboard primero." }
Write-Host "Camaras registradas:" -ForegroundColor Cyan
for ($i=0; $i -lt $cameras.Count; $i++) {
  Write-Host "[$i] $($cameras[$i].name) | $($cameras[$i].url) | $($cameras[$i].id)"
}
$selection = Read-Host "Numero de camara (Enter para 0)"
if ([string]::IsNullOrWhiteSpace($selection)) { $selection = "0" }
$index = 0
if (-not [int]::TryParse($selection, [ref]$index) -or $index -lt 0 -or $index -ge $cameras.Count) { throw "Seleccion invalida" }
$camera = $cameras[$index]
if (-not $CameraUrl) { $CameraUrl = $camera.url }
Write-Host "URL de camara configurada: $CameraUrl" -ForegroundColor Cyan
$override = Read-Host "URL IP Webcam actual (Enter para mantener la anterior)"
if (-not [string]::IsNullOrWhiteSpace($override)) { $CameraUrl = $override.Trim() }
try {
  $uri = [Uri]$CameraUrl
  if ($uri.Scheme -notin @('http','https','rtsp')) { throw "Protocolo no compatible" }
  Write-Host "Comprobando TCP $($uri.Host):$($uri.Port)..." -ForegroundColor Cyan
  $tcp = Test-NetConnection -ComputerName $uri.Host -Port $uri.Port -WarningAction SilentlyContinue
  if (-not $tcp.TcpTestSucceeded) {
    Write-Warning "No se puede conectar al puerto. Revisa Start server en IP Webcam, Wi-Fi y AP Isolation."
    $continue = Read-Host "Intentar OpenCV de todas formas? (s/N)"
    if ($continue -ne 's') { exit 2 }
  }
} catch { Write-Warning "Diagnostico TCP: $($_.Exception.Message)" }

Write-Host "Conectando $($camera.name) desde $CameraUrl a NEXUS. Manten esta ventana abierta." -ForegroundColor Green
& $python scripts/camera_bridge.py --camera-url $CameraUrl --camera-id $camera.id --server $Server --fps 2
