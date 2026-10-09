# NEXUS RISK AI

Plataforma de monitoreo de cámaras IP y análisis de fenómenos naturales con FastAPI, SQLite y un dashboard web.

## Abrir el dashboard

- Sitio: https://nexus-production-6562.up.railway.app/
- El mapa y la geolocalización del teléfono se muestran en el navegador con autorización del usuario.
- Para consultar y administrar datos operativos, la API solicita una clave mediante el encabezado `X-API-Key`. La clave real se configura como variable privada `NEXUS_API_KEY` en Railway. **No guardes claves reales en este repositorio.**

## Estados del sistema

- **API conectada**: el backend responde y permite consultar datos autenticados.
- **Modelo de IA no disponible**: el backend funciona, pero la detección automática no se ejecuta sin los pesos del modelo.
- **Cámara registrada** no significa que el servidor pueda recibir vídeo. Las IP privadas de teléfonos no son accesibles directamente desde Railway por internet.

## Activar el modelo de inteligencia artificial

El detector busca el archivo `models/teachable_machine/model.keras`. Un archivo exportado de Teachable Machine como `model.json` **no es equivalente** a un modelo Keras; debe convertirse y validarse con el preprocesamiento y el orden de clases correctos.

1. Entrena y valida un clasificador con datos reales y etiquetas consistentes.
2. Exporta o convierte el modelo al formato Keras compatible y ubícalo en `models/teachable_machine/model.keras`.
3. Comprueba `models/teachable_machine/metadata.json` y sus etiquetas, si existe.
4. Añade una versión de TensorFlow compatible con el entorno Python de despliegue, teniendo en cuenta memoria y tamaño de la imagen Docker.
5. Ejecuta las pruebas y comprueba `GET /api/model/status` usando autenticación: `ready: true` confirma que se cargó el modelo, **no** que tenga precisión suficiente para alertas reales.
6. Activa el monitoreo periódico solo después de verificar las cámaras, el modelo y los recursos; utiliza `NEXUS_MONITOR_ENABLED=true` cuando corresponda.

Las probabilidades de clasificación no equivalen a pronósticos ni a confirmaciones de desastres. Requieren revisión humana.

## Desarrollo local

Instala las dependencias de `requirements.txt`, configura `NEXUS_API_KEY` con un secreto propio de al menos 24 caracteres, y ejecuta el servidor ASGI definido en `backend.main:app`. Para verificar el proyecto ejecuta `python -m pytest -q`.

## Seguridad y despliegue

No publiques contraseñas, API Keys, URLs privadas de cámaras ni evidencias sensibles. Usa HTTPS, control de acceso y almacenamiento persistente antes de utilizar NEXUS en producción.
