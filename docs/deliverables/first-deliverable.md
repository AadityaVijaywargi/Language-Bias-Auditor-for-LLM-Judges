# Language Bias Auditor for LLM Judges

First deliverable | Why and what of the solution

## Why this solution is needed

AI models increasingly evaluate answers, compare systems and provide feedback. A judge should reward answer quality without unfairly favouring a language or script. For users who write in Hindi, Romanized Hindi or Hinglish, a preference for English could distort scores even when the intended meaning is equivalent. Our project makes these differences measurable so researchers and developers can examine an AI judge before relying on its evaluations.

## What we built

We built a reproducible auditing pipeline and an interactive demo that compare equivalent answers in English, Hindi in Devanagari, Romanized Hindi and Hinglish. The dataset contains 150 questions with four answer forms each, plus 60 deliberately incorrect answer sets. The main experiments evaluate Qwen2.5 7B and GPT OSS 120B as judges.

## How the solution works

The auditor scores answers for correctness, completeness, clarity and language quality, then measures content score gaps relative to English. It compares answer pairs in both presentation orders to check whether preferences change when positions are swapped. It also tests whether a judge prefers an incorrect English answer over a correct answer in another language. Bias aware instructions and translation into English before judging are evaluated as possible mitigations; their effectiveness is measured rather than assumed.

## What the user receives

The demo displays four answer versions, criterion scores, English relative gaps, pairwise winners and source notes. It replays real cached model responses without API keys, while optional live mode uses a configured model service. Saved prompts, raw responses, analysis code and generated tables allow the study to be inspected and reproduced.

## Scope and expected value

The solution helps identify language related evaluation differences and compare possible fixes. An individual score gap is a signal to investigate, not proof of bias or a universal fairness verdict. Human validation remains incomplete: no two rater consensus is available, and bulk assigned ratings are explicitly labelled. The Hindi rubric experiment and comment label validation are deferred. The current contribution is an inspectable audit of the tested models, dataset and prompts.
