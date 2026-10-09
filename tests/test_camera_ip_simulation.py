"""Simulate a phone camera's MJPEG feed without requiring physical hardware."""
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import cv2
import numpy as np

from backend.detection.service import _capture_once


def test_simulated_phone_mjpeg_camera():
    image = np.zeros((120, 160, 3), dtype=np.uint8)
    image[:, :] = (40, 100, 190)
    success, encoded = cv2.imencode(".jpg", image)
    assert success
    jpeg = encoded.tobytes()

    class CameraHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != "/video":
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.end_headers()
            try:
                for _ in range(6):
                    self.wfile.write(
                        b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "
                        + str(len(jpeg)).encode() + b"\r\n\r\n" + jpeg + b"\r\n"
                    )
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), CameraHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        frame = _capture_once(f"http://127.0.0.1:{server.server_port}/video")
        assert frame is not None
        assert frame.shape == (120, 160, 3)
        assert abs(float(frame[:, :, 2].mean()) - 190) < 12
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
