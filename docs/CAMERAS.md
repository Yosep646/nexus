# Cámaras IP en red local

1. Conecta teléfono y PC a la misma red Wi-Fi.
2. Inicia una aplicación que emita MJPEG o RTSP desde el teléfono.
3. Registra la URL local, por ejemplo `http://192.168.1.20:8080/video`.
4. Inicia el backend con `python -m uvicorn backend.main:app --reload`.
5. Abre `frontend/index.html` con Live Server y selecciona «Iniciar vista».

La API sirve `GET /api/cameras/{id}/stream` como MJPEG para transmisiones compatibles con OpenCV.

**Limitaciones de este prototipo:** sin autenticación, persistencia, TLS ni IA activa. Solo ejecutar en una red confiable; no abrir el puerto 8000 a internet. Las cámaras privadas no son accesibles desde GitHub Pages. Las URLs deben usar IP privada, pero aún falta endurecer la protección SSRF (redirecciones, rutas de red, DNS, validación de puertos y aislamiento del proceso).
