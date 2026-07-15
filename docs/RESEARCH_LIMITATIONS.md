# Research limitations

PriDB-Health is a research prototype with promising internal evidence, not a finished clinical system.

## Evidence limitations

- The dataset is synthetic and follows Faker distributions rather than a validated hospital population.
- Results come from one dataset size and one deterministic seed.
- The 97.7% figure is conditional on the repository's PRS formula and equal weights.
- PRS has not been validated as a clinical, legal, or universal privacy-risk scale.
- The baseline RBAC risk reduction is a modeling assumption, not a measured breach probability.
- The current t-closeness distance treats diagnosis categories as unordered.
- No external privacy attacks or independent replication are included yet.

## Engineering limitations

- PostgreSQL superusers and infrastructure compromise are outside the role model.
- SELECT auditing requires production-grade facilities such as pgaudit.
- Key management, backup security, retention, consent, break-glass access, and incident response are not implemented.
- The browser demonstration is educational and does not query the live database.

## Claims

The repository verifies that its implemented three-layer configuration wins under its declared experiment. Establishing worldwide novelty requires a systematic literature review. Establishing compliance requires qualified legal and organizational review. Clinical deployment requires ethics approval, security testing, governance, and validation on representative data.

