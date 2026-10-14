#!/usr/bin/env python3
"""Job and step durations of recent runs from the build timeline API, to back an optimization with numbers; read-only.
API: https://learn.microsoft.com/en-us/rest/api/azure/devops/build/timeline/get?view=azure-devops-rest-7.1"""

import argparse
import json
import math
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'lib'))
import ado  # noqa: E402

USAGE = """Usage:
  step-durations.py --org ORG --project PROJECT --pipeline-id ID [--top N] [--branch REF] [--reason R] [--raw|--json]
  step-durations.py --org ORG --project PROJECT --builds ID,ID,... [--raw|--json]

Default output: one row per job/step with n, min, median, max seconds over the selected completed runs, slowest median first.
  --top N        Last N completed runs (default 10).
  --branch REF   Only runs of this branch, e.g. refs/heads/main.
  --reason R     Only runs with this reason: individualCI, batchedCI, pullRequest, schedule, manual, resourceTrigger.
  --builds IDS   Exactly these runs, for comparing a before and an after set.
  --raw          JSON lines {run, job, step, result, secs, log} instead of the summary.
  --json         The summary as a JSON array.
Skipped steps and steps without both timestamps are left out of the summary."""

SCOPE = 'vso.build (Build: Read)'


def usage_exit():
    print(USAGE, file=sys.stderr)
    sys.exit(2)


def ts(s):
    m = re.fullmatch(r'([^.Z]+)(\.[0-9]+)?Z', s)
    if not m:
        return None
    base = datetime.strptime(m.group(1), '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc).timestamp()
    return base + float(m.group(2) or 0)


def secs(rec):
    if not (rec.get('startTime') and rec.get('finishTime')):
        return None
    a, b = ts(rec['startTime']), ts(rec['finishTime'])
    if a is None or b is None:
        return None
    v = math.floor((b - a) * 10 + 0.5) / 10
    return int(v) if v == int(v) else v


def num(x):
    return str(int(x)) if x == int(x) else repr(x)


def main():
    if any(a in ('-h', '--help') for a in sys.argv[1:]):
        print(USAGE)
        return 0
    p = argparse.ArgumentParser(add_help=False)
    p.error = lambda _msg: usage_exit()
    p.add_argument('--org', default=os.environ.get('ADO_ORG'))
    p.add_argument('--project', default=os.environ.get('ADO_PROJECT'))
    p.add_argument('--pipeline-id')
    p.add_argument('--top', type=int, default=10)
    p.add_argument('--branch')
    p.add_argument('--reason')
    p.add_argument('--builds')
    p.add_argument('--raw', action='store_true')
    p.add_argument('--json', action='store_true')
    a = p.parse_args()
    if not a.project or not (a.pipeline_id or a.builds):
        usage_exit()
    base = f'{ado.org_url(a.org)}/{ado.uri(a.project)}/_apis/build/builds'
    client = ado.Client(ado.org_url(a.org))

    if a.builds:
        ids = [i for i in a.builds.split(',') if i]
    else:
        q = f'definitions={a.pipeline_id}&$top={a.top}&statusFilter=completed&queryOrder=finishTimeDescending&api-version={ado.API_VERSION}'
        if a.branch:
            q += f'&branchName={ado.uri(a.branch)}'
        if a.reason:
            q += f'&reasonFilter={a.reason}'
        ids = [str(b['id']) for b in client.get_json(f'{base}?{q}', SCOPE)['value']]
    if not ids:
        ado.die('no completed runs match')

    rows = []
    for run in ids:
        records = client.get_json(f'{base}/{run}/timeline?api-version={ado.API_VERSION}', SCOPE).get('records') or []
        names = {r['id']: r['name'] for r in records}
        for r in records:
            if r.get('type') not in ('Job', 'Task'):
                continue
            job = r['type'] == 'Job'
            # Checkout names embed the ref, e.g. "Checkout repo@refs/pull/12/merge to s"; folding them keeps one row across PR runs.
            rows.append({'run': int(run), 'job': r['name'] if job else names.get(r.get('parentId')),
                         'step': '(job total)' if job else re.sub(r'@.* to .*$', '', r['name'], count=1),
                         'result': r.get('result'), 'secs': secs(r), 'log': (r.get('log') or {}).get('id')})

    if a.raw:
        for row in rows:
            print(json.dumps(row, ensure_ascii=False, separators=(',', ':')))
        return 0

    groups = {}
    for row in rows:
        if row['secs'] is not None and row['result'] != 'skipped':
            groups.setdefault((row['job'] or '', row['step']), []).append(row['secs'])
    summary = []
    for (job, step), s in sorted(groups.items()):
        s.sort()
        summary.append({'job': job, 'step': step, 'n': len(s), 'min': s[0], 'median': s[len(s) // 2], 'max': s[-1]})
    summary.sort(key=lambda r: -r['median'])

    print(f"runs: {' '.join(ids)} ", file=sys.stderr)
    if a.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    table = [['job', 'step', 'n', 'min', 'median', 'max']]
    table += [[r['job'], r['step'], str(r['n']), num(r['min']), num(r['median']), num(r['max'])] for r in summary]
    widths = [max(len(row[i]) for row in table) for i in range(6)]
    for row in table:
        print('  '.join(c.ljust(w) for c, w in zip(row, widths)).rstrip())
    return 0


if __name__ == '__main__':
    sys.exit(main())
