import json
from collections import Counter

import pytest

from lb import mitigation
from lb.config import experiments_config
from lb.data import load_quadruples
from lb.runners import e5_mitigation as e5
from lb.runners.common import answer_text, plan_pointwise
from lb.stats import bootstrap_rate_diff_ci

JUDGE = "judge-x"


def subset():
    return e5.subset_for(experiments_config())


def test_subset_is_stratified_seeded_and_uses_wrong_twins():
    items = load_quadruples()
    s = subset()
    assert len(s) == 60 and s == e5.subset_for(experiments_config())            # same items every time
    types = Counter(q.type for q in s)
    assert types == {"factual": 40, "open_ended": 20}                           # 100 / 50 of 150, in proportion
    assert all(q.wrong_usable for q in s if q.type == "factual")
    assert len({q.subject for q in s}) >= 20                                    # spread across subjects
    assert [q.item_id for q in s] == [q.item_id for q in items if q in s]       # data order
    parts = [e5.subset_for(experiments_config(), shard=f"{k}/4") for k in range(1, 5)]
    assert sorted(q.item_id for p in parts for q in p) == sorted(q.item_id for q in s)   # shards split the subset


@pytest.mark.parametrize("variant", ["bias_aware", "hindi_rubric"])
def test_plan_reruns_e1_to_e3_with_the_control(variant):
    cfg, s = experiments_config(), subset()
    specs = e5.plan(s, [JUDGE], cfg, variant)
    counts = Counter(sp.experiment for sp in specs)
    assert counts == {"e1": 60 * 4, "e2": 60 * 3 * 2, "e3": 40 * 4 * 2}
    assert {sp.variant for sp in specs} == {variant}
    assert ("wrong:en", "en") in {sp.forms for sp in specs if sp.experiment == "e3"}
    if variant == "bias_aware":
        assert all("must not\naffect" in sp.prompt or "must not affect" in sp.prompt for sp in specs)


def test_unknown_variant_and_untranslated_translate_are_refused():
    cfg, s = experiments_config(), subset()
    with pytest.raises(SystemExit):
        e5.plan(s, [JUDGE], cfg, "majority_vote")
    with pytest.raises(NotImplementedError):
        plan_pointwise("e1", s, [JUDGE], e5.TRANSLATE_VARIANT, cfg)


def test_translate_then_judge_uses_translations_and_keeps_english():
    cfg, s = experiments_config(), subset()
    tspecs = e5.plan_translations(s, "translator-x")
    assert len(tspecs) == 180 and {sp.kind for sp in tspecs} == {"text"}
    assert answer_text(s[0], "hinglish") in tspecs[2].prompt
    calls = {(e5.TRANSLATE, "translator-x", sp.item_id, sp.forms, None): {"text": f"EN {sp.item_id} {sp.forms[0]}"}
             for sp in tspecs}
    text_of = e5.translated_text_of(e5.translations(calls, "translator-x"))
    specs = e5.plan(s, [JUDGE], cfg, e5.TRANSLATE_VARIANT, text_of)
    q = s[0]
    hi_prompt = next(sp.prompt for sp in specs if sp.item_id == q.item_id and sp.forms == ("hi",))
    en_prompt = next(sp.prompt for sp in specs if sp.item_id == q.item_id and sp.forms == ("en",))
    assert f"EN {q.item_id} hi" in hi_prompt and answer_text(q, "hi") not in hi_prompt
    assert answer_text(q, "en") in en_prompt
    with pytest.raises(SystemExit, match="translation step"):
        e5.translated_text_of({})(q, "hi")


def test_missing_translations_counts_only_this_parts_items():
    cfg = experiments_config()
    part1, part2 = e5.subset_for(cfg, shard="1/4"), e5.subset_for(cfg, shard="2/4")
    texts = {(q.item_id, f): "EN" for q in part2 for f in e5.NON_EN}   # another part is fully translated
    assert len(e5.missing_translations(part1, texts)) == len(part1) * 3
    assert e5.missing_translations(part2, texts) == []


def test_rate_diff_bootstrap():
    base, new = [(1, 2)] * 10, [(2, 2)] * 10
    rb, rv, diff, lo, hi = bootstrap_rate_diff_ci(base, new)
    assert (rb, rv, diff, lo, hi) == (0.5, 1.0, 0.5, 0.5, 0.5)


def rec(variant, experiment, judge, item_id, forms, order=None, **parsed):
    return {"run_id": f"{variant}-x", "experiment": experiment, "judge": judge, "prompt_variant": variant,
            "item_id": item_id, "forms": list(forms), "order": order, "parse_ok": True, "parsed": parsed}


def e1(variant, judge, q, form, score):
    return rec(variant, "e1", judge, q.item_id, (form,), correctness=score, completeness=score, clarity=score,
               language_quality=5)


def test_variant_change_and_majority_vote(tmp_path):
    s = subset()
    twins = [q for q in s if q.wrong_usable]
    recs = []
    for judge, base_hinglish in (("j1", 4), ("j2", 3)):
        for q in s:
            recs += [e1("baseline", judge, q, f, 5) for f in ("en", "hi", "hi_rom")]
            recs.append(e1("baseline", judge, q, "hinglish", base_hinglish))
            for order in ("AB", "BA"):             # English always wins at baseline (slot depends on order)
                recs.append(rec("baseline", "e2", judge, q.item_id, ("en", "hinglish"), order,
                                winner="A" if order == "AB" else "B"))
        for q in twins:
            for order in ("AB", "BA"):             # control: correct en beats wrong en
                recs.append(rec("baseline", "e3", judge, q.item_id, ("wrong:en", "en"), order,
                                winner="B" if order == "AB" else "A"))
    for q in s:                                    # bias_aware for j1 closes the hinglish gap; E2 turns to ties
        recs += [e1("bias_aware", "j1", q, f, 5) for f in ("en", "hi", "hi_rom", "hinglish")]
        recs += [rec("bias_aware", "e2", "j1", q.item_id, ("en", "hinglish"), o, winner="tie") for o in ("AB", "BA")]
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "x.jsonl").write_text("".join(json.dumps(r) + "\n" for r in recs), encoding="utf-8")
    out = mitigation.run(raw_dir=raw, tables_dir=tmp_path / "tables")

    signed = next(r for r in out["e1"] if r["variant"] == "bias_aware" and r["form"] == "hinglish"
                  and r["measure"].endswith("(signed)"))
    assert signed["n"] == 60 and signed["base"] == -1 and signed["new"] == 0 and signed["change"] == 1
    e2 = next(r for r in out["e2"] if r["variant"] == "bias_aware" and r["pair"] == "en vs hinglish")
    assert e2["base"] == 1 and e2["n"] == 60 and e2["new"] != e2["new"]          # all ties: no non-tie judgments

    maj = [r for r in out["e1"] if r["variant"] == mitigation.MAJORITY and r["form"] == "hinglish"
           and r["measure"].endswith("(signed)")]
    assert {r["vs_baseline_of"] for r in maj} == {"j1", "j2"}
    assert all(r["new"] == pytest.approx(-1.5) for r in maj)                     # median of -1 and -2 (two judges)
    control = [r for r in out["e3"] if r["variant"] == mitigation.MAJORITY and r["form"] == "en"]
    assert all(r["base"] == 1 and r["new"] == 1 and r["n"] == len(twins) for r in control)
    assert (tmp_path / "tables" / "main_e5.md").exists()


def test_ties_criteria_and_human_agreement_accuracy_cost(tmp_path):
    s = subset()
    quality = {q.item_id: 2 + k % 4 for k, q in enumerate(s)}                    # 2-5, varies across items
    recs = []
    for q in s:
        q_score = quality[q.item_id]
        for f in ("en", "hi", "hi_rom", "hinglish"):
            recs.append(rec("baseline", "e1", "j1", q.item_id, (f,), correctness=q_score, completeness=q_score,
                            clarity=q_score, language_quality=5))
            reversed_hinglish = 7 - q_score if f == "hinglish" else q_score      # agreement reversed in hinglish
            recs.append(rec("bias_aware", "e1", "j1", q.item_id, (f,), correctness=reversed_hinglish,
                            completeness=reversed_hinglish, clarity=reversed_hinglish, language_quality=5))
        for order in ("AB", "BA"):
            recs.append(rec("baseline", "e2", "j1", q.item_id, ("en", "hinglish"), order,
                            winner="A" if order == "AB" else "B"))
            recs.append(rec("bias_aware", "e2", "j1", q.item_id, ("en", "hinglish"), order, winner="tie"))
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "x.jsonl").write_text("".join(json.dumps(r) + "\n" for r in recs), encoding="utf-8")
    grades = tmp_path / "grades.csv"
    lines = ["annotator_id,item_id,form,correctness,completeness,clarity,language_quality,notes"]
    lines += [f"{a},{q.item_id},{f},{quality[q.item_id]},{quality[q.item_id]},{quality[q.item_id]},5,"
              for a in ("a1", "a2") for q in s for f in ("en", "hi", "hi_rom", "hinglish")]
    grades.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out = mitigation.run(raw_dir=raw, tables_dir=tmp_path / "tables", grades_path=grades)

    tie = next(r for r in out["e2_ties"] if r["variant"] == "bias_aware" and r["pair"] == "en vs hinglish")
    assert (tie["base"], tie["new"], tie["change"]) == (0, 1, 1)
    crit = next(r for r in out["e1_criteria"] if r["variant"] == "bias_aware" and r["form"] == "hi"
                and r["criterion"] == "language_quality")
    assert crit["n"] == 60 and crit["change"] == 0
    acc = {(r["form"], r["score"]): r for r in out["accuracy"] if r["variant"] == "bias_aware"}
    assert acc[("hi", "content")]["n"] == 40  # human amendment only; model metrics still use 60
    assert acc[("hi", "content")]["change"] == pytest.approx(0)
    assert acc[("hinglish", "content")]["new"] == pytest.approx(-1)
    assert acc[("hinglish", "content")]["change"] == pytest.approx(-2)
    assert "Accuracy cost" in (tmp_path / "tables" / "main_e5.md").read_text(encoding="utf-8")


def test_no_grades_leaves_the_accuracy_table_empty(tmp_path):
    s = subset()
    recs = [rec("baseline", "e1", "j1", q.item_id, (f,), correctness=5, completeness=5, clarity=5, language_quality=5)
            for q in s for f in ("en", "hi", "hi_rom", "hinglish")]
    recs += [rec("bias_aware", "e1", "j1", r["item_id"], r["forms"], **r["parsed"]) for r in recs]
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "x.jsonl").write_text("".join(json.dumps(r) + "\n" for r in recs), encoding="utf-8")
    out = mitigation.run(raw_dir=raw, tables_dir=tmp_path / "tables", grades_path=tmp_path / "none.csv")
    assert out["accuracy"] == []
    assert "Waits for human grades" in (tmp_path / "tables" / "main_e5.md").read_text(encoding="utf-8")
