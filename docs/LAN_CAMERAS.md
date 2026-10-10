# NEXUS RISK AI — cámaras IP en la LAN

## Dos modos distintos

- **Railway (por defecto):** Railway NO puede acceder a direcciones privadas `192.168.x.x`. Para mostrar una cámara local en el dashboard de Railway, ejecuta el puente de Windows `NEXUS-Camara-IP.exe` en la misma red Wi-Fi que la cámara.
- **Backend Python en la LAN:** ejecuta NEXUS en una computadora conectada a la misma red que las cámaras y activa `NEXUS_LAN_MODE=true`. En este modo el propio backend abre cada cámara mediante OpenCV y publica MJPEG. La transmisión y la inferencia (si hay un modelo instalado) no necesitan internet; la instalación inicial de dependencias sí puede necesitarlo.

## Arranque local en Windows (PowerShell)

Con Python y dependencias instaladas en la computadora LAN:

```powershell
python -m pip install -r requirements.txt
$env:NEXUS_LAN_MODE="true"
$env:NEXUS_API_KEY="CAMBIA_POR_UNA_CLAVE_SEGURA"
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Abre `http://127.0.0.1:8000/dashboard/demo.html` **en esa misma computadora** y usa la API Key que configuraste. Si otras computadoras de la red necesitan acceder al dashboard, configura un proxy local con autenticación/TLS y reglas de firewall adecuadas; no expongas directamente el servicio ni sus credenciales.

## Primera cámara

1. Comprueba desde la PC que `http://192.168.0.16:8080/video` entrega fotogramas reales (no solo una página de estado).
2. Registra «Estación móvil» con esa URL desde el dashboard local. El backend intenta abrirla con OpenCV y leer un fotograma antes de aceptarla.
3. Verifica el estado en `GET /api/cameras/{id}/status` y la imagen en `GET /api/cameras/{id}/frame` usando la cabecera `X-API-Key`.
4. Registra las demás cámaras. Cada una tiene un hilo de captura independiente; la pérdida de una no debe detener las otras.

El dashboard de Railway sigue siendo independiente del backend LAN: no mezcles sus registros ni sus API Keys.

## Limitaciones pendientes de validar

- Probar físicamente una, luego cuatro cámaras y recuperación tras desconexión.
- Credenciales de cámaras protegidas: el registro actual **no admite credenciales embebidas en la URL**. No pongas contraseñas en direcciones URL ni en GitHub.
- Modelos IA: si `/api/model/status` devuelve `ready:false`, la detección real todavía no está habilitada.
- El mapa usa OpenStreetMap en línea; para operación totalmente desconectada se requieren mosaicos locales.
- Preparar instalador y dependencias offline para un despliegue sin internet.
