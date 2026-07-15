# Methodology

## Research question

Does a database-centered combination of access governance, anonymized research releases, and differentially private aggregate queries reduce the declared experimental Privacy Risk Score more than partial configurations?

## Dataset

The pipeline deterministically creates 1,000 synthetic US-style patient records, 30 doctors, 1,495 diagnoses, and 1,068 prescriptions. Faker generates names and locations; no real patient data is used. The seed is 42.

## Threat model

The prototype evaluates three distinct risks:

1. unauthorized or over-broad database access;
2. linkage and sensitive-attribute disclosure in released rows;
3. inference from aggregate query outputs.

Availability attacks, malicious database administrators, side channels, model inversion, compromised endpoints, and operational security failures are outside the current experiment.

## Layer 1: access governance

PostgreSQL roles represent administrators, doctors, nurses, researchers, and patient-portal users. Row-level policies scope patient access. Column grants deny SSN hashes to clinical and portal roles. Nurses and researchers receive secured views instead of base-table access. JSONB triggers record patient and diagnosis mutations.

## Layer 2: anonymization

Quasi-identifiers are age, gender, ZIP code, and marital status. Hierarchies generalize age and geography; residual classes below k are suppressed. Retained classes are checked for distinct l-diversity and categorical t-closeness using total-variation distance. Violating classes are suppressed as whole units and included in utility-loss reporting.

## Layer 3: differential privacy

Counts use global sensitivity 1. Bounded averages clip inputs and use sensitivity `(upper - lower) / n`. Laplace noise is evaluated at ε ∈ {0.1, 0.5, 1.0}. Reported accuracy statistics use 100 seeded trials.

## Privacy Risk Score

The experimental metric is:

```text
PRS = 0.25·RRR + 0.25·(1 − l_sat) + 0.25·(1 − t_sat) + 0.25·DP_risk
```

`DP_risk = ε / (1 + ε)` when the DP layer is active. Inputs are bounded to [0,1]. Equal weights are a declared baseline assumption, not learned clinical priorities.

## Utility

Normalized Certainty Penalty (NCP), record suppression, and DP mean absolute error are reported separately. This avoids presenting privacy improvement without its information cost.

## Reproducibility

The verifier checks files, configurations, the strict PRS ladder, k=5 l/t satisfaction, DP noise, and inverse ε/noise behavior. The certificate is an internal reproducibility artifact, not external peer review.

