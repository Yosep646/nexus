# Dashboard de demostración sin API

Abre `frontend/demo.html` con Live Server en VS Code o desde un servidor estático.
Esta interfaz funciona sin FastAPI ni cámaras IP.

Incluye:
- Panel adaptable a móviles, tarjetas y navegación.
- Cámaras ficticias que se pueden añadir y eliminar.
- Simulador de eventos etiquetados explícitamente como **simulados**.
- Contadores, historial y exportación CSV.
- Persistencia de datos de prueba en `localStorage`.
- Marcador de mapa sin geolocalización ni mapa real.

No hay inferencia, imágenes de cámaras, detecciones reales ni alertas operativas. La conexión con la API se realizará en otra fase. La interfaz técnica original sigue en `frontend/index.html`.
