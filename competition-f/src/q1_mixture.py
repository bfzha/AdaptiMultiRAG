from __future__ import annotations

from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.data.constants import DOMAIN_COLS, LOSS_COLS
from src.data.loaders import get_data_root, load_regmix_pair, merge_regmix
from src.utils import clr_transform, output_dir, save_json


def fit_mixture_model(train_df: pd.DataFrame, q_domain: pd.DataFrame | None = None) -> dict[str, Any]:
    r = train_df[DOMAIN_COLS].values
    X = clr_transform(r)[:, :-1]  # n-1 clr coords
    y = train_df["mean_loss"].values
    if q_domain is not None and "Q_domain" in q_domain.columns:
        q_mean = float(q_domain["Q_domain"].mean())
        X = np.column_stack([X, np.full(len(y), q_mean)])
        feature_names = [f"clr_{i}" for i in range(X.shape[1] - 1)] + ["Q_mean"]
    else:
        feature_names = [f"clr_{i}" for i in range(X.shape[1])]

    model = RandomForestRegressor(n_estimators=200, max_depth=12, random_state=42, n_jobs=-1)
    model.fit(X, y)
    pred = model.predict(X)
    return {
        "model": model,
        "feature_names": feature_names,
        "use_q_feature": q_domain is not None,
        "train_r2": float(r2_score(y, pred)),
        "train_rmse": float(np.sqrt(mean_squared_error(y, pred))),
    }


def evaluate_split(
    model: RandomForestRegressor,
    mix: pd.DataFrame,
    loss: pd.DataFrame,
    q_mean: float,
    use_q_feature: bool,
    target_scale_m: float = 1.0,
    beta_scale: float = 0.05,
) -> dict[str, float]:
    df = merge_regmix(mix, loss)
    r = df[DOMAIN_COLS].values
    X = clr_transform(r)[:, :-1]
    if use_q_feature:
        X = np.column_stack([X, np.full(len(df), q_mean)])
    pred = model.predict(X)
    if target_scale_m != 1.0:
        pred = pred * ((target_scale_m / 1.0) ** (-beta_scale))
    y = df["mean_loss"].values
    return {
        "rmse": float(np.sqrt(mean_squared_error(y, pred))),
        "mae": float(mean_absolute_error(y, pred)),
        "r2": float(r2_score(y, pred)),
        "n": int(len(y)),
        "scale_m": target_scale_m,
    }


def run_mixture_pipeline(q_domain: pd.DataFrame | None = None) -> dict[str, Any]:
    train_mix, train_loss = load_regmix_pair("train_mixture_1m.csv", "train_pile_loss_1m.csv")
    train_df = merge_regmix(train_mix, train_loss)
    q_mean = float(q_domain["Q_domain"].mean()) if q_domain is not None and len(q_domain) else 0.5

    fitted = fit_mixture_model(train_df, q_domain)
    model: RandomForestRegressor = fitted["model"]

    validation = {}
    splits = [
        ("test_1m", "test_mixture_1m.csv", "test_pile_loss_1m.csv", 1.0),
        ("test_60m", "test_mixture_60m.csv", "test_pile_loss_60m.csv", 60.0),
        ("test_1B", "test_mixture_1B.csv", "test_pile_loss_1B.csv", 1000.0),
        ("est_10b", "est_mixture_10b.csv", "est_pile_loss_10b.csv", 10000.0),
        ("est_70b", "est_mixture_70b.csv", "est_pile_loss_70b.csv", 70000.0),
    ]
    tables = get_data_root() / "A_data_value/regmix_tables"
    for name, mix_f, loss_f, scale_m in splits:
        if (tables / mix_f).exists() and (tables / loss_f).exists():
            mix, loss = load_regmix_pair(mix_f, loss_f)
            validation[name] = evaluate_split(
                model, mix, loss, q_mean, fitted["use_q_feature"], target_scale_m=scale_m
            )

    joblib.dump(model, output_dir("q1") / "mixture_loss_model.pkl")
    result = {
        "train_r2": fitted["train_r2"],
        "train_rmse": fitted["train_rmse"],
        "feature_names": fitted["feature_names"],
        "validation": validation,
        "q_mean_used": q_mean,
    }
    save_json(result, output_dir("q1") / "mixture_validation.json")
    return result
