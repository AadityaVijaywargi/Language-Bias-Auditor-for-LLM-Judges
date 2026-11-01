# Qwen E5 analysis verification

Verified 1 November 2026. Raw results were published in commit `b6150448f4a875e32085104c313d15ba88319936` before this analysis update.

## Checks performed

- `python -m pytest -q`: **115 passed**, one `SmallSampleWarning` in the synthetic pilot-report fixture (`test_pilot_report_synthetic`, `stats.py` length regression). This is not a clean zero-warning claim and does not indicate an E5 failure.
- `python -m lb.mitigation`: regenerated **168 E5 rows**, including both translation judges, both bias-aware judges, two-judge aggregation, descriptive criterion gaps and ties. The human-agreement accuracy table remains empty because human grades are absent.
- `python report/refresh_tables.py`: populated **eight paper tables** and refreshed the evidence manifest.
- `python report/verify_snapshot.py`: verified source hashes, independently reconstructed **28 Qwen translation metric rows** from parsed raw records, and rebuilt every E5 CSV/Markdown output in a temporary directory with **byte-identical output**.
- `python -m lb.data_check`: checked the verified dataset without editing its contents.
- `git diff --check`: checked the patch for whitespace errors before publication.

No provider calls were made by these analysis commands. Raw responses and cache entries were not edited. The independent metric reconstruction verifies sample sizes, baseline values, variant values and paired changes; bootstrap intervals are covered by deterministic reproduction and the existing statistical tests, not by a second independent bootstrap implementation.

## Coverage and interpretation

Qwen translation coverage is 240 E1, 360 E2 and 320 E3 planned judgments. All nine final unparseable judgments are in E3. New provider attempts during the original judging run totaled 791; 140 planned judgments reused baseline cache. E3 changes require both answer orders in both baseline and variant, leaving 36 paired items per non-English form and 39 English controls.

The mean absolute Hinglish content gap narrows from 0.533 to 0.183, while the signed Romanized-Hindi gap becomes more negative. Pairwise English preference declines for Romanized Hindi and Hinglish. These findings do not establish translation equivalence or better agreement with humans. Unchanged English-control accuracy reuses identical cached English-only prompts and is not independent evidence of preserved accuracy after translation.

## Scope of publication

The analysis update includes the existing E5 extensions for descriptive criterion gaps, tie rates and future human-agreement costs, together with their tests and analysis-plan disclosure. The unrelated local change to `scripts/e5_calls_left.py` is outside this commit. No audit-branch engineering changes, new judge configurations or unfinished human annotations are included.
