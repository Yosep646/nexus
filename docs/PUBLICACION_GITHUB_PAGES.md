# Publicación del dashboard NEXUS RISK AI

## Estado y dirección
- Repositorio: https://github.com/Yosep646/nexus
- Dashboard estático: https://yosep646.github.io/nexus/demo.html
- Página principal: https://yosep646.github.io/nexus/
- El dominio `nexus.ia` fue retirado del archivo `CNAME` del repositorio: no debe usarse sin adquirir/configurar DNS y verificar propiedad.

## Publicación automática
El workflow `.github/workflows/pages.yml` se ejecuta con cada cambio en `frontend/**` de `main`, valida archivos esenciales y sube únicamente el directorio `frontend`. Se incluye `frontend/.nojekyll`.

## Ajuste necesario en la cuenta de GitHub
El propietario del repositorio debe comprobar en **Settings → Pages → Build and deployment** que la fuente sea **GitHub Actions**. Si la interfaz muestra un dominio personalizado `nexus.ia`, borrarlo y guardar. La integración de repositorios disponible no permite cambiar estos ajustes de Pages directamente.

Verificar ejecución en https://github.com/Yosep646/nexus/actions. El workflow necesita permisos de publicación y que Pages esté habilitado.

## Diagnóstico
- `DNS_PROBE_FINISHED_NXDOMAIN` en `nexus.ia`: DNS del dominio no configurado. Abrir la dirección `github.io`.
- `404` en `github.io`: comprobar fuente Pages, workflow, permisos y que el deploy finalice en verde.
- La página carga pero el mapa no: revisar conexión a Leaflet/OpenStreetMap y consola del navegador.
- La página carga pero no hay cámaras reales: es esperado; `demo.html` usa datos simulados y `localStorage`.

**Seguridad:** no poner `NEXUS_API_KEY`, contraseñas de cámaras ni direcciones privadas en archivos publicados por GitHub Pages. El backend y el modelo TensorFlow se ejecutan por separado, en un entorno privado y protegido.
