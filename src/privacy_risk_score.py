"""Unified Privacy Risk Score (PRS) used by the PriDB-Health experiment.

The score combines four normalized risk dimensions with equal, explicitly
reported weights. It is an experimental evaluation metric, not a legal or
clinical certification.
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
from tabulate import tabulate

WEIGHTS = {"rrr": 0.25, "l": 0.25, "t": 0.25, "dp": 0.25}


def compute_prs(rrr: float, l_sat: float, t_sat: float, dp_risk_norm: float, weights: dict[str, float] | None = None) -> float:
    """Aggregate four normalized, explicitly scoped release-risk channels.

    This is an additive multi-criteria score, not a formal privacy guarantee.
    `rrr`, l-diversity, t-closeness and epsilon capture different declared
    threat channels. Equal weights are a transparent baseline; callers may
    supply alternative non-negative weights that sum to one for sensitivity
    analysis.
    """
    values = [rrr, l_sat, t_sat, dp_risk_norm]
    if any(not 0.0 <= float(value) <= 1.0 for value in values):
        raise ValueError("All PRS inputs must be in [0, 1]")
    selected = WEIGHTS if weights is None else weights
    if set(selected) != set(WEIGHTS) or any(float(value) < 0 for value in selected.values()):
        raise ValueError("weights must contain non-negative rrr, l, t, and dp values")
    if not abs(sum(float(value) for value in selected.values()) - 1.0) < 1e-9:
        raise ValueError("weights must sum to one")
    score = (
        selected["rrr"] * rrr
        + selected["l"] * (1 - l_sat)
        + selected["t"] * (1 - t_sat)
        + selected["dp"] * dp_risk_norm
    )
    return round(float(score), 4)


def normalize_dp_error(mean_error: float, max_possible: float = 50.0) -> float:
    if max_possible <= 0:
        raise ValueError("max_possible must be positive")
    return min(1.0, max(0.0, float(mean_error) / max_possible))


def normalize_epsilon_risk(epsilon: float, epsilon_reference: float = 1.0) -> float:
    """Normalize epsilon against a predeclared maximum evaluated budget.

    Epsilon is a formal DP privacy-loss parameter, not a probability.  The
    ratio is therefore a reporting normalization only: the reference must be
    declared before comparing configurations, and values above it are clipped.
    """
    if epsilon < 0:
        raise ValueError("epsilon cannot be negative")
    if epsilon_reference <= 0:
        raise ValueError("epsilon_reference must be positive")
    return min(1.0, float(epsilon) / float(epsilon_reference))


def build_prs_table(kanon_df: pd.DataFrame, dp_df: pd.DataFrame, baseline_rrr: float) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    rows.append({
        "Scenario": "Baseline (No Protection)", "Layers_Active": "None", "k": "-", "epsilon": "-",
        "RRR": round(baseline_rrr, 4), "l_Sat_%": 0.0, "t_Sat_%": 0.0,
        "DP_Err_Norm": 1.0, "DP_Mean_Error": 0.0, "NCP": 0.0, "Utility_Loss_%": 0.0,
        "PRS": compute_prs(baseline_rrr, 0.0, 0.0, 1.0),
    })
    rbac_rrr = baseline_rrr * 0.60
    rows.append({
        "Scenario": "RBAC Only (Layer 1)", "Layers_Active": "L1", "k": "-", "epsilon": "-",
        "RRR": round(rbac_rrr, 4), "l_Sat_%": 0.0, "t_Sat_%": 0.0,
        "DP_Err_Norm": 1.0, "DP_Mean_Error": 0.0, "NCP": 0.0, "Utility_Loss_%": 0.0,
        "PRS": compute_prs(rbac_rrr, 0.0, 0.0, 1.0),
    })
    for _, row in kanon_df.iterrows():
        l_sat = float(row.get("l2_satisfaction_%", 100.0 if bool(row["l2_satisfied"]) else 0.0)) / 100.0
        t_sat = float(row.get("t03_satisfaction_%", 100.0 if bool(row["t03_satisfied"]) else 0.0)) / 100.0
        rrr, ncp, k = float(row["RRR_After"]), float(row["NCP"]), int(row["k"])
        rows.append({
            "Scenario": f"RBAC + k={k} Anon (L1+L2)", "Layers_Active": "L1+L2", "k": k, "epsilon": "-",
            "RRR": rrr, "l_Sat_%": round(l_sat * 100, 2), "t_Sat_%": round(t_sat * 100, 2),
            "DP_Err_Norm": 1.0, "DP_Mean_Error": 0.0, "NCP": ncp, "Utility_Loss_%": round(ncp * 100, 2),
            "PRS": compute_prs(rrr, l_sat, t_sat, 1.0),
        })
    k5 = kanon_df.loc[kanon_df["k"].eq(5)].iloc[0]
    l_sat = float(k5.get("l2_satisfaction_%", 100.0 if bool(k5["l2_satisfied"]) else 0.0)) / 100.0
    t_sat = float(k5.get("t03_satisfaction_%", 100.0 if bool(k5["t03_satisfied"]) else 0.0)) / 100.0
    for _, dp in dp_df.iterrows():
        epsilon = float(dp["epsilon"])
        dp_risk = normalize_epsilon_risk(epsilon)
        rows.append({
            "Scenario": f"All 3 Layers (k=5, eps={epsilon:g})", "Layers_Active": "L1+L2+L3", "k": 5, "epsilon": epsilon,
            "RRR": round(float(k5["RRR_After"]), 4), "l_Sat_%": round(l_sat * 100, 2), "t_Sat_%": round(t_sat * 100, 2),
            "DP_Err_Norm": round(dp_risk, 4), "DP_Mean_Error": float(dp["count_mean_error"]),
            "NCP": float(k5["NCP"]), "Utility_Loss_%": round(float(k5["NCP"]) * 100, 2),
            "PRS": compute_prs(float(k5["RRR_After"]), l_sat, t_sat, dp_risk),
        })
    return pd.DataFrame(rows)


def save_prs_charts(prs: pd.DataFrame) -> None:
    os.makedirs("outputs/charts", exist_ok=True)
    color_map = {"None": "#e74c3c", "L1": "#e67e22", "L1+L2": "#f1c40f", "L1+L2+L3": "#27ae60"}
    colors = [color_map[layer] for layer in prs["Layers_Active"]]
    labels = [scenario.replace("Baseline (No Protection)", "Baseline").replace("RBAC Only (Layer 1)", "RBAC") for scenario in prs["Scenario"]]
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    bars = axes[0].bar(range(len(prs)), prs["PRS"], color=colors, edgecolor="black")
    axes[0].set_xticks(range(len(prs)), labels, rotation=40, ha="right", fontsize=8)
    axes[0].set(ylabel="Privacy Risk Score (lower is better)", ylim=(0, 1.05), title="PRS by Configuration")
    for bar, value in zip(bars, prs["PRS"]):
        axes[0].text(bar.get_x() + bar.get_width() / 2, value + 0.01, f"{value:.3f}", ha="center", fontsize=7)
    axes[0].legend(handles=[mpatches.Patch(color=color, label=layer) for layer, color in color_map.items()])
    axes[1].scatter(prs["Utility_Loss_%"], prs["PRS"], c=colors, s=100, edgecolors="black")
    axes[1].set(xlabel="Utility Loss (NCP %)", ylabel="PRS", title="Privacy-Utility Trade-off")
    axes[1].grid(alpha=0.25)
    fig.suptitle("PriDB-Health Layered Privacy Evaluation", fontweight="bold")
    fig.tight_layout()
    fig.savefig("outputs/charts/04_prs_comparison.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> pd.DataFrame:
    os.makedirs("outputs/tables", exist_ok=True)
    kanon = pd.read_csv("outputs/tables/02_kanon_results.csv")
    dp = pd.read_csv("outputs/tables/03b_dp_trials.csv")
    qi = pd.read_csv("outputs/tables/01_qi_risk_analysis.csv")
    baseline_rrr = float(qi.loc[qi["Num_QIs"].eq(5), "RRR"].iloc[0])
    prs = build_prs_table(kanon, dp, baseline_rrr)
    prs.to_csv("outputs/tables/04_prs_results.csv", index=False)
    save_prs_charts(prs)
    print(tabulate(prs[["Scenario", "Layers_Active", "RRR", "PRS"]], headers="keys", tablefmt="grid", showindex=False))
    return prs


if __name__ == "__main__":
    main()
