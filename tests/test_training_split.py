"""Offline tests for leakage-resistant grouped dataset splitting."""
import tempfile
import unittest
from pathlib import Path
from tools.train_camera_classifier import discover, split_groups

class DatasetSplitTests(unittest.TestCase):
    def test_group_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for label in ("huayco", "normal"):
                for event in range(10):
                    folder = root / label / f"event_{event:02d}"
                    folder.mkdir(parents=True)
                    for frame in range(3):
                        (folder / f"frame_{frame}.jpg").write_bytes(b"fake")
            labels, items = discover(root)
            self.assertEqual(labels, ["huayco", "normal"])
            splits = split_groups(items)
            seen = {}
            for name, rows in splits.items():
                for path, label in rows:
                    event = Path(path).parent.name
                    group = (label, event)
                    self.assertNotIn(group, seen) if group not in seen else self.assertEqual(seen[group], name)
                    seen[group] = name
            self.assertEqual(len(seen), 20)
            self.assertEqual(sum(len(rows) for rows in splits.values()), 60)

    def test_rejects_too_few_groups(self):
        with self.assertRaisesRegex(ValueError, "at least 5"):
            split_groups([("one.jpg", "normal", "normal/single")])

if __name__ == "__main__":
    unittest.main()
