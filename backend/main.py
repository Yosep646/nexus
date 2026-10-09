from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.routes import router

app = FastAPI(title="NEXUS RISK AI", version="0.1.0")
app.include_router(router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok", "service": "nexus-risk-ai"}
