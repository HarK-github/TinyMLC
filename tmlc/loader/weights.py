"""Weight loader and validator for trained numpy arrays."""

from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import Any

import numpy as np

from tmlc.ast.nodes import DenseNode, ModelNode
from tmlc.errors import TmlcError


@dataclass(frozen=True)
class LoadedLayerWeights:
    """Validated numpy weights and biases for a single Dense layer."""

    layer: DenseNode
    weights: np.ndarray  # Shape: (in_features, out_features), dtype: float32
    bias: np.ndarray  # Shape: (out_features,), dtype: float32


class WeightLoader:
    """Loads, validates, and casts neural network weight arrays."""

    def load_dense_weights(
        self,
        layer: DenseNode,
        base_dir: str | pathlib.Path,
    ) -> LoadedLayerWeights:
        """Load and strictly validate weights and bias for a single Dense layer."""
        base = pathlib.Path(base_dir)

        # E301: Empty string is treated as missing file
        if not layer.weight_path.strip():
            raise TmlcError(
                "E301",
                "Weight path string cannot be empty",
                layer.line,
                layer.col,
            )
        if not layer.bias_path.strip():
            raise TmlcError(
                "E301",
                "Bias path string cannot be empty",
                layer.line,
                layer.col,
            )

        # Resolve paths relative to base_dir (the .tml folder)
        w_path = (base / layer.weight_path).resolve()
        b_path = (base / layer.bias_path).resolve()

        # E301: Missing file check
        if not w_path.is_file():
            raise TmlcError(
                "E301",
                f"Missing weight file: '{layer.weight_path}' (resolved to {w_path})",
                layer.line,
                layer.col,
            )
        if not b_path.is_file():
            raise TmlcError(
                "E301",
                f"Missing bias file: '{layer.bias_path}' (resolved to {b_path})",
                layer.line,
                layer.col,
            )

        # Load numpy files
        try:
            w_raw: Any = np.load(w_path)
        except Exception as ex:
            raise TmlcError(
                "E301",
                f"Failed to load weight array from {w_path}: {ex}",
                layer.line,
                layer.col,
            ) from ex

        try:
            b_raw: Any = np.load(b_path)
        except Exception as ex:
            raise TmlcError(
                "E301",
                f"Failed to load bias array from {b_path}: {ex}",
                layer.line,
                layer.col,
            ) from ex

        w_arr = np.asarray(w_raw)
        b_arr = np.asarray(b_raw)

        # E302: Weight shape check (in_features, out_features)
        expected_w_shape = (layer.in_features, layer.out_features)
        if w_arr.shape != expected_w_shape:
            raise TmlcError(
                "E302",
                f"Weight matrix shape mismatch: expected {expected_w_shape}, got {w_arr.shape}",
                layer.line,
                layer.col,
            )

        # E303: Bias shape check (out_features,) or (1, out_features)
        expected_b_shape = (layer.out_features,)
        if b_arr.shape != expected_b_shape and b_arr.shape != (1, layer.out_features):
            raise TmlcError(
                "E303",
                f"Bias vector shape mismatch: expected {expected_b_shape}, got {b_arr.shape}",
                layer.line,
                layer.col,
            )

        # E304: NaN or Infinity check
        if np.isnan(w_arr).any() or np.isinf(w_arr).any():
            raise TmlcError(
                "E304",
                f"Weight array '{layer.weight_path}' contains NaN or Infinite values",
                layer.line,
                layer.col,
            )

        if np.isnan(b_arr).any() or np.isinf(b_arr).any():
            raise TmlcError(
                "E304",
                f"Bias array '{layer.bias_path}' contains NaN or Infinite values",
                layer.line,
                layer.col,
            )

        # Cast to float32
        w_f32 = w_arr.astype(np.float32)
        b_f32 = b_arr.astype(np.float32).flatten()

        return LoadedLayerWeights(layer=layer, weights=w_f32, bias=b_f32)

    def load_weights(
        self,
        model: ModelNode,
        base_dir: str | pathlib.Path,
    ) -> list[LoadedLayerWeights]:
        """Load and validate all weights for all Dense layers in a Model."""
        loaded: list[LoadedLayerWeights] = []
        for layer in model.layers:
            if isinstance(layer, DenseNode):
                loaded.append(self.load_dense_weights(layer, base_dir))
        return loaded
