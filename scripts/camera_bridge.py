"""NEXUS IP camera bridge: LAN OpenCV capture -> authenticated HTTPS JPEG uploads.

Usage (Windows PowerShell):
  $env:NEXUS_API_KEY = '<your secret>'
  python scripts/camera_bridge.py --camera-url http://192.168.1.50:8080/video --camera-id UUID

The local agent never exposes an inbound port and never sends secrets in URLs or logs.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import quote, urlsplit
from uuid import UUID

import cv2


def api_request(url, key, *, data=None, timeout=10):
    headers = {"X-API-Key": key, "Accept": "application/json"}
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
    key = os.environ.get("NEXUS_API_KEY", "").strip()
    if not key:
        parser.error("Falta NEXUS_API_KEY en el entorno local")
    try:
        UUID(args.camera_id)
    except ValueError:
        parser.error("camera-id debe ser el UUID de una cámara registrada en Railway")
    server = urlsplit(args.server)
    if server.scheme != "https" or not server.netloc or server.username or server.password:
        parser.error("El servidor debe ser una URL HTTPS sin credenciales")
    if not 0.2 <= args.fps <= 5:
        parser.error("--fps debe estar entre 0.2 y 5")
    if urlsplit(args.camera_url).scheme not in ("http", "https", "rtsp"):
        parser.error("La URL local debe utilizar HTTP(S) o RTSP")

    root = args.server.rstrip("/")
    endpoint = f"{root}/api/cameras/{quote(args.camera_id)}/frame"
    print("Verificando acceso HTTPS a Railway...", flush=True)
    try:
        with api_request(f"{root}/api/cameras", key) as response:
            cameras = json.load(response)
        if not any(str(c.get("id")) == args.camera_id for c in cameras):
            print("ERROR: ID de cámara no registrado en este servidor.", flush=True)
            return 2
        with api_request(f"{root}/api/model/status", key) as response:
            model_status = json.load(response)
        print("API autenticada. IA:", "disponible" if model_status.get("ready") else
              "modelo no cargado; el video sí puede transmitirse.", flush=True)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
        print("ERROR al validar Railway:", error_text(exc), flush=True)
        return 2

    delay = 1.0 / args.fps
    consecutive_upload_errors = 0
    while True:
        print("Conectando OpenCV a la cámara local...", flush=True)
        try:
            capture = open_camera(args.camera_url)
        except (cv2.error, OSError) as exc:
            print("OpenCV:", type(exc).__name__, "reintentando en 5 s", flush=True)
            time.sleep(5)
            continue
        if not capture.isOpened():
            capture.release()
            print("No se pudo abrir la cámara. Revisa IP, puerto, Wi-Fi y ruta /video.", flush=True)
            time.sleep(5)
            continue
        print("OpenCV conectado. Enviando fotogramas HTTPS...", flush=True)
        try:
            while True:
                started = time.monotonic()
                ok, frame = capture.read()
                if not ok or frame is None:
                    print("La cámara dejó de enviar fotogramas.", flush=True)
                    break
                try:
                    jpeg = encode_frame(frame)
                    with api_request(endpoint, key, data=jpeg, timeout=10) as response:
                        if response.status != 200:
                            raise RuntimeError(f"Respuesta inesperada: {response.status}")
                    consecutive_upload_errors = 0
                    print(f"Fotograma enviado: {len(jpeg)//1024} KB, "
                          f"envío {round((time.monotonic()-started)*1000)} ms", flush=True)
                except urllib.error.HTTPError as exc:
                    print("Railway rechazó el fotograma:", error_text(exc), flush=True)
                    if exc.code in (401, 403, 404):
                        print("Revisa la API Key o el ID de cámara.", flush=True)
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
