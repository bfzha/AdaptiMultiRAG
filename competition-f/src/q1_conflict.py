from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.data.constants import NEGATIVE_METRICS, QUALITY_METRICS
from src.utils import output_dir, save_json


def detect_conflicts(df_norm: pd.DataFrame, tau: float = 0.75, z_delta: float = 1.5) -> pd.DataFrame:
    """Conflict: high education/fluency but high raw ad_en (ads) on same sample."""
    edu = pd.to_numeric(df_norm.get("fineweb_edu"), errors="coerce")
    flu = pd.to_numeric(df_norm.get("fluency_en"), errors="coerce")
    ads = pd.to_numeric(df_norm.get("ad_en_raw", df_norm.get("ad_en")), errors="coerce")
    if edu.dtype == object:
        edu = edu.apply(lambda x: x[0] if isinstance(x, list) and x else np.nan)
    if flu.dtype == object:
        flu = flu.apply(lambda x: x[0] if isinstance(x, list) and x else np.nan)

    conflict_flags = []
    conflict_scores = []
    for i in range(len(df_norm)):
        e = edu.iloc[i] if hasattr(edu, "iloc") else edu[i]
        f = flu.iloc[i] if hasattr(flu, "iloc") else flu[i]
        a = ads.iloc[i] if hasattr(ads, "iloc") else ads[i]
        pos_high = (pd.notna(e) and e > tau) or (pd.notna(f) and f > tau)
        ads_high = pd.notna(a) and a > tau
        flagged = bool(pos_high and ads_high)
        cscore = float(abs((e or 0) - (1 - (a or 0)))) if flagged else 0.0
        conflict_flags.append(flagged)
        conflict_scores.append(cscore)
    out = df_norm.copy()
    out["conflict"] = conflict_flags
    out["conflict_score"] = conflict_scores
    return out


def resolve_conflicts(df: pd.DataFrame, weights: np.ndarray, lam: float = 0.05) -> pd.DataFrame:
    mat = df[QUALITY_METRICS].astype(float).fillna(0.5).values
    base_q = mat @ weights
    penalty = df["conflict_score"].values * lam
    resolved = base_q - penalty
    out = df.copy()
    out["Q_resolved"] = np.clip(resolved, 0, 1)
    out["Q"] = np.where(df["conflict"], out["Q_resolved"], base_q)
    return out


def run_conflict_pipeline(scored: pd.DataFrame, weights: np.ndarray) -> dict[str, Any]:
    norm_cols = scored[QUALITY_METRICS + ["sample_id", "source_domain", "source_file"]].copy()
    for c in QUALITY_METRICS:
        norm_cols[c] = scored[c]

    detected = detect_conflicts(norm_cols)
    resolved = resolve_conflicts(detected, weights, lam=0.05)

    sample_mask = resolved["source_file"].str.contains("sample", case=False, na=False)
    stats = {
        "conflict_rate_all": float(resolved["conflict"].mean()),
        "conflict_rate_sample": float(resolved.loc[sample_mask, "conflict"].mean()),
        "conflict_rate_extended": float(resolved.loc[~sample_mask, "conflict"].mean()),
        "conflict_count": int(resolved["conflict"].sum()),
    }
    resolved.to_csv(output_dir("q1") / "quality_conflict_resolved.csv", index=False)
    save_json(stats, output_dir("q1") / "conflict_stats.json")
    return {"resolved": resolved, "stats": stats}
