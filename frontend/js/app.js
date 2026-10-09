const API = 'http://localhost:8000/api';
const grid = document.querySelector('#camera-grid');
const count = document.querySelector('#count');
const message = document.querySelector('#message');
const isPages = location.hostname.endsWith('.github.io');
if (isPages) { message.textContent = 'Vista pública: el backend local y las cámaras IP no están disponibles desde GitHub Pages.'; document.querySelector('#camera-form').querySelector('button').disabled = true; }
async function request(path, options) { const response = await fetch(API + path, options); if (!response.ok) { const error = await response.json().catch(() => ({})); throw new Error(error.detail || 'Error de conexión'); } return response.json(); }
async function refresh() {
  try {
    const cameras = await request('/cameras');
    count.textContent = cameras.length + ' cámaras';
    grid.replaceChildren();
    cameras.forEach(camera => {
      const card = document.createElement('article'); card.className = 'camera';
      const title = document.createElement('h3'); title.textContent = camera.name;
      const preview = document.createElement('img'); preview.className = 'camera-feed'; preview.alt = 'Vista de ' + camera.name; preview.loading = 'lazy';
      const placeholder = document.createElement('div'); placeholder.className = 'placeholder'; placeholder.textContent = 'Vista previa no iniciada';
      const url = document.createElement('p'); url.textContent = camera.url;
      const start = document.createElement('button'); start.textContent = 'Iniciar transmisión';
      start.onclick = () => { preview.src = API + '/cameras/' + encodeURIComponent(camera.id) + '/stream'; preview.style.display = 'block'; placeholder.style.display = 'none'; };
      preview.onerror = () => { preview.removeAttribute('src'); preview.style.display = 'none'; placeholder.style.display = 'grid'; placeholder.textContent = 'No se pudo abrir la transmisión. Verifica IP y formato de video.'; };
      const stop = document.createElement('button'); stop.textContent = 'Detener';
      stop.onclick = () => { preview.removeAttribute('src'); preview.style.display = 'none'; placeholder.style.display = 'grid'; };
      const detect = document.createElement('button'); detect.textContent = 'Analizar fotograma';
      const prediction = document.createElement('p'); prediction.textContent = 'Sin análisis';
      detect.onclick = async () => {
        prediction.textContent = 'Analizando...';
        try {
          const result = await request('/cameras/' + encodeURIComponent(camera.id) + '/detect', {method:'POST'});
          prediction.textContent = result.status === 'model_unavailable' ? 'Modelo de IA aún no instalado' :
            (result.predictions[0] ? result.predictions[0].label + ': ' + (result.predictions[0].confidence * 100).toFixed(1) + '%' : 'Sin predicciones');
        } catch(e) { prediction.textContent = e.message; }
      };
      const remove = document.createElement('button'); remove.textContent = 'Eliminar';
      remove.onclick = async () => { try { stop.click(); await request('/cameras/' + camera.id, {method:'DELETE'}); await refresh(); } catch(e) { message.textContent = e.message; } };
      card.append(title,placeholder,preview,url,start,stop,detect,prediction,remove); grid.append(card);
    });
  } catch(e) { message.textContent = 'No se pudo conectar al backend: ' + e.message; }
}
document.querySelector('#camera-form').addEventListener('submit', async event => {
  event.preventDefault(); const form = event.currentTarget; const data = Object.fromEntries(new FormData(form));
  try { await request('/cameras', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)}); form.reset(); message.textContent = 'Cámara registrada'; await refresh(); }
  catch(e) { message.textContent = e.message; }
});
if (!isPages) refresh();
