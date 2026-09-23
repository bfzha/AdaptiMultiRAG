from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

from src.data.loaders import load_b1, load_b6_b8
from src.utils import output_dir, save_json


def classic_scaling(n: np.ndarray, d: np.ndarray, linf: float, a: float, alpha: float, beta: float) -> np.ndarray:
    return linf + a * (n ** (-alpha)) * (d ** (-beta))


def generalized_scaling(
    n: np.ndarray,
    d: np.ndarray,
    q: np.ndarray,
    linf: float,
    a: float,
    alpha: float,
    beta: float,
    gamma: float,
) -> np.ndarray:
    base = classic_scaling(n, d, linf, a, alpha, beta)
    return base * np.exp(-gamma * (1.0 - q))


def fit_b1() -> dict[str, float]:
    b1 = load_b1()
    n = b1["N_params_B"].values.astype(float)
    d = b1["D_tokens_B"].values.astype(float)
    y = b1["val_loss"].values.astype(float)
    p0 = [1.5, 2.0, 0.34, 0.28]
    bounds = ([0.5, 0.01, 0.05, 0.05], [4.0, 20.0, 1.0, 1.0])
    popt, _ = curve_fit(
        lambda nd, linf, a, alpha, beta: classic_scaling(nd[0], nd[1], linf, a, alpha, beta),
        (n, d),
        y,
        p0=p0,
        bounds=bounds,
        maxfev=20000,
    )
    linf, a, alpha, beta = popt
    pred = classic_scaling(n, d, linf, a, alpha, beta)
    ss_res = np.sum((y - pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot
    return {
        "L_inf": float(linf),
        "A": float(a),
        "alpha": float(alpha),
        "beta": float(beta),
        "r2": float(r2),
    }


def fit_quality_factor(base_params: dict[str, float]) -> dict[str, float]:
    b6 = load_b6_b8()
    if not b6:
        return {"gamma": 0.35, "note": "no B6-B8; using default gamma"}
    df = pd.concat(b6.values(), ignore_index=True)
    n = df["N_params_B"].values.astype(float)
    d = df["D_tokens_B"].values.astype(float)
    q = df["Q_score"].values.astype(float)
    y = df["val_loss"].values.astype(float)

    def model(ndq, gamma):
        linf, a, alpha, beta = (
            base_params["L_inf"],
            base_params["A"],
            base_params["alpha"],
            base_params["beta"],
        )
        return generalized_scaling(ndq[0], ndq[1], ndq[2], linf, a, alpha, beta, gamma)

    popt, _ = curve_fit(model, (n, d, q), y, p0=[0.3], bounds=([0.0], [2.0]), maxfev=20000)
    gamma = float(popt[0])
    pred = model((n, d, q), gamma)
    r2 = 1 - np.sum((y - pred) ** 2) / np.sum((y - y.mean()) ** 2)
    return {"gamma": gamma, "r2_b6": float(r2), "n_points": int(len(df))}


def compute_elasticities(params: dict[str, float], n: float, d: float, q: float = 0.8) -> dict[str, float]:
    linf, a, alpha, beta, gamma = (
        params["L_inf"],
        params["A"],
        params["alpha"],
        params["beta"],
        params.get("gamma", 0.35),
    )
    gq = np.exp(-gamma * (1 - q))
    core = a * (n ** (-alpha)) * (d ** (-beta)) * gq
    L = linf + core
    eps_n = -alpha * core / L
    eps_d = -beta * core / L
    eps_q = (gamma * core) / L  # dL/dQ * Q/L with Q=1 scale -> gamma*core/L*(1/L)*...
    return {"epsilon_N": float(eps_n), "epsilon_D": float(eps_d), "epsilon_Q": float(eps_q), "L": float(L)}


def substitution_delta_n(params: dict[str, float], d: float, q0: float, dq: float = 0.1) -> float:
    """Approximate Delta N such that quality increase dq compensates parameter change."""
    linf, a, alpha, beta, gamma = (
        params["L_inf"],
        params["A"],
        params["alpha"],
        params["beta"],
        params.get("gamma", 0.35),
    )
    n0 = 1.0
    L0 = generalized_scaling(np.array([n0]), np.array([d]), np.array([q0]), linf, a, alpha, beta, gamma)[0]
    L1 = generalized_scaling(np.array([n0]), np.array([d]), np.array([q0 + dq]), linf, a, alpha, beta, gamma)[0]
    dL = L1 - L0
    dL_dn = -alpha * (generalized_scaling(np.array([n0]), np.array([d]), np.array([q0 + dq]), linf, a, alpha, beta, gamma)[0] - linf) / n0
    if abs(dL_dn) < 1e-8:
        return float("nan")
    return float(-dL / dL_dn)


def validate_external(base: dict[str, float]) -> dict[str, Any]:
    from src.data.loaders import get_data_root

    out: dict[str, Any] = {}
    bdir = get_data_root() / "B_scaling_laws"
    cereb = bdir / "cerebras_training_log.csv"
    if cereb.exists():
        df = pd.read_csv(cereb)
        pred = classic_scaling(
            df["N_params_B"].values,
            df["D_tokens_B"].values,
            base["L_inf"],
            base["A"],
            base["alpha"],
            base["beta"],
        )
        y = df["val_loss"].values
        out["cerebras_rmse"] = float(np.sqrt(np.mean((y - pred) ** 2)))
    baseline = bdir / "scaling_baseline.csv"
    if baseline.exists():
        df = pd.read_csv(baseline)
        if "val_loss" in df.columns and "N_params_B" in df.columns:
            d_med = float(load_b1()["D_tokens_B"].median())
            pred = classic_scaling(
                df["N_params_B"].values,
                np.full(len(df), d_med),
                base["L_inf"],
                base["A"],
                base["alpha"],
                base["beta"],
            )
            out["baseline_rmse"] = float(np.sqrt(np.mean((df["val_loss"].values - pred) ** 2)))
    return out


def run_scaling_pipeline(q_baseline: float = 0.5) -> dict[str, Any]:
    base = fit_b1()
    qpart = fit_quality_factor(base)
    params = {**base, **qpart}

    n_ref, d_ref = float(load_b1()["N_params_B"].median()), float(load_b1()["D_tokens_B"].median())
    elast = compute_elasticities(params, n_ref, d_ref, q_baseline)
    delta_n = substitution_delta_n(params, d_ref, q_baseline, dq=0.1)

    elast_rows = []
    for q in [0.5, 0.6, 0.7, 0.8, 0.9]:
        e = compute_elasticities(params, n_ref, d_ref, q)
        e["Q"] = q
        elast_rows.append(e)
    pd.DataFrame(elast_rows).to_csv(output_dir("q2") / "elasticity_table.csv", index=False)

    sub = {
        "quality_increase": 0.1,
        "equivalent_delta_N_at_N=1B": delta_n,
        "interpretation": "Delta N such that raising Q by 0.1 matches loss change from scaling N",
    }
    save_json(sub, output_dir("q2") / "substitution_conditions.json")

    validation = validate_external(base)
    result = {
        "params": params,
        "elasticities_at_median": elast,
        "substitution": sub,
        "validation": validation,
        "Q_baseline": q_baseline,
    }
    save_json(result, output_dir("q2") / "scaling_law_params.json")
    return result
