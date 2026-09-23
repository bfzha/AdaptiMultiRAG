from __future__ import annotations

import json
import lzma
from pathlib import Path
from typing import Any, Generator, Iterable

import pandas as pd
import yaml

from .constants import DOMAIN_COLS, LOSS_COLS, QUALITY_METRICS


def load_paths_config() -> dict:
    cfg_path = Path(__file__).resolve().parents[2] / "config" / "paths.yaml"
    with cfg_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_data_root() -> Path:
    return Path(load_paths_config()["data_root"])


def _a_path(*parts: str) -> Path:
    return get_data_root() / "A_data_value" / Path(*parts)


def _b_path(*parts: str) -> Path:
    return get_data_root() / "B_scaling_laws" / Path(*parts)


def _c_path(*parts: str) -> Path:
    return get_data_root() / "C_efficiency_evolution" / Path(*parts)


def load_regmix_pair(mixture_name: str, loss_name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    mix = pd.read_csv(_a_path("regmix_tables", mixture_name))
    loss = pd.read_csv(_a_path("regmix_tables", loss_name))
    return mix, loss


def merge_regmix(mix: pd.DataFrame, loss: pd.DataFrame) -> pd.DataFrame:
    df = mix.merge(loss, on="index", how="inner")
    df["mean_loss"] = df[LOSS_COLS].mean(axis=1, skipna=True)
    return df


def stream_jsonl_xz(path: Path) -> Generator[dict[str, Any], None, None]:
    with lzma.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def iter_quality_files() -> Iterable[Path]:
    root = _a_path()
    sample = root / "slimpajama_quality_signal_sample.jsonl.xz"
    if sample.exists():
        yield sample
    ext = root / "slimpajama_quality_extended"
    if ext.exists():
        yield from sorted(ext.glob("*.jsonl.xz"))


def load_domain_mapping() -> pd.DataFrame:
    return pd.read_csv(_a_path("domain_mapping_guide.csv"))


def load_b1() -> pd.DataFrame:
    return pd.read_csv(_b_path("pythia_training_log_existing.csv"))


def load_b6_b8() -> dict[str, pd.DataFrame]:
    out = {}
    for name in [
        "supplementary_NQ_experiment.csv",
        "supplementary_NQ_experiment_expanded.csv",
        "supplementary_NQ_experiment_large.csv",
    ]:
        p = _b_path(name)
        if p.exists():
            out[name] = pd.read_csv(p)
    return out


def load_c1() -> pd.DataFrame:
    p = _c_path("leaderboard_cleaned.csv")
    if not p.exists():
        p = _c_path("leaderboard_enhanced.csv")
    return pd.read_csv(p)


def load_c6() -> pd.DataFrame:
    p = _c_path("loss_benchmark_bridge_expanded.csv")
    if not p.exists():
        p = _c_path("loss_benchmark_bridge.csv")
    return pd.read_csv(p)


def load_c7() -> pd.DataFrame:
    return pd.read_csv(_c_path("model_architecture_metadata.csv"))


def load_c4() -> pd.DataFrame:
    return pd.read_csv(_c_path("epoch_all_ai_models.csv"))


def load_c8_latest_json(limit: int | None = None) -> list[dict[str, Any]]:
    base = _c_path("detailed_results")
    if not base.exists():
        return []
    records: list[dict[str, Any]] = []
    for model_dir in sorted(base.iterdir()):
        if not model_dir.is_dir():
            continue
        json_files = sorted(model_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
        if not json_files:
            continue
        latest = json_files[-1]
        try:
            with latest.open(encoding="utf-8") as f:
                obj = json.load(f)
            obj["_model_dir"] = model_dir.name
            obj["_json_path"] = str(latest)
            records.append(obj)
        except (json.JSONDecodeError, OSError):
            continue
        if limit and len(records) >= limit:
            break
    return records
