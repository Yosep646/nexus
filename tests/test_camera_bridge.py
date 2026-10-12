"""Bridge regression tests: local capture encoding and cloud authentication preflight."""
import json
import sys
import urllib.error
from unittest.mock import patch
from uuid import uuid4

import numpy as np
import pytest

from scripts import camera_bridge


def test_bridge_jpeg_size_and_dimensions():
    frame = np.zeros((720, 1600, 3), dtype=np.uint8)
    jpeg = camera_bridge.encode_frame(frame)
    assert jpeg.startswith(b"\\xff\\xd8")
    assert jpeg.endswith(b"\\xff\\xd9")
    assert len(jpeg) <= 2_000_000


def test_bridge_rejects_missing_api_key(monkeypatch):
    monkeypatch.delenv("NEXUS_API_KEY", raising=False)
    monkeypatch.setattr(sys, "argv", ["camera_bridge.py", "--camera-url",
                                     "http://192.168.1.2:8080/video",
                                     "--camera-id", str(uuid4())])
    with pytest.raises(SystemExit) as error:
        camera_bridge.main()
    assert error.value.code == 2


def test_bridge_rejects_non_https_server(monkeypatch):
    monkeypatch.setenv("NEXUS_API_KEY", "test-secret-only")
    monkeypatch.setattr(sys, "argv", ["camera_bridge.py", "--camera-url",
                                     "http://192.168.1.2:8080/video",
                                     "--camera-id", str(uuid4()),
                                     "--server", "http://railway.example"])
    with pytest.raises(SystemExit) as error:
        camera_bridge.main()
    assert error.value.code == 2


def test_bridge_preflight_rejects_unknown_camera(monkeypatch):
    monkeypatch.setenv("NEXUS_API_KEY", "test-secret-only")
    monkeypatch.setattr(sys, "argv", ["camera_bridge.py", "--camera-url",
                                     "http://192.168.1.2:8080/video",
                                     "--camera-id", str(uuid4())])
    class FakeResponse:
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def read(self, *_): return b"[]"
    with patch.object(camera_bridge, "api_request", return_value=FakeResponse()), \\
         patch.object(camera_bridge, "open_camera", side_effect=AssertionError("must not open")):
        assert camera_bridge.main() == 2
