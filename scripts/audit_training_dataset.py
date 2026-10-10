"""Audit a labeled disaster-image dataset before training. No fabricated samples."""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from PIL import Image, UnidentifiedImageError

LABELS = ("deslizamiento_de_tierra", "huayco", "inundacion", "normal", "sequia")
EXTS = {".jpg", ".jpeg", ".png", ".webp"}

def audit(root: Path):
    counts = Counter()
    corrupt = []
    duplicates = []
    too_small = []
    hashes = {}
    examples = defaultdict(list)
    for label in LABELS:
        folder = root / label
        if not folder.is_dir():
            continue
        for path in sorted(folder.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in EXTS:
                continue
            try:
                with Image.open(path) as im:
                    im.verify()
                with Image.open(path) as im:
                    width, height = im.size
                if min(width, height) < 224:
                    too_small.append(str(path))
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                if digest in hashes:
                    duplicates.append({"file": str(path), "original": hashes[digest]})
                else:
                    hashes[digest] = str(path)
                    counts[label] += 1
                    examples[label].append(str(path))
            except (OSError, ValueError, UnidentifiedImageError):
                corrupt.append(str(path))
    total = sum(counts.values())
    min_count = min((counts[x] for x in LABELS), default=0)
    report = {
        "total_unique_valid_images": total,
        "images_per_class": {x: counts[x] for x in LABELS},
        "missing_classes": [x for x in LABELS if counts[x] == 0],
        "corrupt_images": corrupt,
        "exact_duplicates": duplicates,
        "images_smaller_than_224px": too_small,
        "minimum_class_count": min_count,
        "ready_for_training": all(counts[x] >= 30 for x in LABELS),
        "note": "30 images/class is only a pipeline minimum, not a quality or accuracy guarantee. Use independent real-world test sets, and group frames from the same video/event before splitting."
    }
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("dataset"))
    parser.add_argument("--output", type=Path, default=Path("data/dataset_audit.json"))
    args = parser.parse_args()
    result = audit(args.data)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["ready_for_training"]:
        raise SystemExit("Dataset insufficient: collect and label real photographs before retraining.")
