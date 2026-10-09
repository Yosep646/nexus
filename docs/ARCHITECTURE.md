# Arquitectura inicial — NEXUS RISK AI

## Módulos
- `frontend/`: panel web responsivo y registro de cámaras.
- `backend/api/`: API FastAPI.
- `backend/cameras/`: validación y registro de cámaras IP privadas.
- `backend/detection/`: integración pendiente del clasificador.
- `backend/database/`: persistencia SQLite pendiente.
- `models/teachable_machine/`: artefactos del modelo.
- `tests/`: pruebas automatizadas.

## Estado
Esta primera versión permite registrar y eliminar referencias a cámaras, pero **no transmite video, no realiza inferencias, no emite alertas y no guarda registros al reiniciar**. No debe utilizarse para decisiones de emergencia.

## Seguridad antes del despliegue
Implementar autenticación, autorización, CORS restringido, protección SSRF, aislamiento de red, límites de recursos y almacenamiento seguro. No exponer la API sin estas medidas.
