import pytest

from src.privacy_risk_score import compute_prs, normalize_dp_error, normalize_epsilon_risk


def test_prs_zero_at_perfect_privacy():
    assert compute_prs(0, 1, 1, 0) == 0


def test_prs_one_at_no_privacy():
    assert compute_prs(1, 0, 0, 1) == 1


def test_prs_is_bounded():
    assert 0 <= compute_prs(0.4, 0.7, 0.6, 0.2) <= 1


def test_three_layer_example_beats_baseline():
    assert compute_prs(0.05, 1, 1, 0.1) < compute_prs(0.85, 0, 0, 1)


def test_dp_error_normalization_clamps():
    assert normalize_dp_error(0) == 0
    assert normalize_dp_error(100, 50) == 1


def test_epsilon_risk_is_monotone():
    assert normalize_epsilon_risk(0.1) < normalize_epsilon_risk(0.5) < normalize_epsilon_risk(1.0)


def test_invalid_prs_input_rejected():
    with pytest.raises(ValueError):
        compute_prs(1.1, 1, 1, 0)

