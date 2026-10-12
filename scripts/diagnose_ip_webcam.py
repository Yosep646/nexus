"""NEXUS: diagnóstico real IP Webcam -> OpenCV -> Railway.
Ejecutar en la laptop conectada a la misma Wi-Fi que el teléfono.
"""
import argparse
import json
import socket
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit, urlunsplit
from uuid import UUID

import cv2


def request(url, data=None):
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "image/jpeg"
    req = urllib.request.Request(url, data=data, headers=headers,
                                 method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=12) as res:
        return res.status, res.headers.get("Content-Type", ""), res.read(2_100_000)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--camera-url", required=True, help="http://IP_TELEFONO:8080/video")
    p.add_argument("--camera-id", required=True)
    p.add_argument("--server", default="https://nexus-production-6562.up.railway.app")
    a = p.parse_args()
    UUID(a.camera_id)
    server = urlsplit(a.server)
    if server.scheme != "https" and not (server.scheme == "http" and server.hostname in ("localhost", "127.0.0.1", "::1")):
        p.error("Railway requiere HTTPS")
    source = urlsplit(a.camera_url)
    if source.scheme not in ("http", "https") or not source.hostname:
        p.error("IP Webcam requiere una URL HTTP válida")
    port = source.port or (443 if source.scheme == "https" else 80)
    stream = a.camera_url if source.path not in ("", "/") else urlunsplit((source.scheme, source.netloc, "/video", "", ""))
    base = a.server.rstrip("/")
    print("[1/5] Probando conexión TCP con el teléfono...", flush=True)
    try:
        with socket.create_connection((source.hostname, port), timeout=5):
            pass
    except ConnectionRefusedError:
        print("FALLO: puerto rechazado. Inicia IP Webcam y comprueba el puerto.")
        return 2
    except socket.timeout:
        print("FALLO: timeout. Comprueba Wi-Fi y aislamiento de clientes.")
        return 2
    except OSError as exc:
        print("FALLO: red local:", type(exc).__name__, str(exc))
        return 2
    print("[2/5] Comprobando OpenCV y lectura de un fotograma...", flush=True)
    cap = None
    try:
        try:
            cap = cv2.VideoCapture(stream, cv2.CAP_FFMPEG,
                                   [cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000,
                                    cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000])
        except (TypeError, cv2.error):
            cap = cv2.VideoCapture(stream)
        if not cap.isOpened():
            print("FALLO: OpenCV no abre /video. Revisa la ruta y el servidor IP Webcam.")
            return 3
        ok, frame = cap.read()
        if not ok or frame is None or frame.size == 0:
            print("FALLO: TCP accesible pero no hay fotogramas decodificables.")
            return 3
        print("OK: fotograma real", frame.shape[1], "x", frame.shape[0], flush=True)
        ok, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 65])
        if not ok or jpeg.nbytes > 2_000_000:
            print("FALLO: JPEG supera 2 MB o no se pudo codificar.")
            return 3
    finally:
        if cap is not None:
            cap.release()
    print("[3/5] Comprobando cámara registrada en Railway...", flush=True)
    try:
        status, _, body = request(base + "/api/cameras")
        cameras = json.loads(body)
        if not any(str(c.get("id")) == a.camera_id for c in cameras):
            print("FALLO: ID de cámara no registrado en Railway.")
            return 4
        print("[4/5] Enviando JPEG real a Railway...", flush=True)
        status, _, body = request(base + "/api/cameras/" + a.camera_id + "/frame", jpeg.tobytes())
        receipt = json.loads(body)
        if status != 200 or receipt.get("status") != "received":
            print("FALLO: respuesta de carga inesperada:", receipt)
            return 4
        print("[5/5] Recuperando el mismo fotograma del servidor...", flush=True)
        status, content_type, downloaded = request(base + "/api/cameras/" + a.camera_id + "/frame")
        if status != 200 or not content_type.startswith("image/jpeg") or not downloaded.startswith(bytes((255, 216))):
            print("FALLO: el backend no devuelve un JPEG válido.")
            return 5
        print("ÉXITO: teléfono -> OpenCV -> Railway -> JPEG recuperado.", flush=True)
        print("Si el dashboard continúa sin señal, revisar JavaScript, caché y refresco.")
        return 0
    except urllib.error.HTTPError as exc:
        print("FALLO HTTP Railway:", exc.code, exc.read(500).decode("utf-8", "replace"))
        return 4
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        print("FALLO de conexión o respuesta Railway:", type(exc).__name__, str(exc))
        return 4


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("Prueba interrumpida.")
        sys.exit(130)
