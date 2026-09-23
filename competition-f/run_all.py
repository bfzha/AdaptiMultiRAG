#!/usr/bin/env python3
"""Run full F-problem modeling pipeline (Q1-Q4)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from scripts.bootstrap_data import main as bootstrap  # noqa: E402
from src.q1_conflict import run_conflict_pipeline  # noqa: E402
from src.q1_mixture import run_mixture_pipeline  # noqa: E402
from src.q1_quality import run_quality_pipeline  # noqa: E402
from src.q2_scaling_law import run_scaling_pipeline  # noqa: E402
from src.q3_optimization import run_optimization_pipeline  # noqa: E402
from src.q4_forecast import run_forecast_pipeline  # noqa: E402


def main() -> None:
    print("=== Bootstrap missing data ===")
    bootstrap()

    print("\n=== Q1: Quality ===")
    q1 = run_quality_pipeline()
    w = [q1["meta"]["weights"][k] for k in q1["meta"]["weights"]]
    import numpy as np

    conflict = run_conflict_pipeline(q1["scored"], np.array(list(q1["meta"]["weights"].values())))
    mixture = run_mixture_pipeline(q1["domain_q"])
    print(f"Q1 train R2={mixture['train_r2']:.4f}, conflict_rate={conflict['stats']['conflict_rate_all']:.4f}")

    print("\n=== Q2: Scaling law ===")
    q0 = q1["meta"]["Q_baseline"]
    q2 = run_scaling_pipeline(q_baseline=q0)
    print(f"Q2 alpha={q2['params']['alpha']:.4f}, gamma={q2['params'].get('gamma', 'n/a')}")

    print("\n=== Q3: Optimization ===")
    q3 = run_optimization_pipeline(q2["params"], q0=q0)
    print(f"Q3 L*={q3['L_star_at_n1_d100']:.2f}, shifts={len(q3['structural_shifts']['shifts'])}")

    print("\n=== Q4: Forecast ===")
    q4 = run_forecast_pipeline()
    print(f"Q4 scale_share={q4['decomposition']['scale_share']:.3f}, 24m frontier={q4['forecast_24m_last']}")

    print("\n=== Pipeline complete ===")
    print(f"Outputs: {ROOT / 'outputs'}")


if __name__ == "__main__":
    main()
