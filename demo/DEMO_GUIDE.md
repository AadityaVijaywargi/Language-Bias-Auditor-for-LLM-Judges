# Presentation demo

Run from PowerShell: `powershell -ExecutionPolicy Bypass -File .\Start-Demo.ps1`.
Open the local URL printed by Gradio. Keep the terminal open.
Install dependencies into this repository's .venv with `python -m pip install -e ".[app]"`. The demo also runs with `python demo/app.py`.

## Five-minute walkthrough
1. Explain the question: does changing the language change a judge's evaluation of equivalent answers?
2. Keep Mode = demo and Prompt variant = baseline. Select a cached dataset item.
3. Show the four answer forms. Click Audit. Explain correctness, completeness, clarity and language quality separately.
4. Compare content gaps against English. These are observations, not proof that language alone caused a difference.
5. Show both pairwise orders and discuss whether the winner changes when positions change.
6. Switch judge where the item lists that judge as cached and repeat.
7. Show results/tables/main_e5.md for mitigation findings and main_baseline_e4.md for the actual human-validation coverage.

## Before presenting
- Rehearse the selected item and judge; confirm all four score rows and six pairwise rows appear.
- Saved results are real cached model responses, not fresh inference. State this explicitly.
- Custom text in demo mode usually has no matching cache. Live mode requires the configured provider or local Ollama service.
- Mitigation caches cover a subset. Missing outputs are reported, never fabricated.
- Human validation is incomplete in this checkout; do not claim completed two-rater agreement. The Hindi-rubric arm is deferred.
- Keep screenshots or a short screen recording as a presentation backup.
