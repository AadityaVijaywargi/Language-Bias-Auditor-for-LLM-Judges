"""Refresh report tables from generated CSVs and freeze the evidence hashes. No judge calls."""
from pathlib import Path
import csv
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'report'
USED = set()


def load(name):
    path = ROOT / 'results/tables' / (name + '.csv')
    USED.add(path)
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def number(value):
    return f'{float(value):.3f}'


def interval(row, key='rate'):
    return f"{number(row[key])} [{number(row['ci_low'])}, {number(row['ci_high'])}]"


def judge(name):
    return {'gpt-oss-120b': 'GPT-OSS', 'qwen2.5-7b-local': 'Qwen'}[name]


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |',
                      '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                     ['| ' + ' | '.join(map(str, row)) + ' |' for row in rows])


def main():
    path = REPORT / 'draft.md'
    text = path.read_text(encoding='utf-8')
    e1 = load('main_baseline_e1')
    pvalue = lambda p: '<0.001' if float(p) < .001 else number(p)
    tables = [
        table(['Judge', 'Comparison', 'n', 'Content gap [CI]', 'Holm p'],
              [[judge(r['judge']), r['comparison'], r['n'], interval(r, 'mean_d'), pvalue(r['holm_p'])]
               for r in e1 if r['measure'] == 'content'])]
    e2 = load('main_baseline_e2')
    rows = []
    for j in ['gpt-oss-120b', 'qwen2.5-7b-local']:
        for pair in ['en vs hi', 'en vs hi_rom', 'en vs hinglish']:
            g = {r['id']: r for r in e2 if r['judge'] == j and r['pair'] == pair}
            r = g['E2.1']
            rows.append([judge(j), pair, f"{r['k']}/{r['n']}", interval(r), interval(g['E2.2']), interval(g['E2.4'])])
    tables.append(table(['Judge', 'Pair', 'English wins / non-ties', 'English win-rate [CI]', 'Tie rate [CI]', 'A-slot rate [CI]'], rows))
    e3 = load('main_baseline_e3')
    tables.append(table(['Judge', 'Correct form', 'Wrong English wins both orders', 'Rate [CI]'],
                        [[judge(r['judge']), r['form'] + (' (control)' if r['control'] == 'True' else ''),
                          f"{r['k']}/{r['n']}", interval(r)] for r in e3 if r['measure'] == 'consistent wrong-English rate']))
    a = load('main_baseline_a_false_acceptance')
    tables.append(table(['Judge', 'Wrong-answer form', 'Accepted / scored', 'Acceptance rate [CI]', 'Paired vs English: Holm p'],
                        [[judge(r['judge']), r['form'], f"{r['k']}/{r['n']}", interval(r),
                          pvalue(r['holm_p']) if r['holm_p'] else '—'] for r in a]))
    e5 = load('main_e5_e1')
    tables.append(table(['Variant', 'Judge', 'Form', 'Content gap measure', 'n', 'Baseline', 'Variant', 'Change [CI]'],
                        [[r['variant'], judge(r['judge']), r['form'], 'absolute' if '(absolute)' in r['measure'] else 'signed',
                          r['n'], number(r['base']), number(r['new']), interval(r, 'change')]
                         for r in e5 if r['variant'] != 'majority_vote']))
    ties = load('main_e5_e2_ties')
    tables.append(table(['Variant', 'Judge', 'Pair', 'n items', 'Baseline tie rate', 'Variant tie rate', 'Change [CI]'],
                        [[r['variant'], judge(r['judge']), r['pair'], r['n'], number(r['base']), number(r['new']), interval(r, 'change')]
                         for r in ties if r['variant'] != 'majority_vote']))
    section = text.index('## 4. Findings')
    # Replace the six original generated tables, preserving optional Qwen detail blocks.
    old = list(re.finditer(r'^\| (?:Judge|Variant) \|[^\n]*\n(?:\|[^\n]*\n?)+', text[section:], re.M))
    original = [m for m in old if not m.group().startswith('| Pair |') and not m.group().startswith('| Correct form |')]
    assert len(original) == 6, 'Unexpected report table structure'
    for match, new in reversed(list(zip(original, tables))):
        start, end = section + match.start(), section + match.end()
        text = text[:start] + new + '\n' + text[end:]
    for key, filename, label in [('qwen_e2', 'main_e5_e2', 'Pair'), ('qwen_e3', 'main_e5_e3', 'Correct form')]:
        rows = [r for r in load(filename) if r['judge'] == 'qwen2.5-7b-local' and r['variant'] == 'translate_then_judge']
        headers = [label, 'Measure', 'n paired items', 'Baseline', 'Translation variant', 'Change [CI]']
        rows = [[r.get('pair', r.get('form')), r['measure'], r['n'], number(r['base']), number(r['new']), interval(r, 'change')] for r in rows]
        block = f'<!-- snapshot:{key} -->\n' + table(headers, rows) + f'\n<!-- /snapshot:{key} -->'
        pattern = rf'<!-- snapshot:{key} -->(?:.*?<!-- /snapshot:{key} -->)?'
        text, n = re.subn(pattern, lambda _: block, text, flags=re.S)
        assert n == 1
    path.write_text(text, encoding='utf-8')
    for name in set(re.findall(r'`(main_[\w]+)\.csv`', text)):
        load(name)
    USED.update((ROOT / rel) for rel in ['analysis/plan.md', 'data/quadruples.jsonl', 'configs/experiments.yaml',
                'configs/judges.yaml', 'data/e4/sample.csv', 'src/lb/mitigation.py', 'src/lb/e4.py', 'src/lb/stats.py',
                'src/lb/analysis.py', 'src/lb/runners/e5_mitigation.py', 'report/refresh_tables.py', 'report/verify_snapshot.py'])
    USED.update((ROOT / 'results/raw').glob('*.jsonl'))
    manifest = {'snapshot_date': '2026-11-01', 'raw_results_commit': subprocess.check_output(
                    ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                'source_state': 'Completed Qwen translation results plus the reviewed E5 analysis extensions committed with this report. Hashes identify exact inputs.',
                'excluded': 'Unrun Hindi rubric and absent human grades. No new model calls made during analysis.',
                'sha256': {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in sorted(USED)}}
    (REPORT / 'evidence_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(f'Refreshed 8 report tables and {len(USED)} source hashes.')


if __name__ == '__main__':
    main()
