"""Reproducible UCI Cleveland benchmark for PriDB-Health's release layer.

This module deliberately evaluates the public UCI data only for the microdata
and aggregate-release layers.  It does not infer an empirical RBAC breach rate
from a clinical table that contains no access-log or authorization outcome.
"""

from __future__ import annotations

import os
from itertools import combinations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:  # Package import for tests; direct import for the root analysis runner.
    from .differential_privacy import DPQueryEngine, EPSILON_VALUES, N_TRIALS, SEED_BASE
    from .privacy_risk_score import compute_prs, normalize_epsilon_risk
except ImportError:  # pragma: no cover - exercised when run as a script
    from differential_privacy import DPQueryEngine, EPSILON_VALUES, N_TRIALS, SEED_BASE
    from privacy_risk_score import compute_prs, normalize_epsilon_risk

RAW_PATH = Path("dataset/raw/processed.cleveland.data")
OUT = Path("outputs/uci_heart")
QI_COLS = ["age", "gender", "chest_pain", "blood_pressure"]
SENSITIVE_COL = "diagnosis_name"
K_VALUES = [3, 5, 10]
COLUMNS = [
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg", "thalach",
    "exang", "oldpeak", "slope", "ca", "thal", "num",
]
CHEST_PAIN = {1: "Typical angina", 2: "Atypical angina", 3: "Non-anginal pain", 4: "Asymptomatic"}


def load_uci_heart(path: Path = RAW_PATH) -> pd.DataFrame:
    """Load the official raw Cleveland file and return the documented analysis cohort."""
    if not path.exists():
        raise FileNotFoundError(f"Official UCI file is missing: {path}")
    raw = pd.read_csv(path, header=None, names=COLUMNS, na_values="?")
    if len(raw) != 303:
        raise ValueError(f"Expected 303 raw Cleveland rows, found {len(raw)}")
    numeric = [column for column in COLUMNS if column != "oldpeak"]
    raw[numeric] = raw[numeric].apply(pd.to_numeric, errors="raise")
    raw["oldpeak"] = pd.to_numeric(raw["oldpeak"], errors="raise")
    cohort = raw.dropna(subset=["ca", "thal"]).copy()
    cohort["patient_id"] = [f"uci-cleveland-{index:03d}" for index in range(1, len(cohort) + 1)]
    cohort["gender"] = cohort["sex"].map({0: "Female", 1: "Male"})
    cohort["chest_pain"] = cohort["cp"].map(CHEST_PAIN)
    cohort["blood_pressure"] = cohort["trestbps"].astype(float)
    cohort["cholesterol"] = cohort["chol"].astype(float)
    cohort["diagnosis_name"] = np.where(cohort["num"].eq(0), "No heart disease", "Heart disease present")
    cohort["severity"] = np.select(
        [cohort["num"].eq(0), cohort["num"].eq(1), cohort["num"].eq(2)],
        ["None", "Mild", "Moderate"], default="Severe",
    )
    cohort["is_chronic"] = cohort["num"].gt(0)
    if len(cohort) != 297:
        raise ValueError(f"Expected 297 complete cases after documented missing-value handling, found {len(cohort)}")
    return cohort


def equivalence_sizes(df: pd.DataFrame, qi_cols: list[str]) -> pd.Series:
    return df.groupby(qi_cols, dropna=False, observed=True)["patient_id"].transform("size")


def rrr(df: pd.DataFrame, qi_cols: list[str]) -> float:
    return 0.0 if df.empty else float(equivalence_sizes(df, qi_cols).eq(1).mean())


def prosecutor_risk(df: pd.DataFrame, qi_cols: list[str]) -> float:
    return 0.0 if df.empty else float((1 / equivalence_sizes(df, qi_cols)).mean())


def qi_results(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for size in range(1, len(QI_COLS) + 1):
        for combo in combinations(QI_COLS, size):
            rows.append({
                "QI_Subset": ", ".join(combo), "Num_QIs": size,
                "RRR": round(rrr(df, list(combo)), 4),
                "Prosecutor_Risk": round(prosecutor_risk(df, list(combo)), 4),
            })
    card = pd.DataFrame([{
        "Column": col, "Unique_Values": df[col].nunique(dropna=False), "Total_Records": len(df),
        "Cardinality_%": round(df[col].nunique(dropna=False) / len(df) * 100, 2),
    } for col in QI_COLS])
    return pd.DataFrame(rows).sort_values(["RRR", "Num_QIs"], ascending=False), card.sort_values("Cardinality_%", ascending=False)


def _age_band(value: float, k: int) -> str:
    width = {3: 10, 5: 20, 10: 30}[k]
    low = int(value) // width * width
    return f"{low}-{low + width - 1}"


def _bp_band(value: float, k: int) -> str:
    if k == 10:
        return "Any blood pressure"
    if k == 5:
        return "<140 mm Hg" if value < 140 else "≥140 mm Hg"
    if value < 120:
        return "<120 mm Hg"
    if value < 140:
        return "120-139 mm Hg"
    return "≥140 mm Hg"


def _chest_pain(value: str, k: int) -> str:
    if k == 10:
        return "Any chest-pain category"
    if k == 5:
        return "Asymptomatic" if value == "Asymptomatic" else "Symptomatic"
    return value


def anonymize(df: pd.DataFrame, k: int) -> pd.DataFrame:
    """Apply the predeclared, data-type-specific hierarchy then suppress small classes."""
    anon = df[["patient_id", *QI_COLS, SENSITIVE_COL]].copy()
    anon["age"] = anon["age"].map(lambda value: _age_band(value, k))
    anon["blood_pressure"] = anon["blood_pressure"].map(lambda value: _bp_band(value, k))
    anon["chest_pain"] = anon["chest_pain"].map(lambda value: _chest_pain(value, k))
    if k == 10:
        anon["gender"] = "Any gender"
    anon["suppressed"] = equivalence_sizes(anon, QI_COLS).lt(k)
    anon.loc[anon["suppressed"], QI_COLS + [SENSITIVE_COL]] = "*"
    return anon


def categorical_distance(p: pd.Series, q: pd.Series) -> float:
    values = p.index.union(q.index)
    return float(sum(abs(float(p.get(value, 0)) - float(q.get(value, 0))) for value in values) / 2)


def enforce_l_diversity(anon: pd.DataFrame, l: int = 2) -> pd.DataFrame:
    out = anon.copy()
    valid = out[SENSITIVE_COL].ne("*")
    diversity = out.loc[valid].groupby(QI_COLS, observed=True)[SENSITIVE_COL].transform("nunique")
    failing = diversity.index[diversity.lt(l)]
    out.loc[failing, QI_COLS + [SENSITIVE_COL]] = "*"
    out.loc[failing, "suppressed"] = True
    return out


def enforce_t_closeness(anon: pd.DataFrame, t: float = 0.3) -> pd.DataFrame:
    out = anon.copy()
    for _ in range(10):
        valid = out[SENSITIVE_COL].ne("*")
        if not valid.any():
            return out
        global_dist = out.loc[valid, SENSITIVE_COL].value_counts(normalize=True)
        failing = []
        for _, group in out.loc[valid].groupby(QI_COLS, observed=True):
            local = group[SENSITIVE_COL].value_counts(normalize=True)
            if categorical_distance(local, global_dist) > t:
                failing.extend(group.index.tolist())
        if not failing:
            return out
        out.loc[failing, QI_COLS + [SENSITIVE_COL]] = "*"
        out.loc[failing, "suppressed"] = True
    return out


def guarantee_metrics(anon: pd.DataFrame, l: int = 2, t: float = 0.3) -> dict[str, float | bool | int]:
    valid = anon.loc[anon[SENSITIVE_COL].ne("*")]
    if valid.empty:
        return {"l2_satisfied": False, "l2_satisfaction_%": 0.0, "t03_satisfied": False, "t03_satisfaction_%": 0.0, "max_tv_distance": 0.0}
    diversity = valid.groupby(QI_COLS, observed=True)[SENSITIVE_COL].nunique()
    l_ok = diversity.ge(l)
    global_dist = valid[SENSITIVE_COL].value_counts(normalize=True)
    distances = [categorical_distance(group[SENSITIVE_COL].value_counts(normalize=True), global_dist) for _, group in valid.groupby(QI_COLS, observed=True)]
    t_ok = [distance <= t for distance in distances]
    return {
        "l2_satisfied": bool(l_ok.all()), "l2_satisfaction_%": round(float(l_ok.mean() * 100), 2),
        "t03_satisfied": bool(all(t_ok)), "t03_satisfaction_%": round(float(np.mean(t_ok) * 100), 2),
        "max_tv_distance": round(float(max(distances)), 4),
    }


def information_loss(k: int, suppression_rate: float) -> float:
    """Declared hierarchy NCP proxy: mean per-QI generalization loss plus suppression."""
    age_loss = {3: 10 / 48, 5: 20 / 48, 10: 30 / 48}[k]
    bp_loss = {3: 1 / 3, 5: 2 / 3, 10: 1.0}[k]
    cp_loss = {3: 0.0, 5: 0.5, 10: 1.0}[k]
    gender_loss = {3: 0.0, 5: 0.0, 10: 1.0}[k]
    generalized = float(np.mean([age_loss, bp_loss, cp_loss, gender_loss]))
    return round(float(suppression_rate + (1 - suppression_rate) * generalized), 4)


def kanon_results(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[int, pd.DataFrame]]:
    rows, releases = [], {}
    for k in K_VALUES:
        anon = enforce_t_closeness(enforce_l_diversity(anonymize(df, k), 2), 0.3)
        releases[k] = anon
        valid = anon.loc[anon[SENSITIVE_COL].ne("*")]
        suppressed = int(anon["suppressed"].sum())
        suppression_rate = suppressed / len(anon)
        guarantees = guarantee_metrics(anon)
        rows.append({
            "k": k, "Records_Kept": len(valid), "Records_Suppressed": suppressed,
            "Suppression_%": round(suppression_rate * 100, 2), "NCP": information_loss(k, suppression_rate),
            "RRR_After": round(rrr(valid, QI_COLS), 4), "Prosecutor_Risk": round(prosecutor_risk(valid, QI_COLS), 4),
            **guarantees,
        })
    return pd.DataFrame(rows), releases


def dp_trials(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for epsilon in EPSILON_VALUES:
        count_errors, age_errors = [], []
        for trial in range(N_TRIALS):
            engine = DPQueryEngine(df, epsilon, random_state=SEED_BASE + trial)
            count_errors.append(engine.dp_count(df[SENSITIVE_COL].eq("Heart disease present"))["error"])
            age_errors.append(engine.dp_avg("age", 0, 100)["error"])
        rows.append({"epsilon": epsilon, "n_trials": N_TRIALS, "count_mean_error": round(float(np.mean(count_errors)), 4),
                     "count_std_error": round(float(np.std(count_errors)), 4), "avg_age_mean_error": round(float(np.mean(age_errors)), 4),
                     "avg_age_std_error": round(float(np.std(age_errors)), 4)})
    return pd.DataFrame(rows)


def prs_results(baseline_rrr: float, kanon: pd.DataFrame, dp: pd.DataFrame) -> pd.DataFrame:
    """Score only release/inference channels; access-control assurance is verified separately."""
    rows = [{"Scenario": "Raw UCI release (no release protection)", "Layers_Active": "None", "k": "-", "epsilon": "-",
             "RRR": baseline_rrr, "l_Sat_%": 0.0, "t_Sat_%": 0.0, "DP_Risk_Norm": 1.0, "NCP": 0.0,
             "PRS": compute_prs(baseline_rrr, 0.0, 0.0, 1.0)}]
    for _, row in kanon.iterrows():
        l_sat, t_sat = float(row["l2_satisfaction_%"]) / 100, float(row["t03_satisfaction_%"]) / 100
        rows.append({"Scenario": f"UCI k={int(row['k'])} release", "Layers_Active": "L2", "k": int(row["k"]), "epsilon": "-",
                     "RRR": float(row["RRR_After"]), "l_Sat_%": l_sat * 100, "t_Sat_%": t_sat * 100, "DP_Risk_Norm": 1.0,
                     "NCP": float(row["NCP"]), "PRS": compute_prs(float(row["RRR_After"]), l_sat, t_sat, 1.0)})
    k5 = kanon.loc[kanon["k"].eq(5)].iloc[0]
    l_sat, t_sat = float(k5["l2_satisfaction_%"]) / 100, float(k5["t03_satisfaction_%"]) / 100
    for _, row in dp.iterrows():
        risk = normalize_epsilon_risk(float(row["epsilon"]))
        rows.append({"Scenario": f"UCI k=5 + DP eps={float(row['epsilon']):g}", "Layers_Active": "L2+L3", "k": 5,
                     "epsilon": float(row["epsilon"]), "RRR": float(k5["RRR_After"]), "l_Sat_%": l_sat * 100,
                     "t_Sat_%": t_sat * 100, "DP_Risk_Norm": risk, "NCP": float(k5["NCP"]),
                     "PRS": compute_prs(float(k5["RRR_After"]), l_sat, t_sat, risk)})
    return pd.DataFrame(rows)


def prs_weight_sensitivity(prs: pd.DataFrame, step: float = 0.1) -> pd.DataFrame:
    """Enumerate simplex weights; report whether the best configuration is rank-stable."""
    rows = []
    grid = np.arange(0, 1 + step / 2, step)
    for w_rrr in grid:
        for w_l in grid:
            for w_t in grid:
                w_dp = round(1 - w_rrr - w_l - w_t, 10)
                if w_dp < -1e-9:
                    continue
                scores = (w_rrr * prs["RRR"] + w_l * (1 - prs["l_Sat_%"] / 100) + w_t * (1 - prs["t_Sat_%"] / 100) + w_dp * prs["DP_Risk_Norm"])
                winner = prs.loc[scores.idxmin(), "Scenario"]
                rows.append({"w_rrr": w_rrr, "w_l": w_l, "w_t": w_t, "w_dp": max(0.0, w_dp), "best_scenario": winner, "best_prs": round(float(scores.min()), 4)})
    return pd.DataFrame(rows)


def save_charts(df: pd.DataFrame, qi: pd.DataFrame, card: pd.DataFrame, kanon: pd.DataFrame, dp: pd.DataFrame, prs: pd.DataFrame, sensitivity: pd.DataFrame) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    df["diagnosis_name"].value_counts().plot.bar(ax=axes[0], color=["#4C78A8", "#E45756"], edgecolor="black")
    axes[0].set(title="UCI Cleveland analysis cohort", xlabel="Diagnosis", ylabel="Records")
    axes[0].tick_params(axis="x", rotation=15)
    axes[1].barh(card["Column"], card["Cardinality_%"], color="#72B7B2", edgecolor="black")
    axes[1].set(title="Quasi-identifier cardinality", xlabel="Unique values (% of cohort)")
    fig.tight_layout(); fig.savefig(OUT / "01_uci_profile.png", dpi=200); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    grouped = qi.groupby("Num_QIs", as_index=False)["RRR"].agg(mean="mean", min="min", max="max")
    ax.errorbar(grouped["Num_QIs"], grouped["mean"], yerr=[grouped["mean"] - grouped["min"], grouped["max"] - grouped["mean"]], fmt="o-", capsize=4, color="#E45756")
    ax.set(title="Baseline re-identification risk by QI-set size", xlabel="Number of QIs combined", ylabel="Record re-identification risk (RRR)", ylim=(0, 1))
    ax.grid(alpha=.3); fig.tight_layout(); fig.savefig(OUT / "02_uci_qi_risk.png", dpi=200); plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    axes[0].plot(kanon["k"], kanon["RRR_After"], "o-", color="#E45756"); axes[0].set(title="Residual RRR", xlabel="k", ylabel="RRR", ylim=(0, 1))
    axes[1].bar(kanon["k"].astype(str), kanon["Suppression_%"], color="#F2CF5B", edgecolor="black"); axes[1].set(title="Suppression cost", xlabel="k", ylabel="Records suppressed (%)")
    axes[2].plot(kanon["k"], kanon["NCP"], "s-", color="#4C78A8"); axes[2].set(title="Declared information loss", xlabel="k", ylabel="NCP proxy", ylim=(0, 1))
    for ax in axes: ax.grid(alpha=.25)
    fig.tight_layout(); fig.savefig(OUT / "03_uci_anonymization_tradeoff.png", dpi=200); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    axes[0].plot(dp["epsilon"], dp["count_mean_error"], "o-", color="#E45756", label="Heart-disease count")
    axes[0].plot(dp["epsilon"], dp["avg_age_mean_error"], "s-", color="#4C78A8", label="Mean age")
    axes[0].set(title="DP accuracy across 100 seeded trials", xlabel="ε (larger = weaker privacy)", ylabel="Mean absolute error"); axes[0].legend(); axes[0].grid(alpha=.3)
    colors = prs["Layers_Active"].map({"None":"#E45756", "L2":"#F2CF5B", "L2+L3":"#54A24B"})
    axes[1].bar(range(len(prs)), prs["PRS"], color=colors, edgecolor="black")
    labels = ["Raw", "k=3", "k=5", "k=10", "k=5\nDP 0.1", "k=5\nDP 0.5", "k=5\nDP 1.0"]
    axes[1].set(title="Normalized experimental PRS", ylabel="Score (lower is better)", xticks=range(len(prs)), xticklabels=labels)
    axes[1].set_ylim(0, 1.05); axes[1].grid(axis="y", alpha=.3)
    fig.tight_layout(); fig.savefig(OUT / "04_uci_dp_and_prs.png", dpi=200); plt.close(fig)

    shares = sensitivity["best_scenario"].value_counts(normalize=True).mul(100).sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 4.5)); shares.plot.bar(ax=ax, color="#54A24B", edgecolor="black")
    ax.set(title="PRS winner across 286 admissible weight sets", xlabel="Best scenario", ylabel="Weight sets selecting scenario (%)", ylim=(0, 100)); ax.tick_params(axis="x", rotation=20); ax.grid(axis="y", alpha=.3)
    fig.tight_layout(); fig.savefig(OUT / "05_prs_weight_sensitivity.png", dpi=200); plt.close(fig)


def main() -> dict[str, pd.DataFrame]:
    OUT.mkdir(parents=True, exist_ok=True)
    df = load_uci_heart()
    qi, card = qi_results(df)
    kanon, releases = kanon_results(df)
    dp = dp_trials(df)
    baseline = rrr(df, QI_COLS)
    prs = prs_results(baseline, kanon, dp)
    sensitivity = prs_weight_sensitivity(prs)
    df.to_csv(OUT / "uci_cleveland_analysis_cohort.csv", index=False)
    qi.to_csv(OUT / "01_qi_risk_analysis.csv", index=False); card.to_csv(OUT / "01b_qi_cardinality.csv", index=False)
    kanon.to_csv(OUT / "02_kanon_results.csv", index=False); dp.to_csv(OUT / "03_dp_trials.csv", index=False)
    prs.to_csv(OUT / "04_prs_results.csv", index=False); sensitivity.to_csv(OUT / "05_prs_weight_sensitivity.csv", index=False)
    for k, release in releases.items(): release.to_csv(OUT / f"uci_cleveland_k{k}_release.csv", index=False)
    save_charts(df, qi, card, kanon, dp, prs, sensitivity)
    return {"cohort": df, "qi": qi, "kanon": kanon, "dp": dp, "prs": prs, "sensitivity": sensitivity}


if __name__ == "__main__":
    main()
