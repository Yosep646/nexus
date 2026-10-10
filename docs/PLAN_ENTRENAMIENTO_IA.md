# Plan de calidad de datos y entrenamiento — NEXUS RISK AI

## Diagnóstico actual
El repositorio carga opcionalmente `models/teachable_machine/model.keras` y metadatos de etiquetas. El `requirements.txt` base no incluye TensorFlow. Sin pesos compatibles, `detector.ready` es falso: no se debe mostrar que la IA está entrenada o lista. No se ha encontrado aquí un inventario verificado de imágenes de entrenamiento.

## Auditoría del dataset
Organiza las imágenes autorizadas por clase bajo `dataset/`, por ejemplo `dataset/huayco/`, `dataset/inundacion/`, `dataset/normal/`, `dataset/sequia/` y `dataset/deslizamiento de tierra/`. Ejecuta:
```powershell
python scripts/audit_dataset.py dataset --output dataset_audit.json
```
El reporte identifica recuentos, desequilibrio y duplicados exactos. No valida etiquetas ni imágenes casi idénticas; esas revisiones requieren inspección adicional. No subir fotografías sensibles ni datasets de varios GB directamente al repositorio Git.

## Recomendaciones para reentrenar
- Recopilar escenas reales autorizadas de cada fenómeno y escenas negativas difíciles (lluvia sin huayco, ríos normales, tierra removida por maquinaria, neblina, caminos húmedos).
- Variar cámara, hora, clima, distancia, ángulo, resolución, movimiento y condiciones nocturnas. No llenar el dataset con fotogramas casi idénticos del mismo video.
- Separar entrenamiento/validación/prueba por **evento, cámara y ubicación** antes de generar aumentos; nunca dividir fotogramas contiguos del mismo evento entre conjuntos.
- Revisar manualmente etiquetas ambiguas y mantener clases mutuamente interpretables. Un fotograma aislado no demuestra que ocurrirá un desastre.
- Usar transferencia de aprendizaje (por ejemplo EfficientNet/MobileNet) y aumentos moderados solo en entrenamiento. Conservar un test externo nunca visto.
- Reportar precisión y recall **por clase**, matriz de confusión, falsos positivos por hora de video, latencia por cámara y calibración de confianza; fijar umbrales con validación, no con el conjunto de prueba.
- Antes de desplegar, exportar un `model.keras` compatible con el preprocesamiento declarado en `metadata.json` y verificar el orden de las cinco etiquetas. Probar con grabaciones de la misma cámara IP.
- Considerar un detector temporal o segmentación para localizar el fenómeno y exigir consistencia durante varios fotogramas antes de escalar alertas. Mantener revisión humana para eventos críticos.

## Próxima prueba local
1. Instalar dependencias del backend y una versión compatible de TensorFlow en un entorno Python apropiado.
2. Activar `NEXUS_LAN_MODE=true` y comprobar fotogramas con la URL MJPEG/RTSP real del teléfono.
3. Confirmar que el modelo se carga y que `/api/model/status` devuelve `ready: true` con API Key.
4. Ejecutar inferencias en grabaciones de prueba etiquetadas y guardar métricas antes de afirmar que la precisión mejoró.

**No hay una cantidad de imágenes que garantice detección perfecta.** La cantidad objetivo debe derivarse de las curvas de aprendizaje y de los errores medidos.
