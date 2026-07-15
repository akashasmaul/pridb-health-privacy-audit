"""Measure baseline re-identification risk from quasi-identifiers."""

from __future__ import annotations

import os
from itertools import combinations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from tabulate import tabulate

QI_COLS = ["age", "gender", "zip_code", "marital_status", "ethnicity"]
SENSITIVE_COL = "diagnosis_name"


def load_data(patient_path: str = "data/raw/patients.csv", diagnoses_path: str = "data/raw/diagnoses.csv") -> pd.DataFrame:
    patients = pd.read_csv(patient_path, dtype={"zip_code": str})
    diagnoses = pd.read_csv(diagnoses_path)
    severity_order = {"Critical": 4, "Severe": 3, "Moderate": 2, "Mild": 1}
    diagnoses["severity_rank"] = diagnoses["severity"].map(severity_order).fillna(0)
    primary_dx = (
        diagnoses.sort_values(["patient_id", "severity_rank", "diagnosis_id"], ascending=[True, False, True])
        .groupby("patient_id", as_index=False)
        .first()[["patient_id", "diagnosis_name", "severity", "is_chronic"]]
    )
    return patients.merge(primary_dx, on="patient_id", how="inner", validate="one_to_one")


def compute_equivalence_class_sizes(df: pd.DataFrame, qi_cols: list[str]) -> pd.Series:
    if df.empty:
        return pd.Series(dtype="int64", index=df.index)
    return df.groupby(qi_cols, dropna=False, observed=True)["patient_id"].transform("count")


def compute_rrr(df: pd.DataFrame, qi_cols: list[str]) -> float:
    if df.empty:
        return 0.0
    return float((compute_equivalence_class_sizes(df, qi_cols) == 1).mean())


def compute_prosecutor_risk(df: pd.DataFrame, qi_cols: list[str]) -> float:
    if df.empty:
        return 0.0
    return float((1.0 / compute_equivalence_class_sizes(df, qi_cols)).mean())


def analyze_qi_combinations(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for size in range(1, len(QI_COLS) + 1):
        for combo in combinations(QI_COLS, size):
            cols = list(combo)
            rows.append({
                "QI_Subset": ", ".join(cols),
                "Num_QIs": size,
                "RRR": round(compute_rrr(df, cols), 4),
                "Prosecutor_Risk": round(compute_prosecutor_risk(df, cols), 4),
            })
    return pd.DataFrame(rows).sort_values(["RRR", "Num_QIs"], ascending=[False, False])


def analyze_qi_cardinality(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "Column": col,
            "Unique_Values": df[col].nunique(dropna=False),
            "Total_Records": len(df),
            "Cardinality_%": round(df[col].nunique(dropna=False) / len(df) * 100, 2),
        }
        for col in QI_COLS
    ]).sort_values("Cardinality_%", ascending=False)


def save_charts(results: pd.DataFrame, cardinality: pd.DataFrame) -> None:
    os.makedirs("outputs/charts", exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Baseline Re-identification Risk (No Anonymization)", fontweight="bold")
    grouped = results.groupby("Num_QIs", as_index=False)["RRR"].mean()
    axes[0].bar(grouped["Num_QIs"], grouped["RRR"], color="#c0392b", edgecolor="black")
    axes[0].set(xlabel="Number of QIs Combined", ylabel="Re-identification Risk Rate", ylim=(0, 1), title="Average RRR by QI Combination Size")
    axes[0].grid(axis="y", alpha=0.25)
    axes[1].barh(cardinality["Column"], cardinality["Cardinality_%"], color="#2980b9", edgecolor="black")
    axes[1].set(xlabel="Cardinality (% unique)", title="QI Cardinality")
    fig.tight_layout()
    fig.savefig("outputs/charts/01_baseline_risk.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> tuple[pd.DataFrame, pd.DataFrame]:
    os.makedirs("outputs/tables", exist_ok=True)
    df = load_data()
    results = analyze_qi_combinations(df)
    cardinality = analyze_qi_cardinality(df)
    results.to_csv("outputs/tables/01_qi_risk_analysis.csv", index=False)
    cardinality.to_csv("outputs/tables/01b_qi_cardinality.csv", index=False)
    save_charts(results, cardinality)
    print(f"  Records: {len(df)} | baseline RRR: {compute_rrr(df, QI_COLS):.2%}")
    print(tabulate(results.head(5), headers="keys", tablefmt="grid", showindex=False))
    return df, results


if __name__ == "__main__":
    main()

