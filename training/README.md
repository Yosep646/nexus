# Entrenamiento de clasificación de fenómenos naturales

El entrenamiento necesita **imágenes reales, etiquetadas y autorizadas**. No se agregan fotografías de Internet sin comprobar derechos y procedencia.

Crear carpetas bajo `datasets/curated/` con exactamente cinco categorías (por ejemplo: `deslizamiento_de_tierra`, `huayco`, `inundacion`, `normal`, `sequia`). Agregar imágenes representativas de distintas cámaras, condiciones de luz, ubicaciones y temporadas.

```bash
pip install tensorflow pillow
python -m training.train --dataset datasets/curated --output models/teachable_machine
```

**Importante:** `training/train.py` entrena un modelo nuevo que incluye la normalización dentro del modelo. El detector backend debe leer `metadata.json` y aplicar el preprocesamiento correspondiente. Un modelo exportado de Teachable Machine puede requerir normalización externa. No intercambiar pesos entre ambas rutas sin validar.

Separar un conjunto de prueba independiente por cámara, lugar y fecha. Reportar matriz de confusión, precision, recall y F1 por clase. No afirmar 100 % de precisión.

El entrenamiento no corre en GitHub Pages. Los pesos pueden ser grandes y deben almacenarse fuera de Git si superan los límites del repositorio.
