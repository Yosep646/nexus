import os
import asyncio
from backend.detection.monitor import monitor_loop
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from backend.database.storage import init_db
from backend.api.routes import router
from backend.security import require_api_key

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task = None
    if os.getenv("NEXUS_MONITOR_ENABLED", "false").lower() == "true":
        task = asyncio.create_task(monitor_loop())
    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

app = FastAPI(title="NEXUS RISK AI", version="0.4.0", lifespan=lifespan)
origins = os.getenv("NEXUS_CORS_ORIGINS", "http://127.0.0.1:5500,http://localhost:5500").split(",")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in origins if o.strip()], allow_methods=["GET","POST","PATCH","DELETE"], allow_headers=["Content-Type","X-API-Key"])
app.include_router(router, prefix="/api", dependencies=[Depends(require_api_key)])

@app.get("/health")
def health():
    return {"status": "ok", "service": "nexus-risk-ai"}


# Serve the operational dashboard from the same Railway hostname.
# API routes remain protected by X-API-Key.
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.is_dir():
    app.mount("/dashboard", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="dashboard")

@app.get("/", include_in_schema=False)
def home():
    if FRONTEND_DIR.is_dir():
        return RedirectResponse(url="/dashboard/demo.html", status_code=307)
    return {"service": "nexus-risk-ai", "status": "ok", "health": "/health", "docs": "/docs"}
