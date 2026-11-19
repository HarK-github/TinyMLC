"""Train a 784-128-64-10 network on real MNIST and export weights to .npy files."""

from __future__ import annotations

import gzip
import pathlib
import struct
import urllib.request

import numpy as np

# Official Google / CVDF MNIST mirror
MNIST_MIRROR = "https://storage.googleapis.com/cvdf-datasets/mnist/"
DATA_FILES = {
    "train_img": "train-images-idx3-ubyte.gz",
    "train_lbl": "train-labels-idx1-ubyte.gz",
    "test_img": "t10k-images-idx3-ubyte.gz",
    "test_lbl": "t10k-labels-idx1-ubyte.gz",
}


def download_mnist(data_dir: pathlib.Path) -> None:
    """Download MNIST gzip files if not already cached."""
    data_dir.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0"}

    for filename in DATA_FILES.values():
        local_path = data_dir / filename
        if not local_path.is_file() or local_path.stat().st_size == 0:
            url = MNIST_MIRROR + filename
            print(f"Downloading {url} -> {local_path}...")
            req = urllib.request.Request(url, headers=headers)
            with (
                urllib.request.urlopen(req, timeout=30) as resp,
                open(local_path, "wb") as f,
            ):
                f.write(resp.read())


def load_mnist_images(filepath: pathlib.Path) -> np.ndarray:
    """Read MNIST idx3 image file into (N, 784) float32 normalized array."""
    with gzip.open(filepath, "rb") as f:
        magic, count, rows, cols = struct.unpack(">IIII", f.read(16))
        assert magic == 2051, f"Invalid magic {magic}"
        data = np.frombuffer(f.read(), dtype=np.uint8)
        return data.reshape(count, rows * cols).astype(np.float32) / 255.0


def load_mnist_labels(filepath: pathlib.Path) -> np.ndarray:
    """Read MNIST idx1 label file into (N,) uint8 array."""
    with gzip.open(filepath, "rb") as f:
        magic, _count = struct.unpack(">II", f.read(8))
        assert magic == 2049, f"Invalid magic {magic}"
        return np.frombuffer(f.read(), dtype=np.uint8)


def train_and_export(
    data_dir: str = "training/data",
    weights_dir: str = "examples/weights",
    epochs: int = 5,
    batch_size: int = 128,
    learning_rate: float = 0.001,
) -> float:
    """Train 784-128-64-10 network on MNIST and export weights."""
    d_dir = pathlib.Path(data_dir)
    w_dir = pathlib.Path(weights_dir)
    w_dir.mkdir(parents=True, exist_ok=True)

    print("Step 1/4: Fetching MNIST dataset...")
    download_mnist(d_dir)

    print("Step 2/4: Loading dataset...")
    x_train = load_mnist_images(d_dir / DATA_FILES["train_img"])
    y_train = load_mnist_labels(d_dir / DATA_FILES["train_lbl"])
    x_test = load_mnist_images(d_dir / DATA_FILES["test_img"])
    y_test = load_mnist_labels(d_dir / DATA_FILES["test_lbl"])

    num_classes = 10
    rng = np.random.default_rng(seed=42)

    # He (Kaiming) normal initialization
    w1 = (
        rng.standard_normal((784, 128), dtype=np.float32) * np.sqrt(2.0 / 784)
    ).astype(np.float32)
    b1 = np.zeros(128, dtype=np.float32)

    w2 = (rng.standard_normal((128, 64), dtype=np.float32) * np.sqrt(2.0 / 128)).astype(
        np.float32
    )
    b2 = np.zeros(64, dtype=np.float32)

    w3 = (rng.standard_normal((64, 10), dtype=np.float32) * np.sqrt(2.0 / 64)).astype(
        np.float32
    )
    b3 = np.zeros(10, dtype=np.float32)

    # Adam optimizer moments
    mw1, vw1 = np.zeros_like(w1), np.zeros_like(w1)
    mb1, vb1 = np.zeros_like(b1), np.zeros_like(b1)
    mw2, vw2 = np.zeros_like(w2), np.zeros_like(w2)
    mb2, vb2 = np.zeros_like(b2), np.zeros_like(b2)
    mw3, vw3 = np.zeros_like(w3), np.zeros_like(w3)
    mb3, vb3 = np.zeros_like(b3), np.zeros_like(b3)

    beta1, beta2, eps = 0.9, 0.999, 1e-8
    t_step = 0
    num_samples = len(x_train)

    print(f"Step 3/4: Training 784->128->64->10 network ({epochs} epochs)...")
    for epoch in range(1, epochs + 1):
        indices = rng.permutation(num_samples)
        x_shuffled = x_train[indices]
        y_shuffled = y_train[indices]

        for offset in range(0, num_samples, batch_size):
            xb = x_shuffled[offset : offset + batch_size]
            yb = y_shuffled[offset : offset + batch_size]
            bs = len(xb)

            # Forward pass
            z1 = xb @ w1 + b1
            a1 = np.maximum(z1, 0.0)

            z2 = a1 @ w2 + b2
            a2 = np.maximum(z2, 0.0)

            z3 = a2 @ w3 + b3
            # Numerically stable softmax
            max_z3 = np.max(z3, axis=1, keepdims=True)
            exp_z3 = np.exp(z3 - max_z3)
            probs = exp_z3 / np.sum(exp_z3, axis=1, keepdims=True)

            # One-hot labels
            y_one_hot = np.zeros((bs, num_classes), dtype=np.float32)
            y_one_hot[np.arange(bs), yb] = 1.0

            # Backward pass
            dz3 = (probs - y_one_hot) / bs
            dw3 = a2.T @ dz3
            db3 = np.sum(dz3, axis=0)

            da2 = dz3 @ w3.T
            dz2 = da2 * (z2 > 0)
            dw2 = a1.T @ dz2
            db2 = np.sum(dz2, axis=0)

            da1 = dz2 @ w2.T
            dz1 = da1 * (z1 > 0)
            dw1 = xb.T @ dz1
            db1 = np.sum(dz1, axis=0)

            # Adam update
            t_step += 1
            for param, grad, m, v in [
                (w1, dw1, mw1, vw1),
                (b1, db1, mb1, vb1),
                (w2, dw2, mw2, vw2),
                (b2, db2, mb2, vb2),
                (w3, dw3, mw3, vw3),
                (b3, db3, mb3, vb3),
            ]:
                m[:] = beta1 * m + (1.0 - beta1) * grad
                v[:] = beta2 * v + (1.0 - beta2) * (grad**2)
                m_hat = m / (1.0 - beta1**t_step)
                v_hat = v / (1.0 - beta2**t_step)
                param -= learning_rate * m_hat / (np.sqrt(v_hat) + eps)

        # Epoch evaluation
        z1_val = x_test @ w1 + b1
        a1_val = np.maximum(z1_val, 0.0)
        z2_val = a1_val @ w2 + b2
        a2_val = np.maximum(z2_val, 0.0)
        z3_val = a2_val @ w3 + b3
        preds = np.argmax(z3_val, axis=1)
        acc = float(np.mean(preds == y_test) * 100.0)
        print(f"  Epoch {epoch}/{epochs} - Test Accuracy: {acc:.2f}%")

    print(f"Step 4/4: Exporting weights in (in, out) orientation to {w_dir}...")
    np.save(w_dir / "dense1_w.npy", w1)
    np.save(w_dir / "dense1_b.npy", b1)
    np.save(w_dir / "dense2_w.npy", w2)
    np.save(w_dir / "dense2_b.npy", b2)
    np.save(w_dir / "dense3_w.npy", w3)
    np.save(w_dir / "dense3_b.npy", b3)

    # Save 5 distinct test samples for Test 18 verification
    sample_indices = [0, 1, 2, 3, 4]
    test_vectors = x_test[sample_indices]
    np.save("examples/test_inputs.npy", test_vectors)
    print("Exported 5 verification test vectors to examples/test_inputs.npy")

    print(f"\nFinal MNIST Test Accuracy: {acc:.2f}%")
    return acc


if __name__ == "__main__":
    train_and_export()
