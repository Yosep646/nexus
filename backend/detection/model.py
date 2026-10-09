"""Load an exported Teachable Machine TensorFlow.js image model using tfjs conversion.
Model inference is optional until converted weights are installed locally.
"""
from pathlib import Path
import json
import numpy as np

LABELS = ["deslizamiento de tierra", "huayco", "inundacion", "normal", "sequia"]
MODEL_DIR = Path(__file__).resolve().parents[2] / "models" / "teachable_machine"
KERAS_MODEL = MODEL_DIR / "model.keras"
METADATA = MODEL_DIR / "metadata.json"

class Detector:
    def __init__(self):
        self.model = None
        self.labels = LABELS
        if METADATA.exists():
            data = json.loads(METADATA.read_text(encoding="utf-8"))
            self.labels = data.get("labels", LABELS)
        if KERAS_MODEL.exists():
            import tensorflow as tf
            self.model = tf.keras.models.load_model(KERAS_MODEL, compile=False)

    @property
    def ready(self):
        return self.model is not None

    def predict(self, bgr_frame):
        if not self.ready:
            return {"status": "model_unavailable", "predictions": []}
        import cv2
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, (224, 224), interpolation=cv2.INTER_AREA)
        # Teachable Machine image models commonly use [-1, 1] normalization.
        batch = (np.asarray(rgb, dtype=np.float32) / 127.5 - 1.0)[None, ...]
        scores = np.asarray(self.model.predict(batch, verbose=0))[0]
        results = sorted(({"label": label, "confidence": float(score)}
                          for label, score in zip(self.labels, scores)), key=lambda x: -x["confidence"])
        return {"status": "ok", "predictions": results}

detector = Detector()
