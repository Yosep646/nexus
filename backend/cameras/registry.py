"""Temporary in-memory camera registry. Replace with persistent storage and authenticated access."""
from ipaddress import ip_address
from urllib.parse import urlparse
from uuid import uuid4

_cameras: dict[str, dict] = {}

def _validate_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https", "rtsp") or not parsed.hostname:
        raise ValueError("Use a valid HTTP(S) or RTSP camera URL")
    try:
        host = ip_address(parsed.hostname)
    except ValueError as exc:
        raise ValueError("Use a numeric IP address on the local network") from exc
    if not host.is_private:
        raise ValueError("Camera must use a private LAN IP address")
    if parsed.username or parsed.password:
        raise ValueError("Do not embed credentials in camera URLs")

def add_camera(name: str, url: str) -> dict:
    _validate_url(url)
    camera = {"id": str(uuid4()), "name": name.strip(), "url": url, "status": "registered"}
    _cameras[camera["id"]] = camera
    return camera

def list_cameras() -> list[dict]:
    return list(_cameras.values())

def remove_camera(camera_id: str) -> bool:
    return _cameras.pop(camera_id, None) is not None
