# Seguridad del backend NEXUS

Para usar la API, define `NEXUS_API_KEY` con una clave aleatoria de al menos 24 caracteres. Enviar en el encabezado `X-API-Key`. Si falta la clave, la API devuelve 503 y no permite usar rutas protegidas.

No publiques la clave en GitHub Pages, frontend estático, repositorio ni capturas. **La autenticación mediante clave compartida es un paso inicial, no una solución multiusuario de producción.** Antes de exponer el backend fuera de una red privada, implementar identidad por usuario, roles, HTTPS, auditoría y protección de flujos MJPEG.

Los streams de cámaras IP deben permanecer en LAN/VPN. La API no debe exponerse directamente a Internet.

Ejemplo local:
```bash
export NEXUS_API_KEY='reemplazar-por-clave-aleatoria-de-al-menos-24-caracteres'
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
En Windows PowerShell usar `$env:NEXUS_API_KEY='...'`.
