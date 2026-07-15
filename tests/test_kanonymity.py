import pandas as pd

from src.kanonymity import apply_k_anonymity, check_l_diversity, check_t_closeness, compute_ncp

SAMPLE = pd.DataFrame({
    "patient_id": list(range(1, 21)),
    "age": [25, 30, 35, 40, 45, 50, 55, 60, 65, 70] * 2,
    "gender": ["Male"] * 10 + ["Female"] * 10,
    "zip_code": ["12345"] * 20,
    "marital_status": ["Single"] * 20,
    "diagnosis_name": ["Hypertension", "Diabetes", "Asthma", "Cancer", "Hypertension", "Diabetes", "Asthma", "Cancer", "Hypertension", "Diabetes"] * 2,
    "severity": ["Moderate"] * 20,
    "is_chronic": [True] * 20,
})


def test_k3_produces_same_number_of_rows():
    anon, suppressed = apply_k_anonymity(SAMPLE, 3)
    assert len(anon) == len(SAMPLE)
    assert 0 <= suppressed <= len(SAMPLE)


def test_kept_groups_meet_k():
    anon, _ = apply_k_anonymity(SAMPLE, 5)
    valid = anon.loc[anon["diagnosis_name"].ne("*")]
    sizes = valid.groupby(["age", "gender", "zip_code", "marital_status"]).size()
    assert sizes.empty or (sizes >= 5).all()


def test_l_diversity_result_is_bounded():
    result = check_l_diversity(apply_k_anonymity(SAMPLE, 3)[0], 2)
    assert isinstance(result["l_satisfied"], bool)
    assert 0 <= result["l_satisfaction_%"] <= 100


def test_t_closeness_result_is_bounded():
    result = check_t_closeness(apply_k_anonymity(SAMPLE, 3)[0], 0.3)
    assert isinstance(result["t_satisfied"], bool)
    assert 0 <= result["max_emd_distance"] <= 1


def test_ncp_is_bounded():
    anon, _ = apply_k_anonymity(SAMPLE, 5)
    assert 0 <= compute_ncp(SAMPLE, anon) <= 1

