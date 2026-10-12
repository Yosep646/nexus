"""Unit checks for the OpenCV LAN capture manager; no physical camera required."""
import os
import time
from unittest.mock import patch
import numpy as np
from backend.cameras.lan_manager import CameraManager, Worker

def test_latest_rejects_stale_frames():
    manager = CameraManager()
    worker = Worker(camera_id="cam-1", url="http://192.168.1.50:8080/video")
    worker.jpeg = b"jpeg"
    worker.last_frame = time.monotonic() - 20
    worker.state = "connected"
    manager.workers[worker.camera_id] = worker
    assert manager.latest(worker.camera_id) is None
    assert manager.status(worker.camera_id)["state"] == "stale"

def test_latest_returns_recent_frame():
    manager = CameraManager()
    worker = Worker(camera_id="cam-1", url="http://192.168.1.50:8080/video")
    worker.jpeg = b"jpeg"
    worker.last_frame = time.monotonic()
    worker.state = "connected"
    manager.workers[worker.camera_id] = worker
    assert manager.latest(worker.camera_id) == b"jpeg"
    assert manager.status(worker.camera_id)["state"] == "connected"

def test_worker_reconnects_after_capture_failure():
    manager = CameraManager()
    worker = Worker(camera_id="cam-2", url="http://192.168.1.51:8080/video")
    class FailingCapture:
        def isOpened(self): return False
        def release(self): worker.stop.set()
    with patch("backend.cameras.lan_manager.cv2.VideoCapture", return_value=FailingCapture()):
        manager._capture(worker)
    assert worker.state == "reconnecting"
    assert "No se pudo abrir" in worker.error
