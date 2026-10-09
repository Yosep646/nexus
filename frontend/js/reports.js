/* Client-only report generation for the simulated dashboard. */
export function summarize(events) {
  const byType = {};
  for (const event of events) {
    const label = String(event.label || 'Desconocido');
    byType[label] = (byType[label] || 0) + 1;
  }
  return {total: events.length, byType};
}
export function renderReport(events) {
  const summary = summarize(events);
  const lines = Object.entries(summary.byType).sort((a,b)=>b[1]-a[1])
    .map(([label,count]) => '<tr><td>'+escapeHtml(label)+'</td><td>'+count+'</td></tr>').join('');
  const rows = events.map(e=>'<tr><td>'+escapeHtml(e.date)+'</td><td>'+escapeHtml(e.camera)+'</td><td>'+escapeHtml(e.label)+'</td></tr>').join('');
  return '<!doctype html><html lang="es"><head><meta charset="utf-8"><title>NEXUS · Reporte demo</title>'+
    '<style>body{font:14px system-ui;padding:35px;color:#142438}h1{color:#0b768b}table{width:100%;border-collapse:collapse;margin:15px 0}td,th{padding:9px;text-align:left;border-bottom:1px solid #ddd}.notice{padding:12px;background:#fff2d8}</style></head><body>'+
    '<h1>NEXUS RISK AI</h1><p class="notice">REPORTE DEMOSTRATIVO: datos simulados, no son alertas ni detecciones reales.</p>'+
    '<p>Eventos simulados: <strong>'+summary.total+'</strong></p><h2>Resumen por categoría</h2><table><thead><tr><th>Clase</th><th>Eventos</th></tr></thead><tbody>'+lines+'</tbody></table>'+
    '<h2>Historial</h2><table><thead><tr><th>Fecha</th><th>Cámara</th><th>Clase</th></tr></thead><tbody>'+rows+'</tbody></table></body></html>';
}
function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
