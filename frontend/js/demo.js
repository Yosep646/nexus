import { renderReport } from './reports.js';
/* Local demo only. No camera streams, model inference or external API calls. */
(() => {
  'use strict';
  const KEY = 'nexus-demo-v1';
  const defaults = () => ({cameras: [
    {id:'demo-1',name:'Cámara demostrativa 01',location:'Ubicación no configurada'},
    {id:'demo-2',name:'Cámara demostrativa 02',location:'Ubicación no configurada'}
  ], events:[]});
  let state;
  try {
    const saved = JSON.parse(localStorage.getItem(KEY));
    state = saved && Array.isArray(saved.cameras) && Array.isArray(saved.events) ? saved : defaults();
  } catch { state = defaults(); }
  const $ = id => document.getElementById(id);
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch {} };
  const el = (tag, text, cls) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (cls) node.className = cls;
    return node;
  };
  function render() {
    $('metric-cameras').textContent = String(state.cameras.length);
    $('metric-events').textContent = String(state.events.length);
    $('metric-review').textContent = String(state.events.filter(e => e.label !== 'Normal').length);
    const grid = $('demo-cameras'); grid.replaceChildren();
    const select = $('event-camera'); select.replaceChildren();
    for (const camera of state.cameras) {
      const card = el('article', undefined, 'camera-card');
      const visual = el('div', undefined, 'camera-visual'); visual.append(el('span','▣','camera-icon'));
      const body = el('div',undefined,'camera-body');
      body.append(el('h3',camera.name),el('p',camera.location));
      const remove = el('button','Eliminar ejemplo');
      remove.addEventListener('click',() => { state.cameras = state.cameras.filter(c=>c.id!==camera.id); save(); render(); });
      body.append(remove); card.append(visual,body); grid.append(card);
      const option = el('option',camera.name); option.value = camera.id; select.append(option);
    }
    $('add-event').disabled = state.cameras.length === 0;
    const tbody = $('event-rows'); tbody.replaceChildren();
    if (!state.events.length) {
      const tr = el('tr'); const td = el('td','Sin eventos simulados.',''); td.colSpan=4; tr.append(td); tbody.append(tr);
    }
    for (const event of [...state.events].reverse()) {
      const tr = el('tr');
      tr.append(el('td',new Date(event.date).toLocaleString('es-PE')),
        el('td',event.camera),el('td',event.label));
      const status = el('td');
      status.append(el('span',event.label==='Normal'?'Informativo':'Revisión simulada',
        event.label==='Normal'?'tag':'tag review'));
      tr.append(status); tbody.append(tr);
    }
  }
  $('add-camera').addEventListener('click', () => {
    if (state.cameras.length >= 12) { alert('Máximo 12 cámaras de ejemplo.'); return; }
    const n = state.cameras.length+1;
    state.cameras.push({id:crypto.randomUUID(),name:'Cámara demostrativa '+String(n).padStart(2,'0'),location:'Ubicación no configurada'});
    save(); render();
  });
  $('add-event').addEventListener('click', () => {
    const camera = state.cameras.find(c=>c.id===$('event-camera').value);
    if (!camera) return;
    state.events.push({id:crypto.randomUUID(),camera:camera.name,label:$('event-type').value,date:new Date().toISOString()});
    state.events=state.events.slice(-500);save();render();
  });
  $('print-report').addEventListener('click', () => {
    const report = renderReport(state.events);
    const blob = new Blob([report], {type:'text/html;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'nexus-reporte-demo.html';
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  });
  $('reset-demo').addEventListener('click',()=>{if(confirm('¿Restablecer los datos simulados?')){state=defaults();save();render();}});
  $('export-csv').addEventListener('click',()=>{
    const rows=[['Fecha','Camara','Fenomeno','Estado'],...state.events.map(e=>[e.date,e.camera,e.label,e.label==='Normal'?'Informativo':'Revision simulada'])];
    const quote = value => '"'+String(value).replace(/^[=+\-@]/,"'$&").replace(/"/g,'""')+'"';
    const csv='\uFEFF'+rows.map(r=>r.map(quote).join(',')).join('\r\n');
    const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));
    const a=document.createElement('a');a.href=url;a.download='nexus-demo-eventos.csv';a.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  const clock=()=>{$('clock').textContent=new Date().toLocaleString('es-PE');};
  clock();setInterval(clock,30000);render();
})();
