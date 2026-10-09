# Instalar el modelo entrenado
El archivo ZIP proporcionado contiene `model.json`, `weights.bin` y `metadata.json` (modelo TensorFlow.js).

1. Extrae los tres archivos del ZIP.
2. Copia los tres a `frontend/models/teachable_machine/`.
3. Ejecuta Live Server desde `frontend/index.html` (no abras con `file://`).
4. En la sección de prueba de IA selecciona una imagen y pulsa **Analizar imagen**.
5. Confirma que aparezcan probabilidades para las cinco etiquetas originales.

El modelo no se ha vuelto a entrenar. Se cargan los pesos existentes. El clasificador predice sobre imágenes completas, no delimita objetos. La predicción no sustituye una alerta validada.

**Estado:** el frontend puede cargar los artefactos cuando se copien al directorio indicado. Los archivos binarios aún no están publicados en el repositorio.
