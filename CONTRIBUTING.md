# Contributing to PriDB-Health

Thank you for helping make privacy research more reproducible.

## Useful contributions

- reproduce the experiment on another operating system or PostgreSQL version;
- add realistic privacy attacks and report both successful and failed attacks;
- evaluate alternative PRS weights with sensitivity analysis;
- improve anonymization utility without weakening declared guarantees;
- add bounded DP queries with explicit sensitivity proofs;
- correct documentation or accessibility issues.

## Development workflow

1. Create an issue describing the research question or defect.
2. Fork the repository and create a focused branch.
3. Install `requirements.txt` in an isolated environment.
4. Run `python -m pytest tests -v`.
5. Run `python run_full_analysis.py` and `python novelty_verifier.py` when analysis changes.
6. Explain changed assumptions, metrics, seeds, and expected outputs in the pull request.

## Research integrity

Do not tune data, metrics, or thresholds only to produce a preferred conclusion. Report negative results. Never add real patient data, secrets, credentials, or re-identifiable health information. Clearly label synthetic, simulated, inferred, and externally validated evidence.

## Style

- Prefer clear functions with explicit inputs and deterministic tests.
- Keep SQL idempotent and least-privileged.
- Document the privacy threat model behind every new mechanism.
- Update methodology and limitations when an assumption changes.

Participation is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

