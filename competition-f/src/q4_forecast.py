from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from src.data.loaders import load_c1, load_c4, load_c6, load_c8_latest_json
from src.utils import output_dir, save_json


BENCH_COLS = ["IFEval", "BBH", "MATH Lvl 5", "GPQA", "MUSR", "MMLU-PRO"]


def fit_loss_benchmark_bridge(df: pd.DataFrame) -> dict[str, Any]:
    loss = df["Val_Loss"].values.astype(float)
    lb_cols = [c for c in df.columns if c.startswith("LB_")]
    models = {}
    for col in lb_cols:
        y = df[col].values.astype(float)
        X = np.log(loss).reshape(-1, 1)
        reg = LinearRegression().fit(X, y)
        models[col] = {"intercept": float(reg.intercept_), "coef_log_loss": float(reg.coef_[0])}
    if "Loss_Comparability" in df.columns:
        high = df[df["Loss_Comparability"].str.lower() == "high"]
        if len(high) >= 3:
            y = high[lb_cols[0]].values
            X = np.log(high["Val_Loss"].values).reshape(-1, 1)
            reg = LinearRegression().fit(X, y)
            models["high_comparability_primary"] = {
                "intercept": float(reg.intercept_),
                "coef": float(reg.coef_[0]),
                "n": int(len(high)),
            }
    return models


def aggregate_c8(records: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for rec in records:
        results = rec.get("results", {})
        mmlu = results.get("mmlu_pro", {})
        bbh = results.get("bbh", {})
        rows.append(
            {
                "model_dir": rec.get("_model_dir"),
                "mmlu_pro_acc": mmlu.get("accuracy"),
                "bbh_acc": bbh.get("accuracy"),
            }
        )
    return pd.DataFrame(rows)


def decomposition(c1: pd.DataFrame, c4: pd.DataFrame | None = None) -> dict[str, Any]:
    df = c1.copy()
    df["Average"] = df[BENCH_COLS].mean(axis=1)
    df["log_N"] = np.log(pd.to_numeric(df["#Params (B)"], errors="coerce").clip(lower=0.1))
    df["year"] = pd.to_datetime(df["Submission Date"], errors="coerce").dt.year
    df = df.dropna(subset=["log_N", "year", "Average"])

    X = df[["log_N", "year"]].values
    y = df["Average"].values
    reg = LinearRegression().fit(X, y)
    scale_effect = reg.coef_[0] * df["log_N"].mean()
    time_effect = reg.coef_[1] * (df["year"].max() - df["year"].min())
    total = df["Average"].max() - df["Average"].min()
    return {
        "beta_log_N": float(reg.coef_[0]),
        "beta_year": float(reg.coef_[1]),
        "intercept": float(reg.intercept_),
        "scale_contribution_proxy": float(scale_effect),
        "tech_contribution_proxy": float(time_effect),
        "total_range": float(total),
        "scale_share": float(abs(scale_effect) / (abs(scale_effect) + abs(time_effect) + 1e-8)),
        "tech_share": float(abs(time_effect) / (abs(scale_effect) + abs(time_effect) + 1e-8)),
        "r2": float(reg.score(X, y)),
    }


def forecast_frontier(c1: pd.DataFrame, months: int = 24, compute_slowdown: float = 0.5) -> pd.DataFrame:
    df = c1.copy()
    df["Average"] = df[BENCH_COLS].mean(axis=1)
    df["date"] = pd.to_datetime(df["Submission Date"], errors="coerce")
    df = df.dropna(subset=["date"])
    monthly = df.groupby(df["date"].dt.to_period("M"))["Average"].max().reset_index()
    monthly["date"] = monthly["date"].dt.to_timestamp()
    if len(monthly) < 3:
        last = float(df["Average"].max())
        future_dates = pd.date_range(df["date"].max(), periods=months + 1, freq="ME")[1:]
        return pd.DataFrame({"date": future_dates, "frontier_pred": last, "lower": last - 3, "upper": last + 3})
    monthly["t"] = np.arange(len(monthly))
    reg = LinearRegression().fit(monthly[["t"]], monthly["Average"])
    slope = reg.coef_[0] * compute_slowdown
    last_t = monthly["t"].max()
    future_t = np.arange(last_t + 1, last_t + months + 1)
    pred = reg.predict(future_t.reshape(-1, 1))
    # Adjust slope for slowdown
    pred = monthly["Average"].iloc[-1] + slope * (future_t - last_t)
    future_dates = pd.date_range(monthly["date"].max(), periods=months + 1, freq="ME")[1:]
    resid_std = float(monthly["Average"].diff().std() or 2.0)
    return pd.DataFrame(
        {
            "date": future_dates,
            "frontier_pred": pred,
            "lower": pred - 1.96 * resid_std,
            "upper": pred + 1.96 * resid_std,
        }
    )


def run_forecast_pipeline() -> dict[str, Any]:
    c6 = load_c6()
    bridge = fit_loss_benchmark_bridge(c6)
    save_json(bridge, output_dir("q4") / "bridge_model.json")

    c8 = load_c8_latest_json(limit=200)
    c8_agg = aggregate_c8(c8)
    c8_agg.to_csv(output_dir("q4") / "c8_task_aggregation.csv", index=False)

    c1 = load_c1()
    try:
        c4 = load_c4()
    except Exception:
        c4 = None
    decomp = decomposition(c1, c4)
    pd.DataFrame([decomp]).to_csv(output_dir("q4") / "decomposition_results.csv", index=False)

    f12 = forecast_frontier(c1, months=12)
    f24 = forecast_frontier(c1, months=24)
    f12.to_csv(output_dir("q4") / "frontier_forecast_12m.csv", index=False)
    f24.to_csv(output_dir("q4") / "frontier_forecast_24m.csv", index=False)

    result = {
        "bridge": bridge,
        "decomposition": decomp,
        "c8_models_aggregated": int(len(c8_agg)),
        "forecast_12m_last": float(f12["frontier_pred"].iloc[-1]) if len(f12) else None,
        "forecast_24m_last": float(f24["frontier_pred"].iloc[-1]) if len(f24) else None,
    }
    save_json(result, output_dir("q4") / "forecast_summary.json")
    return result
