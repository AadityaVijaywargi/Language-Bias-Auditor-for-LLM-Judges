"""Verify report source hashes, Qwen metrics from raw records, and deterministic E5 reproduction.

Uses only local files and temporary output directories; never calls a model or changes raw/cache data.
"""
from pathlib import Path
import collections
import csv
import hashlib
import json
import math
import statistics
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def main():
    manifest = json.loads((ROOT / 'report/evidence_manifest.json').read_text(encoding='utf-8'))
    for relative, digest in manifest['sha256'].items():
        assert hashlib.sha256((ROOT / relative).read_bytes().replace(b'\r\n', b'\n')).hexdigest() == digest, relative
    cells = {'baseline': {}, 'translate_then_judge': {}}
    final = {}
    attempts = 0
    for path in sorted((ROOT / 'results/raw').glob('*.jsonl')):
        for line in path.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r['judge'] != 'qwen2.5-7b-local' or r['run_id'].startswith('pilot-'):
                continue
            variant = r['prompt_variant']
            key = (r['experiment'], r['item_id'], tuple(r['forms']), r['order'])
            if variant in cells and r['parse_ok']:
                cells[variant][key] = r['parsed']
            if r['run_id'] == 'translate_then_judge-qwen-20261101T104744':
                final[key] = r
                attempts += not r['cache_hit']
    assert len(final) == 920 and attempts == 791
    missing = collections.Counter(k[0] for k, r in final.items() if not r['parse_ok'])
    assert dict(missing) == {'e3': 9}
    from lb.runners.e5_mitigation import subset_for
    from lb.config import experiments_config
    items = subset_for(experiments_config())

    def score(variant, item, form, criterion='content'):
        r = cells[variant].get(('e1', item, (form,), None))
        if r is None:
            return None
        return statistics.mean(r[c] for c in ('correctness', 'completeness', 'clarity')) if criterion == 'content' else r[criterion]

    def verdict(variant, exp, item, pair, order):
        r = cells[variant].get((exp, item, pair, order))
        if r is None:
            return None
        w = r['winner']
        if w == 'tie':
            return w
        return pair[0] if ((w == 'A') == (order == 'AB')) else pair[1]

    checked = 0
    for name in ['e1', 'e2', 'e3', 'e1_criteria', 'e2_ties']:
        with (ROOT / f'results/tables/main_e5_{name}.csv').open(encoding='utf-8-sig', newline='') as stream:
            rows = [r for r in csv.DictReader(stream) if r['judge'] == 'qwen2.5-7b-local' and r['variant'] == 'translate_then_judge']
        for row in rows:
            values = {'baseline': {}, 'translate_then_judge': {}}
            for variant in values:
                for q in items:
                    if name in ('e1', 'e1_criteria'):
                        criterion = row.get('criterion', 'content')
                        a, b = score(variant, q.item_id, row['form'], criterion), score(variant, q.item_id, 'en', criterion)
                        if a is not None and b is not None:
                            d = a - b
                            values[variant][q.item_id] = abs(d) if '(absolute)' in row.get('measure', '') else d
                    elif name in ('e2', 'e2_ties'):
                        pair = tuple(row['pair'].split(' vs '))
                        wins = [verdict(variant, 'e2', q.item_id, pair, o) for o in ('AB', 'BA')]
                        wins = [w for w in wins if w is not None]
                        if wins:
                            values[variant][q.item_id] = ((wins.count('tie'), len(wins)) if name == 'e2_ties'
                                                         else (wins.count('en'), sum(w != 'tie' for w in wins)))
                    elif q.wrong_usable:
                        pair = ('wrong:en', row['form'])
                        wins = [verdict(variant, 'e3', q.item_id, pair, o) for o in ('AB', 'BA')]
                        if all(w is not None for w in wins):
                            target = 'en' if row['form'] == 'en' else 'wrong:en'
                            values[variant][q.item_id] = int(all(w == target for w in wins))
            common = sorted(set(values['baseline']) & set(values['translate_then_judge']))
            assert len(common) == int(row['n']), (name, row)
            estimates = []
            for variant in values:
                v = [values[variant][i] for i in common]
                if name in ('e2', 'e2_ties'):
                    estimates.append(sum(x[0] for x in v) / sum(x[1] for x in v))
                else:
                    estimates.append(statistics.mean(v))
            for key, expected in zip(('base', 'new', 'change'), (*estimates, estimates[1] - estimates[0])):
                assert math.isclose(float(row[key]), expected, abs_tol=0.000051), (name, key, row, expected)
            checked += 1
    assert checked == 28
    from lb.mitigation import run
    with tempfile.TemporaryDirectory(prefix='qwen-e5-verify-') as directory:
        out = Path(directory)
        regenerated = run(tables_dir=out)
        for path in out.iterdir():
            assert path.read_bytes() == (ROOT / 'results/tables' / path.name).read_bytes(), path.name
    assert sum(map(len, regenerated.values())) == 168
    print(json.dumps({'source_hashes_verified': len(manifest['sha256']), 'independent_Qwen_metric_rows_checked': checked,
                      'planned_judgments': len(final), 'new_provider_attempts': attempts,
                      'final_unparsed_by_experiment': dict(missing), 'reproduced_E5_rows': 168,
                      'E5_outputs_byte_identical': True, 'new_model_calls': 0}, indent=2))


if __name__ == '__main__':
    main()
