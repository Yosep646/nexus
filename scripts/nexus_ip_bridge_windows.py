"""NEXUS Windows camera bridge: standalone executable, no VS Code or Python required."""
import getpass
import json
import sys
import time
import urllib.error
import urllib.request

SERVER = "https://nexus-production-6562.up.railway.app"
MAX_FRAME = 2_000_000

def request(url, key, payload=None):
    headers = {"X-API-Key": key, "User-Agent": "NEXUS-IP-Bridge/1.0"}
    if payload is not None:
        headers["Content-Type"] = "image/jpeg"
    return urllib.request.urlopen(urllib.request.Request(url, data=payload, headers=headers, method="POST" if payload is not None else "GET"), timeout=15)

def main():
    print("NEXUS RISK AI | Puente seguro de camara IP para Windows")
    print("Conecta tu PC y camara IP a la misma red Wi-Fi.")
    key = getpass.getpass("API Key de Railway (no se almacena): ").strip()
    if not key:
        print("Necesitas una API Key.")
        return 1
    try:
        with request(SERVER + "/api/cameras", key) as response:
            cameras = json.load(response)
    except Exception as error:
        print("No se pudo autenticar o consultar camaras:", error)
        return 1
    if not cameras:
        print("Primero registra una camara IP en el dashboard de NEXUS.")
        return 1
    for i, camera in enumerate(cameras, 1):
        print(f"{i}. {camera['name']} | {camera['url']}")
    try:
        choice = int(input("Numero de camara: ").strip()) - 1
        camera = cameras[choice]
        if choice < 0:
            raise ValueError()
    except (ValueError, IndexError):
        print("Seleccion invalida.")
        return 1
    url = camera["url"]
    if not url.startswith("http://") and not url.startswith("https://"):
        print("Este puente admite fuentes MJPEG HTTP(S), no RTSP.")
        return 1
    endpoint = SERVER + "/api/cameras/" + camera["id"] + "/frame"
    print("Fuente:", url)
    print("Enviando imagenes por HTTPS. Para detener, cierra esta ventana o presiona Ctrl+C.")
    import cv2
    while True:
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            cap.release()
            cap = cv2.VideoCapture(url, cv2.CAP_ANY)
        if not cap.isOpened():
            print("No se pudo conectar con la IP; reintentando en 5 s")
            time.sleep(5)
            continue
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        try:
            last_sent = 0
            while True:
                ok, frame = cap.read()
                if not ok or frame is None:
                    print("La camara dejo de enviar imagenes; reconectando...")
                    break
                if time.monotonic() - last_sent < 0.8:
                    continue
                height, width = frame.shape[:2]
                if width > 960:
                    frame = cv2.resize(frame, (960, max(1, round(height * 960 / width))))
                encoded_ok, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 65])
                if not encoded_ok:
                    continue
                payload = encoded.tobytes()
                if len(payload) > MAX_FRAME:
                    print("Fotograma demasiado grande; omitido")
                    continue
                try:
                    with request(endpoint, key, payload) as result:
                        if result.status != 200:
                            print("Error de envio HTTP", result.status)
                    last_sent = time.monotonic()
                    print("Fotograma IP enviado:", time.strftime("%H:%M:%S"), flush=True)
                except urllib.error.HTTPError as error:
                    print("Servidor rechazo fotograma:", error.code)
                    if error.code in (401, 403, 404):
                        return 1
                except Exception as error:
                    print("Error de red al enviar:", error)
        except KeyboardInterrupt:
            print("Puente detenido.")
            return 0
        finally:
            cap.release()
        time.sleep(5)

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
