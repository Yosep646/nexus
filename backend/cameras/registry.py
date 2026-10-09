"""Validate private-network camera addresses before persistent registration."""
from ipaddress import ip_address, ip_network
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
    allowed = (ip_network("10.0.0.0/8"), ip_network("172.16.0.0/12"), ip_network("192.168.0.0/16"))
    if host.version != 4 or not any(host in subnet for subnet in allowed):
        raise ValueError("Camera must use a numeric RFC1918 LAN IPv4 address")
    if parsed.fragment or parsed.username or parsed.password:
        raise ValueError("Do not embed credentials in camera URLs")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Invalid camera port") from exc
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("Invalid camera port")
    if parsed.scheme in ("http", "https") and parsed.path.startswith("//"):
        raise ValueError("Invalid camera URL path")

def add_camera(name: str, url: str) -> dict:
    _validate_url(url)
    camera = {"id": str(uuid4()), "name": name.strip(), "url": url, "status": "registered"}
    _cameras[camera["id"]] = camera
    return camera

def list_cameras() -> list[dict]:
    return list(_cameras.values())

def remove_camera(camera_id: str) -> bool:
    return _cameras.pop(camera_id, None) is not None
