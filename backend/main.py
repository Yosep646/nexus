import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database.storage import init_db
from backend.api.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="NEXUS RISK AI", version="0.3.0", lifespan=lifespan)
origins = os.getenv("NEXUS_CORS_ORIGINS", "http://127.0.0.1:5500,http://localhost:5500").split(",")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in origins if o.strip()], allow_methods=["GET","POST","DELETE"], allow_headers=["Content-Type"])
app.include_router(router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok", "service": "nexus-risk-ai"}
