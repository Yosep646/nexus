"""Canonical class names; preserves model output index order."""
import unicodedata

CANONICAL = ("deslizamiento de tierra", "huayco", "inundacion", "normal", "sequia")


def normalize_label(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("Class label must be a string")
    value = " ".join(value.strip().lower().replace("_", " ").split())
    value = "".join(ch for ch in unicodedata.normalize("NFKD", value)
                    if not unicodedata.combining(ch))
    aliases = {
        "dezlizamiento de tierra": "deslizamiento de tierra",
        "deslizamiento de tierras": "deslizamiento de tierra",
        "innundacion": "inundacion",
        "inundaciones": "inundacion",
        "sequia": "sequia",
        "huayco": "huayco",
        "normal": "normal",
        "deslizamiento de tierra": "deslizamiento de tierra",
        "inundacion": "inundacion",
    }
    if value not in aliases:
        raise ValueError("Unknown model class: " + value)
    return aliases[value]


def normalize_labels(labels):
    result = [normalize_label(label) for label in labels]
    if len(result) != len(CANONICAL) or set(result) != set(CANONICAL):
        raise ValueError("Model must have exactly five unique supported classes")
    return result
