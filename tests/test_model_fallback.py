import json
from backend.detection import model


def test_bad_metadata_disables_inference_without_crashing(tmp_path, monkeypatch):
    metadata = tmp_path / "metadata.json"
    metadata.write_text(json.dumps({"labels": ["normal"] * 5}), encoding="utf-8")
    monkeypatch.setattr(model, "METADATA", metadata)
    monkeypatch.setattr(model, "KERAS_MODEL", tmp_path / "model.keras")
    monkeypatch.setattr(model, "MODEL_DIR", tmp_path)
    detector = model.Detector()
    assert not detector.ready


def test_unconverted_tfjs_export_is_not_marked_ready(tmp_path, monkeypatch):
    (tmp_path / "model.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(model, "METADATA", tmp_path / "missing.json")
    monkeypatch.setattr(model, "KERAS_MODEL", tmp_path / "missing.keras")
    monkeypatch.setattr(model, "MODEL_DIR", tmp_path)
    assert not model.Detector().ready
