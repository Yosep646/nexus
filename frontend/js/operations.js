const el = id => document.getElementById(id);
let api = '', key = '';
const status = text => { el('connection-status').textContent = text; };
async function request(path, options = {}) {
  if (!api || !key) throw new Error('Conecta la API primero');
  const response = await fetch(api + path, {
    ...options,
    headers: {'X-API-Key': key, ...(options.headers || {})}
  });
  if (!response.ok) throw new Error('HTTP ' + response.status);
  return response.json();
}
function cell(row, value) {
  const td = document.createElement('td');
  td.textContent = String(value ?? '—');
  row.append(td);
  return td;
}
async function load() {
  const [stats, cameras, events] = await Promise.all([
    request('/stats'), request('/cameras'),
    request('/detections?limit=100&review_status=' + encodeURIComponent(el('review-filter').value))
  ]);
  el('camera-count').textContent = stats.cameras;
  el('event-count').textContent = stats.detections_total;
  el('pending-count').textContent = stats.pending_review;
  el('confirmed-count').textContent = stats.confirmed;
  const cameraNames = new Map(cameras.map(camera => [camera.id, camera.name]));
  const cards = el('cameras');
  cards.replaceChildren();
  for (const camera of cameras) {
    const article = document.createElement('article');
    article.className = 'camera';
    const name = document.createElement('h3');
    name.textContent = camera.name;
    const state = document.createElement('p');
    state.textContent = 'Registrada · análisis bajo demanda';
    const analyze = document.createElement('button');
    analyze.textContent = 'Analizar fotograma';
    analyze.onclick = async () => {
      analyze.disabled = true;
      state.textContent = 'Analizando…';
      try {
        const result = await request('/cameras/' + encodeURIComponent(camera.id) + '/detect', {method: 'POST'});
        state.textContent = result.status === 'model_unavailable'
          ? 'Modelo no instalado'
          : result.predictions?.length
            ? result.predictions[0].label + ' · ' + Math.round(result.predictions[0].confidence * 100) + '%'
            : 'Sin resultado';
        await load();
      } catch (error) { state.textContent = error.message; }
      finally { analyze.disabled = false; }
    };
    article.append(name, state, analyze);
    cards.append(article);
  }
  const tbody = el('events');
  tbody.replaceChildren();
  for (const event of events) {
    const tr = document.createElement('tr');
    cell(tr, new Date(event.created_at).toLocaleString('es-PE'));
    cell(tr, cameraNames.get(event.camera_id) || event.camera_id);
    cell(tr, event.label);
    cell(tr, (event.confidence * 100).toFixed(1) + '%');
    const td = cell(tr, event.review_status);
    if (event.review_status === 'pending_human_review') {
      for (const [decision, caption] of [['confirmed', 'Confirmar'], ['dismissed', 'Descartar']]) {
        const button = document.createElement('button');
        button.textContent = caption;
        button.onclick = async () => {
          button.disabled = true;
          try {
            await request('/detections/' + encodeURIComponent(event.id) + '/review', {
              method: 'PATCH', headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({decision})
            });
            await load();
          } catch (error) { status(error.message); button.disabled = false; }
        };
        td.append(button);
      }
    }
    tbody.append(tr);
  }
  status('Conectado · ' + new Date().toLocaleTimeString('es-PE'));
}
el('connection').addEventListener('submit', async event => {
  event.preventDefault();
  if (location.hostname.endsWith('.github.io')) {
    status('La consola privada no admite claves de API en GitHub Pages');
    return;
  }
  const url = el('api-url').value.trim().replace(/\/$/, '');
  if (!/^https:\/\//.test(url) && !/^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?\/api$/.test(url)) {
    status('Utiliza HTTPS o una API local en localhost');
    return;
  }
  api = url;
  key = el('api-key').value;
  el('api-key').value = '';
  try { await load(); } catch (error) { status('Error de conexión: ' + error.message); }
});
el('reload').onclick = () => load().catch(error => status(error.message));
el('filters').onsubmit = event => {
  event.preventDefault();
  load().catch(error => status(error.message));
};

const reportButton = document.createElement('button');
reportButton.type = 'button';
reportButton.textContent = 'Descargar reporte PDF';
el('reload').after(reportButton);
reportButton.onclick = async () => {
  reportButton.disabled = true;
  try {
    if (!api || !key) throw new Error('Conecta la API primero');
    const response = await fetch(api + '/reports/detections.pdf', {
      headers: {'X-API-Key': key}, cache: 'no-store'
    });
    if (!response.ok) throw new Error('Error HTTP ' + response.status);
    const url = URL.createObjectURL(await response.blob());
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = 'nexus-detecciones.pdf';
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 3000);
  } catch (error) {
    status('No se pudo descargar el reporte: ' + error.message);
  } finally {
    reportButton.disabled = false;
  }
};
