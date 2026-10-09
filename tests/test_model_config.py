from pathlib import Path


def test_default_model_path_exists_as_configuration():
    from backend.detection.model import KERAS_MODEL, METADATA
    assert isinstance(KERAS_MODEL, Path)
    assert isinstance(METADATA, Path)


def test_missing_model_does_not_claim_readiness():
    from backend.detection.model import detector
    if not detector.ready:
        assert detector.predict(None)["status"] == "model_unavailable"
