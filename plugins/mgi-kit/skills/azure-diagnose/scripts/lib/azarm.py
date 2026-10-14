"""Shared helpers for find.py and audit.py: tenants from `az account list`, and ARM, Resource Graph, metrics and
Log Analytics calls with a token per tenant, so a default subscription in another tenant does not matter."""

import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ARM = 'https://management.azure.com'
LOGS = 'https://api.loganalytics.io'


def die(msg, code=1):
    print(f'error: {msg}', file=sys.stderr)
    sys.exit(code)


def az_json(*args):
    r = subprocess.run(['az', *args, '-o', 'json'], capture_output=True, text=True)
    if r.returncode != 0:
        die(r.stderr.strip() or f'az {" ".join(args)} failed', 2)
    return json.loads(r.stdout)


def tenants(match=None):
    """{tenant id: {label, domain, subs}} for tenants with an enabled subscription; match is an ID or a name/domain fragment."""
    out = {}
    for s in az_json('account', 'list', '--query', '[?state==`Enabled`]'):
        t = out.setdefault(s['tenantId'], {'label': s.get('tenantDisplayName') or s.get('tenantDefaultDomain') or s['tenantId'],
                                           'domain': s.get('tenantDefaultDomain') or '', 'subs': [], 'names': {}})
        t['subs'].append(s['id'])
        t['names'][s['id']] = s.get('name') or s['id']
    if match:
        f = match.lower()
        out = {k: v for k, v in out.items() if f == k.lower() or f in v['label'].lower() or f in v['domain'].lower()}
        if not out:
            die(f'no enabled subscription in a tenant matching {match!r}')
    return out


def token(tenant, resource):
    r = subprocess.run(['az', 'account', 'get-access-token', '--tenant', tenant, '--resource', resource,
                        '--query', 'accessToken', '-o', 'tsv'], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def _send(url, tok, method='GET', body=None):
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Authorization': f'Bearer {tok}', 'Content-Type': 'application/json'})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            # Cost Management allows a few queries per minute per scope and says when to come back.
            wait = next((v for k, v in e.headers.items() if k.lower() == 'retry-after' or k.lower().endswith('retry-after')), None)
            if e.code == 429 and attempt < 3:
                time.sleep(min(int(wait) if wait and wait.isdigit() else 15, 60))
                continue
            return {'error': f'HTTP {e.code}: {e.read()[:300].decode(errors="replace")}'}
        except urllib.error.URLError as e:
            return {'error': str(e.reason)}


class Arm:
    def __init__(self, tenant):
        self.tenant = tenant
        self.token = token(tenant, f'{ARM}/')
        self._logs = None

    def call(self, method, path, body=None):
        return _send(f'{ARM}{urllib.parse.quote(path, safe="/?=&,-_.~:")}', self.token, method, body)

    def graph(self, subs, query):
        rows, skip = [], None
        while True:
            opts = {'resultFormat': 'objectArray', '$top': 1000}
            if skip:
                opts['$skipToken'] = skip
            d = self.call('POST', '/providers/Microsoft.ResourceGraph/resources?api-version=2022-10-01',
                          {'subscriptions': subs, 'query': query, 'options': opts})
            if 'error' in d:
                print(f'  resource graph: {d["error"]}', file=sys.stderr)
                return rows
            rows += d.get('data') or []
            skip = d.get('$skipToken')
            if not skip:
                return rows

    def metrics(self, rid, names, days, aggregation, interval='PT1H'):
        """{metric name: [values]} for one aggregation (Minimum, Maximum, Average, Total) over the last `days` days."""
        d = self.call('GET', f'{rid}/providers/Microsoft.Insights/metrics?api-version=2023-10-01&metricnames={",".join(names)}'
                             f'&timespan=P{days}D&interval={interval}&aggregation={aggregation}')
        out = {}
        for m in d.get('value') or []:
            vals = [p.get(aggregation.lower()) for ts in m.get('timeseries') or [] for p in ts.get('data') or []]
            out[m['name']['value']] = [v for v in vals if v is not None]
        return out

    def logs(self, workspace_id, query, days):
        """Rows as dicts from a Log Analytics workspace (its customer ID); None when the query fails."""
        if self._logs is None:
            self._logs = token(self.tenant, LOGS) or ''
        d = _send(f'{LOGS}/v1/workspaces/{workspace_id}/query', self._logs, 'POST', {'query': query, 'timespan': f'P{days}D'})
        if 'error' in d or not d.get('tables'):
            return None
        t = d['tables'][0]
        cols = [c['name'] for c in t['columns']]
        return [dict(zip(cols, r)) for r in t['rows']]


def kql(s):
    return "'" + s.replace('\\', '\\\\').replace("'", "\\'") + "'"


def last(rid):
    return (rid or '').rstrip('/').rsplit('/', 1)[-1]
