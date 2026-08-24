# UCI Heart Disease - Cleveland Benchmark

## Provenance

- **Source:** UCI Machine Learning Repository, Heart Disease dataset (ID 45)
- **Official landing page:** https://archive.ics.uci.edu/dataset/45/heart
- **DOI:** https://doi.org/10.24432/C52P4X
- **Citation:** Janosi, A., Steinbrunn, W., Pfisterer, M., & Detrano, R. (1989). *Heart Disease* [Dataset]. UCI Machine Learning Repository.
- **License:** CC BY 4.0
- **Subset used:** the repository's `processed.cleveland.data` file (303 rows; 14 published attributes).
- **Downloaded:** 2026-08-24 from the official UCI static file endpoint.
- **Raw-file SHA-256:** `A74B7EFA387BC9D108D7D0115D831FE9B414B29AE7124F331B622B4EFA0427C8`

## Privacy and scope

This is a public, de-identified historical benchmark, not a contemporary clinical cohort and not evidence of deployment safety. The original UCI documentation states that the full database originally contained direct identifiers that were replaced/removed; this repository uses only the processed Cleveland file.

## Reproducible processing

`src/uci_heart_benchmark.py` reads the raw file without modification, assigns the published 14 column names, converts `?` to missing values, and drops the six rows missing `ca` or `thal`. The analysis cohort therefore contains **297 complete cases**. The target `num` is binarized exactly as described by UCI: `0` is no heart disease and `1`-`4` is heart disease present.

The benchmark QIs are `age`, `gender`, `chest_pain`, and `blood_pressure`; diagnosis is the sensitive attribute. These analytical design choices are documented in `docs/METHODOLOGY.md`; they are not properties guaranteed by UCI.
