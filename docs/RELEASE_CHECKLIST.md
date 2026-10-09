# NEXUS RISK AI — Puesta en marcha segura

Estado: implementación en rama de trabajo; **no equivale a producción verificada**.

## Preparación
1. Proveer imágenes etiquetadas con derechos de uso y ejecutar validación, entrenamiento y evaluación independientes.
2. Instalar `models/teachable_machine/model.keras` y `metadata.json` validados.
3. Generar una clave aleatoria de 32 bytes o más y asignarla a `NEXUS_API_KEY` en el entorno privado. Nunca subirla a GitHub ni escribirla en GitHub Pages.
4. Usar una red privada o VPN para cámaras; restringir el acceso a URLs IP autorizadas. No exponer RTSP a Internet.
5. Ejecutar `python -m pytest -q` y revisar resultados antes de habilitar el monitor.

## Docker
- Demo sin modelo: `docker compose up --build -d` (API en 127.0.0.1:8000).
- Para inferencia, usar imagen compilada desde `Dockerfile.ml` y los pesos validados; reservar RAM y CPU suficientes.
- `NEXUS_MONITOR_ENABLED=true` habilita el procesamiento periódico **solo después** de verificar el modelo y la conectividad de cámaras.
- SQLite y JPEG se conservan en el volumen `nexus_data`. Configurar copias de seguridad externas.

## API privada
- `GET /health` indica vida del proceso, no garantiza inferencia.
- `GET /api/readiness` informa disponibilidad de DB/modelo; exige `X-API-Key`.
- `GET /api/detections`, `GET /api/stats`, `GET /api/audit` muestran eventos.
- `GET /api/detections/{id}/evidence` lista metadatos.
- `GET /api/detections/{id}/evidence/{evidence_id}/image` descarga JPEG verificado.
- `GET /api/reports/detections.pdf` descarga informe PDF.

## Mantenimiento
- Copia consistente: `python -m backend.database.maintenance --backup /backups/nexus.db`
- Simular depuración de evidencias antiguas: `python -m backend.database.maintenance --prune-days 90`
- Aplicar depuración: `python -m backend.database.maintenance --prune-days 90 --apply`
- La depuración no elimina detecciones ni auditorías. Antes de activarla, definir política legal y operativa de retención.

## Bloqueos conocidos
- No se han proporcionado pesos entrenados ni pruebas de rendimiento/precisión reales.
- No se ha confirmado la ejecución de GitHub Actions, el despliegue de Docker ni la conectividad de cámaras.
- La consola operativa requiere un origen privado de confianza; no colocar claves API en la web pública.
- El monitor es por sondeo; no incluye todavía detección de duplicados, reconexión avanzada, colas distribuidas ni notificaciones externas.
- Se requiere HTTPS, control de usuarios y sesiones, gestión de secretos y supervisión antes de exponer el servicio a terceros.
