# Security policy

## Supported version

Security fixes are applied to the latest commit on the default branch.

## Reporting a vulnerability

Please do not open a public issue for a vulnerability that could expose data or bypass access controls. Use GitHub's private vulnerability reporting feature for this repository. Include the affected SQL/Python module, reproduction steps, expected impact, and a suggested mitigation if known.

Do not include real health records, passwords, connection strings, or access tokens in a report.

## Prototype scope

PriDB-Health is research software. It has not undergone clinical validation, penetration testing, HIPAA certification, GDPR conformity assessment, or production hardening. The demonstration password in `.env.example` must never be used in production.

