# Language-Bias Auditor for LLM Judges

**Current status (2026-11-12):** E4 uses 40 questions / 160 answers per grader.
The saved grade file contains 192 a1 entries, including 84 bulk-assigned ratings whose
notes explicitly state that individual review was not recorded. These are not independent
human validation. There is no two-rater consensus result. See
`data/e4/reduced40/bulk_rating_provenance.json` and the coverage tables.
The Hindi-rubric arm and comment-label validation remain deferred.
Use `data/e4/reduced40/sheet_a1.csv` and `sheet_a2.csv`; original row IDs are retained.
Import sheets with `python -m lb.e4 import <path>` and rebuild with `python -m lb.e4`.
The model mitigation analysis still uses its original 60-item subset.

Do LLM judges score the same answer differently when it is written in English, Hindi (Devanagari),
Romanized Hindi or Hinglish? This repo measures the gap (E1 pointwise, E2/E3 pairwise), checks judges
against Hindi-speaking humans (E4), and tests prompt-level fixes (E5). Course project UE24AM343AB5.

**Historical model snapshot (2026-11-01, Qwen translate-then-judge analysed).** 150 quadruples (100 factual, 50 open-ended) and 60 wrong twins, drafted by Claude and all verified by a Hindi speaker. **Main study:** baseline E1-E3 complete for qwen2.5-7b-local and gpt-oss-120b; `make stats` writes both judges' tables to `results/tables/main_baseline.md`. **Section B** (post hoc criterion leakage and comment coding): `make stats-b`; the 200-comment two-rater check is still to be labelled. **Gap A** (wrong twins scored pointwise, pre-registered in `analysis/plan.md`): done for both judges (480 calls); `make stats-a` writes `results/tables/main_baseline_a.md`. **E5** (mitigations on a 60-item subset): bias-aware done for both judges (920 calls each) and majority vote done, `make stats-e5` writes `results/tables/main_e5.md`; translate-then-judge done for both judges (180 shared translations and 920 planned judgments per judge; Qwen has 9 final unparsed E3 judgments); the Hindi rubric not run yet. **Results so far:** `analysis/results_summary.md` (draft). **Paper draft and source audit:** `report/draft.md`, `report/citation_audit.md`; `python report/verify_snapshot.py` checks source hashes, raw Qwen metrics and deterministic E5 table reproduction without provider calls. **Re-audit package:** `make package`. **Pilot:** gpt-oss-120b and gemini-flash done (`make reproduce-pilot` writes `pilot_report.md`). **Reproduce:** `make reproduce` reruns every main-study call from the cache and rebuilds all tables. **E4** (human grading, 100 items in four forms, at least two annotators): blind sheets in `data/e4/` (`make e4-sheets`), guideline `data/e4/guideline.md`, `make e4-import ARGS=<sheet>` merges a graded sheet into `data/human_grades.csv`, `make stats-e4` writes `results/tables/main_baseline_e4.md`; see current grading status above. `make stats-e5` adds the human-agreement accuracy cost once two graders overlap. Items enter analysis only after human verification via the QC sheet.

## Setup

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -e ".[dev]"   # .venv/bin/python on Linux/macOS
```

Or `make setup`. On Windows use `mingw32-make` (ships with MSYS2) in place of `make`.

### Environment variables (keys never go in files)

| Variable | Judge |
|---|---|
| `GEMINI_API_KEY` | gemini-flash (Google AI Studio free tier) |
| `GROQ_API_KEY` | gpt-oss-120b (Groq free tier); also the E5(b) translator |
| `SARVAM_API_KEY` | sarvam (optional, disabled by default) |
| none | qwen2.5-7b-local via Ollama: `ollama pull qwen2.5:7b-instruct` |

## Workflow

```bash
make data-check                      # schema, UTF-8, missing forms, length ratios, QC status
make qc-export                       # unverified items -> data/qc/to_verify.csv for Hindi checkers
make qc-import                       # apply their corrections; items with all rows ok=Y become qc.passed
make budget                          # planned + current-data call counts
make budget-pilot ARGS=--include-unverified   # pilot dry run
make pilot                           # prints the pilot budget and stops
make pilot ARGS=--yes                # actually calls judges (only qc.passed items)
make test
make reproduce                       # rerun every logged main-study call from cache, no network
                                     # (a miss is an error); then make stats stats-b stats-a stats-e5
```

## Call budget

From `python -m lb.budget` with the current config (3 enabled judges for E1-E3; Sarvam disabled):

| Experiment | Calls |
|---|---|
| E1 pointwise (150 x 4 forms x 3 judges) | 1,800 |
| E2 pairwise (3 pairs x 2 orders x 150 x 3) | 2,700 |
| E3 wrong English (3 x 2 x 60 x 3) + control (2 x 60 x 3) | 1,080 + 360 |
| Gap A wrong twins pointwise (60 x 4 forms x 2 judges) | 480 |
| E5 per variant (2 judges, 60 items, 40 twins: E1 480 + E2 720 + E3 640) x 3 variants | 3 x 1,840 |
| E5(b) translations | 180 |
| **Total** | **12,120** |

Made so far: E1-E3 and gap A for qwen2.5-7b-local and gpt-oss-120b; E5 bias-aware and translate-then-judge for both judges. gemini-flash is in the
E1-E3 lists but has only pilot calls (20 per key per day), so its main-study calls are not made. With 4 judges
(brief section 6) E1-E3 are 2,400 / 3,600 / 1,440 + 480. The Phase 0 pilot (20 items, E1 + E2, 2 judges) is
**400 calls**. Parse retries add up to 2 calls per unparseable response. Every runner prints its exact
new-call count and refuses to run without `--yes`. `make budget` shows what is still uncached.

## Adding a judge

1. Add an entry under `judges:` in `configs/judges.yaml` (provider `openai_compat`, `base_url`, `model`,
   `api_key_env`, `requests_per_minute`). Any OpenAI-compatible endpoint works with no code change.
2. For a non-compatible API, add `src/lb/providers/<name>.py` implementing `complete(prompt, temperature)`
   and register it in `providers/__init__.py:make_provider`.
3. Add the judge name to the experiment lists in `configs/experiments.yaml` and check `make budget`.
4. It must not be the drafting model (`drafting_model` in judges.yaml); runners refuse it.

## Layout

See `docs/design.md` for the pipeline diagram and `docs/data_plan.md` for sources and selection rules.
`analysis/plan.md` fixes every comparison before results are seen.

```
configs/   judges.yaml, experiments.yaml          prompts/  versioned prompt text (see prompts/README.md)
data/      questions.jsonl, quadruples.jsonl, drafts/, sources/, qc/
src/lb/    schema, judge, cache, providers/, runners/, budget, stats, qc, data_check
results/   raw/ (one line per call), cache/, tables/   tests/  schema, parsing, cache, order swap, stats
```

## Known limitations

- All non-English texts are machine-drafted (claude-opus-5-5) and then human-verified; residual
  translation artefacts are possible, and the drafter's style may differ from naturally written Hindi.
- Two completed main-study judges; Gemini is pilot-only. Human grading of the 100-item subset is pending.
- Pilot items: 15 factual MMMLU questions and 5 MT-Bench prompts; not representative of the final 150.
- Model ids for free tiers change; confirm `configs/judges.yaml` before each run and record the date.
- The Hindi rubric (E5a) is drafted by Claude and must be verified before use.

## Working demo

Install with `python -m pip install -e ".[app]"` in your virtual environment.
Run `python demo/app.py` from this repository, or use `./Start-Demo.ps1` on Windows
with a `.venv` environment. `make app` also starts it.
Select demo mode, baseline, and dataset item `mmmlu-geo-0013`, then click Audit.
Demo mode replays real cached responses without model calls; custom text usually has no cache hit.
Live mode requires the configured provider credentials or local model server.
See [the presentation guide](demo/DEMO_GUIDE.md).
