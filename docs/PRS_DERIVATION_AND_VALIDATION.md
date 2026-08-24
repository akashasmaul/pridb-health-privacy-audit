# Privacy Risk Score: derivation, interpretation, and validation plan

## Status

The PriDB-Health Privacy Risk Score (PRS) is a **transparent experimental multi-criteria index**. It is not a standard, universally validated privacy-risk probability, a differential-privacy theorem, a legal test, or a clinical safety score. This distinction is part of the method, not a disclaimer added afterward.

## Starting point: established measures

The score does not invent its four inputs.

| Risk channel | Quantity in PRS | Established basis | Interpretation in this project |
|---|---|---|---|
| Identity disclosure in a released microdata table | `RRR` | Equivalence classes and k-anonymity [Sweeney, 2002] | Fraction of records in a singleton QI class; lower is better. |
| Sensitive-attribute disclosure | `1 - l_sat` | Distinct l-diversity [Machanavajjhala et al., 2007] | Fraction of retained equivalence classes that fail the chosen l criterion. |
| Distributional attribute disclosure | `1 - t_sat` | t-closeness [Li et al., 2007] | Fraction of retained classes that exceed the predeclared categorical total-variation threshold. |
| Aggregate-query disclosure | `ε / ε_ref` | ε-differential privacy [Dwork et al., 2006] | A bounded reporting normalization of privacy loss, not a probability. `ε_ref = 1.0` is the largest evaluated budget. |

`l_sat` and `t_sat` are calculated after suppression. Their denominators are the remaining release classes, so record retention and NCP must always be reported beside PRS.

## Derivation

Each component is a dimensionless risk quantity in `[0, 1]`. Let

```text
r = ( RRR, 1 - l_sat, 1 - t_sat, min(1, ε / ε_ref) ).
```

For a chosen non-negative weight vector `w` whose entries sum to one, the additive multi-criteria index is

```text
PRS(w) = w_RRR·RRR + w_l·(1 - l_sat) + w_t·(1 - t_sat) + w_DP·min(1, ε / ε_ref).
```

The default reported analysis sets each weight to `0.25`. Equal weights are an auditable *baseline value judgment* in the absence of elicited stakeholder preferences; they are not learned from data and are not claimed to be clinically universal. Additive aggregation is used because the four terms represent explicitly separated release/inference channels and is a standard multi-criteria decision-analysis form [Keeney & Raiffa, 1976].

The score is bounded because it is a convex combination of bounded inputs. It is monotone in every risk input: lowering any input while holding all others fixed cannot increase PRS. These are mathematical properties of the implementation; they do not establish empirical calibration.

## What was corrected

Earlier code transformed epsilon as `ε/(1+ε)` and multiplied microdata RRR by that transform. Neither operation is a differential-privacy theorem. The revised implementation instead holds microdata RRR unchanged when DP is added—DP protects query answers, not an already released microdata table—and normalizes epsilon only against the declared experimental range.

Similarly, database RBAC/RLS is verified through authorization and policy tests. It is **not** assigned an invented percentage reduction in microdata risk in the UCI benchmark. Access-control evidence and release-risk evidence are reported separately.

## Validation and robustness checks

The pipeline performs the following checks:

1. **Boundedness and monotonicity unit tests** for the score and epsilon normalization.
2. **Ablation comparison** across no release protection, k-anonymized releases, and k-anonymized plus DP releases.
3. **Weight sensitivity:** all 286 simplex weight vectors on a 0.1 grid are evaluated and the winning configuration share is plotted. A conclusion is reported as weight-robust only if it remains stable across the stated grid.
4. **Cross-dataset replication:** the same release metrics are reported for the synthetic control cohort and the UCI Cleveland benchmark.
5. **Utility disclosure:** suppression, hierarchy NCP proxy, and 100-trial DP error are shown beside PRS.

Future work needed before any claim of empirical score validation: preregister an attack benchmark, compare PRS against observed linkage/attribute-inference success, elicit weights from data stewards and privacy experts, and replicate on additional data-generating settings.

## References

- Sweeney, L. (2002). *k-Anonymity: A Model for Protecting Privacy*. International Journal of Uncertainty, Fuzziness and Knowledge-Based Systems, 10(5), 557-570. https://doi.org/10.1142/S0218488502001648
- Machanavajjhala, A., Gehrke, J., Kifer, D., & Venkitasubramaniam, M. (2007). l-Diversity: Privacy Beyond k-Anonymity. *ACM Transactions on Knowledge Discovery from Data*, 1(1). https://doi.org/10.1145/1217299.1217302
- Li, N., Li, T., & Venkatasubramanian, S. (2007). t-Closeness: Privacy Beyond k-Anonymity and l-Diversity. *IEEE ICDE*. https://doi.org/10.1109/ICDE.2007.367856
- Dwork, C., McSherry, F., Nissim, K., & Smith, A. (2006). Calibrating Noise to Sensitivity in Private Data Analysis. *IEEE FOCS*. https://doi.org/10.1109/FOCS.2006.37
- Keeney, R. L., & Raiffa, H. (1976). *Decisions with Multiple Objectives: Preferences and Value Tradeoffs*. Wiley.
