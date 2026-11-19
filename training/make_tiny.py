"""Generate deterministic seeded weights for the 4-8-2 tiny model."""

from __future__ import annotations

import pathlib

import numpy as np


def make_tiny_weights(out_dir: str | pathlib.Path = "examples/weights") -> None:
    """Generate reproducible random weights and biases for tiny.tml."""
    dest = pathlib.Path(out_dir)
    dest.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(seed=42)

    # Layer 1: Dense(4, 8)
    w1 = rng.standard_normal((4, 8), dtype=np.float32) * 0.5
    b1 = rng.standard_normal((8,), dtype=np.float32) * 0.1

    # Layer 2: Dense(8, 2)
    w2 = rng.standard_normal((8, 2), dtype=np.float32) * 0.5
    b2 = rng.standard_normal((2,), dtype=np.float32) * 0.1

    np.save(dest / "tiny_w1.npy", w1)
    np.save(dest / "tiny_b1.npy", b1)
    np.save(dest / "tiny_w2.npy", w2)
    np.save(dest / "tiny_b2.npy", b2)

    print(f"Generated tiny weights in {dest}:")
    print(f"  tiny_w1.npy: {w1.shape}")
    print(f"  tiny_b1.npy: {b1.shape}")
    print(f"  tiny_w2.npy: {w2.shape}")
    print(f"  tiny_b2.npy: {b2.shape}")


if __name__ == "__main__":
    make_tiny_weights()
