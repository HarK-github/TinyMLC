"""Evaluate float32 and int8 dequantized MNIST test accuracy across all 10,000 images."""

from __future__ import annotations

import pathlib
import sys

import numpy as np

# Add project root to sys.path
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tmlc.quantization.int8 import dequantize_weights, quantize_weights
from training.train_mnist import load_mnist_images, load_mnist_labels


def evaluate_mnist_accuracy(
    data_dir: str | pathlib.Path = "training/data",
    weights_dir: str | pathlib.Path = "examples/weights",
) -> tuple[float, float, int, int]:
    """Evaluate accuracy on 10k MNIST test images for float32 and int8 dequantized models.

    Returns:
        tuple (acc_f32, acc_int8, count_f32_correct, count_int8_correct)
    """
    d_path = pathlib.Path(data_dir)
    w_path = pathlib.Path(weights_dir)

    img_file = d_path / "t10k-images-idx3-ubyte.gz"
    lbl_file = d_path / "t10k-labels-idx1-ubyte.gz"

    if not img_file.is_file() or not lbl_file.is_file():
        raise FileNotFoundError(f"Missing MNIST test files in {d_path}")

    images = load_mnist_images(img_file)
    labels = load_mnist_labels(lbl_file)
    total_samples = len(labels)

    # Load weights
    w1 = np.load(w_path / "dense1_w.npy").astype(np.float32)
    b1 = np.load(w_path / "dense1_b.npy").astype(np.float32)
    w2 = np.load(w_path / "dense2_w.npy").astype(np.float32)
    b2 = np.load(w_path / "dense2_b.npy").astype(np.float32)
    w3 = np.load(w_path / "dense3_w.npy").astype(np.float32)
    b3 = np.load(w_path / "dense3_b.npy").astype(np.float32)

    # 1. Float32 forward pass
    z1 = np.maximum(0.0, images @ w1 + b1)
    z2 = np.maximum(0.0, z1 @ w2 + b2)
    logits_f32 = z2 @ w3 + b3
    preds_f32 = np.argmax(logits_f32, axis=1)

    # 2. Int8 dequantized forward pass: W_dequant = quantize(W) * scale
    w1_q, s1 = quantize_weights(w1)
    w1_dequant = dequantize_weights(w1_q, s1)

    w2_q, s2 = quantize_weights(w2)
    w2_dequant = dequantize_weights(w2_q, s2)

    w3_q, s3 = quantize_weights(w3)
    w3_dequant = dequantize_weights(w3_q, s3)

    z1_int8 = np.maximum(0.0, images @ w1_dequant + b1)
    z2_int8 = np.maximum(0.0, z1_int8 @ w2_dequant + b2)
    logits_int8 = z2_int8 @ w3_dequant + b3
    preds_int8 = np.argmax(logits_int8, axis=1)

    # Accuracies
    correct_f32 = int(np.sum(preds_f32 == labels))
    correct_int8 = int(np.sum(preds_int8 == labels))
    acc_f32 = (correct_f32 / total_samples) * 100.0
    acc_int8 = (correct_int8 / total_samples) * 100.0

    # Agreement
    matching_preds = int(np.sum(preds_f32 == preds_int8))
    differing_preds = total_samples - matching_preds
    agreement_pct = (matching_preds / total_samples) * 100.0

    print("=================================================================")
    print("           MNIST TEST ACCURACY EVALUATION (10,000 IMAGES)        ")
    print("=================================================================")
    print(f"Float32 Accuracy : {acc_f32:.2f}% ({correct_f32:,} / {total_samples:,})")
    print(f"Int8 Accuracy    : {acc_int8:.2f}% ({correct_int8:,} / {total_samples:,}) (dequantized NumPy)")
    print(f"Accuracy Delta   : {acc_int8 - acc_f32:+.2f} points ({correct_int8 - correct_f32:+d} net correct)")
    print(f"Prediction Agree : {agreement_pct:.2f}% ({matching_preds:,} / {total_samples:,} identical)")
    print(f"Differing Preds  : {differing_preds} of {total_samples:,} predictions differ")
    print("=================================================================")

    return acc_f32, acc_int8, correct_f32, correct_int8


if __name__ == "__main__":
    evaluate_mnist_accuracy()
