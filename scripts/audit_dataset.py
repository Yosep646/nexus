"""Audit an image-classification dataset before training. Standard library only.
Layout: dataset/<class_name>/*.{jpg,jpeg,png,webp}; no images are copied or modified.
"""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

EXT={".jpg",".jpeg",".png",".webp"}
def audit(root):
    root=Path(root)
    if not root.is_dir(): raise SystemExit(f"Dataset directory missing: {root}")
    counts=Counter(); duplicates=defaultdict(list); errors=[]
    for folder in sorted(p for p in root.iterdir() if p.is_dir()):
        for file in sorted(folder.rglob("*")):
            if not file.is_file() or file.suffix.lower() not in EXT: continue
            try:
                raw=file.read_bytes()
                if not raw: raise ValueError("empty file")
                digest=hashlib.sha256(raw).hexdigest()
                duplicates[digest].append(str(file))
                counts[folder.name]+=1
            except (OSError,ValueError) as exc: errors.append({"file":str(file),"error":str(exc)})
    groups=[paths for paths in duplicates.values() if len(paths)>1]
    total=sum(counts.values())
    warnings=[]
    if not counts: warnings.append("No images found")
    if counts and min(counts.values())<100: warnings.append("One or more classes have fewer than 100 images; investigate coverage (not a universal threshold)")
    if counts and max(counts.values())>3*max(1,min(counts.values())): warnings.append("Class imbalance greater than 3:1")
    if groups: warnings.append("Exact duplicate files detected; remove duplicates before splitting")
    if errors: warnings.append("Unreadable or empty files detected")
    return {"images_total":total,"by_class":dict(counts),"exact_duplicate_groups":groups[:50],
            "exact_duplicate_groups_total":len(groups),"errors":errors[:50],"warnings":warnings,
            "note":"Counts and SHA256 duplicates do not establish model accuracy, label quality, or near-duplicate leakage."}
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("dataset",help="Dataset root with one folder per class")
    parser.add_argument("--output",default=None,help="Optional JSON report path")
    args=parser.parse_args()
    result=audit(args.dataset)
    content=json.dumps(result,indent=2,ensure_ascii=False)
    print(content)
    if args.output: Path(args.output).write_text(content,encoding="utf-8")
