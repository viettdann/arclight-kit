#!/usr/bin/env python3
"""Find Azure resources by name across every tenant `az login` knows, and say where their logs and metrics live; read-only.
Calls ARM with a token per tenant, so a default subscription in another tenant does not matter.
APIs: https://learn.microsoft.com/en-us/rest/api/azureresourcegraph/resourcegraph/resources/resources
      https://learn.microsoft.com/en-us/rest/api/monitor/diagnostic-settings/list"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'lib'))
from azarm import Arm, die, kql, last, tenants as list_tenants  # noqa: E402

USAGE = """Usage:
  find.py NAME [--tenant TENANT] [--type TYPE] [--max N]

NAME matches resource names containing it, case-insensitive. --tenant: a tenant ID or a domain/display-name fragment
(default: every tenant with an enabled subscription). --type: a type fragment such as web/sites or flexibleservers.
For each match (up to --max, default 5): subscription, resource group, kind and runtime, plan and the apps sharing it,
the App Insights component and the workspace IDs to query, and where diagnostic settings send logs.
App setting values are read only to match the App Insights key and are never printed."""

# Resources that describe or wire up a workload rather than run it; shown only with --type.
NOISE = ('microsoft.alertsmanagement/', 'microsoft.insights/metricalerts', 'microsoft.insights/actiongroups',
         'microsoft.insights/activitylogalerts', 'microsoft.insights/scheduledqueryrules', 'microsoft.insights/workbooks',
         'microsoft.insights/datacollection', 'microsoft.web/certificates', 'microsoft.web/connections', 'microsoft.network/',
         'microsoft.compute/disks', 'microsoft.compute/virtualmachines/extensions', 'microsoft.compute/sshpublickeys',
         'microsoft.portal/', 'microsoft.containerregistry/registries/webhooks', 'microsoft.operationalinsights/querypacks')


def workspaces(arm, subs, ids):
    ids = sorted({i.lower() for i in ids if i})
    if not ids:
        return {}
    rows = arm.graph(subs, 'resources | where type =~ "microsoft.operationalinsights/workspaces" and tolower(id) in ('
                     + ','.join(kql(i) for i in ids) + ') | project id=tolower(id), name, cid=tostring(properties.customerId)')
    return {r['id']: f"{r['name']} (workspace ID {r['cid']})" for r in rows}


def diag_settings(arm, rid):
    d = arm.call('GET', f'{rid}/providers/Microsoft.Insights/diagnosticSettings?api-version=2021-05-01-preview')
    if 'error' in d:
        return None, []
    out = []
    for s in d.get('value') or []:
        p = s['properties']
        cats = [x.get('category') or x.get('categoryGroup') for x in p.get('logs') or [] if x.get('enabled')]
        # Unset destination type: App Service and Functions still write resource-specific tables; others write AzureDiagnostics.
        dest = p.get('logAnalyticsDestinationType') or ('resource-specific' if '/microsoft.web/' in rid.lower() else 'AzureDiagnostics')
        out.append((p.get('workspaceId'), cats, 'resource-specific' if dest == 'Dedicated' else dest))
    return True, out


def describe(arm, subs, r):
    t = r['type'].lower()
    p = r.get('properties') or {}
    print(f"\n{r['name']}  {r['type']}" + (f" ({r['kind']})" if r.get('kind') else '') + f"  {r['location']}")
    print(f"  subscription {r['subscriptionId']}  resource group {r['resourceGroup']}")
    print(f"  id {r['id']}")
    ws_ids = []
    lines = []

    if t == 'microsoft.web/sites':
        cfg = p.get('siteConfig') or {}
        print(f"  state {p.get('state')}  runtime {cfg.get('linuxFxVersion') or cfg.get('windowsFxVersion') or '?'}"
              f"  always-on {cfg.get('alwaysOn')}  health check {cfg.get('healthCheckPath') or '-'}")
        plan = p.get('serverFarmId')
        if plan:
            pr = arm.graph(subs, f'resources | where tolower(id) == {kql(plan.lower())} | project name, sku=tostring(sku.name), n=toint(properties.numberOfSites)')
            mates = arm.graph(subs, f'resources | where type =~ "microsoft.web/sites" and tolower(properties.serverFarmId) == {kql(plan.lower())} | project name')
            if pr:
                print(f"  plan {pr[0]['name']} ({pr[0]['sku']}), {len(mates)} app(s): {', '.join(m['name'] for m in mates)}")
        st = arm.call('POST', f"{r['id']}/config/appsettings/list?api-version=2023-12-01")
        props = st.get('properties') or {}
        conn = props.get('APPLICATIONINSIGHTS_CONNECTION_STRING') or ''
        ikey = dict(kv.split('=', 1) for kv in conn.split(';') if '=' in kv).get('InstrumentationKey') or props.get('APPINSIGHTS_INSTRUMENTATIONKEY')
        if 'error' in st:
            lines.append('app insights: could not read app settings')
        elif ikey:
            comp = arm.graph(subs, f'resources | where type =~ "microsoft.insights/components" and properties.InstrumentationKey =~ {kql(ikey)}'
                                   ' | project name, ws=tostring(properties.WorkspaceResourceId)')
            if comp:
                ws_ids.append(comp[0]['ws'])
                lines.append(f"app insights {comp[0]['name']} -> @{comp[0]['ws'].lower()}")
            else:
                lines.append('app insights: key set, component not found in these subscriptions')
        else:
            lines.append('app insights: not configured')
    elif t in ('microsoft.app/containerapps', 'microsoft.app/jobs'):
        env = p.get('environmentId') or p.get('managedEnvironmentId')
        e = arm.graph(subs, f'resources | where tolower(id) == {kql((env or "").lower())} | project cid=tostring(properties.appLogsConfiguration.logAnalyticsConfiguration.customerId), dest=tostring(properties.appLogsConfiguration.destination)')
        tmpl = p.get('template') or {}
        images = [c.get('image') for c in tmpl.get('containers') or []]
        print(f"  environment {last(env)}  images {', '.join(i for i in images if i)}  provisioning {p.get('provisioningState')}")
        if p.get('latestRevisionName'):
            print(f"  latest revision {p['latestRevisionName']}  ready {p.get('latestReadyRevisionName')}  running {p.get('runningStatus')}")
        if e:
            lines.append(f"environment logs -> {e[0]['dest'] or 'none'}" + (f" (workspace ID {e[0]['cid']})" if e[0]['cid'] else ''))
    elif t == 'microsoft.dbforpostgresql/flexibleservers':
        sku = r.get('sku') or {}
        print(f"  PostgreSQL {p.get('version')}  {sku.get('name')} ({sku.get('tier')})  storage {(p.get('storage') or {}).get('storageSizeGB')} GB"
              f"  HA {(p.get('highAvailability') or {}).get('mode')}  state {p.get('state')}  host {p.get('fullyQualifiedDomainName')}")
    elif t == 'microsoft.insights/components':
        ws_ids.append(p.get('WorkspaceResourceId'))
        lines.append(f"workspace -> @{(p.get('WorkspaceResourceId') or '').lower()}")
    elif t == 'microsoft.web/serverfarms':
        mates = arm.graph(subs, f'resources | where type =~ "microsoft.web/sites" and tolower(properties.serverFarmId) == {kql(r["id"].lower())} | project name')
        print(f"  sku {(r.get('sku') or {}).get('name')}  apps: {', '.join(m['name'] for m in mates)}")

    ok, ds = diag_settings(arm, r['id'])
    if ok and ds:
        for ws, cats, dest in ds:
            ws_ids.append(ws)
            lines.append(f"diagnostic setting -> @{(ws or '').lower()} [{', '.join(cats) or 'no logs'}] table: {dest}")
    elif ok and t not in ('microsoft.insights/components',):
        lines.append('diagnostic settings: none')

    names = workspaces(arm, subs, ws_ids)
    for ln in lines:
        for wid, label in names.items():
            ln = ln.replace(f'@{wid}', label)
        print(f'  {ln.replace("@", "")}')


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(USAGE)
        return 0 if len(sys.argv) > 1 else 2
    ap = argparse.ArgumentParser(add_help=False)
    ap.error = lambda _m: (print(USAGE, file=sys.stderr), sys.exit(2))
    ap.add_argument('name')
    ap.add_argument('--tenant')
    ap.add_argument('--type', default='')
    ap.add_argument('--max', type=int, default=5)
    a = ap.parse_args()

    tenants = list_tenants(a.tenant)

    found = 0
    for tid, t in tenants.items():
        arm = Arm(tid)
        if not arm.token:
            print(f'# {t["label"]} ({tid}): no token, run az login --tenant {tid}', file=sys.stderr)
            continue
        rows = arm.graph(t['subs'], f'resources | where name contains {kql(a.name)} and type contains {kql(a.type.lower())}'
                                    ' | project id, name, type, kind, location, resourceGroup, subscriptionId, sku, properties | order by name asc')
        if not a.type:
            rows = [r for r in rows if not r['type'].lower().startswith(NOISE)]
        rows.sort(key=lambda r: (r['name'].lower() != a.name.lower(), not r['name'].lower().startswith(a.name.lower()), r['name'].lower()))
        if not rows:
            continue
        print(f'# tenant {t["label"]} ({tid}): {len(rows)} match(es)')
        for r in rows[:a.max]:
            describe(arm, t['subs'], r)
        for r in rows[a.max:]:
            print(f"  also: {r['name']} ({r['type']}, {r['resourceGroup']})")
        found += len(rows)
    if not found:
        die(f'no resource named like {a.name!r} in {len(tenants)} tenant(s)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
