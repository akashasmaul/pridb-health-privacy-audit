"""Verify reproducible implementation evidence without overstating research claims."""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
EXPECTED_SHA256 = "a74b7efa387bc9d108d7d0115d831fe9b414b29ae7124f331b622b4efa0427c8"
CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str) -> None:
    CHECKS.append((name, bool(condition), detail))
    print(f"  {'PASS' if condition else 'FAIL'}  {name}: {detail}")


def main() -> int:
    raw = ROOT / "dataset/raw/processed.cleveland.data"
    required = [
        raw, ROOT / "dataset/DATASET_CARD.md", ROOT / "docs/PRS_DERIVATION_AND_VALIDATION.md",
        ROOT / "outputs/uci_heart/uci_cleveland_analysis_cohort.csv",
        ROOT / "outputs/uci_heart/02_kanon_results.csv", ROOT / "outputs/uci_heart/03_dp_trials.csv",
        ROOT / "outputs/uci_heart/04_prs_results.csv", ROOT / "outputs/uci_heart/05_prs_weight_sensitivity.csv",
        ROOT / "outputs/uci_heart/05_prs_weight_sensitivity.png", ROOT / "outputs/comparative/01_cross_dataset_comparison.png",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    check("required_artifacts", not missing, "all required artifacts present" if not missing else f"missing: {missing}")
    if missing:
        return 1
    sha256 = hashlib.sha256(raw.read_bytes()).hexdigest()
    check("uci_raw_checksum", sha256 == EXPECTED_SHA256, sha256)
    cohort = pd.read_csv(ROOT / "outputs/uci_heart/uci_cleveland_analysis_cohort.csv")
    kanon = pd.read_csv(ROOT / "outputs/uci_heart/02_kanon_results.csv")
    dp = pd.read_csv(ROOT / "outputs/uci_heart/03_dp_trials.csv").sort_values("epsilon")
    prs = pd.read_csv(ROOT / "outputs/uci_heart/04_prs_results.csv", keep_default_na=False)
    sensitivity = pd.read_csv(ROOT / "outputs/uci_heart/05_prs_weight_sensitivity.csv")
    check("uci_complete_case_cohort", len(cohort) == 297, f"{len(cohort)} rows after documented missing-value handling")
    check("k_release_guarantees", bool(kanon["l2_satisfied"].all() and kanon["t03_satisfied"].all()), "all retained classes satisfy l=2 and t=0.3")
    check("k5_release_retention", int(kanon.loc[kanon["k"].eq(5), "Records_Kept"].iloc[0]) > 0, "k=5 retains records")
    check("k5_residual_rrr", float(kanon.loc[kanon["k"].eq(5), "RRR_After"].iloc[0]) == 0.0, "no singleton retained QI class")
    check("dp_noise_present", bool((dp["count_mean_error"] > 0).all()), f"errors={dp['count_mean_error'].tolist()}")
    check("dp_inverse_utility", float(dp.iloc[0]["count_mean_error"]) > float(dp.iloc[-1]["count_mean_error"]), "smaller epsilon has larger observed noise")
    best = prs.loc[prs["PRS"].idxmin()]
    check("equal_weight_prs_winner", best["Scenario"] == "UCI k=5 + DP eps=0.1", f"{best['Scenario']} PRS={best['PRS']:.4f}")
    check("prs_weight_grid", len(sensitivity) == 286 and sensitivity[["w_rrr", "w_l", "w_t", "w_dp"]].sum(axis=1).round(8).eq(1).all(), f"{len(sensitivity)} valid weight vectors")
    passed = sum(ok for _, ok, _ in CHECKS)
    all_ok = passed == len(CHECKS)
    status = "IMPLEMENTATION AND BENCHMARK CHECKS PASS" if all_ok else f"CHECKS INCOMPLETE ({passed}/{len(CHECKS)})"
    report = [
        "# PriDB-Health research evidence status", "", f"Generated: {datetime.now().isoformat(timespec='seconds')}", "",
        f"## Status: {status}", "", "## Reproducible checks", "",
        *[f"- {'PASS' if ok else 'FAIL'} **{name}** - {detail}" for name, ok, detail in CHECKS], "",
        "## What this establishes", "", "The repository reproduces the documented UCI Cleveland release-layer benchmark, preserves the official raw-file checksum, and produces internally consistent k-anonymity, l-diversity, t-closeness, differential-privacy, PRS, and sensitivity artifacts.", "",
        "## What this does not establish", "", "It does not prove worldwide novelty, publication acceptance, clinical effectiveness, regulatory compliance, or empirical calibration of PRS. UCI validates the release and aggregate-query experiments, not an RBAC breach-rate reduction. The PRS remains a transparent experimental multi-criteria index; its weights require stakeholder or attack-benchmark validation for stronger claims.", "",
    ]
    (ROOT / "RESEARCH_EVIDENCE_STATUS.md").write_text("\n".join(report), encoding="utf-8")
    print(f"\nRESULT: {passed}/{len(CHECKS)} checks passed")
    print("Report: RESEARCH_EVIDENCE_STATUS.md")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
