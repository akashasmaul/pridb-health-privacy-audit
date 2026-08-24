# Research limitations

PriDB-Health is a research prototype with promising internal evidence, not a finished clinical system.

## Evidence limitations

- The synthetic cohort follows Faker distributions rather than a validated hospital population. The UCI Cleveland benchmark is public historical data (297 complete cases after preprocessing), not a contemporary or representative hospital population.
- Results use one public benchmark subset and one synthetic-data seed; external replication remains necessary.
- The 97.7% figure is conditional on the repository's PRS formula and equal weights.
- PRS has not been validated as a clinical, legal, or universal privacy-risk scale.
- The baseline RBAC risk reduction is a modeling assumption, not a measured breach probability.
- The current t-closeness distance treats diagnosis categories as unordered.
- No external privacy attacks, stakeholder weight elicitation, or independent replication are included yet.
- UCI has no access-control outcomes; it cannot validate a numerical RBAC/RLS risk-reduction effect.

## Engineering limitations

- PostgreSQL superusers and infrastructure compromise are outside the role model.
- SELECT auditing requires production-grade facilities such as pgaudit.
- Key management, backup security, retention, consent, break-glass access, and incident response are not implemented.
- The browser demonstration is educational and does not query the live database.

## Claims

The repository verifies that its implemented three-layer configuration wins under its declared experiment. Establishing worldwide novelty requires a systematic literature review. Establishing compliance requires qualified legal and organizational review. Clinical deployment requires ethics approval, security testing, governance, and validation on representative data.

