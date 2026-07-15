"""Generate the five paper figures and two paper tables required by the guide."""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
OUT = Path("outputs/paper_figures")
OUT.mkdir(parents=True, exist_ok=True)

COLORS = {"None": "#D73027", "L1": "#F39C12", "L1+L2": "#3498DB", "L1+L2+L3": "#27AE60"}


def save(fig: plt.Figure, stem: str) -> None:
    fig.savefig(OUT / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def figure1(qi: pd.DataFrame) -> None:
    grouped = qi.groupby("Num_QIs", as_index=False)["RRR"].mean()
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    bars = ax.bar(grouped["Num_QIs"], grouped["RRR"], color="#D73027", edgecolor="black")
    ax.set(xlabel="Number of combined quasi-identifiers", ylabel="Mean RRR", ylim=(0, 1.05), title="Baseline Re-identification Risk")
    ax.bar_label(bars, fmt="%.3f", padding=2, fontsize=8)
    ax.grid(axis="y", alpha=0.25)
    save(fig, "fig1_baseline_risk")


def figure2(kanon: pd.DataFrame) -> None:
    fig, left = plt.subplots(figsize=(6.5, 3.6))
    right = left.twinx()
    left.plot(kanon["k"], kanon["RRR_After"], "o-", color="#D73027", label="RRR")
    right.plot(kanon["k"], kanon["NCP"], "s--", color="#3498DB", label="NCP")
    left.set(xlabel="k", ylabel="Re-identification Risk", title="k-Anonymity Privacy-Utility Trade-off")
    right.set_ylabel("Normalized Certainty Penalty")
    left.grid(alpha=0.25)
    lines = left.lines + right.lines
    left.legend(lines, [line.get_label() for line in lines], loc="best")
    save(fig, "fig2_kanon_tradeoff")


def figure3(dp: pd.DataFrame) -> None:
    x = np.arange(len(dp))
    width = 0.36
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    ax.bar(x - width / 2, dp["count_mean_error"], width, label="COUNT error", color="#D73027")
    ax.bar(x + width / 2, dp["avg_age_mean_error"], width, label="AVG(age) error", color="#3498DB")
    ax.set_xticks(x, [str(value) for value in dp["epsilon"]])
    ax.set(xlabel="Privacy budget epsilon", ylabel="Mean absolute error", title="Differential Privacy Utility Cost")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    save(fig, "fig3_dp_results")


def short_label(value: str) -> str:
    return (value.replace("Baseline (No Protection)", "Baseline")
            .replace("RBAC Only (Layer 1)", "RBAC")
            .replace("RBAC + ", "").replace(" Anon (L1+L2)", "")
            .replace("All 3 Layers ", "3L "))


def figure4(prs: pd.DataFrame) -> None:
    colors = [COLORS[layer] for layer in prs["Layers_Active"]]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.1))
    bars = axes[0].bar(range(len(prs)), prs["PRS"], color=colors, edgecolor="black")
    axes[0].set_xticks(range(len(prs)), [short_label(value) for value in prs["Scenario"]], rotation=38, ha="right", fontsize=7)
    axes[0].set(ylabel="PRS (lower is better)", ylim=(0, 1.05), title="(a) Privacy Risk by Configuration")
    axes[0].bar_label(bars, fmt="%.3f", padding=2, fontsize=6)
    axes[1].scatter(prs["Utility_Loss_%"], prs["PRS"], c=colors, edgecolors="black", s=90)
    axes[1].set(xlabel="Utility Loss (NCP × 100)", ylabel="PRS", title="(b) Privacy-Utility Trade-off")
    axes[1].grid(alpha=0.25)
    axes[1].legend(handles=[mpatches.Patch(color=color, label=layer) for layer, color in COLORS.items()], fontsize=8)
    fig.suptitle("PriDB-Health Privacy Risk Score — Main Experimental Result", fontweight="bold")
    fig.tight_layout()
    save(fig, "fig4_prs_main_result")


def figure5(prs: pd.DataFrame) -> None:
    stages = ["Baseline", "Layer 1\nRBAC + RLS", "Layer 2\nk-anonymity", "Layer 3\nepsilon-DP"]
    values = [
        float(prs.loc[prs["Layers_Active"].eq("None"), "PRS"].iloc[0]),
        float(prs.loc[prs["Layers_Active"].eq("L1"), "PRS"].iloc[0]),
        float(prs.loc[prs["Layers_Active"].eq("L1+L2"), "PRS"].min()),
        float(prs.loc[prs["Layers_Active"].eq("L1+L2+L3"), "PRS"].min()),
    ]
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(stages, values, color=list(COLORS.values()), edgecolor="black", width=0.62)
    ax.set(ylabel="Privacy Risk Score", ylim=(0, 1.08), title="Cumulative PRS Reduction by Privacy Layer")
    ax.bar_label(bars, labels=[f"PRS={value:.3f}" for value in values], padding=3, fontsize=8, fontweight="bold")
    for index in range(1, len(values)):
        reduction = values[index - 1] - values[index]
        ax.annotate(f"−{reduction:.3f}", xy=(index, values[index]), xytext=(index - 0.55, values[index - 1] - 0.04),
                    arrowprops={"arrowstyle": "->", "color": "#1B5E20"}, color="#1B5E20", fontweight="bold")
    ax.grid(axis="y", alpha=0.25)
    save(fig, "fig5_prs_waterfall")


def table_figure(frame: pd.DataFrame, title: str, stem: str) -> None:
    display = frame.copy()
    for column in display.select_dtypes(include="number"):
        display[column] = display[column].map(lambda value: f"{value:.4g}")
    fig_height = max(2.2, 0.35 * (len(display) + 2))
    fig, ax = plt.subplots(figsize=(12, fig_height))
    ax.axis("off")
    table = ax.table(cellText=display.values, colLabels=display.columns, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(7)
    table.auto_set_column_width(range(len(display.columns)))
    for column in range(len(display.columns)):
        table[0, column].set_facecolor("#1F4E79")
        table[0, column].set_text_props(color="white", fontweight="bold")
    ax.set_title(title, fontweight="bold", pad=10)
    save(fig, stem)
    frame.to_csv(OUT / f"{stem}.csv", index=False)


def main() -> None:
    qi = pd.read_csv("outputs/tables/01_qi_risk_analysis.csv")
    kanon = pd.read_csv("outputs/tables/02_kanon_results.csv")
    dp = pd.read_csv("outputs/tables/03b_dp_trials.csv")
    prs = pd.read_csv("outputs/tables/04_prs_results.csv", keep_default_na=False)
    figure1(qi)
    figure2(kanon)
    figure3(dp)
    figure4(prs)
    figure5(prs)
    table_figure(prs[["Scenario", "Layers_Active", "k", "epsilon", "RRR", "NCP", "PRS"]], "Table I: Privacy Risk Score Summary", "table1_prs_visual")
    table_figure(kanon[["k", "Records_Kept", "Records_Suppressed", "NCP", "RRR_After", "l2_satisfied", "t03_satisfied"]], "Table II: k-Anonymity Results", "table2_kanon_results")
    print(f"Generated paper artifacts in {OUT.resolve()}")


if __name__ == "__main__":
    main()
