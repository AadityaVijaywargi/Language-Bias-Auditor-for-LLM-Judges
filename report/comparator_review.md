# Closest-comparator design review

Reviewed 1 November 2026 against the full 11-page [results report](https://github.com/kartiksaste123/hindi-judge-invariance/blob/02064f01145135293daaf8964bec69777c14af29/results/report/results_report.pdf) and the [judge prompt](https://github.com/kartiksaste123/hindi-judge-invariance/blob/02064f01145135293daaf8964bec69777c14af29/prompts/judge_user.txt). Repository commit: `02064f01145135293daaf8964bec69777c14af29`. This is a methods comparison, not an independent reproduction of its results.

| Dimension | Comparator report/prompt | This project |
|---|---|---|
| Coverage | Four written forms | Same four; this is prior overlap |
| Evaluation | Pairwise gold-label accuracy | Pointwise criteria, preferences, wrong-twin scores |
| Language manipulation | Instruction and both candidates translated | English question; answer forms varied |
| Verdict | Forced binary choice | A/B/tie permitted |
| Panel | Six judges | Two completed main judges |
| Repeatability | Repeat-run subset | No repeated stochastic runs |
| Dependence control | Item-clustered bootstrap and GEE | Planned E2 pooled binomial intervals; dependence caveat |
| Human check | Translation-validation subset | One verifier for main items; independent score grading pending |
| Parsing failures | Counted incorrect | Missing for affected comparisons |

The report's scope is pairwise invariance; it does not present the pointwise rubric or intervention panel used here. This observation is limited to the reviewed artifact, rather than a claim about all unpublished work by its authors.

Our defensible distinction is the combination of content/quality criteria, error-detection scores and interventions under one Hindi-form protocol. Human agreement becomes an additional contribution only when E4 is completed. We should not claim that four-form comparison, answer-order control, human translation checks or language-associated degradation are new. The comparator also provides stronger repeatability and dependence controls than our current E2 analysis.

Its finding that Romanized Hindi is difficult is contextual support, not a numerical replication target: the benchmarks, prompts, verdict spaces and outcome measures differ. Its translation-validation wording must not be read as proof that every item received independent human checking.
