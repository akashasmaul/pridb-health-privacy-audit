"""Verify the guide's internal experimental stop conditions.

This verifier establishes reproducibility of the implemented experiment. It
does not replace a literature review, peer review, ethics approval, or a legal
compliance assessment.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str) -> None:
    CHECKS.append((name, bool(condition), detail))
    print(f"  {'PASS' if condition else 'FAIL'}  {name}: {detail}")


def main() -> int:
    required = [
        "outputs/tables/01_qi_risk_analysis.csv", "outputs/tables/01b_qi_cardinality.csv",
        "outputs/tables/02_kanon_results.csv", "outputs/tables/03_dp_query_demo.csv",
        "outputs/tables/03b_dp_trials.csv", "outputs/tables/04_prs_results.csv",
        "outputs/tables/05_compliance.csv", "outputs/charts/01_baseline_risk.png",
        "outputs/charts/02_kanon_tradeoff.png", "outputs/charts/03_dp_tradeoff.png",
        "outputs/charts/04_prs_comparison.png", "data/processed/patients_k3.csv",
        "data/processed/patients_k5.csv", "data/processed/patients_k10.csv",
    ]
    missing = [path for path in required if not Path(path).exists()]
    check("required_outputs", not missing, f"{len(required) - len(missing)}/{len(required)} present")
    if missing:
        print(f"    Missing: {missing}")
        return 1

    prs = pd.read_csv("outputs/tables/04_prs_results.csv", keep_default_na=False)
    kanon = pd.read_csv("outputs/tables/02_kanon_results.csv")
    dp = pd.read_csv("outputs/tables/03b_dp_trials.csv").sort_values("epsilon")
    layers = {layer: prs.loc[prs["Layers_Active"].eq(layer), "PRS"] for layer in ["None", "L1", "L1+L2", "L1+L2+L3"]}
    check("all_layer_configurations", all(not series.empty for series in layers.values()), "None, L1, L1+L2, and L1+L2+L3 present")
    check("prs_rows", len(prs) >= 8, f"{len(prs)} configurations")
    best = prs.loc[prs["PRS"].idxmin()]
    check("three_layer_is_best", best["Layers_Active"] == "L1+L2+L3", f"{best['Scenario']} PRS={best['PRS']:.4f}")
    expected_best = "All 3 Layers (k=5, eps=0.1)"
    check("expected_configuration_is_best", best["Scenario"] == expected_best, str(best["Scenario"]))

    p0, p1, p2, p3 = layers["None"].iloc[0], layers["L1"].iloc[0], layers["L1+L2"].min(), layers["L1+L2+L3"].min()
    check("strict_prs_ladder", p0 > p1 > p2 > p3, f"{p0:.4f} > {p1:.4f} > {p2:.4f} > {p3:.4f}")
    improvement = (p0 - p3) / p0 * 100
    check("improvement_at_least_50pct", improvement >= 50, f"{improvement:.1f}%")

    k5 = kanon.loc[kanon["k"].eq(5)].iloc[0]
    check("k5_l2", bool(k5["l2_satisfied"]), f"satisfaction={k5.get('l2_satisfaction_%', 0):.2f}%")
    check("k5_t03", bool(k5["t03_satisfied"]), f"satisfaction={k5.get('t03_satisfaction_%', 0):.2f}%")
    check("k5_rrr", float(k5["RRR_After"]) < 0.25, f"RRR={k5['RRR_After']:.4f}")
    check("dp_noise", bool((dp["count_mean_error"] > 0).all()), f"errors={dp['count_mean_error'].tolist()}")
    check("dp_inverse_noise", float(dp.iloc[0]["count_mean_error"]) > float(dp.iloc[-1]["count_mean_error"]), "smaller epsilon produces more error")

    passed = sum(ok for _, ok, _ in CHECKS)
    all_ok = passed == len(CHECKS)
    status = "NOVELTY FULLY VERIFIED (AGAINST INTERNAL EXPERIMENTAL CRITERIA)" if all_ok else f"VERIFICATION INCOMPLETE ({passed}/{len(CHECKS)})"
    lines = [
        "=" * 72,
        "PriDB-Health Experimental Verification Certificate",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "=" * 72,
        f"STATUS: {status}",
        "",
        f"Baseline PRS: {p0:.4f}",
        f"Best 3-layer PRS: {p3:.4f}",
        f"Improvement: {improvement:.1f}%",
        f"Best scenario: {best['Scenario']}",
        "",
        "Checks:",
        *[f"  {'PASS' if ok else 'FAIL'} {name} — {detail}" for name, ok, detail in CHECKS],
        "",
        "Scope note: this certificate verifies the repository's declared internal",
        "stop conditions. Claims of worldwide novelty, compliance, clinical safety,",
        "and publication readiness require independent review and external evidence.",
        "=" * 72,
    ]
    Path("NOVELTY_VERIFIED.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nRESULT: {passed}/{len(CHECKS)} checks passed")
    print("Certificate: NOVELTY_VERIFIED.txt")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
