# Entrenamiento RGB y verificación OpenCV — NEXUS

## 1. Obtener imágenes sin introducir etiquetas falsas
- FloodNet (https://github.com/BinaLab/FloodNet-Supervised_v1.0) contiene 2343 imágenes aéreas en total, **no 2343 ejemplos ya etiquetados de inundación**. Respeta sus divisiones originales y licencia CDLA Permissive. Descarga desde el enlace oficial; mapea máscaras y etiquetas antes de copiar imágenes al dataset RGB.
- Landslide4Sense (https://zenodo.org/records/10463239) usa **14 bandas** HDF5 de satélite y NO se debe copiar directamente como imágenes de teléfono. Requiere conversión y evaluación de dominio.
- Para `huayco`, `sequia`, `normal` y otros casos locales prioriza videos y fotos RGB verificadas de cámaras autorizadas. No extraigas imágenes arbitrarias de resultados de búsqueda sin licencia.
- El objetivo de 1000 por clase es orientativo, no una garantía. No dupliques imágenes ni inventes clases.

## 2. Organización
```
dataset/
  huayco/
    evento_001/fotograma_001.jpg
    evento_001/fotograma_002.jpg
    evento_002/...
  inundacion/
    evento_101/...
  deslizamiento de tierra/
    evento_201/...
  sequia/
    evento_301/...
  normal/
    camara_001_sesion_01/...
```
Cada carpeta de evento o sesión es un **grupo**; todos sus fotogramas se mantienen en un mismo split para evitar fuga de datos. No mezcles capturas consecutivas de la misma grabación en train y test. Revisa etiquetas manualmente.

## 3. Preparar y entrenar en tu laptop
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install tensorflow pillow
python tools/dataset_sources.py
python tools/audit_dataset.py dataset
python -m unittest discover -s tests -p test_training_split.py
python tools/train_camera_classifier.py --dataset dataset --epochs 12 --min-images-per-class 100
```
La primera ejecución puede descargar pesos preentrenados de MobileNetV2. Si necesitas operación sin internet, prepara los pesos y dependencias de antemano. TensorFlow en Windows puede requerir configuración específica de CPU/GPU. El script **no puede entrenar sin imágenes locales**.

## 4. Resultados y puesta en servicio
El entrenamiento guarda `models/teachable_machine/model.keras`, `metadata.json` y `evaluation.json`. Revisa matriz de confusión, precisión, recall y F1 por clase antes de habilitar alertas. Un resultado de IA no es una alerta de desastre confirmada.

Activa `NEXUS_LAN_MODE=true` y `NEXUS_MONITOR_ENABLED=true` en el backend local; usa la IP MJPEG/RTSP real del teléfono en la misma Wi-Fi. El detector carga el archivo .keras al iniciar el proceso, por lo que **reinicia el backend** después de entrenar.

## 5. Datos grandes y GitHub
No subas las imágenes ni pesos de gigabytes al repositorio Git normal. Mantén `dataset/` y archivos pesados fuera de Git o utiliza almacenamiento de objetos con acceso autorizado. Registra procedencia, licencia, fecha, ubicación aproximada y partición de cada muestra.

## 6. Pruebas que faltan
- Verificar que el modelo exportado carga con la versión de TensorFlow de la laptop.
- Verificar latencia y FPS de cada cámara OpenCV en Wi-Fi.
- Probar reconexión y errores de IP/puerto.
- Evaluar con escenas nuevas de Huánuco y falsos positivos de barro, agua y laderas estables.
