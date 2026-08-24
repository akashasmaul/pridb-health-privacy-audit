from pathlib import Path

from src.uci_heart_benchmark import (
    K_VALUES,
    QI_COLS,
    SENSITIVE_COL,
    anonymize,
    enforce_l_diversity,
    enforce_t_closeness,
    load_uci_heart,
    prs_weight_sensitivity,
    rrr,
)


def test_official_uci_loader_has_documented_complete_case_size():
    frame = load_uci_heart(Path("dataset/raw/processed.cleveland.data"))
    assert len(frame) == 297
    assert set(QI_COLS + [SENSITIVE_COL]).issubset(frame.columns)
    assert set(frame[SENSITIVE_COL].unique()) == {"No heart disease", "Heart disease present"}


def test_retained_uci_classes_meet_k_after_enforcement():
    frame = load_uci_heart()
    for k in K_VALUES:
        release = enforce_t_closeness(enforce_l_diversity(anonymize(frame, k)))
        kept = release.loc[release[SENSITIVE_COL].ne("*")]
        sizes = kept.groupby(QI_COLS).size()
        assert sizes.empty or (sizes >= k).all()
        assert rrr(kept, QI_COLS) == 0


def test_prs_weight_grid_is_a_simplex():
    frame = load_uci_heart()
    # A tiny valid score table is sufficient to test the weight enumerator.
    import pandas as pd
    scores = pd.DataFrame({"Scenario": ["a", "b"], "RRR": [1.0, 0.0], "l_Sat_%": [0.0, 100.0], "t_Sat_%": [0.0, 100.0], "DP_Risk_Norm": [1.0, 0.1]})
    grid = prs_weight_sensitivity(scores)
    assert len(grid) == 286
    assert (grid[["w_rrr", "w_l", "w_t", "w_dp"]].sum(axis=1).round(8) == 1).all()
