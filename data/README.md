# Data

This analysis uses the **Home Office spending over £25,000** open dataset.

- Source: https://www.gov.uk/government/collections/home-office-spending
- Period: financial year 2025-26 (April 2025 to March 2026), 12 monthly CSV files.

## How to reproduce
1. Download the 12 monthly CSVs (Apr 2025 to Mar 2026) from the link above.
2. Put them in `data/raw/`.
3. Run `python analysis.py` from the repo root.

`ho_fy2526_combined.csv` in this folder is the cleaned, combined dataset
(17,743 transactions) produced by the script, included so the analysis can be
inspected without re-downloading. Raw files are Crown copyright, Open Government Licence v3.0.
