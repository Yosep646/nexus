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
    while True:
        try:
            with urllib.request.urlopen(url, timeout=12) as stream:
                buffer = bytearray()
                last_sent = 0
                while True:
                    chunk = stream.read(8192)
                    if not chunk:
                        raise ConnectionError("La camara cerro la conexion")
                    buffer.extend(chunk)
                    start = buffer.find(bytes((255,216)))
                    if start < 0:
                        buffer.clear()
                        continue
                    if start:
                        del buffer[:start]
                    end = buffer.find(bytes((255,217)), 2)
                    if end < 0:
                        if len(buffer) > MAX_FRAME:
                            buffer.clear()
                        continue
                    frame = bytes(buffer[:end+2])
                    del buffer[:end+2]
                    if len(frame) > MAX_FRAME or time.monotonic()-last_sent < 0.8:
                        continue
                    try:
                        with request(endpoint, key, frame) as result:
                            if result.status != 200:
                                print("Error de envio HTTP", result.status)
                        last_sent = time.monotonic()
                        print("Fotograma enviado:", time.strftime("%H:%M:%S"), end="\\r", flush=True)
                    except urllib.error.HTTPError as error:
                        print("\\nServidor rechazo el fotograma:", error.code, error.read(200).decode("utf-8", "replace"))
                        if error.code in (401,403,404):
                            return 1
                    except Exception as error:
                        print("\\nProblema de red:", error)
        except KeyboardInterrupt:
            print("\\nPuente detenido.")
            return 0
        except Exception as error:
            print("\\nNo se pudo leer la camara IP:", error, "| reintentando en 5 s")
            time.sleep(5)

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(0)
