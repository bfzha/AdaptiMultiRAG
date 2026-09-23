from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def output_dir(*parts: str) -> Path:
    p = project_root() / "outputs" / Path(*parts)
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_json(obj: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, default=_json_default)


def _json_default(o: Any) -> Any:
    if isinstance(o, (np.integer, np.floating)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


def clr_transform(proportions: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    """Centered log-ratio for compositional data (last component dropped in regression)."""
    p = np.asarray(proportions, dtype=float)
    p = np.clip(p, eps, 1.0)
    p = p / p.sum(axis=-1, keepdims=True)
    logp = np.log(p)
    gm = logp.mean(axis=-1, keepdims=True)
    return logp - gm


def entropy_weights(matrix: np.ndarray) -> np.ndarray:
    x = np.asarray(matrix, dtype=float)
    x = np.clip(x, 1e-12, None)
    p = x / x.sum(axis=0, keepdims=True)
    n = x.shape[0]
    k = 1.0 / np.log(n)
    e = -k * np.sum(p * np.log(p + 1e-12), axis=0)
    d = 1 - e
    d = np.clip(d, 0, None)
    if d.sum() <= 0:
        return np.ones(x.shape[1]) / x.shape[1]
    return d / d.sum()
