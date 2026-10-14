"""Shared Azure DevOps REST helpers for preview.py, step-durations.py and task-versions.py."""

import base64
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

# Entra resource ID of Azure DevOps: https://learn.microsoft.com/en-us/azure/devops/cli/entra-tokens?view=azure-devops
ADO_RESOURCE_ID = '499b84ac-1321-427f-aa17-267ca6975798'
API_VERSION = '7.1'

SETUP_HELP = """No Azure DevOps credential found. Use one of:
  export AZURE_DEVOPS_EXT_PAT=<PAT>        # scope: Build (Read) for preview, Agent Pools (Read) for task-versions org
  az login                                  # a bearer token for resource 499b84ac-1321-427f-aa17-267ca6975798 is fetched automatically"""


def die(msg, code=1):
    print(f'error: {msg}', file=sys.stderr)
    sys.exit(code)


def uri(s):
    return urllib.parse.quote(s, safe='-_.~')


def org_url(org):
    """Accepts `myorg`, `https://dev.azure.com/myorg` or `https://myorg.visualstudio.com`; any other host would receive the credential."""
    org = (org or '').rstrip('/')
    if not org:
        die('--org is required (or set ADO_ORG)')
    if '://' not in org:
        return f'https://dev.azure.com/{uri(org)}'
    u = urllib.parse.urlsplit(org)
    host = (u.hostname or '').lower()
    if u.scheme != 'https' or not (host == 'dev.azure.com' or host.endswith('.visualstudio.com')):
        die(f'refusing to send the credential to {org}: only https://dev.azure.com/... or https://*.visualstudio.com')
    return org


def auth_header():
    """PAT wins over az so a CI job with both behaves predictably."""
    pat = os.environ.get('AZURE_DEVOPS_EXT_PAT')
    if pat:
        return 'Basic ' + base64.b64encode(f':{pat}'.encode()).decode()
    if shutil.which('az'):
        r = subprocess.run(['az', 'account', 'get-access-token', '--resource', ADO_RESOURCE_ID, '--query', 'accessToken', '-o', 'tsv'],
                           capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return 'Bearer ' + r.stdout.strip()
    print(SETUP_HELP, file=sys.stderr)
    sys.exit(2)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


class Client:
    def __init__(self):
        self.header = auth_header()

    def request(self, method, url, body=None):
        """Returns (status, raw body). X-TFS-FedAuthRedirect: Suppress turns a rejected credential into a 401 instead of a sign-in redirect."""
        headers = {'Authorization': self.header, 'X-TFS-FedAuthRedirect': 'Suppress', 'Accept': 'application/json'}
        data = None
        if body is not None:
            headers['Content-Type'] = 'application/json'
            data = json.dumps(body).encode()
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with _opener.open(req) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()
        except urllib.error.URLError as e:
            die(f'{url}: {e.reason}')

    def get_json(self, url, scope_hint):
        code, raw = self.request('GET', url)
        if code != 200:
            fail_http(code, raw, scope_hint)
        return json.loads(raw)


def error_message(raw):
    try:
        return json.loads(raw).get('message') or ''
    except (ValueError, AttributeError):
        return raw[:500].decode(errors='replace')


def fail_http(code, raw, scope_hint):
    msg = error_message(raw)
    if code in (401, 403):
        die(f"HTTP {code}: {msg.rstrip('.')}. The token needs scope {scope_hint} on this organization/project.")
    if code in (302, 203):
        die(f'HTTP {code}: redirected to sign-in, the credential was rejected. The token needs scope {scope_hint}.')
    die(f"HTTP {code}: {msg or 'no message'}")
