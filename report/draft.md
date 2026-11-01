# Language-Bias Auditing Across English, Devanagari Hindi, Romanized Hindi and Hinglish

**Working paper draft — 1 November 2026, updated after the completed Qwen translation run.** Methods, related work and findings from completed experiments. Author names and affiliation are to be supplied by the team. This is an editable research draft, not a submission-ready IEEE layout. Numerical evidence is frozen to the CSV files recorded in [evidence_manifest.json](evidence_manifest.json). Rebuild report tables with `python report/refresh_tables.py` after regenerating E5 statistics; run `python report/verify_snapshot.py` to verify provenance and numerical reproduction without provider calls.

## Abstract

LLM judges may assign different scores to answers intended to express the same content in different written forms. We audit two judges using human-verified matched answers in English, Devanagari Hindi, Romanized Hindi and Hinglish. The dataset contains 150 questions and 60 factual wrong-answer twins. We measure pointwise score differences, pairwise preferences in both answer orders, and acceptance of known-wrong answers. Both judges score Devanagari Hindi above Romanized Hindi on average. GPT-OSS shows negative pointwise content gaps for Romanized Hindi and Hinglish and selects English in every non-tie matched-content comparison. Qwen exhibits substantial position sensitivity and accepts more wrong answers in Romanized Hindi than in English. Prompt interventions have different effects across the two judges; translation can also alter answer content. These findings describe the evaluated models and dataset. Human grading, comment-label validation and the remaining mitigation experiments are pending, so no claim about agreement with Hindi-speaking raters is made.

## 1. Introduction

Using language models to evaluate generated answers offers a scalable alternative to repeated human assessment. However, scores are useful only to the extent that they reflect the intended evaluation criteria. Earlier work on MT-Bench documents position, verbosity and self-enhancement biases [R1]. In multilingual settings, the written form of an answer introduces another possible source of variation.

This study asks whether a judge changes its score or preference when answer content is intended to remain constant across English, Devanagari Hindi, Romanized Hindi and Hinglish. The distinction between the last two forms matters: Romanized Hindi changes the writing system, whereas Hinglish also mixes Hindi and English vocabulary. We evaluate pointwise scoring and pairwise selection separately because a small average score gap need not imply balanced pairwise preferences.

Our contribution is a combined audit design: matched four-form answers with human verification, separate content and language-quality scores, known-wrong factual twins, and comparisons of prompt interventions on a shared subset. The planned human study will compare judge–human agreement by written form. We do not claim the first study of Hindi judge bias, the first four-form comparison, or the first multilingual judge–human validation.

## 2. Related work

### 2.1 Multilingual consistency and language preference

Fu and Liu evaluate multilingual judges across several tasks and languages and report low cross-language consistency [R2]. Their findings motivate checking whether the same evaluation task remains stable when language changes. Zhou, Luo and colleagues study pairwise language bias and find that many judges favor English, with answer language more influential than question language [R3]. Zhou, Resck and colleagues instead demonstrate systematic score differences on semantically matched multilingual instruction–response pairs, with more generous scoring in lower-resource languages [R4]. Together, these studies motivate a two-sided analysis: language-associated effects can be either score inflation or score reduction, and pointwise scoring should not be treated as interchangeable with pairwise accuracy.

The closest comparator is `hindi-judge-invariance` [R5]. Its full report evaluates 387 LLMBar items in four forms with six judges, both orders, repeat-run controls, item-clustered intervals and GEE modeling. Unlike our cross-form answer pairs, it translates the instruction and both candidates together; its prompt requires a binary choice. We extend the question through pointwise criteria, matched wrong twins and prompt interventions. Human score validation remains planned. We do not claim broader judge coverage or stronger robustness controls. A [design comparison](comparator_review.md) records the overlap and differences; the comparator remains unpublished.

### 2.2 Human validation of multilingual judges

PARIKSHA compares human and LLM evaluations across Indic languages using both pairwise comparison and direct assessment [R6]. METAL provides native-speaker judgments for multilingual summarization and reports discrepancies between model and human rationales [R7]. CIA introduces the Recon human-scored test set and Hercule, an evaluator that uses English references to assess multilingual responses [R8]. These establish multilingual human validation as prior work. Doğruöz and colleagues additionally document gaps in multilingual human validation and overreliance on individual judges [R15]. Our planned E4 asks a narrower question: whether agreement with human raters differs across written forms of matched Hindi content. Until E4 is complete, the present results establish model behavior rather than human alignment.

### 2.3 Prompt interventions and ensembles

Zubiaga and colleagues study multilingual evaluator design, including instruction translation and supervision choices in English, Spanish and Basque [R9]. This motivates treating rubric language as an experimental factor rather than assuming that localization improves evaluation. Mehrabi, Aliannejadi and Siro find that prompting effects can change direction across judges and depend on task and language [R16]. Their recent preprint directly limits any broad novelty claim for head-to-head multilingual prompting comparisons. Our narrower contribution is the chosen interventions on matched Hindi forms, with human-agreement costs planned. Verga and colleagues propose a panel of diverse model evaluators [R10], providing a precedent for ensemble judging. Our two-member aggregation is a restricted case: the median of two scores is their mean, and a strict majority requires agreement. It therefore cannot establish the general value of a larger jury. We make no exhaustive claim that our specific combination has never been tested elsewhere.

## 3. Methods

### 3.1 Dataset and verification

The local dataset contains 100 factual MMMLU items, 27 MT-Bench items and 23 MT-Bench-Hi items. Dataset sources are documented in [R11–R14] and in `data/quadruples.jsonl`. The factual items have English reference answers; the open-ended items are evaluated without references. Each question has four answer versions: English (`en`), Devanagari Hindi (`hi`), Romanized Hindi (`hi_rom`) and Roman-script Hinglish (`hinglish`). Sixty factual items additionally have matched wrong-answer twins in all four forms.

The dataset records `claude-opus-5-5` as the drafting model. Every item and wrong twin has passed the repository's human-verification gate. The main-item verification records name one verifier, Aaditya Vijaywargi. This establishes recorded sign-off, not independent multi-rater proof of equivalence. Residual differences in vocabulary, naturalness, length and semantic fidelity remain possible. The main-study dataset includes the pilot items; pilot log records are excluded from main analysis, while identical requests may reuse cached responses. Main-study item independence from the pilot must therefore not be claimed.

### 3.2 Judges and execution

The completed main-study panel consists of `openai/gpt-oss-120b` through Groq and `qwen2.5:7b-instruct` through local Ollama. The dataset drafter is excluded from judging. All experiments use temperature zero. Questions are shown in English across answer forms; English references are shown for factual items. This controls question language but limits interpretation to this reference and instruction setting.

Responses are requested as JSON, with up to two parsing retries. Each response and attempt is logged, and cache keys incorporate the model, full prompt, temperature and attempt number. Responses that remain unparseable are missing for the affected comparison; they are not assigned a score or verdict. Baseline coverage is 600 pointwise, 900 matched pairwise and 480 correct-versus-wrong planned judgments per judge. These are logical judgments, not necessarily new provider calls, because caching and retries change execution counts.

### 3.3 Experiments

**E1: pointwise scoring.** Each answer receives integer scores from 1 to 5 for correctness, completeness, clarity and language quality. The primary content score is the mean of the first three; the secondary overall score includes all four. For each item, a form gap is the score of that form minus its English score. We also compare Devanagari with Romanized Hindi and Romanized Hindi with Hinglish. These are operational script and mixing contrasts, not interventions that isolate writing system or lexical mixing perfectly.

**E2: matched-content preference.** English is paired with each other form, and every pair is shown in both orders. We report English wins among non-tie judgments, ties, order consistency, the share of non-tie choices favoring slot A, and English preference among consistent non-tie item verdicts.

**E3: correct versus wrong.** Each correct non-English answer is paired with the wrong English twin in both orders. Correct English versus wrong English provides a control. We distinguish any-order wrong-English wins from wins in both orders; the latter is less vulnerable to interpreting a single order reversal as a stable content preference.

**Gap A: wrong-answer pointwise scores.** Each wrong twin receives the E1 rubric. False acceptance is pre-specified as correctness at least 3. We report acceptance by form, wrong-score differences from English, and the discrimination margin between each correct answer and its wrong twin. The English reference is visible, which may make detection easier.

**E4: planned human reference.** Two or more Hindi-fluent annotators will each grade 100 items in all four forms. The sample contains the E5 subset and totals 67 factual and 33 open-ended items. Sheets hide item and form identifiers and shuffle answers into balanced blocks; language and repeated content remain observable. Annotators work independently using the same four criteria. Only cells graded by at least two annotators enter mean-human agreement analyses. No grades are available in this snapshot.

**E5: mitigations.** A seeded 60-item subset contains 40 factual items with verified wrong twins and 20 open-ended items. Each variant has 240 E1, 360 E2 and 320 E3 planned judgments per judge. Hindi-rubric prompts require human approval before use. Translate-then-judge uses a fixed GPT-OSS translator for the 180 non-English correct answers, while English answers and wrong English twins pass through. The bias-aware variant appends an instruction to disregard language or script. Aggregation reuses baseline outputs without new calls. Variant changes are paired against each judge's baseline on the same subset.

### 3.4 Statistical analysis and provenance

The analysis plan specifies paired item bootstrap confidence intervals using 10,000 resamples and seed 20261023. E1 uses two-sided Wilcoxon signed-rank tests and Holm correction across the five primary content comparisons within each judge. An OLS adjustment on log word-length ratio is a sensitivity analysis, not a complete control for stylistic differences. E2 uses Wilson intervals and binomial tests with Holm correction across the three language pairs. Its planned pooled test counts both answer orders; those judgments share an item, so its nominal binomial uncertainty may be optimistic. Order-consistent summaries are reported alongside it. A future item-clustered sensitivity analysis would need to be labeled as an addition to the plan.

E3 and Gap A acceptance proportions use Wilson intervals. Gap A compares paired acceptance with exact McNemar tests and Holm correction across non-English forms. E5 differences use item-level bootstrap intervals; its absolute gap is the mean of per-item absolute differences, not the absolute value of a pooled signed gap. E4 will report inter-annotator quadratic-weighted kappa, judge–human content Spearman correlation, criterion kappa and paired differences from English.

Section B was added after baseline results and is explicitly post hoc. It examines score co-movement, an English-only halo baseline, criterion equality, and keyword-coded comments. Shared scoring calls prevent causal attribution from score correlations. Comment rates remain unvalidated until the two-rater sample has agreed labels. Additional type splits, criterion-level mitigation summaries and E2 tie-rate changes are identified as descriptive where required by the change log.

## 4. Findings from completed experiments

The numerical tables below are generated directly from the frozen source CSVs. Abbreviated judge names are GPT-OSS and Qwen. Confidence intervals are 95% intervals; values displayed as `<0.001` are rounded small p-values, never exact zero.

### 4.1 Pointwise scores differ by form and judge

| Judge | Comparison | n | Content gap [CI] | Holm p |
| --- | --- | --- | --- | --- |
| GPT-OSS | hi vs en | 150 | 0.022 [-0.020, 0.078] | 1.000 |
| GPT-OSS | hi_rom vs en | 150 | -0.164 [-0.209, -0.120] | <0.001 |
| GPT-OSS | hinglish vs en | 150 | -0.164 [-0.220, -0.113] | <0.001 |
| GPT-OSS | hi vs hi_rom | 150 | 0.187 [0.142, 0.238] | <0.001 |
| GPT-OSS | hi_rom vs hinglish | 150 | 0.000 [-0.053, 0.056] | 1.000 |
| Qwen | hi vs en | 150 | 0.156 [0.064, 0.249] | 0.006 |
| Qwen | hi_rom vs en | 150 | -0.024 [-0.140, 0.089] | 0.961 |
| Qwen | hinglish vs en | 150 | -0.100 [-0.211, 0.011] | 0.268 |
| Qwen | hi vs hi_rom | 150 | 0.180 [0.089, 0.271] | 0.002 |
| Qwen | hi_rom vs hinglish | 150 | 0.076 [-0.002, 0.158] | 0.187 |

GPT-OSS has little average content difference between Devanagari Hindi and English, but negative gaps for Romanized Hindi and Hinglish. Both judges score Devanagari above Romanized Hindi. The Romanized–Hinglish contrast is not statistically resolved for either judge after the specified correction. Consequently, these data support reporting the forms separately; they do not support a universal claim that code-mixing improves or worsens evaluation.

Qwen's pooled scores also conceal differences by item type. Its exploratory factual gaps are positive, while its open-ended gaps are negative. The script contrast should therefore be interpreted with item type and answer construction in view. Criterion-level GPT-OSS tables place much of the Romanized-form reduction in clarity and language quality. A smaller content gap after length adjustment is consistent with length being associated with part of the difference, but does not establish a causal explanation.

Sources: `main_baseline_e1.csv`, `main_baseline_e1_by_type.csv`, `main_baseline_e1_criteria.csv`.

### 4.2 Pairwise preference and position sensitivity

| Judge | Pair | English wins / non-ties | English win-rate [CI] | Tie rate [CI] | A-slot rate [CI] |
| --- | --- | --- | --- | --- | --- |
| GPT-OSS | en vs hi | 139/139 | 1.000 [0.973, 1.000] | 0.537 [0.480, 0.592] | 0.568 [0.485, 0.648] |
| GPT-OSS | en vs hi_rom | 224/224 | 1.000 [0.983, 1.000] | 0.253 [0.207, 0.305] | 0.513 [0.448, 0.578] |
| GPT-OSS | en vs hinglish | 200/200 | 1.000 [0.981, 1.000] | 0.333 [0.282, 0.389] | 0.610 [0.541, 0.675] |
| Qwen | en vs hi | 174/300 | 0.580 [0.523, 0.634] | 0.000 [0.000, 0.013] | 0.813 [0.765, 0.853] |
| Qwen | en vs hi_rom | 226/300 | 0.753 [0.702, 0.799] | 0.000 [0.000, 0.013] | 0.720 [0.667, 0.768] |
| Qwen | en vs hinglish | 206/298 | 0.691 [0.637, 0.741] | 0.000 [0.000, 0.013] | 0.795 [0.746, 0.837] |

GPT-OSS chooses English in every non-tie matched-content judgment, including the Devanagari comparison where its mean pointwise content gap is small. Its non-tie denominator varies substantially because it often returns ties. A conditional win-rate of one must therefore be read together with the tie rate.

Qwen's slot-A rates show strong position sensitivity. A one-order preference cannot be interpreted as a stable preference for a written form. Its consistent-verdict summaries should accompany pooled win-rates. This difference between pointwise scores and pairwise choices illustrates why neither measure alone characterizes judge invariance.

Source: `main_baseline_e2.csv`.

### 4.3 Wrong-answer comparisons reveal different failure modes

| Judge | Correct form | Wrong English wins both orders | Rate [CI] |
| --- | --- | --- | --- |
| GPT-OSS | hi | 0/60 | 0.000 [0.000, 0.060] |
| GPT-OSS | hi_rom | 0/60 | 0.000 [0.000, 0.060] |
| GPT-OSS | hinglish | 0/60 | 0.000 [0.000, 0.060] |
| GPT-OSS | en (control) | 0/60 | 0.000 [0.000, 0.060] |
| Qwen | hi | 5/53 | 0.094 [0.041, 0.203] |
| Qwen | hi_rom | 7/54 | 0.130 [0.064, 0.244] |
| Qwen | hinglish | 6/55 | 0.109 [0.051, 0.218] |
| Qwen | en (control) | 0/59 | 0.000 [0.000, 0.061] |

Qwen selects wrong English over correct non-English answers in both orders for some items, while the English control has no consistent wrong-answer wins. Any-order rates are higher and especially vulnerable to position effects. Missing Qwen cells reduce denominators below the planned sample. GPT-OSS records no consistent wrong-English wins, but zero observations are compatible with nonzero population rates, as its intervals show.

| Judge | Wrong-answer form | Accepted / scored | Acceptance rate [CI] | Paired vs English: Holm p |
| --- | --- | --- | --- | --- |
| GPT-OSS | en | 0/60 | 0.000 [0.000, 0.060] | — |
| GPT-OSS | hi | 0/60 | 0.000 [0.000, 0.060] | 1.000 |
| GPT-OSS | hi_rom | 0/60 | 0.000 [0.000, 0.060] | 1.000 |
| GPT-OSS | hinglish | 0/60 | 0.000 [0.000, 0.060] | 1.000 |
| Qwen | en | 10/60 | 0.167 [0.093, 0.280] | — |
| Qwen | hi | 17/60 | 0.283 [0.185, 0.408] | 0.039 |
| Qwen | hi_rom | 35/60 | 0.583 [0.457, 0.699] | <0.001 |
| Qwen | hinglish | 27/60 | 0.450 [0.331, 0.575] | <0.001 |

Pointwise wrong-answer scoring exposes a separate Qwen failure mode: acceptance is more frequent in Romanized Hindi and Hinglish than in English under the pre-specified threshold. GPT-OSS rejects all wrong twins under this protocol. The reference-guided factual setting can produce a floor in errors and does not establish that GPT-OSS is language-neutral in open-ended evaluation.

Sources: `main_baseline_e3.csv`, `main_baseline_a_false_acceptance.csv`, `main_baseline_a_margin.csv`.

### 4.4 Mitigation effects depend on the judge and metric

| Variant | Judge | Form | Content gap measure | n | Baseline | Variant | Change [CI] |
| --- | --- | --- | --- | --- | --- | --- | --- |
| translate_then_judge | GPT-OSS | hi | signed | 60 | 0.022 | -0.011 | -0.033 [-0.150, 0.050] |
| translate_then_judge | GPT-OSS | hi | absolute | 60 | 0.133 | 0.078 | -0.056 [-0.161, 0.017] |
| translate_then_judge | GPT-OSS | hi_rom | signed | 60 | -0.144 | -0.200 | -0.056 [-0.267, 0.133] |
| translate_then_judge | GPT-OSS | hi_rom | absolute | 60 | 0.211 | 0.333 | 0.122 [-0.056, 0.333] |
| translate_then_judge | GPT-OSS | hinglish | signed | 60 | -0.150 | -0.061 | 0.089 [0.006, 0.172] |
| translate_then_judge | GPT-OSS | hinglish | absolute | 60 | 0.172 | 0.139 | -0.033 [-0.111, 0.044] |
| translate_then_judge | Qwen | hi | signed | 60 | 0.100 | -0.161 | -0.261 [-0.433, -0.078] |
| translate_then_judge | Qwen | hi | absolute | 60 | 0.422 | 0.317 | -0.106 [-0.278, 0.056] |
| translate_then_judge | Qwen | hi_rom | signed | 60 | -0.067 | -0.444 | -0.378 [-0.650, -0.094] |
| translate_then_judge | Qwen | hi_rom | absolute | 60 | 0.522 | 0.478 | -0.044 [-0.278, 0.200] |
| translate_then_judge | Qwen | hinglish | signed | 60 | -0.189 | -0.094 | 0.094 [-0.094, 0.289] |
| translate_then_judge | Qwen | hinglish | absolute | 60 | 0.533 | 0.183 | -0.350 [-0.511, -0.200] |
| bias_aware | GPT-OSS | hi | signed | 60 | 0.022 | 0.017 | -0.006 [-0.067, 0.050] |
| bias_aware | GPT-OSS | hi | absolute | 60 | 0.133 | 0.083 | -0.050 [-0.094, -0.011] |
| bias_aware | GPT-OSS | hi_rom | signed | 60 | -0.144 | -0.033 | 0.111 [0.033, 0.200] |
| bias_aware | GPT-OSS | hi_rom | absolute | 60 | 0.211 | 0.133 | -0.078 [-0.150, 0.006] |
| bias_aware | GPT-OSS | hinglish | signed | 60 | -0.150 | -0.083 | 0.067 [-0.011, 0.156] |
| bias_aware | GPT-OSS | hinglish | absolute | 60 | 0.172 | 0.183 | 0.011 [-0.067, 0.100] |
| bias_aware | Qwen | hi | signed | 60 | 0.100 | 0.128 | 0.028 [-0.072, 0.133] |
| bias_aware | Qwen | hi | absolute | 60 | 0.422 | 0.428 | 0.006 [-0.089, 0.100] |
| bias_aware | Qwen | hi_rom | signed | 60 | -0.067 | -0.044 | 0.022 [-0.067, 0.111] |
| bias_aware | Qwen | hi_rom | absolute | 60 | 0.522 | 0.533 | 0.011 [-0.067, 0.094] |
| bias_aware | Qwen | hinglish | signed | 60 | -0.189 | -0.178 | 0.011 [-0.083, 0.106] |
| bias_aware | Qwen | hinglish | absolute | 60 | 0.533 | 0.467 | -0.067 [-0.150, 0.011] |

For GPT-OSS, the bias-aware instruction reduces the signed Romanized-Hindi penalty on the shared subset. It also produces many more ties in E2, while remaining non-tie picks still favor English. For Qwen, the absolute-gap changes do not establish an improvement: their intervals include zero. These results do not isolate model size as the explanation, because the two judges differ in architecture, training and deployment as well as scale.

The completed GPT-OSS translation arm has mixed results. Its Hinglish signed gap moves toward zero, but the Romanized-Hindi absolute gap increases, with an interval that includes zero. Translation changes the evaluated text and may introduce content errors; it cannot be treated as a pure removal of the original script. Previously inspected translation examples are an informal diagnostic, not a systematic human-verified translation-error rate.

**Completed Qwen translate-then-judge results.** Translation narrows the mean absolute Hinglish content gap from 0.533 to 0.183, a paired change of -0.350 [-0.511, -0.200]. The absolute-gap intervals for Devanagari and Romanized Hindi include zero. The signed Romanized-Hindi gap becomes more negative (-0.067 to -0.444), even though the average per-item absolute gap changes little. These metrics can move differently: a signed mean can hide positive and negative per-item gaps that cancel. Translation therefore does not uniformly improve pointwise invariance.

<!-- snapshot:qwen_e2 -->
| Pair | Measure | n paired items | Baseline | Translation variant | Change [CI] |
| --- | --- | --- | --- | --- | --- |
| en vs hi | English win-rate | 60 | 0.567 | 0.504 | -0.062 [-0.154, 0.022] |
| en vs hi_rom | English win-rate | 60 | 0.758 | 0.580 | -0.178 [-0.270, -0.092] |
| en vs hinglish | English win-rate | 60 | 0.733 | 0.521 | -0.212 [-0.292, -0.135] |
<!-- /snapshot:qwen_e2 -->

Qwen's English win-rate among non-tie judgments falls for Romanized Hindi and Hinglish, with both change intervals below zero. These remain comparisons between original English and translated English answers, labeled by the answers' original form. A smaller English preference is evidence of a changed evaluation outcome, not proof of equivalent translations or human alignment. The E5 confidence intervals resample items together with their answer orders, unlike the pooled baseline E2 binomial intervals discussed in the limitations.

<!-- snapshot:qwen_e3 -->
| Correct form | Measure | n paired items | Baseline | Translation variant | Change [CI] |
| --- | --- | --- | --- | --- | --- |
| hi | consistent wrong-English rate | 36 | 0.111 | 0.028 | -0.083 [-0.167, 0.000] |
| hi_rom | consistent wrong-English rate | 36 | 0.139 | 0.028 | -0.111 [-0.222, -0.028] |
| hinglish | consistent wrong-English rate | 36 | 0.139 | 0.028 | -0.111 [-0.222, -0.028] |
| en | control accuracy (correct en preferred) | 39 | 0.872 | 0.872 | 0.000 [0.000, 0.000] |
<!-- /snapshot:qwen_e3 -->

Consistent wrong-English preference falls to one item among the 36 jointly analyzable items in each non-English form. The Devanagari change interval reaches zero; Romanized Hindi and Hinglish intervals exclude it. This paired denominator requires parsed AB and BA judgments in both baseline and variant; it is not the full 40-item wrong-twin subset. The Qwen run recorded all 920 planned judgments (240 E1, 360 E2 and 320 E3), with nine final unparseable judgments, all in E3. They remain missing, not correct or incorrect verdicts. Judging used 791 new provider attempts including retries, with 140 planned judgments satisfied from the existing baseline cache.

| Variant | Judge | Pair | n items | Baseline tie rate | Variant tie rate | Change [CI] |
| --- | --- | --- | --- | --- | --- | --- |
| translate_then_judge | GPT-OSS | en vs hi | 60 | 0.517 | 0.900 | 0.383 [0.267, 0.500] |
| translate_then_judge | GPT-OSS | en vs hi_rom | 60 | 0.275 | 0.775 | 0.500 [0.375, 0.625] |
| translate_then_judge | GPT-OSS | en vs hinglish | 60 | 0.325 | 0.917 | 0.592 [0.483, 0.692] |
| translate_then_judge | Qwen | en vs hi | 60 | 0.000 | 0.008 | 0.008 [0.000, 0.025] |
| translate_then_judge | Qwen | en vs hi_rom | 60 | 0.000 | 0.008 | 0.008 [0.000, 0.025] |
| translate_then_judge | Qwen | en vs hinglish | 60 | 0.000 | 0.008 | 0.008 [0.000, 0.025] |
| bias_aware | GPT-OSS | en vs hi | 60 | 0.517 | 0.992 | 0.475 [0.383, 0.575] |
| bias_aware | GPT-OSS | en vs hi_rom | 60 | 0.275 | 0.942 | 0.667 [0.567, 0.758] |
| bias_aware | GPT-OSS | en vs hinglish | 60 | 0.325 | 0.975 | 0.650 [0.558, 0.742] |
| bias_aware | Qwen | en vs hi | 60 | 0.000 | 0.000 | 0.000 [0.000, 0.000] |
| bias_aware | Qwen | en vs hi_rom | 60 | 0.000 | 0.000 | 0.000 [0.000, 0.000] |
| bias_aware | Qwen | en vs hinglish | 60 | 0.000 | 0.000 | 0.000 [0.000, 0.000] |

The English correct-versus-wrong control remains perfect for GPT-OSS under the bias-aware and translate-then-judge variants. Qwen's paired English-control accuracy is unchanged at 34/39 (0.872). English-only judgments reuse baseline prompts and cached responses; unchanged control performance is expected under this design and is not an independent rerun confirmation. This control does not measure translation fidelity. Human-agreement accuracy cost is unavailable until E4. Thus, the appropriate claim is unchanged cached control performance on this subset, not an established absence of accuracy cost.

Two-judge aggregation gives every disagreement a tie and averages pointwise scores. Its behavior depends on the stronger and weaker member and the tie convention; it cannot support a general recommendation for majority voting. Full aggregation results remain in `main_e5_*` tables.

Sources: `main_e5_e1.csv`, `main_e5_e2.csv`, `main_e5_e2_ties.csv`, `main_e5_e3.csv`. Per-criterion E5 results and tie-rate changes are descriptive additions.

### 4.5 Exploratory criterion analysis

Section B describes co-movement between language quality and content criteria. Qwen's English-only halo baseline and frequent equality between clarity and language quality make causal leakage claims inappropriate. GPT-OSS's factual correctness scores are at ceiling, limiting detectable variation. These results motivate more targeted validation but cannot establish that language-quality assessment causes correctness changes. Keyword-coded comment statistics are withheld from the headline findings until the human validation sample is complete.

Sources: `main_baseline_b_halo.csv`, `main_baseline_b_copy.csv`, `main_baseline_b_leakage.csv`, `main_baseline_b_coder_check.csv`.

## 5. Limitations and pending evidence

The study uses two main judges, one configuration per judge, a small constructed dataset and a single recorded verifier. Machine drafting and human sign-off do not guarantee exact equivalence or natural writing. Formal vocabulary, informal Romanization and mixing choices may interact with script. English questions and factual English references restrict generalization and may explain ceiling or floor effects. Temperature zero does not guarantee repeat-run stability, which is not measured here.

Rubric scores are bounded and ordinal. Mean differences and OLS are useful summaries but do not remove this limitation. E2's two orders are correlated. Complete-case comparisons may be affected by differential parse failure. Both judges' score distributions and all missing denominators should accompany the final report. Small-cell and exploratory results require caution; zero observed errors do not establish zero risk.

E4 human grades and the two-rater comment check are absent. Hindi-rubric experiments await human prompt approval. Translate-then-judge is complete for both main judges, but its form-specific outcomes and unverified translation fidelity prevent a universal mitigation ranking. No final conclusion about judge–human alignment is warranted. The app is implemented on a separate local branch and has not been integrated into the main deliverable.

## 6. Current conclusion

The completed experiments show that judge behavior varies across written forms and evaluation formats. Devanagari–Romanized score differences coexist with judge-specific position effects, wrong-answer acceptance and tie behavior. Prompt interventions can change some of these measures without establishing general invariance. The final interpretation requires the pending human reference and completed mitigation panel.

## References

[R1] L. Zheng et al., “Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena,” NeurIPS Datasets and Benchmarks, 2023. [Primary source](https://arxiv.org/abs/2306.05685).

[R2] X. Fu and W. Liu, “How Reliable is Multilingual LLM-as-a-Judge?,” Findings of EMNLP, pp. 11040–11053, 2025. [Primary source](https://aclanthology.org/2025.findings-emnlp.587/).

[R3] X. Zhou et al., “Fairness or Fluency? An Investigation into Language Bias of Pairwise LLM-as-a-Judge,” arXiv:2601.13649, 2026. [Primary source](https://arxiv.org/abs/2601.13649).

[R4] E. Zhou, L. Resck, Z. Hui and A. Korhonen, “Lower-Resource, Higher Scores: Language Bias in LLM Evaluators,” COLM, 2026. [Official pre-proceedings](https://proceedings.colm.cc/paper_files/paper/2026/hash/d4f2c4e0cc3b39243151c03235fa39fb-Abstract-Conference.html); [arXiv v3](https://arxiv.org/abs/2607.14480v3). The official volume labels itself pre-proceedings pending DOI assignment.

[R5] kartiksaste123, “hindi-judge-invariance,” unpublished GitHub repository, accessed 1 November 2026. [Primary source](https://github.com/kartiksaste123/hindi-judge-invariance).

[R6] I. Watts, V. Gumma, A. Yadavalli, V. Seshadri, M. Swaminathan and S. Sitaram, “PARIKSHA: A Large-Scale Investigation of Human-LLM Evaluator Agreement on Multilingual and Multi-Cultural Data,” EMNLP, pp. 7900–7932, 2024. [Primary source](https://aclanthology.org/2024.emnlp-main.451/).

[R7] R. Hada, V. Gumma, M. Ahmed, K. Bali and S. Sitaram, “METAL: Towards Multilingual Meta-Evaluation,” Findings of NAACL, 2024. [Primary source](https://aclanthology.org/2024.findings-naacl.148/).

[R8] S. Doddapaneni et al., “Cross-Lingual Auto Evaluation for Assessing Multilingual LLMs,” ACL, pp. 29297–29329, 2025. [Primary source](https://aclanthology.org/2025.acl-long.1419/).

[R9] I. Zubiaga, A. Soroa and R. Agerri, “Towards Reliable Multilingual LLMs-as-a-Judge: An Empirical Study,” Findings of EMNLP, pp. 630–644, 2026. [Proceedings source](https://aclanthology.org/2026.findings-emnlp.32/). Title follows the retrieved proceedings page and PDF.

[R10] P. Verga et al., “Replacing Judges with Juries: Evaluating LLM Generations with a Panel of Diverse Models,” arXiv:2404.18796, 2024. [Primary source](https://arxiv.org/abs/2404.18796).

[R11] OpenAI, “MMMLU,” dataset. [Primary source](https://huggingface.co/datasets/openai/MMMLU).

[R12] Hugging Face H4, “mt_bench_prompts,” dataset. [Dataset distribution](https://huggingface.co/datasets/HuggingFaceH4/mt_bench_prompts); original benchmark: [R1].

[R13] A. Kamath et al., “Benchmarking Hindi LLMs: A New Suite of Datasets and a Comparative Analysis,” Proceedings of BHASHA, pp. 52–68, 2025. [Proceedings source](https://aclanthology.org/2025.bhasha-1.5/).

[R14] D. Hendrycks et al., “Measuring Massive Multitask Language Understanding,” ICLR, 2021. [Primary source](https://arxiv.org/abs/2009.03300v3). The local factual source-matching procedure is recorded in `docs/data_plan.md` and `scripts/fetch_sources.py`.

[R15] A. S. Doğruöz, X. Liao, V. Blaschke, J. Prange, S. Li and D. I. Adelani, “Challenges and Recommendations for LLM-as-a-Judge in Multilingual Settings and for Low-Resource Languages,” Findings of EMNLP, pp. 43001–43026, 2026. [Proceedings source](https://aclanthology.org/2026.findings-emnlp.2021/).

[R16] A. Mehrabi, M. Aliannejadi and C. Siro, “Prompting Strategy Effects Depend on the Judge: A Multilingual Study of LLM-as-a-Judge Robustness,” arXiv:2610.31172, 2026. [Primary source](https://arxiv.org/abs/2610.31172). Preprint submitted 22 October 2026.
