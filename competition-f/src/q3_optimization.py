from __future__ import annotations

from typing import Any, Callable

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from src.data.loaders import load_c7
from src.utils import output_dir, save_json


def cq_exponential(q0: float, q: float, kappa: float = 1e19, lam: float = 5.0) -> float:
    if q <= q0:
        return 0.0
    return kappa * (np.exp(lam * (q - q0)) - 1.0)


def cq_power(q0: float, q: float, kappa: float = 1e20, beta: float = 2.0) -> float:
    if q <= q0:
        return 0.0
    return kappa * ((q - q0) ** beta)


def cq_log(q0: float, q: float, kappa: float = 1e20) -> float:
    if q <= q0:
        return 0.0
    eps = 1e-6
    return kappa * np.log((1.0 - q0 + eps) / (1.0 - q + eps))


def loss_generalized(n: float, d: float, q: float, params: dict[str, float]) -> float:
    linf = params["L_inf"]
    a, alpha, beta, gamma = params["A"], params["alpha"], params["beta"], params.get("gamma", 0.35)
    core = a * (n ** (-alpha)) * (d ** (-beta)) * np.exp(-gamma * (1.0 - q))
    return float(linf + core)


FLOP_SCALE = 1e18  # N,D in billions -> C_train = 6*N*D*1e18 FLOPs


def training_flops(n: float, d: float) -> float:
    return 6.0 * n * d * FLOP_SCALE


def critical_context_length(n: float, d: float, k: float = 1e9) -> float:
    """Solve k L^2 = training_flops(n,d) for context length L."""
    tf = max(training_flops(n, d), 1e-12)
    return float(np.sqrt(tf / k))


def optimize_allocation(
    c_total: float,
    params: dict[str, float],
    q0: float,
    l_ctx: float,
    cq_fn: Callable[[float, float], float],
    k_attn: float = 1e9,
) -> dict[str, float]:
    attn = k_attn * (l_ctx ** 2)
    budget = max(c_total - attn, c_total * 0.01)

    def objective(x: np.ndarray) -> float:
        n, d, q = x
        return loss_generalized(n, d, q, params)

    def constraint(x: np.ndarray) -> float:
        n, d, q = x
        return budget - (training_flops(n, d) + cq_fn(q0, q))

    x0 = np.array([1.0, 100.0, min(0.99, q0 + 0.1)])
    bounds = [(1e-4, 1e3), (1.0, 1e5), (q0, 1.0)]
    cons = {"type": "ineq", "fun": constraint}
    res = minimize(objective, x0, method="SLSQP", bounds=bounds, constraints=cons, options={"maxiter": 500})
    n, d, q = res.x
    train = training_flops(n, d)
    cq = cq_fn(q0, q)
    return {
        "N_params_B": float(n),
        "D_tokens_B": float(d),
        "Q": float(q),
        "L_ctx": float(l_ctx),
        "C_train": float(train),
        "C_quality": float(cq),
        "C_attention": float(attn),
        "C_total": float(c_total),
        "Loss": float(res.fun),
        "success": bool(res.success),
        "budget_used": float(train + cq + attn),
    }


def detect_structural_shifts(scan_results: pd.DataFrame) -> dict[str, Any]:
    df = scan_results.sort_values("C_total")
    logc = np.log10(df["C_total"].values)
    shares = df[["share_ND", "share_Q", "share_attn"]].values
    shifts = []
    for j, name in enumerate(["share_ND", "share_Q", "share_attn"]):
        y = shares[:, j]
        dy = np.diff(y)
        if len(dy):
            idx = int(np.argmax(np.abs(dy)))
            shifts.append({"variable": name, "jump_at_index": idx, "jump_size": float(dy[idx])})
    return {"shifts": shifts, "n_budget_points": int(len(df))}


def run_optimization_pipeline(params: dict[str, float], q0: float = 0.5) -> dict[str, Any]:
    budgets = [1e20, 1e22, 1e24]
    cq_forms = {
        "exponential": cq_exponential,
        "power": cq_power,
        "log": cq_log,
    }

    try:
        c7 = load_c7()
        ctx_lengths = c7["max_position_embeddings"].dropna().astype(float).unique().tolist()
    except Exception:
        ctx_lengths = [2048.0, 4096.0, 8192.0, 32768.0]

    if not ctx_lengths:
        ctx_lengths = [2048.0, 8192.0]

    rows = []
    for cq_name, cq_fn in cq_forms.items():
        for c in budgets:
            for l_ctx in ctx_lengths[:4]:
                n_med, d_med = 1.0, 100.0
                l_star = critical_context_length(n_med, d_med)
                opt = optimize_allocation(c, params, q0, l_ctx, cq_fn)
                opt["cq_form"] = cq_name
                opt["L_star_nd_match"] = l_star
                opt["share_ND"] = opt["C_train"] / c
                opt["share_Q"] = opt["C_quality"] / c
                opt["share_attn"] = opt["C_attention"] / c
                rows.append(opt)

    df = pd.DataFrame(rows)
    df.to_csv(output_dir("q3") / "optimal_configs.csv", index=False)

    # Budget scan for shift detection (exponential cq, median context)
    l_med = float(np.median(ctx_lengths))
    scan = []
    for exp in np.linspace(19.5, 24.5, 15):
        c = 10 ** exp
        opt = optimize_allocation(c, params, q0, l_med, cq_exponential)
        opt["C_total"] = c
        opt["share_ND"] = opt["C_train"] / c
        opt["share_Q"] = opt["C_quality"] / c
        opt["share_attn"] = opt["C_attention"] / c
        scan.append(opt)
    scan_df = pd.DataFrame(scan)
    shifts = detect_structural_shifts(scan_df)

    sens = []
    n_ref, d_ref = 1.0, 100.0
    for l_ctx in ctx_lengths:
        sens.append(
            {
                "L_ctx": l_ctx,
                "L_star": critical_context_length(n_ref, d_ref),
                "attn_cost": 1e9 * l_ctx ** 2,
            }
        )
    pd.DataFrame(sens).to_csv(output_dir("q3") / "L_sensitivity.csv", index=False)

    result = {
        "budgets": budgets,
        "structural_shifts": shifts,
        "L_star_at_n1_d100": critical_context_length(1.0, 100.0),
        "context_lengths": ctx_lengths,
    }
    save_json(result, output_dir("q3") / "structural_shift_analysis.json")
    save_json(result, output_dir("q3") / "optimization_summary.json")
    return result
