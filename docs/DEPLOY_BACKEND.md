# Backend local seguro (MVP)

La API corre **solo en localhost** mediante Docker Compose; GitHub Pages no ejecuta el backend.

1. Instalar Docker Desktop.
2. Definir una clave aleatoria larga en el entorno: `NEXUS_API_KEY` (mínimo 24 caracteres). No subir la clave a Git.
3. Ejecutar `docker compose up --build -d`.
4. Comprobar `http://127.0.0.1:8000/health`.
5. Para llamadas privadas enviar `X-API-Key` con el secreto.

El modelo `model.keras` solo se carga si está presente en `models/teachable_machine/` y si TensorFlow está instalado. La imagen Docker base no instala TensorFlow: requiere una variante de imagen específica y un modelo validado antes de habilitar inferencia.

Para conectar frontend y API en producción se requiere una capa de autenticación con sesión segura (cookie HttpOnly) y proxy HTTPS, además de proteger MJPEG. **No incluir la clave en JavaScript público ni en parámetros de URL.**

No usar Docker Compose para exponer puertos de cámaras IP a Internet. Este archivo no configura un servidor público.
