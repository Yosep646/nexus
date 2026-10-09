# Persistencia SQLite

El backend crea `data/nexus.db` al iniciarse (o la ruta definida en `NEXUS_DB_PATH`).

Tablas:
- `cameras`: ID, nombre, URL de red local, estado, fecha.
- `detections`: ID, cámara, clase, confianza y fecha UTC.

Endpoints: `GET /api/detections?limit=100`, `GET /api/stats`.
Las detecciones solo se registran cuando hay un modelo cargado y se ejecuta una clasificación explícita. No hay monitoreo continuo ni alertas automáticas todavía.
No publiques el archivo SQLite ni las URLs de cámaras en un hosting público. No expongas el backend sin autenticación y controles SSRF.
