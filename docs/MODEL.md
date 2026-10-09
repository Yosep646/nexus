# Integración del modelo Teachable Machine

El modelo adjuntado se exportó en formato TensorFlow.js (`model.json`, `weights.bin`, `metadata.json`). **No se puede cargar directamente con tf.keras.models.load_model**.

## Conversión local

1. Extrae el ZIP de Teachable Machine en `models/teachable_machine/`.
2. Instala TensorFlow y tensorflowjs en un entorno compatible con las versiones del exportador.
3. Convierte el modelo de capas TFJS a un modelo Keras mediante el conversor compatible con tu versión de TensorFlow.js. Comprueba la compatibilidad del conversor antes de usarlo; algunos formatos requieren volver a exportar desde Teachable Machine en Keras.
4. Guarda el resultado como `models/teachable_machine/model.keras` y conserva `metadata.json`.
5. Ejecuta `GET /api/model/status` para comprobar disponibilidad.

**Importante:** hasta instalar un modelo Keras compatible, el sistema informa `model_unavailable` y no inventa detecciones. Verifica la normalización del modelo exportado y realiza pruebas con imágenes independientes antes de habilitar alertas.

Para producción, ejecutar inferencias periódicas con un planificador por cámara y limitar conexiones simultáneas. El endpoint de esta fase hace una clasificación puntual a petición del usuario.
