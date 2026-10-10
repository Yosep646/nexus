"""Offline dataset audit for environmental image classification.

Expected layout: dataset/<class_name>/<image files>. Reports duplicate hashes,
unreadable images, class imbalance and image sizes. Never invents training metrics.
"""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
import cv2

EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

def audit(root: Path):
    if not root.is_dir():
        raise ValueError(f"Dataset directory not found: {root}")
    counts = Counter()
    invalid = []
    duplicate_groups = defaultdict(list)
    dimensions = Counter()
    for folder in sorted(p for p in root.iterdir() if p.is_dir()):
        for path in sorted(folder.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
                continue
            try:
                raw = path.read_bytes()
                img = cv2.imdecode(__import__("numpy").frombuffer(raw, dtype="uint8"), cv2.IMREAD_COLOR)
                if img is None:
                    invalid.append(str(path))
                    continue
                counts[folder.name] += 1
                dimensions[f"{img.shape[1]}x{img.shape[0]}"] += 1
                duplicate_groups[hashlib.sha256(raw).hexdigest()].append(str(path))
            except (OSError, cv2.error, ValueError):
                invalid.append(str(path))
    duplicates = [paths for paths in duplicate_groups.values() if len(paths) > 1]
    maximum = max(counts.values(), default=0)
    return {
        "counts_per_class": dict(counts),
        "total_valid": sum(counts.values()),
        "unreadable_files": invalid,
        "exact_duplicate_groups": duplicates,
        "dimensions": dict(dimensions),
        "class_balance_relative_to_largest": {key: round(n / maximum, 3) for key, n in counts.items()} if maximum else {},
        "warnings": [
            *([ "No valid labeled images found" ] if not counts else []),
            *([ "Class imbalance: some classes have fewer than half the examples of the largest class" ] if any(n < maximum / 2 for n in counts.values()) else []),
            *([ "Exact duplicate images found; remove cross-split leakage before evaluating" ] if duplicates else []),
        ],
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--output", type=Path, default=Path("dataset_audit.json"))
    args = parser.parse_args()
    report = audit(args.dataset)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
