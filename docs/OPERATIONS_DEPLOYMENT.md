# Despliegue NEXUS RISK AI — guía operativa

## Separación de entornos

- `frontend/demo.html`: demostración estática, datos simulados; publicable en GitHub Pages.
- `frontend/operations.html`: consola para una red privada; **no introducir claves de producción en GitHub Pages**.
- FastAPI y cámaras IP: red privada/VPN, nunca acceso directo a Internet sin autenticación de usuarios, HTTPS, control de acceso y auditoría.
- GitHub Pages no ejecuta Python, OpenCV, TensorFlow ni SQLite.

## Preparar backend

1. Generar `NEXUS_API_KEY` aleatoria de al menos 24 caracteres, fuera de Git.
2. Configurar `.env` local (no subirlo).
3. Ejecutar `docker compose up --build -d`.
4. Comprobar `curl http://127.0.0.1:8000/health`.
5. Comprobar `GET /api/readiness` con cabecera `X-API-Key`.
6. Servir `frontend/operations.html` desde un origen privado autorizado por `NEXUS_CORS_ORIGINS`.
7. Registrar cámaras con IPv4 RFC1918 accesibles desde el contenedor.

## Modelo

`python -m training.validate_dataset --dataset datasets/curated`

`python -m training.train --dataset datasets/curated --output models/teachable_machine`

Evaluar con un conjunto de prueba independiente antes de usar alertas operativas. El contenedor base no instala TensorFlow; para inferencia hay que crear una imagen con la versión compatible de TensorFlow y los pesos `model.keras`. Sin esto `/api/model/status` devuelve `ready: false`.

## Verificaciones antes de producción

- Ejecutar `python -m pytest -q` y comprobar GitHub Actions.
- Validar rutas de cámaras y protocolos; restringir acceso a LAN/VPN.
- Revisar CORS y permisos, protección contra SSRF y DoS, retención de evidencias y copias de seguridad de SQLite.
- Verificar latencia y memoria de inferencia bajo carga; fijar límites por cámara.
- No interpretar confianza del clasificador como probabilidad calibrada ni sustituir el criterio de Protección Civil.

## Publicación

La rama de desarrollo no equivale a despliegue. Para publicar la demo, fusionar cambios revisados a `main` y habilitar GitHub Pages con fuente GitHub Actions. La consola real y la API requieren infraestructura privada independiente.
