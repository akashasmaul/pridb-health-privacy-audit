import numpy as np
import pandas as pd

from src.differential_privacy import DPQueryEngine

DF = pd.DataFrame({"age": np.arange(20, 120), "diagnosis_name": ["Hypertension"] * 50 + ["Diabetes"] * 50})


def test_dp_count_is_nonnegative():
    result = DPQueryEngine(DF, 1.0, random_state=1).dp_count()
    assert result["dp_value"] >= 0


def test_dp_conditional_count_has_correct_true_value():
    result = DPQueryEngine(DF, 0.5, random_state=2).dp_count(DF["diagnosis_name"].eq("Hypertension"))
    assert result["true_value"] == 50


def test_dp_average_is_clipped_to_bounds():
    result = DPQueryEngine(DF, 0.5, random_state=3).dp_avg("age", 0, 120)
    assert 0 <= result["dp_value"] <= 120


def test_smaller_epsilon_has_more_mean_noise():
    low = [DPQueryEngine(DF, 0.1, random_state=i).dp_count()["error"] for i in range(100)]
    high = [DPQueryEngine(DF, 10, random_state=i).dp_count()["error"] for i in range(100)]
    assert np.mean(low) > np.mean(high)

