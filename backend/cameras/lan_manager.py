"""LAN-only OpenCV capture manager. One independent worker per camera.
Enable with NEXUS_LAN_MODE=true only on a trusted LAN host; never on Railway.
"""
import os
import threading
import time
from dataclasses import dataclass, field
from urllib.parse import urlparse
import cv2
from backend.database import storage

def enabled():
    return os.getenv("NEXUS_LAN_MODE", "false").lower() == "true"

@dataclass
class Worker:
    camera_id: str
    url: str
    stop: threading.Event = field(default_factory=threading.Event)
    lock: threading.Lock = field(default_factory=threading.Lock)
    jpeg: bytes | None = None
    last_frame: float = 0
    state: str = "connecting"
    error: str = ""
    thread: threading.Thread | None = None

class CameraManager:
    def __init__(self):
        self.lock = threading.RLock()
        self.workers: dict[str, Worker] = {}

    def start(self, camera):
        if not enabled():
            return
        with self.lock:
            if camera["id"] in self.workers:
                return
            worker = Worker(camera_id=camera["id"], url=camera["url"])
            self.workers[camera["id"]] = worker
            worker.thread = threading.Thread(target=self._capture, args=(worker,), daemon=True, name="nexus-camera-"+camera["id"][:8])
            worker.thread.start()

    def remove(self, camera_id):
        with self.lock:
            worker = self.workers.pop(camera_id, None)
        if worker:
            worker.stop.set()
            if worker.thread and worker.thread is not threading.current_thread():
                worker.thread.join(timeout=2)

    def shutdown(self):
        with self.lock:
            ids = list(self.workers)
        for camera_id in ids:
            self.remove(camera_id)

    def status(self, camera_id):
        with self.lock:
            worker = self.workers.get(camera_id)
        if not worker:
            return {"state": "not_running", "last_frame_age": None}
        with worker.lock:
            age = round(time.monotonic()-worker.last_frame, 2) if worker.last_frame else None
            return {"state": worker.state if age is None or age <= 8 else "stale", "last_frame_age": age, "error": worker.error}

    def latest(self, camera_id):
        with self.lock:
            worker = self.workers.get(camera_id)
        if not worker:
            return None
        with worker.lock:
            if worker.last_frame and time.monotonic()-worker.last_frame <= 8:
                return worker.jpeg
            return None

    def _capture(self, worker):
        while not worker.stop.is_set():
            cap = None
            try:
                params = [cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 6000, cv2.CAP_PROP_READ_TIMEOUT_MSEC, 6000]
                try:
                    cap = cv2.VideoCapture(worker.url, cv2.CAP_FFMPEG, params)
                except (cv2.error, TypeError):
                    cap = cv2.VideoCapture(worker.url, cv2.CAP_FFMPEG)
                if not cap.isOpened():
                    cap.release()
                    cap = cv2.VideoCapture(worker.url, cv2.CAP_ANY)
                if not cap.isOpened():
                    raise ConnectionError("No se pudo abrir la fuente: verifica IP, puerto, protocolo y credenciales")
                with worker.lock:
                    worker.state, worker.error = "connected", ""
                while not worker.stop.is_set():
                    ok, frame = cap.read()
                    if not ok or frame is None:
                        raise ConnectionError("La fuente dejó de enviar fotogramas")
                    height, width = frame.shape[:2]
                    if width > 960:
                        frame = cv2.resize(frame, (960, max(1, round(height*960/width))))
                    valid, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 72])
                    if valid:
                        with worker.lock:
                            worker.jpeg = encoded.tobytes()
                            worker.last_frame = time.monotonic()
                            worker.state = "connected"
                    worker.stop.wait(0.08)
            except Exception as exc:
                with worker.lock:
                    worker.state, worker.error = "reconnecting", str(exc)[:180]
            finally:
                if cap is not None:
                    cap.release()
            worker.stop.wait(3)

manager = CameraManager()

def startup():
    if enabled():
        for camera in storage.list_cameras():
            manager.start(camera)

def probe(url):
    """Probe on the local backend host before registration, never from Railway."""
    from backend.cameras.registry import _validate_url
    _validate_url(url)
    try:
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG, [
            cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000, cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000
        ])
    except (cv2.error, TypeError):
        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    try:
        if not cap.isOpened():
            return False, "IP/puerto/protocolo inaccesible o autenticación rechazada"
        ok, frame = cap.read()
        if not ok or frame is None:
            return False, "Conectó, pero no se recibieron fotogramas"
        return True, "Fotograma real recibido mediante OpenCV"
    finally:
        cap.release()
