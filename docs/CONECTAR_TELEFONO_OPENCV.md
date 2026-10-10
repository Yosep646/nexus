# NEXUS RISK AI — conexión real de teléfono a laptop (LAN)

## Preparación en Windows
1. Conecta el teléfono y la laptop a la **misma red Wi-Fi**. Desactiva aislamiento de clientes/AP isolation en el router si existe.
2. En Android, inicia una aplicación de cámara IP que emita **HTTP/MJPEG** o RTSP y copia su URL exacta. Ejemplo ilustrativo: `http://192.168.1.20:8080/video` (no es una IP detectada).
3. En el navegador de la laptop abre la URL HTTP/MJPEG y confirma que la cámara transmite. En RTSP utiliza VLC para comprobar el enlace.
4. Abre PowerShell en la raíz del proyecto y ejecuta:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:NEXUS_LAN_MODE = "true"
$env:NEXUS_MONITOR_ENABLED = "true"
$env:NEXUS_API_KEY = "CAMBIA_ESTA_CLAVE_POR_UNA_LARGA_Y_PRIVADA"
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

5. En la **misma laptop**, abre `http://127.0.0.1:8000/dashboard/demo.html`. Introduce la clave definida en `NEXUS_API_KEY`, pulsa **Conectar** y registra la URL real de la cámara. El backend LAN comprueba la conectividad mediante OpenCV antes de registrarla.
6. La cuadrícula mostrará los fotogramas obtenidos por Python. **Analizar IA** invoca el modelo configurado. Para análisis periódico, el monitor requiere `NEXUS_MONITOR_ENABLED=true` y un modelo instalado y listo.
7. Si la transmisión no funciona: comprueba URL/puerto, credenciales, firewall, Wi-Fi, permisos de cámara y si el teléfono ha suspendido la aplicación. Prueba la URL en VLC o navegador antes de diagnosticar OpenCV.

## Verificación independiente de OpenCV
```powershell
python -c "import cv2; u=input('URL de cámara: '); c=cv2.VideoCapture(u); print('abierta:',c.isOpened()); ok,f=c.read(); print('fotograma:',ok, f.shape if ok else None); c.release()"
```

**Seguridad:** no publiques en Internet la cámara, el puerto del backend ni su API Key. Evita incluir usuario/contraseña en capturas de pantalla, logs o commits. Usa solo cámaras propias o autorizadas. En LAN, inicia el servidor en loopback para el navegador de la laptop; no necesitas exponer el puerto 8000.

**Limitaciones verificables:** la transmisión depende de que la aplicación del teléfono realmente ofrezca MJPEG/RTSP y de que OpenCV/FFmpeg admita el códec. No se ha realizado todavía una prueba con tu teléfono físico. Railway sigue siendo un entorno remoto distinto de tu red local.
