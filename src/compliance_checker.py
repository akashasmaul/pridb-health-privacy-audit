"""Map implemented controls to selected GDPR and HIPAA requirements."""

from __future__ import annotations

import os

import pandas as pd
from tabulate import tabulate

CONTROLS = [
    {"Regulation": "GDPR", "Article": "Art.5(1)(f)", "Requirement": "Integrity and confidentiality", "Mechanism": "RBAC + PostgreSQL RLS", "Status": "ADDRESSED", "Gap": "SELECT auditing requires pgaudit in production"},
    {"Regulation": "GDPR", "Article": "Art.25", "Requirement": "Privacy by design/default", "Mechanism": "Three-layer schema and analysis design", "Status": "ADDRESSED", "Gap": "Requires organizational validation"},
    {"Regulation": "GDPR", "Article": "Art.89(1)", "Requirement": "Research safeguards", "Mechanism": "Researcher anonymized view and k-anonymity", "Status": "ADDRESSED", "Gap": "Rare-disease cohorts need separate assessment"},
    {"Regulation": "GDPR", "Article": "Art.30", "Requirement": "Processing records", "Mechanism": "JSONB audit log and triggers", "Status": "ADDRESSED", "Gap": "Retention schedule is deployment-specific"},
    {"Regulation": "HIPAA", "Article": "§164.312(a)(1)", "Requirement": "Access control", "Mechanism": "Least-privilege roles and RLS", "Status": "ADDRESSED", "Gap": "Emergency break-glass workflow not included"},
    {"Regulation": "HIPAA", "Article": "§164.312(b)", "Requirement": "Audit controls", "Mechanism": "Insert-only audit trail for non-admin roles", "Status": "ADDRESSED", "Gap": "Off-site immutable export not included"},
    {"Regulation": "HIPAA", "Article": "§164.514(b)", "Requirement": "De-identification", "Mechanism": "Generalized researcher view and experiment", "Status": "PARTIAL", "Gap": "Not a formal Expert Determination"},
    {"Regulation": "HIPAA", "Article": "§164.312(c)(1)", "Requirement": "Integrity controls", "Mechanism": "FK, NOT NULL, CHECK, and trigger controls", "Status": "ADDRESSED", "Gap": "Cryptographic log signing not included"},
]


def main() -> pd.DataFrame:
    os.makedirs("outputs/tables", exist_ok=True)
    frame = pd.DataFrame(CONTROLS)
    frame.to_csv("outputs/tables/05_compliance.csv", index=False)
    print(tabulate(frame, headers="keys", tablefmt="grid", showindex=False, maxcolwidths=28))
    return frame


if __name__ == "__main__":
    main()

