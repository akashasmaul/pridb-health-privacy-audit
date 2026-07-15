"""Differentially private aggregate queries using the Laplace mechanism."""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from diffprivlib.mechanisms import Laplace
from tabulate import tabulate

EPSILON_VALUES = [0.1, 0.5, 1.0]
N_TRIALS = 100


class DPQueryEngine:
    def __init__(self, df: pd.DataFrame, epsilon: float, random_state: int | None = None):
        if epsilon <= 0:
            raise ValueError("epsilon must be greater than zero")
        self.df = df
        self.epsilon = float(epsilon)
        self.random_state = random_state

    def _laplace(self, sensitivity: float) -> Laplace:
        return Laplace(epsilon=self.epsilon, sensitivity=sensitivity, random_state=self.random_state)

    def dp_count(self, condition: pd.Series | None = None) -> dict[str, float | str]:
        true_value = int(condition.sum()) if condition is not None else len(self.df)
        private_value = max(0, round(self._laplace(1.0).randomise(true_value)))
        return {"query": "COUNT(*)", "true_value": true_value, "dp_value": private_value, "error": abs(private_value - true_value), "epsilon": self.epsilon}

    def dp_avg(self, column: str, lower: float, upper: float) -> dict[str, float | str]:
        if lower >= upper:
            raise ValueError("lower must be smaller than upper")
        clipped = self.df[column].clip(lower, upper)
        true_value = float(clipped.mean())
        sensitivity = (upper - lower) / max(1, len(clipped))
        private_value = float(np.clip(self._laplace(sensitivity).randomise(true_value), lower, upper))
        return {"query": f"AVG({column})", "true_value": round(true_value, 4), "dp_value": round(private_value, 4), "error": round(abs(private_value - true_value), 4), "epsilon": self.epsilon}


def run_trial_analysis(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for epsilon in EPSILON_VALUES:
        count_errors, average_errors = [], []
        for trial in range(N_TRIALS):
            engine = DPQueryEngine(df, epsilon, random_state=SEED_BASE + trial)
            count_errors.append(engine.dp_count()["error"])
            average_errors.append(engine.dp_avg("age", 0, 100)["error"])
        rows.append({
            "epsilon": epsilon,
            "privacy_level": "High" if epsilon <= 0.1 else ("Medium" if epsilon <= 0.5 else "Low"),
            "count_mean_error": round(float(np.mean(count_errors)), 4),
            "count_std_error": round(float(np.std(count_errors)), 4),
            "avg_age_mean_error": round(float(np.mean(average_errors)), 4),
            "avg_age_std_error": round(float(np.std(average_errors)), 4),
            "n_trials": N_TRIALS,
        })
    return pd.DataFrame(rows)


SEED_BASE = 7300


def demonstrate_queries(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for index, epsilon in enumerate(EPSILON_VALUES):
        engine = DPQueryEngine(df, epsilon, random_state=SEED_BASE + 100 + index)
        hypertension = df["diagnosis_name"].eq("Essential Hypertension")
        for result, description in [
            (engine.dp_count(hypertension), "COUNT: Hypertension patients"),
            (engine.dp_avg("age", 0, 100), "AVG: Patient age"),
            (engine.dp_count(), "COUNT: All patients"),
        ]:
            rows.append({"epsilon": epsilon, "Query": description, "True": result["true_value"], "DP_Value": result["dp_value"], "Error": result["error"]})
    output = pd.DataFrame(rows)
    output.to_csv("outputs/tables/03_dp_query_demo.csv", index=False)
    return output


def main() -> pd.DataFrame:
    from quasi_identifier_analysis import load_data

    os.makedirs("outputs/tables", exist_ok=True)
    os.makedirs("outputs/charts", exist_ok=True)
    df = load_data()
    demo = demonstrate_queries(df)
    trials = run_trial_analysis(df)
    trials.to_csv("outputs/tables/03b_dp_trials.csv", index=False)
    print(tabulate(demo, headers="keys", tablefmt="grid", showindex=False))
    print(tabulate(trials, headers="keys", tablefmt="grid", showindex=False))
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    labels = trials["epsilon"].astype(str)
    colors = ["#c0392b", "#e67e22", "#27ae60"]
    axes[0].bar(labels, trials["count_mean_error"], color=colors, edgecolor="black")
    axes[0].set(xlabel="epsilon", ylabel="Mean absolute count error", title="COUNT utility cost")
    axes[1].bar(labels, trials["avg_age_mean_error"], color=colors, edgecolor="black")
    axes[1].set(xlabel="epsilon", ylabel="Mean absolute age error", title="AVG(age) utility cost")
    fig.suptitle("Differential Privacy: Privacy-Utility Trade-off", fontweight="bold")
    fig.tight_layout()
    fig.savefig("outputs/charts/03_dp_tradeoff.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    return trials


if __name__ == "__main__":
    main()

