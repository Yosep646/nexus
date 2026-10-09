"""Evaluate a saved model on an independent, labeled test dataset."""
import argparse
import json
from pathlib import Path
import numpy as np

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", type=Path, default=Path("models/teachable_machine/model.keras"))
    p.add_argument("--test", type=Path, required=True)
    p.add_argument("--output", type=Path, default=Path("reports/model_evaluation.json"))
    args = p.parse_args()
    import tensorflow as tf
    model = tf.keras.models.load_model(args.model, compile=False)
    metadata = json.loads((args.model.parent / "metadata.json").read_text(encoding="utf-8"))
    labels = metadata["labels"]
    dataset = tf.keras.utils.image_dataset_from_directory(
        args.test, image_size=(224,224), batch_size=16, shuffle=False)
    if dataset.class_names != labels:
        raise ValueError(f"Class mismatch: test={dataset.class_names}, model={labels}")
    y_true, y_pred = [], []
    for images, targets in dataset:
        batch = images.numpy()
        if metadata.get("preprocessing") != "raw_0_255_pixels_model_rescaling":
            batch = batch / 127.5 - 1
        scores = model.predict(batch, verbose=0)
        y_true.extend(targets.numpy().tolist())
        y_pred.extend(np.argmax(scores, axis=1).tolist())
    n = len(labels)
    confusion = [[0] * n for _ in range(n)]
    for truth, prediction in zip(y_true, y_pred):
        confusion[truth][prediction] += 1
    metrics = {}
    for i, label in enumerate(labels):
        tp = confusion[i][i]
        fp = sum(confusion[j][i] for j in range(n) if j != i)
        fn = sum(confusion[i][j] for j in range(n) if j != i)
        precision = tp / (tp + fp) if tp + fp else 0
        recall = tp / (tp + fn) if tp + fn else 0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
        metrics[label] = {"precision":round(precision,4),"recall":round(recall,4),"f1":round(f1,4),"support":sum(confusion[i])}
    accuracy = sum(confusion[i][i] for i in range(n)) / len(y_true) if y_true else 0
    report = {"labels":labels,"samples":len(y_true),"accuracy":round(accuracy,4),
              "confusion_matrix":confusion,"by_class":metrics,
              "warning":"Independent field validation required before operational use"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__ == "__main__":
    main()
