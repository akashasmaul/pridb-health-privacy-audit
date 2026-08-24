# PriDB-Health UCI Integration and Research Status

## Purpose of this document

This document is the complete handoff for the real-data extension of PriDB-Health. It records what was implemented, the exact data used, the calculations and results produced, the figures generated, what evidence now supports, and what cannot honestly be claimed yet.

The extension was created because the original experiment used a deterministic Faker-generated hospital-like dataset. That synthetic cohort remains useful for exercising the larger database schema and comparing behavior at a controlled scale, but it is not a clinically observed cohort. The UCI Cleveland benchmark adds a public, de-identified healthcare dataset for the microdata-release and aggregate-query experiments.

## Executive summary

The project now has a reproducible two-dataset evaluation:

1. **Synthetic control cohort:** 1,000 generated records. It exercises the complete PriDB-Health schema-oriented pipeline, including the PostgreSQL design.
2. **Public UCI Cleveland benchmark:** 297 complete-case records derived from the official 303-row UCI Heart Disease processed file. It provides real public-health-data evidence for the release-protection and differential-privacy experiments.

On the UCI benchmark, the raw QI release had record re-identification risk rate (RRR) **0.9158** for the declared four-QI set. Every tested anonymized release (`k=3`, `k=5`, and `k=10`) had **zero singleton retained QI classes**, and all retained classes satisfied the configured distinct `l=2` and categorical `t=0.3` criteria after enforcement. The selected balanced release, `k=5`, retained **188 of 297 records (63.30%)**, suppressed **109 (36.70%)**, and had an NCP proxy of **0.6176**.

For the differential-privacy aggregate experiment, lower epsilon produced larger expected error exactly as required by the Laplace mechanism: mean absolute heart-disease-count error was **9.00** at epsilon `0.1`, **1.79** at `0.5`, and **0.88** at `1.0`, each over 100 deterministic trials. Under the explicitly declared equal-weight PRS baseline, `k=5 + DP eps=0.1` achieved PRS **0.0250**, compared with **0.9790** for the unprotected UCI release.

These are reproducible experimental findings—not proof of publication acceptance, worldwide novelty, compliance, clinical safety, or universal validity of the PRS.

## 1. What was added or changed

### 1.1 Official data and provenance

The official UCI Heart Disease Cleveland processed data file was downloaded into:

```text
dataset/raw/processed.cleveland.data
```

The source is the [UCI Heart Disease repository](https://archive.ics.uci.edu/dataset/45/heart), dataset ID 45, DOI [10.24432/C52P4X](https://doi.org/10.24432/C52P4X), released under CC BY 4.0. The repository records the raw-file SHA-256 checksum:

```text
A74B7EFA387BC9D108D7D0115D831FE9B414B29AE7124F331B622B4EFA0427C8
```

The full source, license, checksum, citation, and data-handling record is in [`dataset/DATASET_CARD.md`](../dataset/DATASET_CARD.md). This provides a verifiable provenance chain rather than relying on an undocumented third-party mirror.

### 1.2 Reproducible UCI adapter

[`src/uci_heart_benchmark.py`](../src/uci_heart_benchmark.py) implements the UCI analysis without changing the raw file. It:

- assigns UCI's published 14 columns;
- converts `?` to missing values;
- excludes the six rows missing `ca` or `thal` via one documented complete-case rule;
- creates a 297-row analysis cohort;
- maps `sex` to readable `gender` values;
- maps chest-pain codes to documented categories;
- maps `num=0` to **No heart disease** and `num=1` through `4` to **Heart disease present**;
- uses `age`, `gender`, `chest_pain`, and `blood_pressure` as declared QIs; and
- uses the binary heart-disease outcome as the sensitive attribute.

### 1.3 Dual-dataset pipeline and comparative charts

[`run_full_analysis.py`](../run_full_analysis.py) now runs the original synthetic sequence, the UCI benchmark, and a synthetic-versus-UCI comparison. [`src/comparative_visuals.py`](../src/comparative_visuals.py) creates the cross-dataset figure.

The UCI output set is in `outputs/uci_heart/`; cross-dataset output is in `outputs/comparative/`.

### 1.4 PRS correction and justification

The original PRS code used an assumed 40% RBAC reduction and multiplied microdata RRR by an epsilon transform. Those operations are not properties of differential privacy and should not be represented as measured UCI findings.

The revised PRS implementation and documentation make the following distinctions:

- A microdata RRR is not reduced merely because a DP mechanism protects a separate aggregate query.
- Epsilon is a formal DP privacy-loss parameter, not a probability; the project uses `min(1, epsilon / epsilon_ref)` only as a declared bounded reporting normalization, with `epsilon_ref=1.0`.
- UCI contains no access logs, authorization decisions, or breach outcomes. Therefore it cannot establish a numerical RBAC/RLS risk-reduction percentage. Layer 1 is verified through its PostgreSQL policy and permission design, not inferred from UCI.
- Equal weights are a transparent baseline assumption, not learned clinical truth. A 286-point simplex weight sensitivity check makes this assumption visible.

The complete derivation, literature basis, mathematical properties, correction record, and next validation steps are in [`docs/PRS_DERIVATION_AND_VALIDATION.md`](PRS_DERIVATION_AND_VALIDATION.md).

## 2. Method used for the UCI release experiment

### 2.1 Threat channels

The UCI extension addresses two channels:

1. **Released-row linkage and attribute disclosure (Layer 2):** attacker knowledge is represented by the declared QI set.
2. **Aggregate-query inference (Layer 3):** noisy counts and bounded averages use the Laplace mechanism.

It does not infer real access-control incidents from UCI; access governance is a separate schema/security evaluation.

### 2.2 Anonymization hierarchy

The hierarchy is declared in code before analysis:

| QI | k=3 | k=5 | k=10 |
|---|---|---|---|
| Age | 10-year band | 20-year band | 30-year band |
| Resting blood pressure | `<120`, `120-139`, `>=140` mm Hg | `<140` vs `>=140` mm Hg | one broad category |
| Chest pain | four published categories | symptomatic vs asymptomatic | one broad category |
| Gender | retained | retained | generalized to one category |

After generalization, classes below k are suppressed. Entire retained classes failing distinct `l=2` or categorical total-variation `t=0.3` are then suppressed. The procedure reports RRR, prosecutor risk, suppression, the hierarchy NCP proxy, and the l/t checks together; it does not hide utility loss behind a privacy score.

### 2.3 Differential privacy

The project evaluates:

- the count of patients with heart disease (global sensitivity 1); and
- bounded mean age, clipped to `[0, 100]`.

The Laplace mechanism is evaluated at epsilon values `0.1`, `0.5`, and `1.0` over 100 seeded trials for each setting.

### 2.4 PRS equation

The release/inference PRS is:

```text
PRS(w) = w_RRR * RRR
       + w_l   * (1 - l_sat)
       + w_t   * (1 - t_sat)
       + w_DP  * min(1, epsilon / epsilon_ref)
```

where every component is in `[0, 1]`, weights are non-negative and sum to one, and the default baseline is equal weights (`0.25` each). It is a convex multi-criteria index, so it is bounded and monotone in each declared risk input. It is **not** a calibrated probability of re-identification or breach.

## 3. Results

### 3.1 Baseline UCI re-identification exposure

| QI set | RRR | Prosecutor risk |
|---|---:|---:|
| Age + gender + chest pain + blood pressure | 0.9158 | 0.9562 |
| Age + chest pain + blood pressure | 0.8687 | 0.9327 |
| Age + gender + blood pressure | 0.7845 | 0.8822 |
| Age + blood pressure | 0.6532 | 0.8081 |
| Age + gender | 0.0505 | 0.2458 |

The principal observation is that combining the declared clinical and demographic QIs creates high singleton exposure in the raw release. This establishes a measurable motivation for the release-protection layer on a real public benchmark.

### 3.2 k-anonymity, l-diversity, t-closeness, and utility

| k | Kept | Suppressed | Suppression | NCP proxy | RRR after | Prosecutor risk | l=2 | t=0.3 | Max TV distance |
|---:|---:|---:|---:|---:|---:|---:|---|---|---:|
| 3 | 115 | 182 | 61.28% | 0.6652 | 0.0000 | 0.1130 | Pass | Pass | 0.2478 |
| 5 | 188 | 109 | 36.70% | 0.6176 | 0.0000 | 0.0479 | Pass | Pass | 0.2766 |
| 10 | 296 | 1 | 0.34% | 0.9066 | 0.0000 | 0.0068 | Pass | Pass | 0.1196 |

`k=5` is the balanced reporting configuration because it meets the configured privacy checks, retains 63.30% of the cohort, and has lower declared NCP than the very coarse `k=10` hierarchy. This is a design choice supported by the reported trade-off; it is not a universally optimal k for every dataset or use case.

### 3.3 Differential-privacy utility

| Epsilon | Count MAE | Count SD | Mean-age MAE | Mean-age SD | Trials |
|---:|---:|---:|---:|---:|---:|
| 0.1 | 9.0000 | 8.4593 | 3.0488 | 2.8440 | 100 |
| 0.5 | 1.7900 | 1.6988 | 0.6098 | 0.5688 | 100 |
| 1.0 | 0.8800 | 0.9516 | 0.3049 | 0.2844 | 100 |

The result follows the expected privacy-utility relationship: smaller epsilon offers stronger formal privacy but increases error. This is direct empirical behavior of the implemented mechanism, not a claim that `epsilon=0.1` is universally appropriate.

### 3.4 Experimental PRS results

| Scenario | RRR | l satisfaction | t satisfaction | DP norm | NCP proxy | PRS |
|---|---:|---:|---:|---:|---:|---:|
| Raw UCI release | 0.9158 | 0% | 0% | 1.0 | 0.0000 | 0.9790 |
| UCI k=3 release | 0.0000 | 100% | 100% | 1.0 | 0.6652 | 0.2500 |
| UCI k=5 release | 0.0000 | 100% | 100% | 1.0 | 0.6176 | 0.2500 |
| UCI k=10 release | 0.0000 | 100% | 100% | 1.0 | 0.9066 | 0.2500 |
| UCI k=5 + DP eps=0.1 | 0.0000 | 100% | 100% | 0.1 | 0.6176 | 0.0250 |
| UCI k=5 + DP eps=0.5 | 0.0000 | 100% | 100% | 0.5 | 0.6176 | 0.1250 |
| UCI k=5 + DP eps=1.0 | 0.0000 | 100% | 100% | 1.0 | 0.6176 | 0.2500 |

The equal-weight index selects `k=5 + DP eps=0.1`. Across the 286 valid tested weight vectors (0.1-simplex grid), that setting is the lowest-score choice in **220/286 (76.92%)** of cases; `k=3` is selected in **66/286 (23.08%)**. Therefore the preferred setting is substantial but **not weight-invariant**. This sensitivity result is an essential part of the conclusion, not a weakness to omit.

## 4. Figures and charts created

All figures are generated from the actual CSV outputs by the pipeline, not drawn manually.

| File | What it shows | What it supports | Interpretation boundary |
|---|---|---|---|
| [`01_uci_profile.png`](../outputs/uci_heart/01_uci_profile.png) | UCI diagnosis distribution and QI cardinality | The real-data cohort profile and which QIs have high distinctness | It does not establish population representativeness. |
| [`02_uci_qi_risk.png`](../outputs/uci_heart/02_uci_qi_risk.png) | RRR across all QI-combination sizes | Adding QIs increases raw-release linkage exposure | It measures the declared attacker-QI model only. |
| [`03_uci_anonymization_tradeoff.png`](../outputs/uci_heart/03_uci_anonymization_tradeoff.png) | Residual RRR, suppression rate, NCP proxy at k=3/5/10 | Privacy requirements and utility loss must be interpreted together | NCP is a declared hierarchy-aware proxy, not a clinical utility validation. |
| [`04_uci_dp_and_prs.png`](../outputs/uci_heart/04_uci_dp_and_prs.png) | DP error across epsilon and UCI PRS scenarios | Expected epsilon/error trade-off and the defined composite ranking | PRS is an experimental multi-criteria index, not a universal risk probability. |
| [`05_prs_weight_sensitivity.png`](../outputs/uci_heart/05_prs_weight_sensitivity.png) | Winning PRS scenario across 286 weight vectors | Whether the equal-weight conclusion is robust to stated weight changes | The grid is a sensitivity analysis, not stakeholder preference elicitation. |
| [`01_cross_dataset_comparison.png`](../outputs/comparative/01_cross_dataset_comparison.png) | Synthetic vs UCI raw RRR, suppression, and DP count error | The real benchmark replicates the release/DP evaluation alongside the synthetic control | Dataset differences prevent causal or population-level comparison. |

The raw numeric counterparts are stored beside these figures in `outputs/uci_heart/` and `outputs/comparative/`.

## 5. Verification performed

The following commands were executed in an isolated `.venv` environment:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe run_full_analysis.py
.\.venv\Scripts\python.exe verify_research_evidence.py
.\.venv\Scripts\python.exe novelty_verifier.py
```

Results:

- **19/19 Python tests passed**, including the UCI loader, anonymization invariants, PRS simplex grid, existing DP tests, and existing PRS tests.
- **10/10 UCI evidence checks passed**: official raw checksum, cohort size, l/t guarantees, k=5 retention and no-singleton result, DP noise direction, equal-weight PRS result, sensitivity-grid validity, and required artifacts.
- **12/12 legacy synthetic experimental checks passed.** `NOVELTY_VERIFIED.txt` remains only as a legacy filename; its content now correctly says **Internal Experimental Conditions Verified**.
- Figure files were visually inspected after generation for labels and readability.

The machine-readable verification conclusion is in [`RESEARCH_EVIDENCE_STATUS.md`](../RESEARCH_EVIDENCE_STATUS.md).

## 6. What is achieved

The following research and engineering objectives are achieved:

- A reproducible public healthcare-data benchmark has been integrated with a documented source, license, DOI, preprocessing protocol, and raw-data checksum.
- The project no longer relies only on synthetic data for its privacy-release results.
- A real-data UCI cohort demonstrates high raw QI linkage exposure under a declared attacker model.
- The implementation demonstrably applies k-anonymity, l-diversity, t-closeness, suppression, and Laplace differential privacy to the UCI cohort.
- It reports privacy and utility outputs together, including all relevant trade-offs.
- The PRS is no longer presented as an unexplained formula; its sources, structure, assumptions, boundedness, monotonicity, and weight sensitivity are documented.
- The result artifacts, tests, code, and checks can be rerun by another researcher.
- The PostgreSQL RBAC/RLS/audit layer remains implemented as a distinct schema-level component of the system.

This is a credible, reproducible **research prototype and benchmark evaluation**. The contribution is the transparent integration and evaluation of complementary privacy controls, not a claim that any one privacy mechanism was invented here.

## 7. What is not yet achieved

The following claims are not supported by this repository and must not be made in a paper, presentation, or abstract:

- “Publication is guaranteed.”
- “The research is worldwide novel” or “first” without a systematic literature review.
- “PRS is a universally proved/validated privacy-risk equation.”
- “The project is HIPAA/GDPR compliant” or deployment-ready.
- “UCI proves the RBAC/RLS layer reduces breach risk by a measured percentage.”
- “The UCI cohort represents current hospital populations.”
- “The selected k or epsilon is universally optimal.”

The PRS still needs empirical calibration against actual privacy attacks, expert/stakeholder weight elicitation, more datasets, multiple sampling settings, and independent replication. The database layer needs a live PostgreSQL deployment verification in the target environment if a deployment claim is to be made; the UCI extension itself did not rerun a PostgreSQL server because no server credentials/environment were supplied for this run.

## 8. Recommended paper claim

The defensible central claim is:

> On a documented public UCI Cleveland benchmark and a synthetic schema-control cohort, PriDB-Health reproducibly evaluates a database-oriented combination of access governance, k-anonymity with l-diversity and t-closeness, and Laplace differential privacy. Under the stated threat model, hierarchy, parameters, and experimental PRS definition, the protected UCI releases remove singleton QI classes and satisfy the selected l/t checks; the DP experiments expose the expected privacy-utility trade-off. The composite PRS is an interpretable, sensitivity-tested experimental index rather than a universal privacy probability.

This claim is evidence-based, clear about its scope, and suitable for a methods/results section. It is stronger and more defensible than an absolute novelty or guaranteed-publication claim.

## 9. Main project files

| Purpose | File |
|---|---|
| UCI source, license, checksum, preprocessing | [`dataset/DATASET_CARD.md`](../dataset/DATASET_CARD.md) |
| UCI loader and analysis | [`src/uci_heart_benchmark.py`](../src/uci_heart_benchmark.py) |
| Cross-dataset chart generator | [`src/comparative_visuals.py`](../src/comparative_visuals.py) |
| PRS implementation | [`src/privacy_risk_score.py`](../src/privacy_risk_score.py) |
| PRS derivation and validation | [`docs/PRS_DERIVATION_AND_VALIDATION.md`](PRS_DERIVATION_AND_VALIDATION.md) |
| Methodology | [`docs/METHODOLOGY.md`](METHODOLOGY.md) |
| Limitations | [`docs/RESEARCH_LIMITATIONS.md`](RESEARCH_LIMITATIONS.md) |
| Automated evidence verifier | [`verify_research_evidence.py`](../verify_research_evidence.py) |
| Evidence status | [`RESEARCH_EVIDENCE_STATUS.md`](../RESEARCH_EVIDENCE_STATUS.md) |
