# NEXUS RISK AI - IP Webcam local bridge launcher
param(
  [string]$CameraUrl = "",
  [string]$Server = "http://127.0.0.1:8000"
)
$ErrorActionPreference = 'Stop'
Set-Location (Resolve-Path (Join-Path $PSScriptRoot '..'))
$python = Join-Path (Get-Location) '.venv-bridge\Scripts\python.exe'
if (-not (Test-Path $python)) { throw "Ejecuta scripts\install_camera_bridge.ps1 primero." }
$uri = [Uri]$Server
$localServer = ($uri.Host -in @('localhost', '127.0.0.1', '::1'))
if (-not $localServer -and $uri.Scheme -ne 'https') { throw "Servidor remoto requiere HTTPS." }
if (-not $localServer -and -not $env:NEXUS_API_KEY) {
  $secret = Read-Host "API Key del servidor remoto" -AsSecureString
  $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
  try { $env:NEXUS_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
  finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}
if (-not $localServer -and -not $env:NEXUS_API_KEY) { throw "Servidor remoto requiere autenticacion." }
$headers = @{}
if (-not $localServer) { $headers['X-API-Key'] = $env:NEXUS_API_KEY }
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
$override = Read-Host "URL actual de IP Webcam (Enter para $CameraUrl)"
if (-not [string]::IsNullOrWhiteSpace($override)) { $CameraUrl = $override.Trim() }
$cameraUri = [Uri]$CameraUrl
if ($cameraUri.Scheme -notin @('http', 'https', 'rtsp')) { throw "URL de camara invalida." }
$port = $cameraUri.Port
Write-Host "Probando $($cameraUri.Host):$port ..."
$test = Test-NetConnection -ComputerName $cameraUri.Host -Port $port -WarningAction SilentlyContinue
if (-not $test.TcpTestSucceeded) { Write-Warning "Puerto inaccesible: revisa IP Webcam, Wi-Fi, puerto y aislamiento AP." }
Write-Host "Iniciando puente OpenCV para $($camera.name) ..."
if ($localServer) { Remove-Item Env:NEXUS_API_KEY -ErrorAction SilentlyContinue }
& $python scripts/camera_bridge.py --camera-url $CameraUrl --camera-id $camera.id --server $Server --fps 2
exit $LASTEXITCODE
