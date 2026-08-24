"""Cross-dataset charts.  These compare measured outputs, never cohort identities."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def main() -> None:
    out = Path("outputs/comparative")
    out.mkdir(parents=True, exist_ok=True)
    synthetic_qi = pd.read_csv("outputs/tables/01_qi_risk_analysis.csv")
    synthetic_k = pd.read_csv("outputs/tables/02_kanon_results.csv")
    synthetic_dp = pd.read_csv("outputs/tables/03b_dp_trials.csv")
    uci_qi = pd.read_csv("outputs/uci_heart/01_qi_risk_analysis.csv")
    uci_k = pd.read_csv("outputs/uci_heart/02_kanon_results.csv")
    uci_dp = pd.read_csv("outputs/uci_heart/03_dp_trials.csv")

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    profile = pd.DataFrame({
        "Dataset": ["Synthetic", "UCI Cleveland"],
        "Baseline RRR": [synthetic_qi.loc[synthetic_qi["Num_QIs"].eq(5), "RRR"].iloc[0], uci_qi.loc[uci_qi["Num_QIs"].eq(4), "RRR"].iloc[0]],
    })
    axes[0].bar(profile["Dataset"], profile["Baseline RRR"], color=["#4C78A8", "#E45756"], edgecolor="black")
    axes[0].set(title="Raw-release RRR", ylabel="RRR", ylim=(0, 1)); axes[0].grid(axis="y", alpha=.3)
    for frame, label, color in [(synthetic_k, "Synthetic", "#4C78A8"), (uci_k, "UCI Cleveland", "#E45756")]:
        axes[1].plot(frame["k"], frame["Suppression_%"], "o-", label=label, color=color)
    axes[1].set(title="Suppression trade-off", xlabel="k", ylabel="Suppressed (%)"); axes[1].legend(); axes[1].grid(alpha=.3)
    for frame, label, color in [(synthetic_dp, "Synthetic", "#4C78A8"), (uci_dp, "UCI Cleveland", "#E45756")]:
        axes[2].plot(frame["epsilon"], frame["count_mean_error"], "o-", label=label, color=color)
    axes[2].set(title="DP count accuracy (100 trials)", xlabel="ε", ylabel="Mean absolute error"); axes[2].legend(); axes[2].grid(alpha=.3)
    fig.suptitle("PriDB-Health: synthetic control versus public UCI benchmark", fontweight="bold")
    fig.tight_layout(); fig.savefig(out / "01_cross_dataset_comparison.png", dpi=220); plt.close(fig)


if __name__ == "__main__":
    main()
