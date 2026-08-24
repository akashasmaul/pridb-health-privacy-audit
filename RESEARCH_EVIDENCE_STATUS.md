# PriDB-Health research evidence status

Generated: 2026-08-24T21:11:58

## Status: IMPLEMENTATION AND BENCHMARK CHECKS PASS

## Reproducible checks

- PASS **required_artifacts** - all required artifacts present
- PASS **uci_raw_checksum** - a74b7efa387bc9d108d7d0115d831fe9b414b29ae7124f331b622b4efa0427c8
- PASS **uci_complete_case_cohort** - 297 rows after documented missing-value handling
- PASS **k_release_guarantees** - all retained classes satisfy l=2 and t=0.3
- PASS **k5_release_retention** - k=5 retains records
- PASS **k5_residual_rrr** - no singleton retained QI class
- PASS **dp_noise_present** - errors=[9.0, 1.79, 0.88]
- PASS **dp_inverse_utility** - smaller epsilon has larger observed noise
- PASS **equal_weight_prs_winner** - UCI k=5 + DP eps=0.1 PRS=0.0250
- PASS **prs_weight_grid** - 286 valid weight vectors

## What this establishes

The repository reproduces the documented UCI Cleveland release-layer benchmark, preserves the official raw-file checksum, and produces internally consistent k-anonymity, l-diversity, t-closeness, differential-privacy, PRS, and sensitivity artifacts.

## What this does not establish

It does not prove worldwide novelty, publication acceptance, clinical effectiveness, regulatory compliance, or empirical calibration of PRS. UCI validates the release and aggregate-query experiments, not an RBAC breach-rate reduction. The PRS remains a transparent experimental multi-criteria index; its weights require stakeholder or attack-benchmark validation for stronger claims.
