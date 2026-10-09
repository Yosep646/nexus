"""Explicit maintenance commands. Run only in a trusted private environment."""
import argparse
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from backend.database import storage
from backend.evidence.service import evidence_root


def backup_database(destination: Path):
    destination = destination.resolve()
    if destination == storage.DB_PATH.resolve():
        raise ValueError("Backup destination must differ from live database")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with storage.connect() as source, sqlite3.connect(str(destination)) as target:
        source.backup(target)
    return destination


def prune_evidence(days: int, dry_run: bool = True):
    """Delete old evidence files and metadata; keep detection and audit history."""
    if days < 1:
        raise ValueError("Retention must be at least one day")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    with storage.connect() as db:
        records = [dict(row) for row in db.execute(
            "SELECT id,detection_id,filename FROM evidence WHERE created_at < ?", (cutoff,))]
    if dry_run:
        return len(records)
    root = evidence_root()
    for item in records:
        path = root / item["detection_id"] / item["filename"]
        path.unlink(missing_ok=True)
        with storage.connect() as db:
            db.execute("DELETE FROM evidence WHERE id=?", (item["id"],))
    return len(records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--prune-days", type=int)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.backup:
        print("Backup:", backup_database(args.backup))
    if args.prune_days is not None:
        print("Evidence candidates:", prune_evidence(args.prune_days, dry_run=not args.apply))
