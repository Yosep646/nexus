from pathlib import Path
import pytest
from training.validate_dataset import validate, LABELS

def test_rejects_missing_categories(tmp_path):
    (tmp_path / "huayco").mkdir()
    with pytest.raises(ValueError, match="Expected folders"):
        validate(tmp_path)

def test_rejects_small_classes(tmp_path):
    for label in LABELS:
        (tmp_path / label).mkdir()
    with pytest.raises(ValueError, match="minimum"):
        validate(tmp_path)

def test_validates_class_counts(tmp_path):
    for label in LABELS:
        folder = tmp_path / label
        folder.mkdir()
        (folder / "sample.jpg").write_bytes(b"placeholder")
    result = validate(tmp_path, min_images=1)
    assert result["total"] == 5
    assert result["valid"] is True
