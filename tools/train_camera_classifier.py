"""Train an RGB camera-scene classifier offline; never generate synthetic performance scores.

Dataset layout: dataset/<class>/<event_or_camera_group>/*.jpg.
Images directly in a class folder are treated as independent groups; for video
frames always put frames from the same recording in the same group directory.
Requires: pip install tensorflow pillow
"""
import argparse
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
SEED = 42

def discover(root):
    if not root.is_dir():
        raise ValueError(f"Dataset directory missing: {root}")
    labels = sorted(p.name for p in root.iterdir() if p.is_dir())
    if len(labels) < 2:
        raise ValueError("At least two class directories are required")
    items = []
    for label in labels:
        folder = root / label
        for path in sorted(folder.rglob("*")):
            if path.is_file() and path.suffix.lower() in EXTENSIONS:
                rel = path.relative_to(folder)
                group = rel.parts[0] if len(rel.parts) > 1 else path.stem
                items.append((str(path), label, label + "/" + group))
    return labels, items

def split_groups(items):
    """Deterministic group split; fail when there are too few independent groups."""
    groups = {}
    for path, label, group in items:
        groups.setdefault(label, {}).setdefault(group, []).append((path, label))
    result = {"train": [], "val": [], "test": []}
    for label, group_map in groups.items():
        keys = sorted(group_map, key=lambda k: hashlib.sha256((str(SEED) + k).encode()).hexdigest())
        if len(keys) < 5:
            raise ValueError(f"{label}: at least 5 independent camera/event groups required, found {len(keys)}")
        n = len(keys)
        n_test = max(1, round(n * .15))
        n_val = max(1, round(n * .15))
        for i, key in enumerate(keys):
            split = "test" if i < n_test else "val" if i < n_test + n_val else "train"
            result[split].extend(group_map[key])
    return result

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", type=Path, default=Path("dataset"))
    p.add_argument("--output", type=Path, default=Path("models/teachable_machine"))
    p.add_argument("--epochs", type=int, default=12)
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--min-images-per-class", type=int, default=100)
    args = p.parse_args()
    if args.epochs < 1 or args.batch_size < 1:
        p.error("epochs and batch-size must be positive")
    labels, items = discover(args.dataset)
    counts = Counter(label for _, label, _ in items)
    for label in labels:
        if counts[label] < args.min_images_per_class:
            raise ValueError(f"{label}: {counts[label]} images, minimum {args.min_images_per_class}; do not fabricate samples")
    splits = split_groups(items)
    if any(not splits[k] for k in splits):
        raise ValueError("All train/val/test splits must contain examples")
    import tensorflow as tf
    import numpy as np
    tf.keras.utils.set_random_seed(SEED)
    tf.config.experimental.enable_op_determinism()
    index = {name: i for i, name in enumerate(labels)}

    def dataset(rows, shuffle=False):
        paths = [p for p, _ in rows]
        targets = [index[label] for _, label in rows]
        ds = tf.data.Dataset.from_tensor_slices((paths, targets))
        if shuffle:
            ds = ds.shuffle(len(rows), seed=SEED, reshuffle_each_iteration=True)
        def decode(path, target):
            raw = tf.io.read_file(path)
            img = tf.io.decode_image(raw, channels=3, expand_animations=False)
            img.set_shape((None, None, 3))
            img = tf.image.resize(img, (224, 224))
            img = tf.cast(img, tf.float32) / 127.5 - 1.0
            return img, target
        return ds.map(decode, num_parallel_calls=tf.data.AUTOTUNE).batch(args.batch_size).prefetch(tf.data.AUTOTUNE)

    train, val, test = (dataset(splits[k], shuffle=(k == "train")) for k in ("train", "val", "test"))
    base = tf.keras.applications.MobileNetV2(input_shape=(224, 224, 3), include_top=False, weights="imagenet")
    base.trainable = False
    inputs = tf.keras.Input(shape=(224, 224, 3))
    x = tf.keras.layers.RandomFlip("horizontal")(inputs)
    x = tf.keras.layers.RandomRotation(.05)(x)
    x = base(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(.3)(x)
    outputs = tf.keras.layers.Dense(len(labels), activation="softmax")(x)
    model = tf.keras.Model(inputs, outputs)
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
                  loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    callbacks = [tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=4, restore_best_weights=True)]
    model.fit(train, validation_data=val, epochs=args.epochs, callbacks=callbacks)
    scores = model.predict(test, verbose=0)
    y_true = np.concatenate([y.numpy() for _, y in test])
    y_pred = np.argmax(scores, axis=1)
    confusion = np.zeros((len(labels), len(labels)), dtype=int)
    for true, pred in zip(y_true, y_pred):
        confusion[int(true), int(pred)] += 1
    per_class = {}
    for i, label in enumerate(labels):
        tp = int(confusion[i, i])
        precision = tp / max(1, int(confusion[:, i].sum()))
        recall = tp / max(1, int(confusion[i, :].sum()))
        per_class[label] = {"precision": round(precision, 4), "recall": round(recall, 4),
                            "f1": round(2 * precision * recall / (precision + recall), 4) if precision + recall else 0}
    args.output.mkdir(parents=True, exist_ok=True)
    model.save(args.output / "model.keras")
    (args.output / "metadata.json").write_text(json.dumps({
        "labels": labels, "preprocessing": "external_minus_one_to_one",
        "training_source": "local_camera_rgb", "input_size": [224, 224],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    report = {"seed": SEED, "class_counts": dict(counts),
              "split_counts": {k: len(v) for k, v in splits.items()},
              "confusion_matrix": confusion.tolist(), "per_class": per_class,
              "test_accuracy": round(float(np.mean(y_true == y_pred)), 4),
              "notes": "Results only apply to held-out grouped dataset; field performance must be validated separately."}
    (args.output / "evaluation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
