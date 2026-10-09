"""Inspect dataset structure and reject missing or undersized classes."""
import argparse
import json
from pathlib import Path

LABELS = {"deslizamiento_de_tierra", "huayco", "inundacion", "normal", "sequia"}
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def validate(root: Path, min_images: int = 20):
    if not root.is_dir():
        raise ValueError("Dataset directory does not exist")
    folders = {path.name for path in root.iterdir() if path.is_dir()}
    if folders != LABELS:
        raise ValueError("Expected folders: " + ", ".join(sorted(LABELS)))
    counts = {}
    for label in sorted(LABELS):
        images = [p for p in (root / label).rglob("*") if p.is_file() and p.suffix.lower() in EXTENSIONS]
        counts[label] = len(images)
        if len(images) < min_images:
            raise ValueError(f"{label}: {len(images)} images; minimum {min_images}")
    return {"valid": True, "images_per_class": counts, "total": sum(counts.values())}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--min-images", type=int, default=20)
    args = parser.parse_args()
    if args.min_images < 1:
        parser.error("min-images must be positive")
    try:
        print(json.dumps(validate(args.dataset, args.min_images), ensure_ascii=False, indent=2))
    except ValueError as exc:
        parser.error(str(exc))

if __name__ == "__main__":
    main()
