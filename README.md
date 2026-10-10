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

## Ampliación del entrenamiento con fotografías reales

El ZIP original de Teachable Machine contiene la arquitectura y pesos, **no las fotografías de entrenamiento**. Por ello no se puede reentrenar responsablemente solo con ese ZIP. Se agregaron herramientas para auditar imágenes y entrenar una nueva versión sin sobrescribir el modelo existente.

Estructura esperada:

```text
dataset/
  train/
    deslizamiento_de_tierra/  huayco/  inundacion/  normal/  sequia/
  val/
    deslizamiento_de_tierra/  huayco/  inundacion/  normal/  sequia/
  test/
    deslizamiento_de_tierra/  huayco/  inundacion/  normal/  sequia/
```

Coloca fotografías originales en cada carpeta; conserva **imágenes del mismo evento, lugar, vídeo o ráfaga en un solo subconjunto** para evitar fuga de información. No uses copias, fotogramas contiguos ni imágenes generadas artificialmente como pruebas independientes. Comprueba derechos de uso y elimina metadatos personales cuando corresponda.

```bash
pip install Pillow
python scripts/audit_training_dataset.py --data dataset/train --output data/audit_train.json
python scripts/audit_training_dataset.py --data dataset/val --output data/audit_val.json
python scripts/audit_training_dataset.py --data dataset/test --output data/audit_test.json
pip install -r requirements-ai.txt
python scripts/train_disaster_classifier.py --data dataset --output data/trained_model
```

El entrenamiento utiliza MobileNetV2 preentrenado y aumentos **solo en entrenamiento**, guarda `model.keras` y evalúa el conjunto de prueba independiente. La evaluación debe complementarse con matriz de confusión, revisión de falsos positivos y validación de escenarios locales antes de generar alertas. La nueva versión no sustituye automáticamente al modelo original ni está activada en Railway hasta ser validada.

## Puente local para cámaras IP en Railway

Railway no puede acceder directamente a direcciones LAN `192.168.x.x`. Desde un PC Windows **en la misma Wi-Fi que el teléfono**, el agente `scripts/camera_bridge.py` lee el MJPEG local y envía JPEGs hacia Railway por HTTPS autenticado. El dashboard muestra los últimos fotogramas recientes cada ~3 segundos, **no una transmisión de video continua ni inferencia IA**.

1. Registra la cámara en NEXUS y copia su ID (desde la respuesta API `GET /api/cameras` o la interfaz de documentación `/docs`, autenticada).
2. En PowerShell en la carpeta del proyecto, instala `pip install opencv-python-headless`.
3. Define `$env:NEXUS_API_KEY = 'TU_CLAVE'` únicamente en tu terminal local; nunca subas la clave a GitHub.
4. Ejecuta:
```powershell
python scripts/camera_bridge.py --camera-url "http://192.168.0.16:8080/video" --camera-id "ID-DE-TU-CAMARA" --server "https://nexus-production-6562.up.railway.app" --fps 2
```
5. Mantén el PC encendido y el agente ejecutándose. Repite el agente por cámara con su ID correspondiente. El servidor rechaza JPEGs corruptos o mayores de 2 MB y no publica las imágenes sin la API Key.

La ruta `POST /api/cameras/{id}/frame` recibe JPEGs, `GET /api/cameras/{id}/frame` muestra solo imágenes recientes (menos de 15 s). Este puente es de **captura visual**: la inferencia del modelo entrenado y el procesamiento continuo de eventos siguen pendientes. Para producción conviene una credencial exclusiva de ingestión por cámara y límites de tasa.

### Instalación automática del puente en Windows

Con el repositorio abierto en VS Code, ejecuta en PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install_camera_bridge.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\start_camera_bridge.ps1
```

El instalador crea `.venv-bridge` e instala OpenCV de forma aislada. El iniciador solicita la API Key sin guardarla en archivos, consulta cámaras registradas y permite seleccionar el ID sin copiarlo manualmente. Python 3.10+ debe estar previamente instalado; si falta, el script explica cómo instalarlo. El PC y el teléfono deben compartir Wi-Fi, y el PC debe permanecer encendido mientras se envían imágenes.

### Transmisión desde Chrome sin instalar aplicaciones

1. Abre NEXUS mediante HTTPS, introduce la API Key y pulsa **Conectar**.
2. Registra una cámara en el dashboard (la dirección IP se conserva como referencia de fuente).
3. En la tarjeta correspondiente pulsa **Iniciar transmisión** y acepta el permiso de cámara del navegador.
4. La imagen aparece en vivo en tu navegador y se envían fotogramas JPEG autenticados al servidor aproximadamente cada 1.5 segundos. Otros navegadores autenticados pueden consultar los fotogramas recientes.
5. Pulsa **Detener transmisión** para liberar la cámara. Si cierras la pestaña o el dispositivo entra en suspensión, el envío se detiene.

**Limitaciones:** getUserMedia solo accede a cámaras disponibles para el navegador (webcam integrada, USB, o cámara virtual previamente instalada). No abre automáticamente un stream HTTP MJPEG privado `192.168.x.x` desde un sitio HTTPS; para esa cámara se necesita el puente LAN seguro. Los fotogramas enviados no son video continuo ni activan el modelo de IA. Evita transmitir personas sin su consentimiento. No compartas la API Key.
