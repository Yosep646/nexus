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

## Instalación opcional de TensorFlow en Railway

La imagen Docker predeterminada mantiene la API ligera y operativa sin pesos entrenados. Para desplegar la inferencia, primero coloca un modelo Keras **entrenado y validado** en el volumen persistente de Railway (`/app/data/models/model.keras`) junto con su metadata compatible (`/app/data/models/metadata.json`). Después selecciona `Dockerfile.ai` como Dockerfile de Railway y configura las variables:

```text
NEXUS_MODEL_PATH=/app/data/models/model.keras
NEXUS_MODEL_METADATA_PATH=/app/data/models/metadata.json
NEXUS_DB_PATH=/app/data/nexus.db
NEXUS_EVIDENCE_DIR=/app/data/evidence
```

`Dockerfile.ai` instala TensorFlow CPU mediante `requirements-ai.txt`. No cambies a esa imagen sin verificar límites de memoria, compatibilidad del modelo y recursos del servicio. El modelo no se genera al instalar TensorFlow. Después del despliegue, comprueba `/api/model/status` con autenticación y valida inferencias sobre imágenes de prueba antes de habilitar `NEXUS_MONITOR_ENABLED=true`.

El volumen de Railway tiene un límite de 500 MB en el plan actual. Configura almacenamiento externo para evidencias grandes, políticas de retención y copias de seguridad. Montar un volumen nuevo en `/app/data` puede ocultar datos anteriores guardados dentro del contenedor; comprueba y migra los registros previos antes de asumir que se conservan.


## Estado actual de la integración del modelo

El formulario de importación manual del ZIP fue retirado del dashboard. El modelo TensorFlow.js original no está empaquetado en el contenedor de producción. Hasta integrar los pesos reales en el backend, el estado de inferencia se mantiene como **NO DISPONIBLE** y no se emiten detecciones ficticias. La configuración de acceso a la API sigue siendo obligatoria para operaciones protegidas.
