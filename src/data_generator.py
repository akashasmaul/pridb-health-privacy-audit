"""Deterministically generate the synthetic PriDB-Health research dataset."""

from __future__ import annotations

import hashlib
import os
import random
from datetime import date

import pandas as pd
from faker import Faker

SEED = 42
N_PATIENTS = 1000
N_DOCTORS = 30

DIAGNOSES = [
    ("I10", "Essential Hypertension", "Moderate", True),
    ("E11.9", "Type 2 Diabetes", "Moderate", True),
    ("J45.9", "Asthma", "Mild", True),
    ("C50.9", "Breast Cancer", "Severe", False),
    ("I25.1", "Coronary Artery Disease", "Severe", True),
    ("F32.1", "Major Depressive Disorder", "Moderate", True),
    ("N18.3", "Chronic Kidney Disease Stg3", "Severe", True),
    ("J18.9", "Pneumonia", "Moderate", False),
    ("M54.5", "Low Back Pain", "Mild", False),
    ("K21.0", "Gastroesophageal Reflux", "Mild", True),
    ("G43.9", "Migraine", "Mild", True),
    ("A09", "Infectious Diarrhea", "Mild", False),
    ("I50.9", "Heart Failure", "Critical", True),
    ("J06.9", "Upper Respiratory Infection", "Mild", False),
    ("E78.5", "Hyperlipidemia", "Mild", True),
]
DRUGS = [
    ("Metformin", "500mg", "Twice daily"),
    ("Lisinopril", "10mg", "Once daily"),
    ("Atorvastatin", "20mg", "Once nightly"),
    ("Amlodipine", "5mg", "Once daily"),
    ("Omeprazole", "20mg", "Once daily"),
    ("Albuterol", "90mcg/puff", "As needed"),
    ("Sertraline", "50mg", "Once daily"),
    ("Furosemide", "40mg", "Once daily"),
    ("Aspirin", "81mg", "Once daily"),
    ("Ibuprofen", "400mg", "Three times daily"),
]
ETHNICITIES = [
    "White", "Black or African American", "Hispanic or Latino", "Asian",
    "Native American", "Pacific Islander", "Other",
]
BLOOD_TYPES = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
MARITAL = ["Single", "Married", "Divorced", "Widowed"]
SPECIALTIES = [
    "Cardiology", "Oncology", "Neurology", "Endocrinology",
    "Pulmonology", "Nephrology", "General Practice",
]


def _rngs(seed: int = SEED) -> tuple[random.Random, Faker]:
    rng = random.Random(seed)
    fake = Faker("en_US")
    fake.seed_instance(seed)
    return rng, fake


def hash_ssn(ssn: str) -> str:
    return hashlib.sha256(ssn.encode("utf-8")).hexdigest()


def generate_doctors(rng: random.Random, fake: Faker) -> pd.DataFrame:
    rows = []
    for doctor_id in range(1, N_DOCTORS + 1):
        rows.append({
            "doctor_id": doctor_id,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "specialty": rng.choice(SPECIALTIES),
            "license_number": f"LIC{100000 + doctor_id}",
            "department": rng.choice(SPECIALTIES),
            "is_active": True,
        })
    return pd.DataFrame(rows)


def generate_patients(rng: random.Random, fake: Faker) -> pd.DataFrame:
    rows = []
    today = date.today()
    for patient_id in range(1, N_PATIENTS + 1):
        dob = fake.date_of_birth(minimum_age=0, maximum_age=90)
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        rows.append({
            "patient_id": patient_id,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "dob": dob.isoformat(),
            "age": age,
            "gender": rng.choices(["Male", "Female", "Other"], weights=[48, 50, 2])[0],
            "blood_type": rng.choice(BLOOD_TYPES),
            "zip_code": fake.zipcode(),
            "city": fake.city(),
            "marital_status": rng.choice(MARITAL),
            "ethnicity": rng.choices(ETHNICITIES, weights=[60, 13, 18, 6, 1, 1, 1])[0],
            "ssn_hash": hash_ssn(fake.ssn()),
        })
    return pd.DataFrame(rows)


def generate_diagnoses(patients: pd.DataFrame, rng: random.Random, fake: Faker) -> pd.DataFrame:
    rows = []
    diagnosis_id = 1
    for patient_id in patients["patient_id"]:
        count = rng.choices([1, 2, 3], weights=[60, 30, 10])[0]
        for icd, name, severity, chronic in rng.sample(DIAGNOSES, k=count):
            rows.append({
                "diagnosis_id": diagnosis_id,
                "patient_id": int(patient_id),
                "icd10_code": icd,
                "diagnosis_name": name,
                "severity": severity,
                "diagnosed_date": fake.date_between(start_date="-5y", end_date="today").isoformat(),
                "diagnosing_doctor_id": rng.randint(1, N_DOCTORS),
                "is_chronic": chronic,
            })
            diagnosis_id += 1
    return pd.DataFrame(rows)


def generate_prescriptions(patients: pd.DataFrame, rng: random.Random, fake: Faker) -> pd.DataFrame:
    rows = []
    prescription_id = 1
    for patient_id in patients["patient_id"]:
        count = rng.choices([0, 1, 2], weights=[20, 50, 30])[0]
        for _ in range(count):
            drug, dosage, frequency = rng.choice(DRUGS)
            rows.append({
                "prescription_id": prescription_id,
                "patient_id": int(patient_id),
                "doctor_id": rng.randint(1, N_DOCTORS),
                "drug_name": drug,
                "dosage": dosage,
                "frequency": frequency,
                "start_date": fake.date_between(start_date="-3y", end_date="today").isoformat(),
                "end_date": None,
                "is_active": True,
            })
            prescription_id += 1
    return pd.DataFrame(rows)


def main() -> tuple[pd.DataFrame, pd.DataFrame]:
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    rng, fake = _rngs()
    doctors = generate_doctors(rng, fake)
    patients = generate_patients(rng, fake)
    diagnoses = generate_diagnoses(patients, rng, fake)
    prescriptions = generate_prescriptions(patients, rng, fake)
    datasets = {
        "doctors": doctors,
        "patients": patients,
        "diagnoses": diagnoses,
        "prescriptions": prescriptions,
    }
    for name, frame in datasets.items():
        path = f"data/raw/{name}.csv"
        frame.to_csv(path, index=False)
        print(f"  {len(frame):>5} {name:<13} -> {path}")
    return patients, diagnoses


if __name__ == "__main__":
    main()

