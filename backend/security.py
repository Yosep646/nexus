"""NEXUS authentication: keyless only for requests originating on the same host.

Cloud deployments remain protected by the configured NEXUS_API_KEY.
Set NEXUS_LOCAL_NO_AUTH=true only when running the backend on a trusted laptop.
"""
import ipaddress
import os
import secrets

from fastapi import Header, HTTPException, Request


def require_api_key(request: Request, x_api_key: str | None = Header(default=None)):
    if os.getenv("NEXUS_LOCAL_NO_AUTH", "").lower() == "true":
        host = request.client.host if request.client else ""
        try:
            is_loopback = ipaddress.ip_address(host).is_loopback
        except ValueError:
            is_loopback = False
        if is_loopback:
            return
    expected = os.getenv("NEXUS_API_KEY", "")
    if not expected or len(expected) < 24:
        raise HTTPException(status_code=503, detail="API key is not configured")
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid API key")
