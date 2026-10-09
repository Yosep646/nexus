"""Load an exported Teachable Machine TensorFlow.js image model using tfjs conversion.
Model inference is optional until converted weights are installed locally.
"""
from pathlib import Path
import json
import logging
import numpy as np

log = logging.getLogger(__name__)
from backend.detection.labels import normalize_labels

LABELS = ["deslizamiento de tierra", "huayco", "inundacion", "normal", "sequia"]
MODEL_DIR = Path(__file__).resolve().parents[2] / "models" / "teachable_machine"
KERAS_MODEL = MODEL_DIR / "model.keras"
METADATA = MODEL_DIR / "metadata.json"

class Detector:
    def __init__(self):
        self.model = None
        self.labels = normalize_labels(LABELS)
        self.preprocessing = 'external_minus_one_to_one'
        if METADATA.exists():
            try:
                data = json.loads(METADATA.read_text(encoding="utf-8"))
                self.labels = normalize_labels(data.get("labels", LABELS))
                self.preprocessing = data.get("preprocessing", "external_minus_one_to_one")
            except (ValueError, OSError, TypeError):
                log.exception("Invalid model metadata; inference disabled")
                return
        if KERAS_MODEL.exists():
            try:
                import tensorflow as tf
                self.model = tf.keras.models.load_model(KERAS_MODEL, compile=False)
            except (ImportError, ValueError, OSError):
                log.exception("Could not load Keras model; inference disabled")
        elif (MODEL_DIR / "model.json").exists():
            # A raw TensorFlow.js export is not a Keras model.
            # Keep inference unavailable instead of pretending weights are loaded.
            self.model = None

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
        batch = np.asarray(rgb, dtype=np.float32)
        if self.preprocessing != "raw_0_255_pixels_model_rescaling":
            batch = batch / 127.5 - 1.0
        batch = batch[None, ...]
        scores = np.asarray(self.model.predict(batch, verbose=0))[0]
        if scores.ndim != 1 or len(scores) != len(self.labels) or not np.all(np.isfinite(scores)):
            raise ValueError("Model output does not match configured labels")
        results = sorted(({"label": label, "confidence": float(score)}
                          for label, score in zip(self.labels, scores)), key=lambda x: -x["confidence"])
        return {"status": "ok", "predictions": results}

detector = Detector()
