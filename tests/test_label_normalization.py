import pytest
from backend.detection.labels import normalize_labels


def test_known_typo_aliases_preserve_order():
    labels = ["dezlizamiento de tierra", "huayco", "innundacion", "normal", "sequía"]
    assert normalize_labels(labels) == [
        "deslizamiento de tierra", "huayco", "inundacion", "normal", "sequia"
    ]


def test_reject_duplicated_or_unknown_classes():
    with pytest.raises(ValueError):
        normalize_labels(["normal"] * 5)
    with pytest.raises(ValueError):
        normalize_labels(["normal", "huayco", "inundacion", "sequia", "fuego"])
