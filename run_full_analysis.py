"""Execute the complete PriDB-Health analysis pipeline from the project root."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "src"))


def _step(number: int, title: str) -> None:
    print(f"\n{'=' * 68}\n STEP {number}: {title}\n{'=' * 68}")


def main() -> None:
    started = time.time()
    _step(1, "Generate deterministic synthetic hospital data")
    from data_generator import main as generate
    generate()

    _step(2, "Analyze quasi-identifier re-identification risk")
    from quasi_identifier_analysis import main as analyze_qi
    analyze_qi()

    _step(3, "Evaluate k-anonymity, l-diversity, and t-closeness")
    from kanonymity import main as analyze_kanon
    analyze_kanon()

    _step(4, "Evaluate differential privacy")
    from differential_privacy import main as analyze_dp
    analyze_dp()

    _step(5, "Compute the unified Privacy Risk Score")
    from privacy_risk_score import main as analyze_prs
    prs = analyze_prs()

    _step(6, "Generate compliance control mapping")
    from compliance_checker import main as check_compliance
    check_compliance()

    _step(7, "Evaluate the official UCI Cleveland benchmark")
    from uci_heart_benchmark import main as analyze_uci
    uci = analyze_uci()

    _step(8, "Generate synthetic-versus-UCI comparative visualizations")
    from comparative_visuals import main as compare
    compare()

    baseline = float(prs.loc[prs["Layers_Active"].eq("None"), "PRS"].iloc[0])
    best = prs.loc[prs["PRS"].idxmin()]
    improvement = (baseline - float(best["PRS"])) / baseline * 100
    print(f"\n{'=' * 68}")
    print(f" PIPELINE COMPLETE in {time.time() - started:.1f}s")
    print(f" Baseline PRS: {baseline:.4f}")
    print(f" Best PRS:     {best['PRS']:.4f} ({best['Scenario']})")
    print(f" Improvement:  {improvement:.1f}%")
    uci_best = uci["prs"].loc[uci["prs"]["PRS"].idxmin()]
    print(f" UCI best PRS: {uci_best['PRS']:.4f} ({uci_best['Scenario']})")
    print(f"{'=' * 68}")


if __name__ == "__main__":
    main()

