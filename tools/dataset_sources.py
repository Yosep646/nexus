"""Inspect external dataset source manifest without downloading unreviewed content."""
import argparse
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("datasets/sources.json"))
    parser.add_argument("--dataset", type=Path, default=Path("dataset"))
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    print("Fuentes verificadas (sin descarga automática):")
    for src in data["sources"]:
        print(f"- {src['title']} | {src['modality']} | {src['license']} | {src['download_page']}")
        print(f"  Estado: {src['import_status']}")
    print("\nImágenes locales existentes:")
    for label in ["huayco", "inundacion", "deslizamiento de tierra", "sequia", "normal"]:
        folder = args.dataset / label
        n = sum(1 for p in folder.rglob("*") if p.is_file() and p.suffix.lower() in {".jpg",".jpeg",".png",".webp"}) if folder.exists() else 0
        print(f"{label}: {n} / 1000 (meta orientativa, no requisito)")
    print("\nNo se importaron ni se etiquetaron imágenes automáticamente. Revisar licencias y modalidades antes de entrenar.")

if __name__ == "__main__":
    main()
