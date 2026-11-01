# Citation and claim audit

Checked 1 November 2026. This is a bounded source check for the accompanying draft, not a systematic review or a completed audit of every citation in the older research notes.

## Sources admitted to the draft

The following primary landing pages, abstracts, dataset cards and repository artifacts were retrieved. The follow-up pass read the full comparator report and its judge prompts, and checked the first page of the published R9 PDF. Other claims remain bounded by the listed checks; this is not a full-text audit of every source. Reference identifiers match `draft.md`.

| Ref | Primary source checked | Claim used in draft | Scope restriction |
|---|---|---|---|
| R1 | [MT-Bench paper](https://arxiv.org/abs/2306.05685) | LLM judging and position/verbosity/self-enhancement bias | No transfer of its human-agreement figures to this study |
| R2 | [Fu and Liu, Findings of EMNLP 2025](https://aclanthology.org/2025.findings-emnlp.587/) | Multilingual judge consistency is an established concern | No unverified Hindi-specific numerical breakdown |
| R3 | [Zhou, Luo et al.](https://arxiv.org/abs/2601.13649) | Pairwise language preference; answer vs question language | Cite as arXiv; no conference venue inferred |
| R4 | [Official COLM 2026 paper page](https://proceedings.colm.cc/paper_files/paper/2026/hash/d4f2c4e0cc3b39243151c03235fa39fb-Abstract-Conference.html) | Matched multilingual pointwise scores; lower-resource generosity | COLM confirmed; volume is pre-proceedings pending DOI assignment |
| R5 | [Full report and prompts](comparator_review.md) | Closely overlapping four-form pairwise study | Full report read; methods compared, results not independently reproduced |
| R6 | [PARIKSHA](https://aclanthology.org/2024.emnlp-main.451/) | Indic human–LLM comparison in pairwise and direct assessment | No new extraction of Hindi figure values or matched-content claim |
| R7 | [METAL](https://aclanthology.org/2024.findings-naacl.148/) | Native-speaker multilingual summarization meta-evaluation; rationale discrepancies | Abstract confirms multilingual scope, not a Hindi-specific statement |
| R8 | [CIA/Recon/Hercule](https://aclanthology.org/2025.acl-long.1419/) | Human-scored multilingual evaluation and English-reference judging | Hindi inclusion not rechecked in full text, so not asserted |
| R9 | [Findings of EMNLP 2026](https://aclanthology.org/2026.findings-emnlp.32/) and PDF first page | Instruction translation and evaluator training choices | Venue/pages verified; retrieved PDF retains the original LLMs-as-a-Judge title |
| R10 | [PoLL](https://arxiv.org/abs/2404.18796) | Diverse-model evaluator panels have precedent | Its results do not validate this two-member aggregation |
| R11 | [OpenAI MMMLU](https://huggingface.co/datasets/openai/MMMLU) | Factual dataset provenance | Local item counts come from local data, not the external card |
| R12 | [H4 MT-Bench distribution](https://huggingface.co/datasets/HuggingFaceH4/mt_bench_prompts) | Downloaded prompt distribution | Original benchmark attributed separately to R1 |
| R13 | [BHASHA 2025 proceedings](https://aclanthology.org/2025.bhasha-1.5/) | MT-Bench-Hi benchmark provenance | Publication/pages confirmed; no claim our answers are original source answers |
| R14 | [MMLU, v3](https://arxiv.org/abs/2009.03300v3) | Original factual benchmark attribution | Venue confirmed as ICLR 2021 on arXiv page |
| R15 | [Doğruöz et al., Findings 2026](https://aclanthology.org/2026.findings-emnlp.2021/) | Multilingual validation gaps and single-judge reliance | Proceedings metadata and abstract checked |
| R16 | [Mehrabi et al., October 2026 preprint](https://arxiv.org/abs/2610.31172) | Prompt effects depend on judge, task and language | Abstract checked; this narrows broad mitigation-comparison novelty |

Search used in this pass: `LLM judge Hindi Romanized Hinglish language bias mitigation 2026`, plus direct retrieval of the above known sources. Search engines may miss recent or unindexed work. Secondary search snippets were used to discover candidates, not to substantiate claims in the draft. No claim of exhaustive novelty is made.

## Claims revised while drafting

| Older wording or tempting inference | Wording used now | Reason |
|---|---|---|
| “Script, not language” | Devanagari–Romanized contrast on these constructed items | Vocabulary, naturalness and transliteration can differ too |
| “No accuracy cost” | Unchanged GPT-OSS English-control performance for two variants; human-agreement cost pending | English controls bypass translation and do not measure translation fidelity |
| Meta-instruction following requires a larger model | Different effects across these two judges | Model size is confounded with architecture/training/deployment |
| GPT-OSS is unbiased because it catches all wrong twins | No observed acceptance under reference-guided factual testing | A floor effect cannot establish general invariance |
| Co-movement proves language quality leaks into correctness | Post-hoc association, compatible with shared-call halo | All criteria were scored together |
| A comment without keywords hides language bias | Automated comment counts remain unvalidated | Missing keywords do not identify the cause of a score change |
| First Hindi human validation or first four-form study | Combined design, with explicit prior work | PARIKSHA and the overlapping repository already cover parts of this space |
| Pilot is an independent dataset | Pilot logs excluded; pilot items are within the main dataset | Cached request reuse and item overlap are disclosed |
| Two answer orders are independent trials | Planned pooled E2 binomial intervals plus dependence caveat | Both orders share an item; do not silently change the registered analysis |

## Sources and novelty questions still requiring deeper checks

- Comparator full-report and judge-prompt comparison is now complete at the methods level; see `comparator_review.md`. Reproduction of its raw results remains outside this audit.
- Check whether MM-Eval's released matched-content data include Romanized Hindi (`hin_Latn`).
- Check METAL and Recon language lists in their full text before adding Hindi-specific coverage.
- Read the translated-vs-direct judging appendix of Kew, Schottmann and Sennrich, [arXiv:2312.12683](https://arxiv.org/abs/2312.12683), before asserting translate-then-judge is new.
- Check M-RewardBench translation provenance against [its original paper](https://arxiv.org/abs/2410.15522), rather than relying on a citing paper's description.
- Datta/Baitalik: publication identifier remains unverified. The earlier notes' proposed ACL SRW identifier is withheld as a citation and is not in the paper bibliography. Establish the authoritative paper and metadata before adding this comparator.
- Revisit the original notes' 2026 reasoning, calibration and translationese papers if adding those arguments. They are outside the verified draft's evidence scope.
- Recheck proceedings and recent preprints near submission. Do not turn this bounded search into a “no study exists” claim.

## Evidence and release status

Eight numerical tables in the draft now include the completed Qwen translation run. E5 statistics were regenerated from local records with no provider calls. `evidence_manifest.json` records SHA-256 hashes of numerical tables, protocol/code inputs and all raw JSONL files. The reviewed local E5 extensions are included with this report. `report/verify_snapshot.py` independently checks 28 Qwen metric rows and reproduces all 168 E5 output rows byte-for-byte. The full suite passed 115 tests with one synthetic small-sample warning; see `validation.md`. These checks do not establish security certification, human alignment or an independent reproduction of every baseline analysis.

Pending before a final paper: human E4 results, comment-coder validation, Hindi-rubric results, team review of interpretations, authors/affiliation, final figure selection, IEEE layout and final reproducibility checks.

## Follow-up after external feedback

R4, R9 and R13 now use verified proceedings status. R15 and R16 were added, and the draft now explicitly acknowledges that multilingual prompting comparisons already exist. The alternative R9 title suggested in the feedback was not supported by the retrieved proceedings page or PDF; the published title is retained. The comparator review replaces the earlier README-only scope. That bibliography revision left numerical results unchanged; the subsequent Qwen refresh below updates E5 results and source hashes.

Additional searches: exact R9 title; Hindi benchmark + BHASHA; R4 + COLM; multilingual judge prompting strategies; exact survey title. Publication records were checked on ACL Anthology and the official COLM pre-proceedings.

## Completed Qwen analysis refresh

The 1 November Qwen run is complete and included in E5 tables and paper findings. Its nine final failures are E3 missing values. Shared translations and unchanged English-only cached judgments are disclosed; no human-agreement accuracy cost is claimed. The existing two-judge scope, fixed subset, translator and statistical measures were retained. Hindi-rubric and human work remain pending.
