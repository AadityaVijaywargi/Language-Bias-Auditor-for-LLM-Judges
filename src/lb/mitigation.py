"""E5 tables per analysis/plan.md: each mitigation variant against the baseline, same subset items, same judge.

    python -m lb.mitigation                        # every variant and judge with E5 results, plus majority vote

Reads results/raw (pilot runs excluded). For each variant with records (hindi_rubric, translate_then_judge,
bias_aware) and each judge that ran it, compares against that judge's baseline on the E5 subset items:
the E1 content gap per form (signed and absolute change), the E2 English win-rate, the E3 consistent
wrong-English rate, and the E3 control accuracy (correct English preferred in both orders, the accuracy
cost). majority_vote needs no calls: the median baseline score (pointwise) and the majority slot verdict
(pairwise, ties when there is no majority) across the judges with baseline results, compared against each
of those judges. The other accuracy cost is the change in judge-human agreement per form, once
data/human_grades.csv has cells graded by two annotators (lb.e4). Also descriptive: the per-criterion gaps and
the E2 tie rate. Writes results/tables/main_e5_*.csv and main_e5.md.
"""
from __future__ import annotations

import argparse
import statistics
from collections import Counter
from pathlib import Path

from .analysis import (CRITERIA, E2_PAIRS, SEED, WRONG, e1_scores, exploratory, fmt, judges_in, load_calls,
                       pair_verdicts, write_csv)
from .config import RAW, TABLES, experiments_config
from .data import load_quadruples
from .e4 import GRADES, MEASURES, consensus, human_scores, judge_human_pairs, load_grades
from .runners.e5_mitigation import NON_EN, subset_for
from .stats import bootstrap_agreement_diff_ci, bootstrap_rate_diff_ci, paired_bootstrap_ci

MAJORITY = "majority_vote"


def e1_gaps(calls: dict, judge: str, items, form: str, measure: str = "content") -> dict:
    """{item_id: measure(form) - measure(en)}."""
    s = e1_scores(calls, judge, items)
    return {i: v[form][measure] - v["en"][measure] for i, v in s.items() if form in v and "en" in v}


def e2_counts(calls: dict, judge: str, items, x: str, y: str) -> dict:
    """{item_id: (English wins, English wins + losses)} over the orders that parsed."""
    out = {}
    for i, cell in pair_verdicts(calls, "e2", judge, items, x, y).items():
        forms = [f for _, f in cell.values()]
        out[i] = (forms.count(x), forms.count(x) + forms.count(y))
    return out


def e2_ties(calls: dict, judge: str, items, x: str, y: str) -> dict:
    """{item_id: (ties, judgments)} over the orders that parsed."""
    return {i: (sum(f == "tie" for _, f in cell.values()), len(cell))
            for i, cell in pair_verdicts(calls, "e2", judge, items, x, y).items()}


def e3_flags(calls: dict, judge: str, items, form: str) -> dict:
    """{item_id: True if the wrong English answer wins in both orders} (form = en: True if the correct
    English answer wins in both orders, the control's accuracy). Items missing an order are dropped."""
    out = {}
    for i, cell in pair_verdicts(calls, "e3", judge, items, WRONG, form).items():
        if len(cell) == 2:
            target = "en" if form == "en" else WRONG
            out[i] = all(f == target for _, f in cell.values())
    return out


def change_row(base: dict, new: dict) -> dict:
    common = sorted(set(base) & set(new))
    d = [float(new[i]) - float(base[i]) for i in common]
    mean, lo, hi = paired_bootstrap_ci(d, seed=SEED)
    return {"n": len(common), "base": sum(float(base[i]) for i in common) / len(common) if common else float("nan"),
            "new": sum(float(new[i]) for i in common) / len(common) if common else float("nan"),
            "change": mean, "ci_low": lo, "ci_high": hi, "exploratory": exploratory(len(common))}


def agreement_rows(base_calls: dict, base_judge: str, new_calls: dict, new_judge: str, items, mean: dict,
                   label: dict) -> list[dict]:
    """Judge-human agreement per form (lb.e4's measures), variant against baseline on items with both."""
    if not mean:
        return []
    bs, ns = e1_scores(base_calls, base_judge, items), e1_scores(new_calls, new_judge, items)
    rows = []
    for form in ("en", *NON_EN):
        for key, measure in MEASURES:
            b = {i: (x, y) for i, x, y in judge_human_pairs(bs, mean, items, form, key)}
            v = {i: (x, y) for i, x, y in judge_human_pairs(ns, mean, items, form, key)}
            ids = [i for i in b if i in v]
            new, base, diff, lo, hi = bootstrap_agreement_diff_ci(
                measure, [v[i][0] for i in ids], [v[i][1] for i in ids],
                [b[i][0] for i in ids], [b[i][1] for i in ids], seed=SEED)
            rows.append({**label, "form": form, "score": key, "measure": measure, "n": len(ids), "base": base,
                         "new": new, "change": diff, "ci_low": lo, "ci_high": hi,
                         "exploratory": exploratory(len(ids))})
    return rows


def compare(base_calls: dict, base_judge: str, new_calls: dict, new_judge: str, items, twins, label: dict,
            mean: dict | None = None) -> dict:
    e1, e2, e3, criteria, ties = [], [], [], [], []
    for form in NON_EN:
        b, v = e1_gaps(base_calls, base_judge, items, form), e1_gaps(new_calls, new_judge, items, form)
        e1.append({**label, "form": form, "measure": "content gap vs en (signed)", **change_row(b, v)})
        e1.append({**label, "form": form, "measure": "content gap vs en (absolute)",
                   **change_row({i: abs(x) for i, x in b.items()}, {i: abs(x) for i, x in v.items()})})
        for c in CRITERIA:
            criteria.append({**label, "form": form, "criterion": c,
                             **change_row(e1_gaps(base_calls, base_judge, items, form, c),
                                          e1_gaps(new_calls, new_judge, items, form, c))})
    for x, y in E2_PAIRS:
        b, v = e2_counts(base_calls, base_judge, items, x, y), e2_counts(new_calls, new_judge, items, x, y)
        common = sorted(set(b) & set(v))
        rb, rv, diff, lo, hi = bootstrap_rate_diff_ci([b[i] for i in common], [v[i] for i in common], seed=SEED)
        e2.append({**label, "pair": f"{x} vs {y}", "measure": "English win-rate", "n": len(common), "base": rb,
                   "new": rv, "change": diff, "ci_low": lo, "ci_high": hi, "exploratory": exploratory(len(common))})
        b, v = e2_ties(base_calls, base_judge, items, x, y), e2_ties(new_calls, new_judge, items, x, y)
        common = sorted(set(b) & set(v))
        rb, rv, diff, lo, hi = bootstrap_rate_diff_ci([b[i] for i in common], [v[i] for i in common], seed=SEED)
        ties.append({**label, "pair": f"{x} vs {y}", "n": len(common), "base": rb, "new": rv, "change": diff,
                     "ci_low": lo, "ci_high": hi, "exploratory": exploratory(len(common))})
    for form in (*NON_EN, "en"):
        b, v = e3_flags(base_calls, base_judge, twins, form), e3_flags(new_calls, new_judge, twins, form)
        measure = "control accuracy (correct en preferred)" if form == "en" else "consistent wrong-English rate"
        e3.append({**label, "form": form, "measure": measure, **change_row(b, v)})
    return {"e1": e1, "e2": e2, "e3": e3, "e1_criteria": criteria, "e2_ties": ties,
            "accuracy": agreement_rows(base_calls, base_judge, new_calls, new_judge, items, mean or {}, label)}


def majority_calls(calls: dict, judges: list[str], items, twins) -> dict:
    """Baseline records combined across judges as one judge, MAJORITY: median of each criterion (E1) and
    the majority slot verdict (E2, E3; tie when no verdict has more than half). Only keys every judge has."""
    out = {}
    for q in items:
        for form in ("en", *NON_EN):
            got = [calls.get(("e1", j, q.item_id, (form,), None)) for j in judges]
            if all(got):
                out[("e1", MAJORITY, q.item_id, (form,), None)] = {
                    c: statistics.median(float(p[c]) for p in got) for c in CRITERIA}
    pairwise = [("e2", items, x, y) for x, y in E2_PAIRS] + [("e3", twins, WRONG, f) for f in (*NON_EN, "en")]
    for exp, its, x, y in pairwise:
        for q in its:
            for order in ("AB", "BA"):
                got = [calls.get((exp, j, q.item_id, (x, y), order)) for j in judges]
                if all(got):
                    top, n = Counter(p["winner"] for p in got).most_common(1)[0]
                    out[(exp, MAJORITY, q.item_id, (x, y), order)] = {"winner": top if n * 2 > len(got) else "tie"}
    return out


def analyse(judges: list[str] | None = None, raw_dir: Path = RAW, grades_path: Path = GRADES) -> dict:
    cfg = experiments_config()
    items = subset_for(cfg)
    twins = [q for q in items if q.wrong_usable]
    base = load_calls("baseline", None, raw_dir)
    mean = consensus(human_scores(load_grades(grades_path)))
    tables = {"e1": [], "e2": [], "e3": [], "e1_criteria": [], "e2_ties": [], "accuracy": []}
    for variant in cfg["experiments"]["e5"]["variants"]:
        calls = load_calls(variant, judges, raw_dir)
        ran = [j for j in judges_in({k: v for k, v in calls.items() if k[0] in ("e1", "e2", "e3")})]
        for j in ran:
            out = compare(base, j, calls, j, items, twins, {"variant": variant, "judge": j, "vs_baseline_of": j},
                          mean)
            for k in tables:
                tables[k] += out[k]
    panel = [j for j in judges_in({k: v for k, v in base.items() if k[0] == "e1"}) if not judges or j in judges]
    if len(panel) >= 2:
        maj = majority_calls(base, panel, items, twins)
        for j in panel:
            out = compare(base, j, maj, MAJORITY, items, twins,
                          {"variant": MAJORITY, "judge": "+".join(panel), "vs_baseline_of": j}, mean)
            for k in tables:
                tables[k] += out[k]
    return tables


def ci(r: dict) -> str:
    return f"{fmt(r['change'])} [{fmt(r['ci_low'])}, {fmt(r['ci_high'])}]"


def flag(r: dict) -> str:
    return " (exploratory)" if r.get("exploratory") else ""


def render_markdown(tables: dict) -> str:
    L = ["# E5: mitigations vs baseline (same subset items, same judge)", "",
         "Generated by `python -m lb.mitigation` from results/raw (pilot runs excluded), per analysis/plan.md E5. "
         "Change = variant minus baseline, paired by item, with a bootstrap 95% CI (10,000 resamples, seed "
         "20261023). majority_vote combines the baseline judges listed in the Judge column and is compared with "
         "each one's own baseline.", "",
         "## E1: content gap vs English", "",
         "A smaller absolute gap means the variant narrowed the language gap.", "",
         "| Variant | Judge | vs baseline of | Form | Measure | n | baseline | variant | change [95% CI] |",
         "|---|---|---|---|---|---|---|---|---|"]
    L += [f"| {r['variant']} | {r['judge']} | {r['vs_baseline_of']} | {r['form']} | {r['measure']} | {r['n']}{flag(r)} | "
          f"{fmt(r['base'])} | {fmt(r['new'])} | {ci(r)} |" for r in tables["e1"]]
    L += ["", "## E2: English win-rate (non-tie judgments, both orders)", "",
          "| Variant | Judge | vs baseline of | Pair | n items | baseline | variant | change [95% CI] |",
          "|---|---|---|---|---|---|---|---|"]
    L += [f"| {r['variant']} | {r['judge']} | {r['vs_baseline_of']} | {r['pair']} | {r['n']}{flag(r)} | {fmt(r['base'])} | "
          f"{fmt(r['new'])} | {ci(r)} |" for r in tables["e2"]]
    L += ["", "## E3: wrong English vs correct answer, and the control", "",
          "Consistent wrong-English rate = the wrong English answer wins in both orders (lower is better). Control "
          "accuracy = the correct English answer beats the wrong one in both orders (a drop is an accuracy cost).", "",
          "| Variant | Judge | vs baseline of | Correct form | Measure | n | baseline | variant | change [95% CI] |",
          "|---|---|---|---|---|---|---|---|---|"]
    L += [f"| {r['variant']} | {r['judge']} | {r['vs_baseline_of']} | {r['form']} | {r['measure']} | {r['n']}{flag(r)} | "
          f"{fmt(r['base'])} | {fmt(r['new'])} | {ci(r)} |" for r in tables["e3"]]
    L += ["", "## Accuracy cost: judge-human agreement (E4)", ""]
    if tables["accuracy"]:
        L += ["Agreement with the mean human grade (lb.e4): Spearman on content, quadratic-weighted kappa per "
              "criterion. Change = variant minus baseline on the same items, paired bootstrap. A drop is an accuracy "
              "cost.", "", "| Variant | Judge | vs baseline of | Form | Score | Measure | n | baseline | variant | "
              "change [95% CI] |", "|---|---|---|---|---|---|---|---|---|---|"]
        L += [f"| {r['variant']} | {r['judge']} | {r['vs_baseline_of']} | {r['form']} | {r['score']} | {r['measure']} | "
              f"{r['n']}{flag(r)} | {fmt(r['base'])} | {fmt(r['new'])} | {ci(r)} |" for r in tables["accuracy"]]
    else:
        L += ["Waits for human grades: no cell of data/human_grades.csv has two annotators yet."]
    L += ["", "## Per-criterion gap vs English (descriptive)", "",
          "| Variant | Judge | vs baseline of | Form | Criterion | n | baseline | variant | change [95% CI] |",
          "|---|---|---|---|---|---|---|---|---|"]
    L += [f"| {r['variant']} | {r['judge']} | {r['vs_baseline_of']} | {r['form']} | {r['criterion']} | {r['n']}{flag(r)} | "
          f"{fmt(r['base'])} | {fmt(r['new'])} | {ci(r)} |" for r in tables["e1_criteria"]]
    L += ["", "## E2 tie rate (descriptive, post hoc)", "",
          "| Variant | Judge | vs baseline of | Pair | n items | baseline | variant | change [95% CI] |",
          "|---|---|---|---|---|---|---|---|"]
    L += [f"| {r['variant']} | {r['judge']} | {r['vs_baseline_of']} | {r['pair']} | {r['n']}{flag(r)} | {fmt(r['base'])} | "
          f"{fmt(r['new'])} | {ci(r)} |" for r in tables["e2_ties"]]
    return "\n".join(L) + "\n"


def run(judges: list[str] | None = None, raw_dir: Path = RAW, tables_dir: Path = TABLES,
        grades_path: Path = GRADES) -> dict:
    tables = analyse(judges, raw_dir, grades_path)
    if not any(tables.values()):
        raise SystemExit(f"no E5 variant results and fewer than 2 baseline judges in {raw_dir}")
    for name, rows in tables.items():
        write_csv(tables_dir / f"main_e5_{name}.csv", rows)
    (tables_dir / "main_e5.md").write_text(render_markdown(tables), encoding="utf-8")
    return tables


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--judges", default=None, help="comma-separated; default: every judge with results")
    args = p.parse_args()
    out = run(args.judges.split(",") if args.judges else None)
    print(f"wrote results/tables/main_e5_*.csv and main_e5.md ({sum(len(v) for v in out.values())} rows)")


if __name__ == "__main__":
    main()
