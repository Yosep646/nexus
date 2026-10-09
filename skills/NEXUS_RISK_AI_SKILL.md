---
name: nexus-risk-ai-development
description: Guía de implementación y validación de NEXUS RISK AI, plataforma de monitoreo multicíamara IP y clasificación preliminar de fenómenos naturales.
---

# SKILL — NEXUS RISK AI (plan maestro)

## 1. Misión y límites
Desarrollar un centro de operaciones web, mantenible y seguro, capaz de conectar múltiples cámaras IP autorizadas, analizar fotogramas mediante un modelo de clasificación, registrar evidencias y mostrar eventos para **revisión humana**. Clases objetivo: huayco, inundación, deslizamiento de tierra, sequía y normal.

**Regla obligatoria:** las predicciones son señales preliminares, nunca avisos oficiales ni emergencias confirmadas. El sistema debe mostrar fuente, fecha, cámara, clase, confianza y estado de revisión. Evitar lenguaje de certeza absoluta.

## 2. Estado real del repositorio (octubre de 2026)
- `main`: frontend estático (`frontend/index.html`) y demo independiente (`frontend/demo.html`) con cámaras ficticias, eventos ficticios, estadísticas, filtros, CSV, reporte HTML imprimible, mapa Leaflet y formulario de coordenadas manuales. La demo usa `localStorage` y **no** cámaras reales.
- `feature/detection-mvp`: prototipo FastAPI, SQLite, registro de cámaras, relay MJPEG, inferencia a demanda, carga opcional de Teachable Machine y políticas iniciales de revisión. La integración no está terminada ni verificada.
- **No afirmar** que el modelo entrenado está instalado, que la API está conectada a la demo, que se realizaron pruebas o que GitHub Pages está operativo sin verificarlo.
- GitHub Pages aloja únicamente frontend estático. No ejecuta FastAPI, SQLite, TensorFlow Python ni puede acceder por sí solo a una cámara en LAN.

## 3. Arquitectura objetivo
```text
Cámaras IP autorizadas (LAN)
       │ RTSP/HTTP/MJPEG
       ▼
Ingesta Python / OpenCV ──► Supervisor de cámaras (reconexión, timeout, FPS)
       │
       ├──► Inferencia TensorFlow / modelo versionado
       │       └──► Política de umbral + revisión humana
       ├──► Capturas y metadatos de evidencia
       └──► API FastAPI (auth, validación, rate limiting)
                         │
                    SQLite (MVP)
                         │
                   Frontend web
             dashboard / mapa / alertas / reportes
```
La inferencia debe correr fuera del hilo de la API; usar colas acotadas y backpressure. Para despliegue multiusuario considerar PostgreSQL, almacenamiento de objetos y trabajadores dedicados. Docker Compose debe incluir servicios necesarios, límites de recursos y volúmenes persistentes.

## 4. Backlog priorizado y criterios de aceptación

### P0 — Integridad y seguridad antes de integrar
1. **Unificar ramas** mediante PR revisado y pruebas. No fusionar cambios que rompan el dashboard.
2. **Instalar modelo real** desde artefactos originales del usuario: `model.json`, `weights.bin`, `metadata.json` para TFJS o exportación Keras compatible para Python. No inventar pesos ni resultados.
3. **Versionar el modelo** y registrar checksum SHA-256, fecha, clases y preprocesamiento. Validar orden de etiquetas y forma de entrada.
4. **Autenticación y autorización**: operador, supervisor, administrador; credenciales seguras, expiración, protección de rutas de video, logs de acceso. Nunca exponer cámaras o tokens en HTML público.
5. **SSRF y cámaras**: permitir solo orígenes autorizados, IP privadas de red definida, bloquear loopback, link-local, metadatos cloud, redirecciones y DNS rebinding. Validar de nuevo al conectar, no solo al registrar. No aceptar URL arbitraria desde Internet.
6. **Configuración** mediante variables de entorno; `.env` fuera de Git; CORS por origen específico; HTTPS/reverse proxy; límites de solicitudes; dependencias fijadas y análisis de vulnerabilidades.
7. **Datos**: migraciones SQLite, índices, foreign keys activadas, transacciones, respaldos, retención configurable, control de tamaño de capturas, política de eliminación.

**Aceptación P0:** pruebas automatizadas de autenticación, URL bloqueadas, validación de modelos, persistencia, fallos de conexión y CORS; ninguna contraseña, URL con credenciales o secreto expuesto al público.

### P1 — Cámaras e inferencia operativa
1. Registrar/editar/eliminar N cámaras IP con nombre, tipo, ubicación y estado.
2. Mostrar inicialmente una cámara y agregar tarjetas dinámicamente, sin reservar espacios vacíos.
3. Capturar RTSP/HTTP/MJPEG de smartphones y cámaras IP con reconexión exponencial, timeout, heartbeat, estado offline/online y FPS configurable.
4. Ejecutar detección por cámara de forma independiente, con umbral por clase, enfriamiento (cooldown) y eliminación de duplicados.
5. Registrar todas las predicciones relevantes con `camera_id`, `model_version`, clase, confianza, timestamp UTC y captura opcional.
6. Mostrar la predicción **en cada tarjeta de cámara** y una lista agregada de eventos.
7. Implementar botón de pausar/reanudar, prueba de conexión y manejo explícito de modelo no disponible.
8. No iniciar procesamiento continuo hasta comprobar límites de CPU/RAM y permisos.

**Aceptación P1:** prueba con al menos dos fuentes autorizadas simultáneas, desconexión/reconexión, ninguna mezcla de etiquetas entre cámaras y registro reproducible de eventos.

### P2 — Centro de operaciones y mapa
1. Mantener tipografía legible, responsive, accesibilidad teclado, contrastes y estados vacíos.
2. Panel con KPI: cámaras conectadas, eventos por categoría, pendientes de revisión, último evento y salud de servicios.
3. Mapa Leaflet con coordenadas reales **solo si fueron configuradas**; marcadores por cámara, agrupación y filtro; vista regional y opción de globo 3D si el rendimiento lo permite.
4. Solicitar geolocalización del navegador únicamente con consentimiento explícito; nunca usar la ubicación del operador como ubicación de una cámara sin confirmación.
5. Filtros por cámara, clase, fecha, confianza y estado; búsqueda y paginación.
6. Gráficos de tendencia diaria/semanal y distribución de clases, con separación estricta entre datos reales y simulados.
7. Panel de alertas: `pendiente`, `confirmada por operador`, `descartada`, `resuelta`; autor, notas y auditoría.
8. Mostrar fuentes de mapa y modo degradado cuando no haya Internet.

**Aceptación P2:** interfaz usable en escritorio y móvil; sin falsos estados de conexión; mapa sin puntos inventados.

### P3 — Evidencias, reportes y automatización
1. Guardar captura de evento con identificador, fecha UTC, cámara y hash de integridad.
2. Exportar CSV y PDF con filtros, metadatos, versión de modelo, aviso de incertidumbre y fecha de generación.
3. Definir retención, respaldo, acceso restringido, restauración y borrado verificable.
4. Notificaciones internas y, opcionalmente, correo/Telegram/n8n con confirmación humana y deduplicación.
5. Protocolo de escalamiento: ningún mensaje público automático basado únicamente en clasificación de imagen.
6. Auditoría de revisiones, cambios de configuración, accesos y errores.

**Aceptación P3:** reporte reproducible a partir de la BD, capturas accesibles solo a roles autorizados y prueba de restauración.

### P4 — Calidad, despliegue y documentación
1. `pytest` para API/SQLite/políticas; pruebas de integración con video de prueba sin datos privados.
2. Tests frontend para filtros, gráficos, persistencia y manejo de fallos; accesibilidad y responsive.
3. CI en GitHub Actions con lint, tests, análisis de dependencias y build de frontend.
4. Dockerfile backend y Compose local con healthchecks, volúmenes y límites; **Docker no reduce por sí mismo el tamaño del repositorio ni permite subir 4.9 GB a GitHub**.
5. `.gitignore` para datasets, videos, capturas, bases de datos y secretos; usar almacenamiento externo o Git LFS solo si corresponde y se conocen cuotas.
6. Guías de instalación Windows/Ubuntu, entrenamiento/exportación del modelo, conexión de smartphone IP, arquitectura, seguridad, recuperación y operación.
7. Despliegue: GitHub Pages solo frontend demo; backend en servidor privado/VPN o hosting protegido. Configurar URL API por entorno; nunca asumir `localhost` desde un sitio público.
8. Prueba final con cámaras reales autorizadas, modelo real, tiempos de respuesta, tasa de falsos positivos y uso de recursos.

**Aceptación P4:** instalación reproducible desde cero y pipeline CI en verde.

## 5. Contratos de datos recomendados
- `Camera`: id, name, stream_url (secreto/protegido), latitude?, longitude?, status, created_at, updated_at.
- `Detection`: id, camera_id, class_name, confidence, model_version, captured_at, image_path?, review_status.
- `Review`: detection_id, reviewer_id, decision, notes, reviewed_at.
- `AuditEvent`: id, actor_id, action, resource_id, timestamp, metadata_sanitized.
- API versionada: `/api/v1/cameras`, `/api/v1/detections`, `/api/v1/reviews`, `/api/v1/stats`, `/api/v1/health`; definir paginación y errores uniformes.
- Migrar gradualmente desde rutas existentes sin romper clientes.

## 6. Política de IA responsable
- Verificar que la imagen no provenga de una escena de entrenamiento.
- Separar entrenamiento/validación/prueba por ubicación, cámara y fecha para reducir fuga de datos.
- Reportar precisión, recall, F1 y matriz de confusión por clase; medir falsos negativos de riesgo.
- Calibrar umbrales por clase y condiciones ambientales; monitorear deriva y escenarios de poca luz.
- Registrar incertidumbre y habilitar abstención cuando no hay evidencia suficiente.
- Revisar manualmente antes de activar notificaciones externas.
- No usar el prototipo como sustituto de alertas oficiales ni de protocolos de defensa civil.

## 7. Instrucciones para agente de desarrollo (Cloud Code / Codex / Open Code)
1. Inspecciona estructura, ramas y pruebas antes de editar; no supongas archivos inexistentes.
2. Selecciona una tarea P0/P1 concreta, implementa cambios pequeños y reversibles.
3. Conserva el dashboard demo funcional y **no mezcles datos simulados con eventos reales**.
4. Escribe o actualiza pruebas, ejecútalas cuando exista entorno y comunica resultados reales.
5. No hardcodees contraseñas, claves ni endpoints privados. No incluyas videos/datasets grandes en Git.
6. Documenta cada nueva variable de entorno y migración.
7. Comprueba rutas, CORS, acceso a cámaras y estados de error.
8. Presenta al terminar: archivos modificados, commits, pruebas ejecutadas, riesgos y siguiente tarea.
9. No afirmes que el despliegue o una cámara funcionan sin evidencia de ejecución.
10. Minimiza tokens: lee solo archivos relevantes, usa diffs pequeños y reutiliza módulos existentes.

## 8. Próxima secuencia de ejecución sugerida
- [ ] Verificar demo pública y corregir problemas de JS/Leaflet.
- [ ] Añadir pruebas automáticas a la demo (coordenadas, eventos, exportación).
- [ ] Auditar y proteger backend, especialmente SSRF y autenticación.
- [ ] Recuperar y validar pesos originales de Teachable Machine.
- [ ] Integrar detección a demanda con dos cámaras y SQLite.
- [ ] Implementar worker de detección continua y revisión humana.
- [ ] Conectar dashboard con API autenticada.
- [ ] Añadir capturas, reportes PDF y auditoría.
- [ ] Contenerizar, automatizar CI y probar despliegue seguro.

## 9. Definición de terminado
No considerar NEXUS RISK AI finalizado hasta que la demo y el sistema real estén claramente diferenciados, el modelo esté instalado y validado, el acceso esté protegido, dos cámaras funcionen simultáneamente en pruebas, los eventos y evidencias persistan, existan reportes verificables, se hayan ejecutado pruebas y el despliegue sea reproducible.
