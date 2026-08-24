# Methodology

## Research question

Does a database-centered combination of access governance, anonymized research releases, and differentially private aggregate queries reduce the declared experimental Privacy Risk Score more than partial configurations?

## Datasets and reproducibility

The study has two deliberately separate data settings. The synthetic control cohort deterministically creates 1,000 US-style patient records, 30 doctors, diagnoses, and prescriptions (seed 42). It is retained to exercise the full PostgreSQL-style schema and scalability path; it is not presented as clinical evidence.

The primary public benchmark for release-layer evaluation is UCI's Heart Disease, processed Cleveland subset: 303 historical de-identified rows and the 14 published attributes. The raw official file is stored unchanged at `dataset/raw/processed.cleveland.data`, with SHA-256 and CC BY 4.0 provenance in `dataset/DATASET_CARD.md`. Six rows with missing `ca` or `thal` are excluded by a documented complete-case rule, yielding 297 analysis records. `num=0` is mapped to *No heart disease* and `num=1`-`4` to *Heart disease present*. UCI has no names, access logs, or authorization outcomes, so it evaluates Layers 2-3—not a measured Layer-1 breach rate.

## Threat model

The prototype evaluates three distinct risks:

1. unauthorized or over-broad database access;
2. linkage and sensitive-attribute disclosure in released rows;
3. inference from aggregate query outputs.

Availability attacks, malicious database administrators, side channels, model inversion, compromised endpoints, and operational security failures are outside the current experiment.

## Layer 1: access governance

PostgreSQL roles represent administrators, doctors, nurses, researchers, and patient-portal users. Row-level policies scope patient access. Column grants deny SSN hashes to clinical and portal roles. Nurses and researchers receive secured views instead of base-table access. JSONB triggers record patient and diagnosis mutations.

## Layer 2: anonymization

For the synthetic cohort, quasi-identifiers are age, gender, ZIP code, and marital status. For UCI, they are age, sex/gender, chest-pain category, and resting blood pressure; heart-disease presence is the sensitive attribute. The UCI hierarchy is predeclared in code: age bands widen from 10 to 30 years, blood-pressure categories widen to one category, chest-pain categories merge, and gender is suppressed only at `k=10`. Classes smaller than k are suppressed. Retained classes are checked for distinct l-diversity and categorical t-closeness using total-variation distance. Violating classes are suppressed as whole units and included in utility-loss reporting.

## Layer 3: differential privacy

Counts use global sensitivity 1. Bounded averages clip inputs and use sensitivity `(upper - lower) / n`. Laplace noise is evaluated at ε ∈ {0.1, 0.5, 1.0}. Reported accuracy statistics use 100 seeded trials.

## Privacy Risk Score

The experimental metric is:

```text
PRS = w_RRR·RRR + w_l·(1 − l_sat) + w_t·(1 − t_sat) + w_DP·min(1, ε / ε_ref)
```

All inputs are bounded to [0,1]. Equal weights (`w=0.25`) are a declared baseline assumption, not learned clinical priorities. `ε_ref=1.0` is the largest evaluated privacy budget, so the epsilon term is a reporting normalization rather than a probability. DP does not reduce the microdata RRR: it protects aggregate answers in a distinct channel. The derivation, citations, weight sensitivity analysis, mathematical properties, and limitations are in `docs/PRS_DERIVATION_AND_VALIDATION.md`.

## Utility

Normalized Certainty Penalty (NCP), record suppression, and DP mean absolute error are reported separately. This avoids presenting privacy improvement without its information cost.

## Reproducibility

`verify_research_evidence.py` checks the raw UCI checksum, cohort size, release guarantees, DP noise direction, equal-weight PRS output, sensitivity-grid validity, and required artifacts. Its report is an internal reproducibility artifact, not external peer review.

