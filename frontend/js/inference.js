import { NexusDetector } from './detector.js';
const detector = new NexusDetector();
const status = document.getElementById('ai-status');
const results = document.getElementById('ai-results');
const imageInput = document.getElementById('ai-image');
const run = document.getElementById('ai-analyze');
run.addEventListener('click', async () => {
  const file = imageInput.files?.[0];
  if (!file) { status.textContent = 'Selecciona una imagen'; return; }
  run.disabled = true; status.textContent = 'Cargando modelo y analizando...'; results.replaceChildren();
  const bitmap = await createImageBitmap(file).catch(() => null);
  try {
    if (!bitmap) throw new Error('La imagen no se pudo abrir');
    const predictions = await detector.predict(bitmap);
    for (const p of predictions) {
      const line = document.createElement('p');
      line.textContent = p.label + ': ' + (p.confidence * 100).toFixed(2) + '%';
      results.append(line);
    }
    status.textContent = 'Predicción completada (no es una alerta verificada)';
  } catch (e) { status.textContent = 'Error: ' + e.message; }
  finally { bitmap?.close(); run.disabled = false; }
});
