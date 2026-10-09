"""Train an image classifier from *user-provided, labeled* images.

Usage: pip install tensorflow pillow
python -m training.train --dataset datasets/curated --output models/teachable_machine

Dataset layout: datasets/curated/<class_name>/*.jpg
Do not use generated images as substitutes for real evaluation data.
"""
import argparse
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("models/teachable_machine"))
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if not args.dataset.is_dir():
        parser.error("Dataset directory not found; supply labeled images first")
    if args.epochs < 1 or args.epochs > 200:
        parser.error("epochs must be between 1 and 200")
    from training.validate_dataset import validate
    validate(args.dataset)
    import tensorflow as tf
    tf.keras.utils.set_random_seed(args.seed)
    train = tf.keras.utils.image_dataset_from_directory(
        args.dataset, validation_split=0.2, subset="training", seed=args.seed,
        image_size=(224,224), batch_size=16)
    validation = tf.keras.utils.image_dataset_from_directory(
        args.dataset, validation_split=0.2, subset="validation", seed=args.seed,
        image_size=(224,224), batch_size=16)
    labels = train.class_names
    if len(labels) != 5:
        parser.error(f"Expected exactly five class folders, found {len(labels)}: {labels}")
    # MobileNetV2 expects pixel range [-1,1]; same as detector.py.
    base = tf.keras.applications.MobileNetV2(
        include_top=False, weights="imagenet", input_shape=(224,224,3))
    base.trainable = False
    inputs = tf.keras.Input(shape=(224,224,3))
    x = tf.keras.layers.Rescaling(1/127.5, offset=-1)(inputs)
    x = base(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.25)(x)
    outputs = tf.keras.layers.Dense(len(labels), activation="softmax")(x)
    model = tf.keras.Model(inputs, outputs)
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3),
                  loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    callbacks = [tf.keras.callbacks.EarlyStopping(patience=3, restore_best_weights=True)]
    history = model.fit(train, validation_data=validation, epochs=args.epochs,
                        callbacks=callbacks)
    args.output.mkdir(parents=True, exist_ok=True)
    model.save(args.output / "model.keras")
    (args.output / "metadata.json").write_text(
        json.dumps({"labels":labels,"source":"local-training","input_size":[224,224],
                    "preprocessing":"raw_0_255_pixels_model_rescaling",
                    "seed":args.seed}, ensure_ascii=False, indent=2),encoding="utf-8")
    (args.output / "training_history.json").write_text(
        json.dumps(history.history, indent=2),encoding="utf-8")
    print("Training completed. Evaluate on a held-out test set before use.")
if __name__ == "__main__":
    main()
