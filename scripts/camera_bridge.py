"""Bridge a LAN MJPEG camera to NEXUS Railway using authenticated outbound HTTPS JPEG frames.

Example:
 python scripts/camera_bridge.py --camera-url http://192.168.0.16:8080/video --camera-id UUID --server https://nexus-production-6562.up.railway.app
 Set NEXUS_API_KEY in your local environment. Never paste it into source code.
"""
import argparse
import os
import time
import urllib.request
import urllib.error
import cv2

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--camera-url", required=True)
    p.add_argument("--camera-id", required=True)
    p.add_argument("--server", default="https://nexus-production-6562.up.railway.app")
    p.add_argument("--fps", type=float, default=2)
    a=p.parse_args()
    key=os.environ.get("NEXUS_API_KEY")
    if not key: p.error("Set NEXUS_API_KEY environment variable")
    if not a.server.startswith("https://"): p.error("HTTPS server required")
    if not 0.2<=a.fps<=5: p.error("fps must be between 0.2 and 5")
    endpoint=a.server.rstrip("/")+"/api/cameras/"+a.camera_id+"/frame"
    delay=1/a.fps
    while True:
        # FFmpeg-first IP capture, as in the previous working project.
        cap=cv2.VideoCapture(a.camera_url, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            cap.release()
            cap=cv2.VideoCapture(a.camera_url, cv2.CAP_ANY)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        if not cap.isOpened():
            print("Camera unavailable; retrying in 5s",flush=True);cap.release();time.sleep(5);continue
        try:
            while True:
                start=time.monotonic()
                ok,frame=cap.read()
                if not ok or frame is None: break
                h,w=frame.shape[:2]
                if w>1280:
                    frame=cv2.resize(frame,(1280,round(h*1280/w)))
                success,encoded=cv2.imencode(".jpg",frame,[cv2.IMWRITE_JPEG_QUALITY,70])
                if success:
                    request=urllib.request.Request(endpoint,data=encoded.tobytes(),
                        headers={"X-API-Key":key,"Content-Type":"image/jpeg"},method="POST")
                    try:
                        with urllib.request.urlopen(request,timeout=10) as response:
                            if response.status!=200: print("Server status",response.status,flush=True)
                    except urllib.error.HTTPError as error:
                        print("Upload rejected:",error.code,flush=True)
                        if error.code in (401,403,404): return
                    except (urllib.error.URLError,TimeoutError) as error:
                        print("Upload error:",str(error),flush=True)
                time.sleep(max(0,delay-(time.monotonic()-start)))
        finally:
            cap.release()
        print("Camera disconnected; retrying in 5s",flush=True)
        time.sleep(5)

if __name__=="__main__":
    main()
