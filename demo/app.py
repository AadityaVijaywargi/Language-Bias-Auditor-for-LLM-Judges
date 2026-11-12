"""Language-Bias Auditor (brief section 8). Run with `make app`.

Demo mode (the default) replays judge responses cached in results/cache and never calls a provider: pick a
dataset item whose responses are cached, or type your own answers (a cache miss is reported, never filled in).
Live mode calls the chosen judge only when its API key is in the environment; like every run, its calls are
cached in results/cache and logged to results/raw. Every number shown comes from a file under results/.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lb import prompts  # noqa: E402
from lb.analysis import underlying_winner  # noqa: E402
from lb.cache import Cache  # noqa: E402
from lb.config import RESULTS, experiments_config, judges_config  # noqa: E402
from lb.data import load_quadruples, reference_for  # noqa: E402
from lb.judge import MAX_PARSE_RETRIES, CallMeta, Judge  # noqa: E402
from lb.parse import parse_pairwise, parse_pointwise  # noqa: E402

FORMS = ["en", "hi", "hi_rom", "hinglish"]
FORM_LABELS = {"en": "English", "hi": "Hindi (Devanagari)", "hi_rom": "Romanized Hindi", "hinglish": "Hinglish"}
VARIANTS = {"baseline": "Baseline (English rubric)", "hindi_rubric": "Hindi rubric",
            "translate_then_judge": "Translate-then-judge", "bias_aware": "Bias-aware instruction"}
CSS = "textarea, table, .prose { font-family: 'Noto Sans', 'Noto Sans Devanagari', 'Nirmala UI', 'Mangal', sans-serif; }"


def load_thresholds(path: Path = RESULTS / "thresholds.json") -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def gap_warnings(gaps: dict[str, float], judge: str, thresholds: dict) -> list[str]:
    """One warning per form whose |content gap vs English| exceeds the judge's p95 threshold."""
    if not (t := thresholds.get(judge)):
        return []
    thr = t["p95_abs_content_gap"]
    return [f"⚠️ **{FORM_LABELS[f]} vs English: content-score gap {g:+.2f} exceeds the threshold of {thr:.2f} "
            f"for judge {judge}.** The answers were meant to be equivalent, so a gap this large warrants investigation for "
            f"language bias (threshold = 95th percentile of the absolute content gap over {t['n_pairs']} matched "
            f"baseline pairs, results/thresholds.json)."
            for f, g in gaps.items() if round(abs(g), 6) > round(thr, 6)]   # rounding: gaps are thirds


def consistency(form_ab: str | None, form_ba: str | None) -> str:
    if form_ab is None or form_ba is None:
        return "n/a (one order missing)"
    return f"consistent ({form_ab})" if form_ab == form_ba else "INCONSISTENT (winner changes after swap)"


def _text(t: str | None) -> str:
    if not t or not t.strip():
        raise ValueError("empty response")
    return t.strip()


class Session:
    """One audit: a judge, a prompt variant and a mode. Collects a note for every missing number."""

    def __init__(self, judge: str, variant: str, live: bool, item_id: str):
        cfg, self.exp = judges_config(), experiments_config()
        temp = self.exp.get("temperature", 0)
        self.judge = Judge(judge, cfg["judges"][judge], offline=not live, temperature=temp)
        self.translator = Judge("translator", cfg["translator"], offline=not live, temperature=temp)
        self.vp, self.variant, self.live, self.item_id = self.exp["prompt_variants"][variant], variant, live, item_id
        self.run_id, self.notes = "app-live-" + datetime.now().strftime("%Y%m%dT%H%M%S"), []

    def ask(self, judge: Judge, prompt: str, parser, what: str, forms: list[str], order: str | None = None):
        if self.live:
            meta = CallMeta(self.run_id, "app", self.variant, self.item_id, forms, order)
            try:
                out = judge.run_prompt(prompt, parser, meta)
            except Exception as e:  # provider/network error: report it, never invent a result
                self.notes.append(f"{what}: call to {judge.name} failed ({e}).")
                return None
            if out is None:
                self.notes.append(f"{what}: {judge.name} replied {MAX_PARSE_RETRIES + 1} times without valid JSON.")
            return out
        for attempt in range(MAX_PARSE_RETRIES + 1):        # same retry chain as Judge.run_prompt, cache only
            hit = judge.cache.get(judge.key(prompt, attempt))
            if hit is None:
                self.notes.append(f"{what}: no cached response for {judge.name} / {self.variant} with this exact "
                                  "text. Demo mode never calls a judge, so no number is shown.")
                return None
            try:
                return parser(hit["text"])
            except ValueError:
                continue
        self.notes.append(f"{what}: cached responses from {judge.name} could not be parsed.")
        return None

    def prepare(self, form: str, text: str) -> str | None:
        """Translate-then-judge sends English text to the judge; every other variant sends the answer as is."""
        if "translate" not in self.vp or form == "en":
            return text
        return self.ask(self.translator, prompts.render_translation(text), _text,
                        f"{FORM_LABELS[form]} translation", [form])

    def score(self, question, ref, form, text):
        prompt = prompts.render_pointwise(self.vp["pointwise"], question, text, ref, self.vp.get("suffix"))
        return self.ask(self.judge, prompt, parse_pointwise, f"{FORM_LABELS[form]} score", [form])

    def compare(self, question, ref, x, y, texts):
        out = {}
        for order, (a, b) in (("AB", (x, y)), ("BA", (y, x))):
            prompt = prompts.render_pairwise(self.vp["pairwise"], question, texts[a], texts[b], ref,
                                             self.vp.get("suffix"))
            v = self.ask(self.judge, prompt, parse_pairwise, f"{x} vs {y} ({order})", [x, y], order)
            if v is not None:
                out[order] = (v.winner, underlying_winner(v.winner, order, x, y), a, b)
        return out


def audit(mode, judge, variant, question, forms, *answers, items=None, thresholds=None):
    items = load_quadruples() if items is None else items
    thresholds = load_thresholds() if thresholds is None else thresholds
    answers = dict(zip(FORMS, answers))
    forms = [f for f in FORMS if f in (forms or [])]
    empty = [FORM_LABELS[f] for f in forms if not (answers[f] or "").strip()]
    if len(forms) < 2 or empty or not (question or "").strip():
        msg = "Enter a question and select at least two answers" + (f" (empty: {', '.join(empty)})" if empty else "")
        return msg + ".", None, None, None, ""
    live, jcfg = mode == "live", judges_config()
    need = [jcfg["judges"][judge].get("api_key_env")]
    if "translate" in experiments_config()["prompt_variants"][variant]:
        need.append(jcfg["translator"].get("api_key_env"))
    missing = [e for e in need if e and not os.environ.get(e)]
    if live and missing:
        return (f"Live mode needs {', '.join(missing)} in the environment. Set it, or switch to demo mode "
                "to replay cached results.", None, None, None, "")
    item = next((q for q in items if q.question_en == question), None)
    ref = reference_for(item, experiments_config()["reference_guided"]) if item else None
    s = Session(judge, variant, live, item.item_id if item else "custom")

    texts, scores = {}, {}
    for f in forms:
        t = s.prepare(f, answers[f])
        if t is not None:
            texts[f] = t
            sc = s.score(question, ref, f, t)
            if sc is not None:
                scores[f] = sc
    score_rows = [[FORM_LABELS[f], answers[f][:60], sc.correctness, sc.completeness, sc.clarity,
                   sc.language_quality, round(sc.content, 2), round(sc.overall, 2), sc.comment]
                  for f, sc in scores.items()]

    base = "en" if "en" in forms else forms[0]
    pair_rows = []
    for y in (f for f in forms if f != base):
        if base not in texts or y not in texts:
            continue
        res = s.compare(question, ref, base, y, texts)
        flag = consistency(res.get("AB", (None,) * 4)[1], res.get("BA", (None,) * 4)[1])
        pair_rows += [[f"{base} vs {y}", o, FORM_LABELS[a], FORM_LABELS[b], slot, won, flag]
                      for o, (slot, won, a, b) in res.items()]

    gaps, gap_rows, thr = {}, [], thresholds.get(judge)
    if "en" in scores:
        for f in (f for f in scores if f != "en"):
            gaps[f] = scores[f].content - scores["en"].content
            gap_rows.append([FORM_LABELS[f], round(gaps[f], 2), round(scores[f].overall - scores["en"].overall, 2),
                             round(thr["p95_abs_content_gap"], 2) if thr else "none"])
    elif "en" not in forms:
        s.notes.append("No English answer selected, so there is no gap vs English.")
    if gaps and not thr:
        s.notes.append(f"results/thresholds.json has no threshold for {judge}, so no bias warning can be given.")
    warns = gap_warnings(gaps, judge, thresholds)
    if gaps and thr and not warns:
        warns = [f"✅ No gap vs English exceeds the {judge} threshold of {thr['p95_abs_content_gap']:.2f}."]

    import pandas as pd
    src = ("Live calls (cached to results/cache, logged to results/raw)" if live
           else "Replayed from results/cache; no judge was called")
    notes = f"**Source:** {src}. Judge {judge}, variant {VARIANTS[variant]}" + \
        (f", item {item.item_id}." if item else ", custom input (no reference answer).")
    notes += "".join(f"\n- {n}" for n in s.notes)
    return ("\n\n".join(warns),
            pd.DataFrame(score_rows, columns=["Answer", "Text (start)", "Correctness", "Completeness", "Clarity",
                                              "Language quality", "Content", "Overall", "Judge comment"]),
            pd.DataFrame(pair_rows, columns=["Pair", "Order", "Answer A", "Answer B", "Verdict", "Winner",
                                             "Position consistency"]),
            pd.DataFrame(gap_rows, columns=["Answer", "Content gap vs English", "Overall gap vs English",
                                            "Threshold (content)"]),
            notes)


def cached_items(items, judges: list[str]) -> dict[str, list[str]]:
    """{item_id: [judges whose four baseline pointwise responses are all cached]} for the demo picker."""
    exp, cfg, out = experiments_config(), judges_config(), {}
    vp, cache = exp["prompt_variants"]["baseline"], Cache()
    jobs = {j: Judge(j, cfg["judges"][j], cache=cache, offline=True, temperature=exp.get("temperature", 0))
            for j in judges}
    for q in items:
        ref = reference_for(q, exp["reference_guided"])
        ps = [prompts.render_pointwise(vp["pointwise"], q.question_en, q.answers.get(f).text, ref) for f in FORMS]
        js = [j for j in judges if all(jobs[j].key(p) in cache for p in ps)]
        if js:
            out[q.item_id] = js
    return out


def build_ui():
    import gradio as gr
    items = load_quadruples()
    judges = [j for j, c in judges_config()["judges"].items() if c.get("enabled", True)]
    cached = cached_items(items, judges)
    by_id = {q.item_id: q for q in items}
    choices = [(f"{i} · {by_id[i].question_en.splitlines()[0][:70]} [cached: {', '.join(js)}]", i)
               for i, js in cached.items()]
    default_judge = next((js[0] for js in cached.values()), judges[0])

    def load_item(item_id):
        if not item_id: return [gr.update()] * 7  # noqa: E701
        q = by_id[item_id]
        return [q.question_en, *(q.answers.get(f).text for f in FORMS), FORMS, cached[item_id][0]]

    with gr.Blocks(title="Language-Bias Auditor") as demo:
        gr.Markdown("# Language-Bias Auditor for LLM judges\nScore the same answer in English, Hindi, Romanized "
                    "Hindi and Hinglish, compare them pairwise in both orders, and flag gaps above the judge's "
                    f"threshold. **Demo mode** replays cached results ({len(cached)} dataset items cached); "
                    "**live mode** calls the judge only when its API key is set.")
        with gr.Row():
            mode = gr.Radio(["demo", "live"], value="demo", label="Mode")
            judge = gr.Dropdown(judges, value=default_judge, label="Judge")
            variant = gr.Dropdown([(v, k) for k, v in VARIANTS.items()], value="baseline", label="Prompt variant")
        item = gr.Dropdown(choices, value=None, label="Dataset item with cached responses (fills the boxes below)")
        question = gr.Textbox(label="Question", lines=3)
        with gr.Row():
            boxes = [gr.Textbox(label=FORM_LABELS[f], lines=5) for f in FORMS]
        forms = gr.CheckboxGroup([(FORM_LABELS[f], f) for f in FORMS], value=FORMS,
                                 label="Answers to audit (at least two)")
        run = gr.Button("Audit", variant="primary")
        warning = gr.Markdown()
        scores = gr.Dataframe(label="Scores per answer (1-5; content = mean of correctness, completeness, clarity)")
        pairs = gr.Dataframe(label="Pairwise result in both orders")
        gaps = gr.Dataframe(label="Gap vs English")
        notes = gr.Markdown()
        item.change(load_item, item, [question, *boxes, forms, judge])
        run.click(lambda *a: audit(*a, items=items), [mode, judge, variant, question, forms, *boxes],
                  [warning, scores, pairs, gaps, notes])
    return demo


if __name__ == "__main__":
    build_ui().launch(css=CSS)
