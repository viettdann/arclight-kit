#!/usr/bin/env python3
"""Tells whether the current credential authenticates to an organization; prints the identity, never the token."""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'lib'))
import ado  # noqa: E402


def main():
    p = argparse.ArgumentParser(description='Exit 0 when AZURE_DEVOPS_EXT_PAT (else az login) authenticates to ORG, 1 otherwise.')
    p.add_argument('--org', default=os.environ.get('ADO_ORG'))
    a = p.parse_args()
    code, raw = ado.Client(ado.org_url(a.org)).request('GET', f'{ado.org_url(a.org)}/_apis/connectionData')
    if code != 200:
        ado.die(f'HTTP {code}: credential rejected by {ado.org_url(a.org)}')
    user = json.loads(raw).get('authenticatedUser') or {}
    print(f"ok: {user.get('providerDisplayName') or user.get('customDisplayName') or user.get('id')}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
