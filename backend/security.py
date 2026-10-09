"""API key authentication for local/private NEXUS deployments."""
import os
import secrets
from fastapi import Header, HTTPException

def require_api_key(x_api_key: str | None = Header(default=None)):
    expected = os.getenv("NEXUS_API_KEY", "")
    if not expected or len(expected) < 24:
        raise HTTPException(status_code=503, detail="API key is not configured")
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")
