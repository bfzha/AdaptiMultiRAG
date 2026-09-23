from __future__ import annotations

import statistics
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.data.constants import LIST_METRICS, NEGATIVE_METRICS, QUALITY_METRICS
from src.data.loaders import get_data_root, iter_quality_files, load_domain_mapping, stream_jsonl_xz
from src.utils import entropy_weights, output_dir, save_json


def _scalarize(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, list):
        if not value:
            return None
        return float(statistics.fmean(v for v in value if v is not None))
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_metric_vector(record: dict[str, Any]) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for m in QUALITY_METRICS:
        out[m] = _scalarize(record.get(m))
    return out


def load_quality_records(max_records: int | None = None) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for path in iter_quality_files():
        domain_hint = None
        if "arxiv" in path.name:
            domain_hint = "arxiv"
        elif "github" in path.name:
            domain_hint = "github"
        for rec in stream_jsonl_xz(path):
            domain = rec.get("_source_domain") or domain_hint or "unknown"
            vec = extract_metric_vector(rec)
            vec["sample_id"] = rec.get("id", len(rows))
            vec["source_domain"] = domain
            vec["source_file"] = path.name
            rows.append(vec)
            if max_records and len(rows) >= max_records:
                break
        if max_records and len(rows) >= max_records:
            break
    return pd.DataFrame(rows)


def normalize_metrics(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, dict[str, float]]]:
    norm = df.copy()
    bounds: dict[str, dict[str, float]] = {}
    for m in QUALITY_METRICS:
        col = pd.to_numeric(norm[m], errors="coerce")
        lo, hi = col.quantile(0.01), col.quantile(0.99)
        if pd.isna(lo) or pd.isna(hi) or hi <= lo:
            lo, hi = col.min(), col.max()
        if pd.isna(lo) or pd.isna(hi) or hi <= lo:
            norm[m] = 0.5
            bounds[m] = {"lo": 0.0, "hi": 1.0}
            continue
        scaled = (col - lo) / (hi - lo)
        scaled = scaled.clip(0, 1)
        if m == "ad_en":
            norm["ad_en_raw"] = scaled.copy()
        if m in NEGATIVE_METRICS:
            scaled = 1 - scaled
        norm[m] = scaled
        bounds[m] = {"lo": float(lo), "hi": float(hi)}
    return norm, bounds


def compute_quality_scores(df_norm: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    mat = df_norm[QUALITY_METRICS].astype(float).fillna(df_norm[QUALITY_METRICS].median())
    w = entropy_weights(mat.values)
    q = mat.values @ w
    out = df_norm.copy()
    out["Q"] = q
    return out, w


def aggregate_domain_scores(df: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    """Map 7 quality domains -> 17 mixture domains via A16 weights."""
    q_dom = df.groupby("source_domain", as_index=False)["Q"].mean()
    q_map = {r["source_domain"]: r["Q"] for _, r in q_dom.iterrows()}
    rows = []
    for _, row in mapping.iterrows():
        mix_dom = row["mixture_domain"]
        q_src = row["quality_domain"]
        weight = float(row.get("weight", 1.0))
        q_val = q_map.get(q_src, np.nan)
        rows.append({"mixture_domain": mix_dom, "quality_domain": q_src, "weight": weight, "Q": q_val})
    dom = pd.DataFrame(rows)
    agg = (
        dom.dropna(subset=["Q"])
        .groupby("mixture_domain", as_index=False)
        .apply(lambda g: pd.Series({"Q_domain": np.average(g["Q"], weights=g["weight"])}))
        .reset_index(drop=True)
    )
    return agg


def run_quality_pipeline(max_records: int | None = None) -> dict[str, Any]:
    raw = load_quality_records(max_records=max_records)
    norm, bounds = normalize_metrics(raw)
    scored, weights = compute_quality_scores(norm)
    mapping = load_domain_mapping()
    domain_q = aggregate_domain_scores(scored, mapping)

    out_sample = output_dir("q1") / "quality_scores_sample.csv"
    out_domain = output_dir("q1") / "quality_scores_domain.csv"
    scored.to_csv(out_sample, index=False)
    domain_q.to_csv(out_domain, index=False)

    # Split A1 vs extended for comparison
    sample_mask = scored["source_file"].str.contains("sample", case=False, na=False)
    comparison = {
        "sample_mean_Q": float(scored.loc[sample_mask, "Q"].mean()),
        "extended_mean_Q": float(scored.loc[~sample_mask, "Q"].mean()),
        "sample_count": int(sample_mask.sum()),
        "extended_count": int((~sample_mask).sum()),
    }
    by_file = scored.groupby("source_file")["Q"].agg(["mean", "count"]).reset_index()
    by_file.to_csv(output_dir("q1") / "quality_by_source_file.csv", index=False)

    meta = {
        "weights": {m: float(w) for m, w in zip(QUALITY_METRICS, weights)},
        "bounds": bounds,
        "comparison_sample_vs_extended": comparison,
        "Q_baseline": float(scored["Q"].quantile(0.25)),
    }
    save_json(meta, output_dir("q1") / "quality_meta.json")
    return {"scored": scored, "domain_q": domain_q, "meta": meta}
