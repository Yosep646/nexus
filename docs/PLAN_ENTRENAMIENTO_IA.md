# Entrenamiento verificable de NEXUS RISK AI

## Estado del repositorio
El detector actual carga `models/teachable_machine/model.keras` si existe, pero `requirements.txt` no instala TensorFlow. El modelo puede permanecer no disponible hasta instalar una versión de TensorFlow compatible y aportar pesos válidos. No se puede afirmar precisión sin dataset etiquetado y evaluación.

## Datos recomendados
Categorías actuales: deslizamiento de tierra, huayco, inundación, normal y sequía. Añade ejemplos de lluvia y otras clases **solo si el modelo y sus metadatos se reentrenan con esas etiquetas**.

Usa material de cámaras reales de distintas ubicaciones, horarios, distancias, estaciones, resoluciones y condiciones de iluminación. Incluye negativos difíciles: ríos normales, laderas estables, lluvia sin inundación, barro de obras y niebla. Evita recopilar imágenes privadas sin autorización.

**Meta inicial orientativa**, no requisito de exactitud: 500–1,000 imágenes diversas por clase, revisadas manualmente; la cantidad final depende de los errores observados. Divide por evento/cámara/ubicación (no fotogramas vecinos repartidos entre train y test), por ejemplo 70% entrenamiento, 15% validación y 15% prueba.

## Auditoría de imágenes
```powershell
python tools/audit_dataset.py dataset --output dataset_audit.json
```
Estructura: `dataset/huayco/*.jpg`, `dataset/inundacion/*.jpg`, `dataset/normal/*.jpg`, etc. La herramienta detecta archivos ilegibles, duplicados exactos y desbalance. No detecta duplicados visuales casi idénticos ni etiquetas incorrectas; revisarlos manualmente.

## Protocolo de evaluación
1. Congela un conjunto de prueba independiente por cámara, evento y ubicación.
2. Entrena un modelo base (p. ej., transferencia de aprendizaje MobileNetV2/EfficientNet), usando el preprocesamiento que corresponda a esa arquitectura.
3. Registra matriz de confusión, precisión, recall y F1 **por clase**, con especial atención a falsos negativos de huaycos e inundaciones.
4. Compara contra el modelo anterior en el mismo conjunto de prueba.
5. Ajusta umbrales de alertas en validación y confirma manualmente señales críticas.
6. Mide latencia por cámara, consumo de CPU/RAM, pérdida de fotogramas y reconexión de OpenCV.
7. Despliega el nuevo modelo solo si supera los criterios de aceptación establecidos.

**Seguridad operacional:** la clasificación visual no confirma desastres ni sustituye a especialistas o avisos oficiales. Nunca muestres como 'confirmado' un resultado de IA no verificado.

## Cámara del teléfono
Activa `NEXUS_LAN_MODE=true` en la laptop y registra la URL MJPEG/RTSP real del teléfono en la misma Wi-Fi. El backend OpenCV ya dispone de un trabajador por cámara. La prueba física con tu dispositivo aún está pendiente.
