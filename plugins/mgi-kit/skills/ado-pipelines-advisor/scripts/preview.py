#!/usr/bin/env python3
"""Expands a pipeline server-side with the Runs Preview API and prints finalYaml; nothing is queued.
API: https://learn.microsoft.com/en-us/rest/api/azure/devops/pipelines/preview/preview?view=azure-devops-rest-7.1"""

import argparse
import json
import os
import posixpath
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'lib'))
import ado  # noqa: E402

USAGE = """Usage:
  preview.py --org ORG --project PROJECT --pipeline-id ID [options]
  preview.py --org ORG --project PROJECT --list [--repo NAME]

Options:
  --yaml FILE         Replace the pipeline's root YAML with FILE (- for stdin). Templates still come from the repo at --ref.
  --param KEY=VALUE   Runtime parameter, repeatable. object/stringList values are YAML or JSON text, e.g. envs='["dev","prod"]'.
  --ref BRANCH        Branch, tag or full ref of the self repository (default: the pipeline's default branch).
  --var KEY=VALUE     Pipeline variable that is settable at queue time, repeatable.
  --skip-stage NAME   Stage to skip, repeatable.
  --list              List pipelines with their repository and YAML path, to pick a host for --yaml.
  --repo NAME         With --list, only pipelines whose repository is NAME.

Environment: ADO_ORG, ADO_PROJECT as defaults; AZURE_DEVOPS_EXT_PAT, else `az login`.
Exit codes: 0 finalYaml printed, 1 API or expansion error (message on stderr), 2 missing credential or bad usage."""


def usage_exit():
    print(USAGE, file=sys.stderr)
    sys.exit(2)


def kv(pairs):
    out = {}
    for p in pairs:
        if '=' not in p:
            ado.die(f"expected KEY=VALUE, got '{p}'")
        k, v = p.split('=', 1)
        out[k] = v
    return out


def main():
    if any(a in ('-h', '--help') for a in sys.argv[1:]):
        print(USAGE)
        return 0
    p = argparse.ArgumentParser(add_help=False)
    p.error = lambda _msg: usage_exit()
    p.add_argument('--org', default=os.environ.get('ADO_ORG'))
    p.add_argument('--project', default=os.environ.get('ADO_PROJECT'))
    p.add_argument('--pipeline-id')
    p.add_argument('--yaml')
    p.add_argument('--param', action='append', default=[])
    p.add_argument('--var', action='append', default=[])
    p.add_argument('--ref', default='')
    p.add_argument('--skip-stage', action='append', default=[])
    p.add_argument('--list', action='store_true')
    p.add_argument('--repo', default='')
    a = p.parse_args()
    if not a.project:
        usage_exit()
    base = f'{ado.org_url(a.org)}/{ado.uri(a.project)}'
    client = ado.Client(ado.org_url(a.org))

    if a.list:
        defs = client.get_json(f'{base}/_apis/build/definitions?includeAllProperties=true&api-version={ado.API_VERSION}', 'vso.build (Build: Read)')
        rows = [d for d in defs['value'] if d.get('process', {}).get('type') == 2 and (not a.repo or d['repository']['name'] == a.repo)]
        for d in sorted(rows, key=lambda d: d['id']):
            print(f"{d['id']}\t{d['name']}\t{d['repository']['name']}\t{d['process']['yamlFilename'].lstrip('/')}")
        return 0

    if not a.pipeline_id:
        usage_exit()
    # templateParameters is a string map: a JSON array or object there is ignored or rejected, so every value is sent as text.
    # previewRun must stay true: without it the same endpoint queues a real run.
    body = {'previewRun': True}
    if a.param:
        body['templateParameters'] = kv(a.param)
    if a.var:
        body['variables'] = {k: {'value': v} for k, v in kv(a.var).items()}
    if a.skip_stage:
        body['stagesToSkip'] = a.skip_stage
    ref = a.ref if not a.ref or a.ref.startswith('refs/') else f'refs/heads/{a.ref}'
    if ref:
        body['resources'] = {'repositories': {'self': {'refName': ref}}}

    if a.yaml:
        if a.yaml == '-':
            body['yamlOverride'] = sys.stdin.read()
        else:
            path = Path(a.yaml)
            if not path.is_file():
                ado.die(f'YAML file not found: {a.yaml}')
            body['yamlOverride'] = path.read_text()
        code, raw = client.request('GET', f'{base}/_apis/pipelines/{a.pipeline_id}?api-version={ado.API_VERSION}')
        if code == 200:
            host = (json.loads(raw).get('configuration') or {}).get('path', '').lstrip('/')
            # The override is parsed as if it lived at the host's path, so a relative template path resolves from that folder.
            if host:
                print(f'note: override evaluated as /{host}; relative template paths resolve from /{posixpath.dirname(host)}/, '
                      'a leading / resolves from the repo root', file=sys.stderr)

    code, raw = client.request('POST', f'{base}/_apis/pipelines/{a.pipeline_id}/preview?api-version={ado.API_VERSION}', body)
    if code == 200:
        print(json.loads(raw)['finalYaml'])
        return 0
    if code == 400:
        ado.die(f'expansion failed: {ado.error_message(raw)}')
    ado.fail_http(code, raw, 'vso.build (Build: Read)')


if __name__ == '__main__':
    sys.exit(main())
