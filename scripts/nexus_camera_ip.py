"""Interactive Windows entry point for NEXUS IP Webcam bridge.
Build with scripts/build_camera_bridge.ps1 on Windows.
"""
import json
import runpy
import sys
import urllib.request
from pathlib import Path

SERVER = "https://nexus-production-6562.up.railway.app"


def main():
    print("NEXUS RISK AI | IP Webcam -> Railway", flush=True)
    server = input(f"Servidor [{SERVER}]: ").strip() or SERVER
    try:
        with urllib.request.urlopen(server.rstrip("/") + "/api/cameras", timeout=15) as response:
            cameras = json.load(response)
        if not cameras:
            print("No hay cámaras registradas. Registra una en el dashboard.")
            return 2
        for i, camera in enumerate(cameras):
            print(f"[{i}] {camera.get('name', 'Camara')} | {camera['id']}")
        selection = input("Número de cámara [0]: ").strip() or "0"
        index = int(selection)
        if index < 0 or index >= len(cameras):
            raise ValueError("Selección fuera de rango")
        camera = cameras[index]
        default_url = camera.get("url") or "http://192.168.1.50:8080/video"
        url = input(f"URL IP Webcam [{default_url}]: ").strip() or default_url
        import camera_bridge
        sys.argv = ["camera_bridge", "--camera-url", url,
                    "--camera-id", str(camera["id"]), "--server", server, "--fps", "2"]
        return camera_bridge.main()
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR de inicio: {type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("Puente detenido.")
        sys.exit(0)
