/* Demo camera geolocation helpers: user-entered coordinates only. */
export function parseCoordinates(latInput, lngInput) {
  const lat = Number(latInput), lng = Number(lngInput);
  if (String(latInput).trim() === '' || String(lngInput).trim() === '' ||
      !Number.isFinite(lat) || !Number.isFinite(lng) ||
      lat < -90 || lat > 90 || lng < -180 || lng > 180) {
    throw new Error('Ingresa coordenadas válidas: latitud -90 a 90, longitud -180 a 180.');
  }
  return {lat, lng};
}
export function syncCameraMarkers(map, layer, cameras) {
  if (!map || !layer || !window.L) return;
  layer.clearLayers();
  for (const camera of cameras) {
    if (!Number.isFinite(camera.lat) || !Number.isFinite(camera.lng)) continue;
    const marker = L.circleMarker([camera.lat,camera.lng],{
      radius:8,color:'#22d3ee',fillColor:'#0c647a',fillOpacity:0.9
    }).addTo(layer);
    const title = document.createElement('strong'); title.textContent = camera.name;
    const description = document.createElement('p');
    description.textContent = 'Cámara de demostración. Coordenadas proporcionadas manualmente; sin transmisión real.';
    const wrapper = document.createElement('div'); wrapper.append(title,description);
    marker.bindPopup(wrapper);
  }
}
