"""NEXUS IP camera bridge: LAN OpenCV capture -> HTTPS JPEG uploads.

Usage (Windows PowerShell):
  python scripts/camera_bridge.py --camera-url http://192.168.1.50:8080/video --camera-id UUID

The local agent never exposes an inbound port and never sends secrets in URLs or logs.
"""
import argparse
import json
import socket
import os
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import quote, urlsplit, urlunsplit
from uuid import UUID

import cv2


def api_request(url, key, *, data=None, timeout=10):
    headers = {"Accept": "application/json"}
    if key:
        headers["X-API-Key"] = key
    if data is not None:
        headers["Content-Type"] = "image/jpeg"
    request = urllib.request.Request(url, headers=headers, data=data,
                                     method="POST" if data is not None else "GET")
    return urllib.request.urlopen(request, timeout=timeout)


def error_text(exc):
    if isinstance(exc, urllib.error.HTTPError):
        try:
            body = exc.read(500).decode("utf-8", errors="replace")
            detail = json.loads(body).get("detail", body)
        except (ValueError, OSError):
            detail = exc.reason
        return f"HTTP {exc.code}: {detail}"
    return f"{type(exc).__name__}: {exc}"


def open_camera(url):
    params = [cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000,
              cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000]
    try:
        capture = cv2.VideoCapture(url, cv2.CAP_FFMPEG, params)
    except (cv2.error, TypeError):
        capture = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    if not capture.isOpened():
        capture.release()
        capture = cv2.VideoCapture(url, cv2.CAP_ANY)
    if capture.isOpened():
        capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return capture


def encode_frame(frame):
    height, width = frame.shape[:2]
    if width > 960:
        frame = cv2.resize(frame, (960, max(1, round(height * 960 / width))))
    for quality in (72, 55, 40):
        ok, encoded = cv2.imencode(".jpg", frame,
                                   [cv2.IMWRITE_JPEG_QUALITY, quality])
        if ok and 100 <= encoded.nbytes <= 2_000_000:
            return encoded.tobytes()
    raise ValueError("JPEG inválido o superior a 2 MB")


def main():
    parser = argparse.ArgumentParser(description="NEXUS LAN camera -> Railway")
    parser.add_argument("--camera-url", required=True)
    parser.add_argument("--camera-id", required=True)
    parser.add_argument("--server", default="https://nexus-production-6562.up.railway.app")
    parser.add_argument("--fps", type=float, default=2.0)
    args = parser.parse_args()
    key = ""  # NEXUS keyless API
    try:
        UUID(args.camera_id)
    except ValueError:
        parser.error("camera-id debe ser el UUID de una cámara registrada en Railway")
    server = urlsplit(args.server)
    if (server.scheme != "https" and not (server.scheme == "http" and server.hostname in ("localhost", "127.0.0.1", "::1"))) or not server.netloc or server.username or server.password:
        parser.error("Usa HTTPS o HTTP únicamente para localhost")
    local_hosts = ("127.0.0.1", "localhost", "::1")
    if server.hostname in local_hosts:
        key = ""  # Local mode never sends an API key
    if not 0.2 <= args.fps <= 5:
        parser.error("--fps debe estar entre 0.2 y 5")
    if urlsplit(args.camera_url).scheme not in ("http", "https", "rtsp"):
        parser.error("La URL local debe utilizar HTTP(S) o RTSP")

    root = args.server.rstrip("/")
    endpoint = f"{root}/api/cameras/{quote(args.camera_id)}/frame"
    print("Verificando API NEXUS sin clave...", flush=True)
    try:
        with api_request(f"{root}/api/cameras", key) as response:
            cameras = json.load(response)
        if not any(str(c.get("id")) == args.camera_id for c in cameras):
            print("ERROR: ID de cámara no registrado en este servidor.", flush=True)
            return 2
        try:
            with api_request(f"{root}/api/model/status", key) as response:
                model_status = json.load(response)
            print("API conectada. IA:", "disponible" if model_status.get("ready") else
                  "modelo no cargado; el video sí puede transmitirse.", flush=True)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as model_error:
            print("Estado IA no disponible; continuando con la transmisión:", error_text(model_error), flush=True)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
        print("ERROR al validar Railway:", error_text(exc), flush=True)
        return 2

    camera_parts = urlsplit(args.camera_url)
    if camera_parts.scheme in ("http", "https") and camera_parts.path in ("", "/"):
        args.camera_url = urlunsplit((camera_parts.scheme, camera_parts.netloc, "/video", "", ""))
        camera_parts = urlsplit(args.camera_url)
        print("IP Webcam: URL normalizada a /video", flush=True)
    if not camera_parts.hostname:
        parser.error("URL de IP Webcam sin host")
    camera_port = camera_parts.port or (554 if camera_parts.scheme == "rtsp" else 443 if camera_parts.scheme == "https" else 80)
    delay = 1.0 / args.fps
    consecutive_upload_errors = 0
    uploaded_frames = 0
    while True:
        print(f"Comprobando TCP {camera_parts.hostname}:{camera_port}...", flush=True)
        try:
            with socket.create_connection((camera_parts.hostname, camera_port), timeout=5):
                pass
        except ConnectionRefusedError:
            print("Puerto rechazado: inicia IP Webcam o revisa el puerto.", flush=True)
            time.sleep(5)
            continue
        except socket.timeout:
            print("Timeout: revisa Wi-Fi, IP y aislamiento de clientes.", flush=True)
            time.sleep(5)
            continue
        except OSError as exc:
            print(f"Error de red: {type(exc).__name__}: {exc}", flush=True)
            time.sleep(5)
            continue
        print("TCP conectado. Abriendo OpenCV...", flush=True)
        try:
            capture = open_camera(args.camera_url)
            if not capture.isOpened() and camera_parts.scheme in ("http", "https") and camera_parts.path == "/video":
                fallback = urlunsplit((camera_parts.scheme, camera_parts.netloc, "/videofeed", "", ""))
                print("Probando ruta alternativa /videofeed...", flush=True)
                capture.release()
                capture = open_camera(fallback)
        except (cv2.error, OSError) as exc:
            print("OpenCV:", type(exc).__name__, "reintentando en 5 s", flush=True)
            time.sleep(5)
            continue
        if not capture.isOpened():
            capture.release()
            print("TCP accesible, OpenCV no abre: revisa /video, formato y permisos.", flush=True)
            time.sleep(5)
            continue
        print("OpenCV conectado. Enviando fotogramas a NEXUS...", flush=True)
        try:
            while True:
                started = time.monotonic()
                try:
                    ok, frame = capture.read()
                except (cv2.error, OSError) as read_error:
                    print("Error leyendo IP Webcam:", type(read_error).__name__, str(read_error), flush=True)
                    break
                if not ok or frame is None:
                    print("La cámara dejó de enviar fotogramas.", flush=True)
                    break
                try:
                    jpeg = encode_frame(frame)
                    with api_request(endpoint, key, data=jpeg, timeout=10) as response:
                        if response.status != 200:
                            raise RuntimeError(f"Respuesta inesperada: {response.status}")
                    consecutive_upload_errors = 0
                    uploaded_frames += 1
                    if uploaded_frames == 1 or uploaded_frames % 20 == 0:
                        try:
                            with api_request(f"{root}/api/cameras/{quote(args.camera_id)}/status", key, timeout=8) as check_response:
                                remote_status = json.load(check_response)
                            if remote_status.get("state") == "connected":
                                print("Railway confirma recepción de video; antigüedad:", remote_status.get("last_frame_age"), "s", flush=True)
                            else:
                                print("Railway no confirma imagen reciente:", remote_status.get("state"), flush=True)
                        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, OSError) as verify_error:
                            print("No se pudo consultar el estado remoto:", error_text(verify_error), flush=True)
                    print(f"Fotograma enviado: {len(jpeg)//1024} KB, "
                          f"envío {round((time.monotonic()-started)*1000)} ms", flush=True)
                except urllib.error.HTTPError as exc:
                    print("Railway rechazó el fotograma:", error_text(exc), flush=True)
                    if exc.code in (401, 403, 404):
                        print("Revisa el ID de cámara o la autorización del servidor remoto.", flush=True)
                        return 3
                    consecutive_upload_errors += 1
                except (urllib.error.URLError, TimeoutError, OSError, ValueError, RuntimeError) as exc:
                    print("Fallo de captura/envío:", error_text(exc), flush=True)
                    consecutive_upload_errors += 1
                if consecutive_upload_errors >= 5:
                    print("5 fallos consecutivos; revalidando conexión en 5 s.", flush=True)
                    time.sleep(5)
                    consecutive_upload_errors = 0
                    break
                time.sleep(max(0, delay - (time.monotonic() - started)))
        except KeyboardInterrupt:
            print("Transmisión detenida.", flush=True)
            return 0
        finally:
            capture.release()
        time.sleep(3)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("Transmisión detenida.", flush=True)
        sys.exit(0)
