"""Regression checks: cloud mode must never open a private IP stream."""
import asyncio
from unittest.mock import patch
from fastapi import HTTPException
import pytest

from backend.api import routes
from backend.detection import service


def test_cloud_stream_is_not_a_private_ip_proxy():
    with patch("backend.cameras.lan_manager.enabled", return_value=False):
        with pytest.raises(HTTPException) as error:
            asyncio.run(routes.camera_stream("any-camera"))
    assert error.value.status_code == 409


def test_cloud_snapshot_requires_uploaded_frame():
    camera = {"id": "test-camera", "url": "http://192.168.1.5:8080/video"}
    with patch("backend.database.storage.get_camera", return_value=camera), \
         patch("backend.cameras.lan_manager.enabled", return_value=False), \
         patch.dict("os.environ", {"NEXUS_CAMERA_FRAMES_DIR": "/tmp/nexus-no-camera-frames-test"}):
        with pytest.raises(HTTPException) as error:
            asyncio.run(routes.camera_snapshot("test-camera"))
    assert error.value.status_code == 503


def test_cloud_inference_never_opens_private_ip_without_bridge():
    camera = {"id": "test-camera", "url": "http://192.168.1.5:8080/video"}
    fake_detector = type("FakeDetector", (), {"ready": True})()
    with patch.object(service, "get_camera", return_value=camera), \
         patch.object(service, "detector", fake_detector), \
         patch("backend.cameras.lan_manager.enabled", return_value=False), \
         patch.dict("os.environ", {"NEXUS_CAMERA_FRAMES_DIR": "/tmp/nexus-no-camera-frames-test"}), \
         patch.object(service.cv2, "VideoCapture", side_effect=AssertionError("Cloud IP access forbidden")):
        with pytest.raises(HTTPException) as error:
            asyncio.run(service.classify_camera("test-camera"))
    assert error.value.status_code == 503
