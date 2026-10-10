"""Optional supervised fine-tuning; requires real, independently labeled images."""
import argparse
import json
from pathlib import Path

LABELS = ["deslizamiento_de_tierra", "huayco", "inundacion", "normal", "sequia"]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True, help="Dataset directory with train/, val/, test/ and class subfolders")
    parser.add_argument("--output", type=Path, default=Path("data/trained_model"))
    parser.add_argument("--epochs", type=int, default=20)
    args = parser.parse_args()
    import tensorflow as tf
    from scripts.audit_training_dataset import audit
    for split in ("train", "val", "test"):
        report = audit(args.data / split)
        if not report["ready_for_training"]:
            raise SystemExit(f"{split} split missing classes or insufficient independent images: {report['images_per_class']}")
    datasets = {}
    for split in ("train", "val", "test"):
        datasets[split] = tf.keras.utils.image_dataset_from_directory(
            args.data / split, labels="inferred", label_mode="categorical",
            class_names=LABELS, image_size=(224, 224), batch_size=16,
            shuffle=(split == "train"), seed=42)
    augment = tf.keras.Sequential([
        tf.keras.layers.RandomFlip("horizontal"),
        tf.keras.layers.RandomRotation(0.08),
        tf.keras.layers.RandomZoom(0.12),
        tf.keras.layers.RandomContrast(0.1),
    ], name="training_only_augmentation")
    base = tf.keras.applications.MobileNetV2(input_shape=(224, 224, 3), include_top=False, weights="imagenet")
    base.trainable = False
    inputs = tf.keras.Input(shape=(224, 224, 3))
    x = augment(inputs)
    x = tf.keras.applications.mobilenet_v2.preprocess_input(x)
    x = base(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.25)(x)
    outputs = tf.keras.layers.Dense(len(LABELS), activation="softmax")(x)
    model = tf.keras.Model(inputs, outputs)
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
                  loss="categorical_crossentropy", metrics=["accuracy"])
    args.output.mkdir(parents=True, exist_ok=True)
    model.fit(datasets["train"], validation_data=datasets["val"],
              epochs=args.epochs, callbacks=[
                  tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=4, restore_best_weights=True),
                  tf.keras.callbacks.ModelCheckpoint(str(args.output / "best.keras"), monitor="val_loss", save_best_only=True)])
    loss, accuracy = model.evaluate(datasets["test"], verbose=0)
    model.save(args.output / "model.keras")
    (args.output / "metadata.json").write_text(json.dumps({
        "labels": [x.replace("_", " ") for x in LABELS],
        "preprocessing": "raw_0_255_pixels_model_rescaling",
        "test_accuracy": float(accuracy), "test_loss": float(loss),
        "note": "Use separate event/site/time splits to prevent leakage. Never treat test accuracy as guaranteed field performance."
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Independent test accuracy: {accuracy:.3f}; loss: {loss:.3f}")

if __name__ == "__main__":
    main()
