#!/usr/bin/env python3
"""Why a run failed: template validation errors, failed stages/jobs/steps with their issues, and the tail of each failed step's log; read-only.
API: https://learn.microsoft.com/en-us/rest/api/azure/devops/build/timeline/get?view=azure-devops-rest-7.1"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'lib'))
import ado  # noqa: E402

USAGE = """Usage:
  run-failure.py --org ORG --project PROJECT --build ID [--lines N]
  run-failure.py --org ORG --project PROJECT (--pipeline-id ID | --pipeline NAME) [--branch REF] [--lines N]

--build takes the run ID from a URL (...results?buildId=ID). --pipeline-id or --pipeline (a name; exact match wins,
otherwise the matches are listed) picks that pipeline's latest failed or partially succeeded run, optionally on
--branch (e.g. refs/heads/main). --lines: log lines per failed step after dropping image-pull noise (default 60).
The first lines show the pipeline's last runs, so a failure already fixed by a later run is visible."""

SCOPE = 'vso.build (Build: Read)'
# Image pull progress buries the error in the tail; it never explains a failure.
NOISE = re.compile(r'^[0-9a-f]{12}: (Pull complete|Waiting|Downloading|Extracting|Verifying Checksum|Download complete|'
                   r'Already exists|Pulling fs layer)\s*$')
# Framework frames between the app's own frames; the exception line and the app frames carry the meaning.
FRAME = re.compile(r'^\s+at (System\.|Microsoft\.|Npgsql\.|Volo\.|Castle\.|Polly\.)|^\s*--- End of (inner exception )?stack trace')
STAMP = re.compile(r'^﻿?\d{4}-\d\d-\d\dT[\d:.]+Z |\x1b\[[0-9;]*m')


def usage_exit():
    print(USAGE, file=sys.stderr)
    sys.exit(2)


def main():
    if any(a in ('-h', '--help') for a in sys.argv[1:]):
        print(USAGE)
        return 0
    p = argparse.ArgumentParser(add_help=False)
    p.error = lambda _msg: usage_exit()
    p.add_argument('--org', default=os.environ.get('ADO_ORG'))
    p.add_argument('--project', default=os.environ.get('ADO_PROJECT'))
    p.add_argument('--build')
    p.add_argument('--pipeline-id')
    p.add_argument('--pipeline')
    p.add_argument('--branch')
    p.add_argument('--lines', type=int, default=60)
    a = p.parse_args()
    if not a.project or not (a.build or a.pipeline_id or a.pipeline):
        usage_exit()
    org = ado.org_url(a.org)
    base = f'{org}/{ado.uri(a.project)}/_apis/build/builds'
    client = ado.Client(org)

    if a.pipeline and not a.pipeline_id:
        defs = client.get_json(f'{org}/{ado.uri(a.project)}/_apis/build/definitions?name=*{ado.uri(a.pipeline)}*'
                               f'&api-version={ado.API_VERSION}', SCOPE)['value']
        exact = [d for d in defs if d['name'].lower() == a.pipeline.lower()]
        if not exact and len(defs) != 1:
            ado.die('no pipeline matches' if not defs else 'several pipelines match, pass --pipeline-id:\n' +
                    '\n'.join(f"  {d['id']}  {d['name']}" for d in defs))
        a.pipeline_id = str((exact or defs)[0]['id'])

    run = a.build
    if not run:
        q = (f'definitions={a.pipeline_id}&$top=1&resultFilter=failed,partiallySucceeded&queryOrder=finishTimeDescending'
             f'&api-version={ado.API_VERSION}')
        if a.branch:
            q += f'&branchName={ado.uri(a.branch)}'
        runs = client.get_json(f'{base}?{q}', SCOPE)['value']
        if not runs:
            ado.die('no failed run for this pipeline')
        run = str(runs[0]['id'])

    b = client.get_json(f'{base}/{run}?api-version={ado.API_VERSION}', SCOPE)
    recent = client.get_json(f"{base}?definitions={b['definition']['id']}&$top=4&queryOrder=queueTimeDescending"
                             f'&api-version={ado.API_VERSION}', SCOPE)['value']
    print('recent runs: ' + ', '.join(f"{x['id']} {x.get('result') or x.get('status')} ({(x.get('sourceBranch') or '').removeprefix('refs/heads/')})"
                                      for x in recent))
    print(f"run {b['id']} {b['definition']['name']} #{b.get('buildNumber')}: {b.get('status')}/{b.get('result')}")
    print(f"  branch {b.get('sourceBranch')} @ {(b.get('sourceVersion') or '')[:8]}  reason {b.get('reason')}  "
          f"by {(b.get('requestedFor') or {}).get('displayName')}  finished {b.get('finishTime')}")
    print(f"  {org}/{ado.uri(a.project)}/_build/results?buildId={b['id']}")
    for v in b.get('validationResults') or []:
        if v.get('result') in ('error', 'warning'):
            print(f"validation {v['result']}: {v.get('message')}")

    records = client.get_json(f'{base}/{run}/timeline?api-version={ado.API_VERSION}', SCOPE).get('records') or []
    by_id = {r['id']: r for r in records}

    def path(r):
        names = []
        while r:
            if r.get('type') in ('Stage', 'Job', 'Task'):
                names.append(r['name'])
            r = by_id.get(r.get('parentId'))
        return ' > '.join(reversed(names))

    failed = [r for r in records if r.get('result') in ('failed', 'canceled') or
              any(i.get('type') == 'error' for i in r.get('issues') or [])]
    # A failed job usually only repeats its failed step; keep it when no step under it explains the failure.
    has_failed_child = {r.get('parentId') for r in failed if r.get('type') == 'Task'}
    failed = [r for r in failed if r.get('type') == 'Task' or (r.get('type') == 'Job' and r['id'] not in has_failed_child)]
    if not failed and not b.get('validationResults'):
        print('no failed step in the timeline')
    shown_jobs = set()
    for r in sorted(failed, key=lambda r: (r.get('startTime') or '', r.get('order') or 0)):
        log_id = (r.get('log') or {}).get('id')
        print(f"\n{r['result'] or 'error'}: {path(r)}" + (f'  (log {log_id})' if log_id else ''))
        job = r if r.get('type') == 'Job' else by_id.get(r.get('parentId'))
        if job and job['id'] not in shown_jobs:
            shown_jobs.add(job['id'])
            steps = sorted((x for x in records if x.get('parentId') == job['id'] and x.get('type') == 'Task'), key=lambda x: x.get('order') or 0)
            print('  steps: ' + ' > '.join(f"{x['name']} [{x.get('result') or x.get('state')}]" for x in steps))
        for i in r.get('issues') or []:
            if i.get('type') in ('error', 'warning'):
                print(f"  {i['type']}: {i.get('message')}")
        if log_id and a.lines > 0:
            lines = client.get_json(f'{base}/{run}/logs/{log_id}?api-version={ado.API_VERSION}', SCOPE).get('value') or []
            kept, skipped = [], 0
            for ln in (STAMP.sub('', x) for x in lines):
                if NOISE.match(ln):
                    continue
                if FRAME.match(ln):
                    skipped += 1
                    continue
                if skipped:
                    kept.append(f'   ... {skipped} framework frame(s)')
                    skipped = 0
                kept.append(ln)
            tail = kept[-a.lines:]
            print(f'  --- last {len(tail)} of {len(lines)} log lines (image pull progress and framework frames dropped) ---')
            print('\n'.join(tail))
    return 0


if __name__ == '__main__':
    sys.exit(main())
