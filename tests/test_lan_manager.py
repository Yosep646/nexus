"""Unit tests use synthetic in-memory frames only; no claim of physical camera validation."""
import threading
import time
from unittest.mock import patch
import numpy as np
from backend.cameras.lan_manager import CameraManager, probe

class FakeCapture:
    def __init__(self, *args, **kwargs):
        self.open = True
        self.calls = 0
    def isOpened(self): return self.open
    def read(self):
        self.calls += 1
        return True, np.zeros((32, 48, 3), dtype=np.uint8)
    def release(self): self.open = False

def test_probe_accepts_real_decoded_frame_from_capture():
    with patch("backend.cameras.lan_manager.cv2.VideoCapture", side_effect=lambda *args: FakeCapture()):
        ok, msg = probe("http://192.168.0.16:8080/video")
        assert ok and "OpenCV" in msg

def test_two_workers_isolated_and_hot_removed(monkeypatch):
    monkeypatch.setenv("NEXUS_LAN_MODE", "true")
    manager = CameraManager()
    with patch("backend.cameras.lan_manager.cv2.VideoCapture", side_effect=lambda *args: FakeCapture()):
        manager.start({"id":"a","url":"http://192.168.0.16:8080/video"})
        manager.start({"id":"b","url":"http://192.168.0.17:8080/video"})
        until = time.monotonic() + 3
        while time.monotonic() < until and not (manager.latest("a") and manager.latest("b")):
            time.sleep(0.03)
        assert manager.latest("a") and manager.latest("b")
        manager.remove("a")
        assert manager.latest("a") is None
        assert manager.latest("b") is not None
        manager.shutdown()
