#!/usr/bin/env python3
"""Health audit of a tenant's workloads: what is failing now, what is at risk, and what has no logs; read-only.
Covers App Service and Functions (and their plans), Container Apps and jobs, Container Instances, PostgreSQL flexible
servers, Service Bus, App Insights exceptions, and VMs. Runtime support dates come from https://endoflife.date."""

import argparse
import concurrent.futures
import datetime
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'lib'))
from azarm import Arm, kql, last, tenants as list_tenants  # noqa: E402

USAGE = """Usage:
  audit.py [--tenant TENANT] [--days N] [--rg FRAGMENT] [--no-cost]

--tenant: a tenant ID or a domain/display-name fragment (default: every tenant with an enabled subscription).
--days: metric and log window (default 7). --rg: only resource groups whose name contains FRAGMENT.
Prints, per tenant: BROKEN (failing now), RISK (will fail or degrade), BLIND (no logs to investigate with), the top
exceptions per App Insights role, COST (30 days against the 30 before, idle candidates, Advisor cost recommendations;
--no-cost skips it, Cost Management allows only a few queries a minute), then what was checked. App setting values are read only to find App Insights and are
never printed."""

TYPES = ('microsoft.web/sites', 'microsoft.web/serverfarms', 'microsoft.app/containerapps', 'microsoft.app/jobs',
         'microsoft.app/managedenvironments', 'microsoft.containerinstance/containergroups',
         'microsoft.dbforpostgresql/flexibleservers', 'microsoft.servicebus/namespaces', 'microsoft.insights/components',
         'microsoft.operationalinsights/workspaces', 'microsoft.compute/virtualmachines', 'microsoft.compute/disks',
         'microsoft.network/publicipaddresses')
STACKS = {'DOTNETCORE': 'dotnet', 'DOTNET-ISOLATED': 'dotnet', 'DOTNET': 'dotnet', 'NODE': 'nodejs', 'PYTHON': 'python', 'PHP': 'php'}
TODAY = datetime.date.today()


ENVS = (('prod', {'prod', 'pro', 'production', 'prd', 'live'}), ('staging', {'staging', 'stg', 'stage'}),
        ('beta', {'beta', 'uat', 'preprod'}), ('test', {'test', 'qa'}), ('dev', {'dev', 'develop', 'poc'}))


def env_of(name, rg):
    """A guess from name tokens, then resource group tokens; the name wins because one group can hold several stages."""
    for text in (name, rg):
        tokens = set(re.split(r'[-_.]', text.lower()))
        env = next((env for env, words in ENVS if tokens & words), None)
        if env:
            return env
    return '?'


class Report:
    def __init__(self):
        self.items = {'BROKEN': [], 'RISK': [], 'BLIND': []}
        self.notes = []

    def add(self, level, r, text):
        self.items[level].append((r['type'].split('/')[-1].lower(), r['name'], r['resourceGroup'], text, env_of(r['name'], r['resourceGroup'])))


def eol_table():
    out = {}
    for product in sorted(set(STACKS.values())) + ['postgresql']:
        try:
            with urllib.request.urlopen(f'https://endoflife.date/api/{product}.json', timeout=20) as r:
                out[product] = {str(c['cycle']): c.get('eol') for c in json.load(r)}
        except (OSError, ValueError):
            pass
    return out


def eol_check(rep, r, eol, product, version, label):
    cycles = eol.get(product)
    if cycles is None:
        return
    cycle = version if version in cycles else version.split('.')[0]
    end = cycles.get(cycle)
    if not isinstance(end, str):
        return
    days = (datetime.date.fromisoformat(end) - TODAY).days
    if days < 0:
        rep.add('RISK', r, f'{label} {version} out of support since {end}')
    elif days <= 120:
        rep.add('RISK', r, f'{label} {version} support ends {end} ({days} days)')


def total(vals):
    return sum(vals) if vals else 0


def peak(vals):
    return max(vals) if vals else None


def hot(rep, r, label, hourly, days, limit=90):
    """Sustained load from hourly averages: a few one-minute spikes (deploys, backups) are not a finding."""
    if not hourly:
        return
    mean, busy = sum(hourly) / len(hourly), sum(1 for v in hourly if v >= limit)
    if mean >= 80:
        rep.add('BROKEN', r, f'{label} averages {mean:.0f}% over {days}d')
    elif busy >= 3:
        rep.add('RISK', r, f'{label} averaged >= {limit}% in {busy} of {len(hourly)} hours')


def check_site(arm, rep, r, plans, eol, days):
    p = r['properties'] or {}
    cfg = p.get('siteConfig') or {}
    kind = r.get('kind') or ''
    plan = plans.get((p.get('serverFarmId') or '').lower()) or {}
    sku = (plan.get('sku') or {}).get('name') or ''
    serverless = sku in ('Y1', 'FC1')
    if p.get('state') != 'Running':
        rep.add('RISK', r, f"state {p.get('state')}")
        return
    fx = cfg.get('linuxFxVersion') or ''
    stack, _, ver = fx.partition('|')
    if stack.upper() in STACKS and ver:
        eol_check(rep, r, eol, STACKS[stack.upper()], re.sub(r'-lts$', '', ver.lower()), stack.upper())
    if not serverless and cfg.get('alwaysOn') is False:
        rep.add('RISK', r, 'always-on off: idle unloads, first request after idle is slow' +
                (', timer and queue triggers stall' if 'functionapp' in kind else ''))
    if not serverless and 'functionapp' not in kind and not cfg.get('healthCheckPath'):
        rep.add('RISK', r, 'no health check path: a hung instance keeps receiving traffic')

    settings = arm.call('POST', f"{r['id']}/config/appsettings/list?api-version=2023-12-01").get('properties') or {}
    has_ai = any(k in settings for k in ('APPLICATIONINSIGHTS_CONNECTION_STRING', 'APPINSIGHTS_INSTRUMENTATIONKEY'))
    diag = arm.call('GET', f"{r['id']}/providers/Microsoft.Insights/diagnosticSettings?api-version=2021-05-01-preview").get('value')
    if not has_ai and not diag:
        rep.add('BLIND', r, 'no App Insights and no diagnostic setting: runtime logs are not kept anywhere')

    m = arm.metrics(r['id'], ['Http5xx', 'Requests'], days, 'Total')
    errors, reqs = total(m.get('Http5xx')), total(m.get('Requests'))
    rate = errors / reqs * 100 if reqs else 0
    # A handful of 5xx among tens of thousands of requests is background noise (bots, client aborts).
    if errors and (errors >= 10 and rate >= 0.1 or rate >= 1 or not reqs):
        daily = [int(v) for v in arm.metrics(r['id'], ['Http5xx'], days, 'Total', 'P1D').get('Http5xx') or []]
        rep.add('BROKEN' if rate >= 1 else 'RISK', r, f'{int(errors)} HTTP 5xx in {days}d ({rate:.2f}% of {int(reqs)} requests), '
                                                       f'per day oldest first: {" ".join(map(str, daily))}')


def check_plan(arm, rep, r, apps, days):
    sku = r.get('sku') or {}
    tier = (sku.get('tier') or '').lower()
    names = apps.get(r['id'].lower(), [])
    if tier in ('basic', 'free', 'shared') and len(names) > 1:
        rep.add('RISK', r, f"{sku.get('name')} shared by {len(names)} apps ({', '.join(names)}): one busy app slows the rest; "
                           'Basic has no autoscale or slots')
    if sku.get('name') in ('Y1', 'FC1') or not names:
        return
    avg = arm.metrics(r['id'], ['CpuPercentage', 'MemoryPercentage'], days, 'Average')
    for name, label in (('CpuPercentage', 'CPU'), ('MemoryPercentage', 'memory')):
        hot(rep, r, label, avg.get(name) or [], days)


def check_containerapp(arm, rep, r, envs, days):
    p = r['properties'] or {}
    if (p.get('provisioningState') or '').lower() == 'failed':
        rep.add('BROKEN', r, 'provisioning failed')
    latest, ready = p.get('latestRevisionName'), p.get('latestReadyRevisionName')
    if latest and latest != ready:
        rep.add('BROKEN', r, f'latest revision {latest} is not ready; traffic stays on {ready or "nothing"}')
    restarts = total(arm.metrics(r['id'], ['RestartCount'], days, 'Total').get('RestartCount'))
    if restarts:
        rep.add('RISK', r, f'{int(restarts)} container restarts in {days}d')
    env = envs.get((p.get('environmentId') or p.get('managedEnvironmentId') or '').lower())
    if env is not None and not env.get('cid'):
        rep.add('BLIND', r, f"environment {env['name']} sends logs nowhere")


def check_job(arm, rep, r, days):
    d = arm.call('GET', f"{r['id']}/executions?api-version=2024-03-01")
    since = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)).isoformat()
    runs = [e for e in d.get('value') or [] if ((e.get('properties') or {}).get('startTime') or '') >= since]
    failed = [e for e in runs if (e.get('properties') or {}).get('status') == 'Failed']
    if failed:
        rep.add('BROKEN', r, f"{len(failed)} of {len(runs)} executions failed in {days}d, last {failed[0]['properties'].get('startTime', '')[:16]}")


def check_aci(rep, r):
    p = r['properties'] or {}
    for c in p.get('containers') or []:
        st = ((c.get('properties') or {}).get('instanceView') or {}).get('currentState') or {}
        if st.get('exitCode') not in (None, 0) or st.get('detailStatus') == 'Error':
            rep.add('BROKEN', r, f"container {c.get('name')} exited {st.get('exitCode')} at {(st.get('finishTime') or '')[:16]}"
                                 + (' (134: .NET unhandled exception)' if st.get('exitCode') == 134 else ''))


def check_pg(arm, rep, r, eol, days):
    p = r['properties'] or {}
    sku = r.get('sku') or {}
    if p.get('state') != 'Ready':
        rep.add('RISK', r, f"state {p.get('state')}")
        return
    eol_check(rep, r, eol, 'postgresql', str(p.get('version')), 'PostgreSQL')
    cfg = arm.call('GET', f"{r['id']}/configurations/max_connections?api-version=2024-08-01")
    maxc = int(((cfg.get('properties') or {}).get('value')) or 0)
    mn = arm.metrics(r['id'], ['cpu_credits_remaining'], days, 'Minimum')
    mx = arm.metrics(r['id'], ['active_connections', 'storage_percent'], days, 'Maximum')
    avg = arm.metrics(r['id'], ['cpu_percent', 'memory_percent'], days, 'Average')
    hot(rep, r, 'CPU', avg.get('cpu_percent') or [], days)
    hot(rep, r, 'memory', avg.get('memory_percent') or [], days)
    tot = arm.metrics(r['id'], ['connections_failed', 'deadlocks'], days, 'Total')
    credits = peak([-v for v in mn.get('cpu_credits_remaining') or []])
    if (sku.get('tier') or '').lower() == 'burstable' and credits is not None:
        low = -credits
        if low <= 0:
            rep.add('BROKEN', r, f"{sku.get('name')} ran out of CPU credits in {days}d: CPU throttled to base, every query slows")
        elif low < 30:
            rep.add('RISK', r, f"{sku.get('name')} CPU credits fell to {low:.0f}")
    conns = peak(mx.get('active_connections'))
    if maxc and conns is not None and conns >= 0.8 * maxc:
        rep.add('BROKEN' if conns >= 0.95 * maxc else 'RISK', r, f'connections peaked at {conns:.0f} of max_connections {maxc}')
    hi = peak(mx.get('storage_percent'))
    if hi is not None and hi >= 80:
        rep.add('BROKEN' if hi >= 95 else 'RISK', r, f'storage {hi:.0f}% full')
    failed, deadlocks = total(tot.get('connections_failed')), total(tot.get('deadlocks'))
    if failed:
        rep.add('RISK', r, f'{int(failed)} failed connections in {days}d (auth errors or max_connections reached)')
    if deadlocks:
        rep.add('RISK', r, f'{int(deadlocks)} deadlocks in {days}d')
    diag = arm.call('GET', f"{r['id']}/providers/Microsoft.Insights/diagnosticSettings?api-version=2021-05-01-preview").get('value')
    if not diag:
        rep.add('BLIND', r, 'no diagnostic setting: server errors, slow queries and sessions are not kept')


def check_servicebus(arm, rep, r, days):
    incoming = total(arm.metrics(r['id'], ['IncomingMessages'], days, 'Total').get('IncomingMessages'))
    entities = []
    for q in arm.call('GET', f"{r['id']}/queues?api-version=2021-11-01").get('value') or []:
        entities.append((q['name'], (q.get('properties') or {}).get('countDetails') or {}))
    for t in arm.call('GET', f"{r['id']}/topics?api-version=2021-11-01").get('value') or []:
        for s in arm.call('GET', f"{t['id']}/subscriptions?api-version=2021-11-01").get('value') or []:
            entities.append((f"{t['name']}/{s['name']}", (s.get('properties') or {}).get('countDetails') or {}))
    for name, c in entities:
        dead, active = c.get('deadLetterMessageCount') or 0, c.get('activeMessageCount') or 0
        if dead and not incoming:
            rep.add('RISK', r, f'{name}: {dead} old dead-lettered messages; no message arrived in {days}d, so nothing is failing now')
        elif dead:
            rep.add('BROKEN', r, f'{name}: {dead} dead-lettered messages with traffic in the last {days}d (consumer failing or messages expiring)')
        if active >= 1000:
            rep.add('RISK', r, f'{name}: {active} messages waiting (consumer down or too slow)')


def check_vm(rep, r):
    code = (((r['properties'] or {}).get('extended') or {}).get('instanceView') or {}).get('powerState', {}).get('code', '')
    if code == 'PowerState/stopped':
        rep.add('RISK', r, 'stopped but still allocated: billed as running; deallocate or start it')


def aca_warnings(arm, rep, envs, apps, days):
    """Warning events per app from each environment's workspace; newer environments drop the _CL suffix and type suffixes."""
    rollout = ('RevisionCreation', 'RevisionDeactivating', 'RollingRevisionCompleted')
    pick = ' or '.join(f'Reason{{s}} == "{r}"' for r in rollout)
    queries = (f'ContainerAppSystemLogs_CL | where Type_s == "Warning" or {pick.format(s="_s")} | summarize n=count(), '
               'lastSeen=max(TimeGenerated) by app=ContainerAppName_s, reason=Reason_s',
               f'ContainerAppSystemLogs | where Type == "Warning" or {pick.format(s="")} | summarize n=count(), '
               'lastSeen=max(TimeGenerated) by app=ContainerAppName, reason=Reason')
    # One app can log to two workspaces after its environment's destination changed; merge them.
    per_app, rollouts = {}, {}
    for cid in {e['cid'] for e in envs.values() if e.get('cid')}:
        rows = next((x for x in (arm.logs(cid, q, days) for q in queries) if x is not None), None)
        if rows is None:
            rep.notes.append(f'Container Apps workspace {cid}: no system log table yet (no events written, or logs go elsewhere); '
                             'warnings for apps in that environment were not checked')
        for row in rows or []:
            app = (row['app'] or '').lower()
            if row['reason'] in rollout:
                rollouts[app] = rollouts.get(app, 0) + (row['n'] if row['reason'] == 'RevisionCreation' else 0)
                continue
            # Single events (a probe during a deploy, one restart) are normal churn; ScaledObjectDeleted is a revision
            # being deactivated, which every rollout does.
            if row['reason'] != 'ScaledObjectDeleted':
                cur = per_app.setdefault(app, {}).setdefault(row['reason'], {'reason': row['reason'], 'n': 0, 'lastSeen': ''})
                cur['n'] += row['n']
                cur['lastSeen'] = max(cur['lastSeen'], row['lastSeen'])
    for name, by_reason in per_app.items():
        r = apps.get(name)
        found = sorted((x for x in by_reason.values() if x['n'] >= 5), key=lambda x: -x['n'])
        if r and found:
            lastseen = max(x['lastSeen'] for x in found)[:16]
            n = rollouts.get(name, 0)
            rep.add('RISK', r, f"warnings in {days}d: " + ', '.join(f"{x['reason']} {x['n']}" for x in found) + f" (last {lastseen})"
                    + (f'; {n} revision creation events in the window: unhealthy replicas and scaler errors while one drains are '
                       'expected, so check whether the warnings fall outside rollouts' if n else ''))


def exceptions(arm, workspaces, days):
    out = []
    q = (f'AppExceptions | summarize n=count(), lastSeen=max(TimeGenerated), msg=take_any(coalesce(InnermostMessage, OuterMessage)) by AppRoleName, ExceptionType'
         ' | top 15 by n')
    for wid, name in workspaces.items():
        rows = arm.logs(wid, q, days)
        for row in rows or []:
            out.append((row['n'], row['AppRoleName'] or name, row['ExceptionType'], (row['msg'] or '').replace('\n', ' ')[:140], row['lastSeen'][:16]))
    merged = {}
    for n, role, typ, msg, seen in out:
        m = merged.setdefault((role, typ), [0, msg, seen])
        m[0] += n
        m[2] = max(m[2], seen)
    return sorted(((n, role, typ, msg, seen) for (role, typ), (n, msg, seen) in merged.items()), reverse=True)[:20]


def cost_rows(arm, sub, start, end):
    """{(resource id, currency): actual cost} for one subscription, and {resource id: service name}."""
    body = {'type': 'ActualCost', 'timeframe': 'Custom', 'timePeriod': {'from': str(start), 'to': str(end)},
            'dataset': {'granularity': 'None', 'aggregation': {'c': {'name': 'Cost', 'function': 'Sum'}},
                        'grouping': [{'type': 'Dimension', 'name': 'ResourceId'}, {'type': 'Dimension', 'name': 'ServiceName'}]}}
    out, svc, url = {}, {}, f'/subscriptions/{sub}/providers/Microsoft.CostManagement/query?api-version=2023-11-01'
    while url:
        d = arm.call('POST', url.removeprefix('https://management.azure.com'), body)
        if 'error' in d:
            return d['error']
        p = d.get('properties') or {}
        cols = [c['name'] for c in p.get('columns') or []]
        for row in p.get('rows') or []:
            r = dict(zip(cols, row))
            key = ((r.get('ResourceId') or '').lower(), r.get('Currency') or '')
            out[key] = out.get(key, 0) + (r.get('Cost') or 0)
            svc[key[0]] = r.get('ServiceName') or ''
        url = p.get('nextLink')
    return out, svc


def rg_of(rid, svc=None):
    """The resource group, or for spend billed on the subscription itself (an Azure DevOps organization, a purchase) the service."""
    parts = rid.split('/')
    if 'resourcegroups' in parts:
        return parts[parts.index('resourcegroups') + 1]
    return f"{(svc or {}).get(rid) or 'other'} ({last(rid) or 'no resource'}, outside resource groups)"


def costs(arm, t, by, apps, rg):
    """Spend per subscription and resource group over 30 days against the 30 before, idle candidates with their cost, and open
    Advisor cost recommendations. Idle means a state (unattached, no apps), not proof nobody needs it."""
    end = TODAY - datetime.timedelta(days=1)  # today's usage is still arriving
    lines, denied, spent = [f'## COST: 30 days to {end} against the 30 before (actual cost)'], [], {}
    for sub in t['subs']:
        cur = cost_rows(arm, sub, end - datetime.timedelta(days=29), end)
        if isinstance(cur, str):
            code = re.search(r'"code":\s*"(\w+)"', cur)
            denied.append(f"{t['names'][sub]} ({code.group(1) if code else cur[:40]})")
            continue
        cur, svc = cur
        prev = cost_rows(arm, sub, end - datetime.timedelta(days=59), end - datetime.timedelta(days=30))
        prev = prev[0] if isinstance(prev, tuple) else {}
        keep = lambda rid: not rg or rg.lower() in rg_of(rid).lower()  # noqa: E731
        spent.update({rid: v for (rid, _), v in cur.items()})
        for ccy in sorted({c for _, c in cur} | {c for _, c in prev}):
            now = {rid: v for (rid, c), v in cur.items() if c == ccy and keep(rid)}
            was = {rid: v for (rid, c), v in prev.items() if c == ccy and keep(rid)}
            if not now and not was:
                continue
            tn, tw = sum(now.values()), sum(was.values())
            lines.append(f"- {t['names'][sub]}: {tn:,.0f} {ccy}" + (f' (before {tw:,.0f}, {(tn - tw) / tw * 100:+.0f}%)' if tw else ''))
            groups = {}
            for rid, v in now.items():
                groups.setdefault(rg_of(rid, svc), [0, 0])[0] += v
            for rid, v in was.items():
                groups.setdefault(rg_of(rid, svc), [0, 0])[1] += v
            for g, (n, w) in sorted(groups.items(), key=lambda x: -x[1][0])[:6]:
                lines.append(f'  {g}: {n:,.0f}' + (f' (before {w:,.0f})' if abs(n - w) >= max(10, 0.25 * w) else ''))
            rises = sorted(((now.get(rid, 0) - was.get(rid, 0), rid) for rid in set(now) | set(was) if rid), reverse=True)
            for delta, rid in [x for x in rises if x[0] >= 20][:5]:
                lines.append(f'  up {delta:,.0f}: {last(rid)} ({rg_of(rid)}) {was.get(rid, 0):,.0f} -> {now.get(rid, 0):,.0f}')

    idle = []
    for d in by.get('microsoft.compute/disks', []):
        if (d['properties'] or {}).get('diskState') == 'Unattached':
            idle.append((d, f"unattached {(d.get('sku') or {}).get('name') or ''} disk, {(d['properties'] or {}).get('diskSizeGB')} GB"))
    for ip in by.get('microsoft.network/publicipaddresses', []):
        p = ip['properties'] or {}
        if not p.get('ipConfiguration') and not p.get('natGateway'):
            idle.append((ip, 'public IP not attached to anything'))
    for pid, plan in ((p['id'].lower(), p) for p in by.get('microsoft.web/serverfarms', [])):
        sku = (plan.get('sku') or {}).get('name') or ''
        if not apps.get(pid) and sku not in ('Y1', 'FC1', 'F1', 'D1'):
            idle.append((plan, f'{sku} App Service plan with no apps: billed while empty'))
    if idle:
        lines.append('- idle candidates (confirm with the owner before removing; cost over the 30 days):')
        for r, why in idle:
            v = spent.get(r['id'].lower())
            lines.append(f"  {r['name']} ({r['resourceGroup']}): {why}" + (f', {v:,.0f}' if v else ''))

    recs = arm.graph(t['subs'], "advisorresources | where type == 'microsoft.advisor/recommendations' and properties.category == 'Cost'"
                     " and properties.recommendationStatus != 'Completed' | project rid=tolower(tostring(properties.resourceMetadata.resourceId)),"
                     " sub=tostring(properties.extendedProperties.recommendationSubCategory), what=tostring(properties.impactedValue),"
                     " problem=tostring(properties.shortDescription.problem), yearly=todouble(properties.extendedProperties.annualSavingsAmount),"
                     " ccy=tostring(properties.extendedProperties.savingsCurrency), daily=todouble(properties.savings.retail.dailyPotentialSavings),"
                     " ccy2=tostring(properties.savings.providerCurrency)")
    seen = {r['id'].lower() for r, _ in idle}
    advice, commit = {}, {}
    for x in recs:
        if rg and rg.lower() not in rg_of(x['rid'] or '').lower():
            continue
        yearly, ccy = x['yearly'] or (x['daily'] or 0) * 365, x['ccy'] or x['ccy2']
        if x['sub'] in ('Reservations', 'SavingsPlans') or any(w in x['problem'].lower() for w in ('reserved', 'savings plan')):
            # One recommendation per term and scope: report the best, not the sum.
            commit[x['problem']] = max(commit.get(x['problem'], (0, ccy)), (yearly, ccy))
        elif x['rid'] not in seen:
            advice.setdefault((x['problem'], ccy), []).append((x['what'], yearly))
    if advice:
        lines.append('- Advisor:')
        for (problem, ccy), items in sorted(advice.items(), key=lambda i: -sum(y for _, y in i[1])):
            save = sum(y for _, y in items)
            lines.append(f"  {problem}: {', '.join(sorted(w for w, _ in items))}" + (f' (~{save:,.0f} {ccy}/year)' if save else ''))
    for problem, (yearly, ccy) in commit.items():
        lines.append(f'- Advisor, commitment: {problem}: up to ~{yearly:,.0f} {ccy}/year for a 1 or 3 year term; only for capacity that will stay')
    if denied:
        lines.append(f"- cost not readable: {', '.join(denied)}; AuthorizationFailed needs Cost Management Reader on the subscription, "
                     'SubscriptionCostDisabled is a CSP subscription whose partner hides cost')
    return lines


def audit(tid, t, a, eol):
    arm = Arm(tid)
    if not arm.token:
        print(f'# {t["label"]} ({tid}): no token, run az login --tenant {tid}')
        return
    rows = arm.graph(t['subs'], 'resources | where type in~ (' + ','.join(kql(x) for x in TYPES) + ')'
                     # Environments, workspaces and plans often sit in a shared group; keep them so the apps' logs resolve.
                     + (f' and (resourceGroup contains {kql(a.rg)} or type in~ ("microsoft.app/managedenvironments",'
                        f' "microsoft.operationalinsights/workspaces", "microsoft.insights/components"))' if a.rg else '')
                     + ' | project id, name, type=tolower(type), kind, resourceGroup, location, sku, properties')
    by = {}
    for r in rows:
        by.setdefault(r['type'], []).append(r)
    sites = by.get('microsoft.web/sites', [])
    plans = {p['id'].lower(): p for p in by.get('microsoft.web/serverfarms', [])}
    apps = {}
    for s in sites:
        apps.setdefault(((s['properties'] or {}).get('serverFarmId') or '').lower(), []).append(s['name'])
    envs = {e['id'].lower(): {'name': e['name'], 'cid': ((((e['properties'] or {}).get('appLogsConfiguration') or {})
                                                         .get('logAnalyticsConfiguration') or {}).get('customerId'))}
            for e in by.get('microsoft.app/managedenvironments', [])}
    ws_ids = {w['id'].lower(): (w['properties'] or {}).get('customerId') for w in by.get('microsoft.operationalinsights/workspaces', [])}
    ai_ws = {}
    for c in by.get('microsoft.insights/components', []):
        cid = ws_ids.get(((c['properties'] or {}).get('WorkspaceResourceId') or '').lower())
        if cid:
            ai_ws[cid] = c['name']

    rep = Report()
    jobs = [lambda s=s: check_site(arm, rep, s, plans, eol, a.days) for s in sites]
    jobs += [lambda p=p: check_plan(arm, rep, p, apps, a.days) for p in plans.values()]
    jobs += [lambda c=c: check_containerapp(arm, rep, c, envs, a.days) for c in by.get('microsoft.app/containerapps', [])]
    jobs += [lambda j=j: check_job(arm, rep, j, a.days) for j in by.get('microsoft.app/jobs', [])]
    jobs += [lambda g=g: check_pg(arm, rep, g, eol, a.days) for g in by.get('microsoft.dbforpostgresql/flexibleservers', [])]
    jobs += [lambda n=n: check_servicebus(arm, rep, n, a.days) for n in by.get('microsoft.servicebus/namespaces', [])]
    for g in by.get('microsoft.containerinstance/containergroups', []):
        check_aci(rep, g)
    for v in by.get('microsoft.compute/virtualmachines', []):
        check_vm(rep, v)
    aca = {c['name'].lower(): c for c in by.get('microsoft.app/containerapps', []) + by.get('microsoft.app/jobs', [])}
    jobs.append(lambda: aca_warnings(arm, rep, envs, aca, a.days))
    with concurrent.futures.ThreadPoolExecutor(8) as pool:
        top = pool.submit(exceptions, arm, ai_ws, a.days)
        spend = pool.submit(costs, arm, t, by, apps, a.rg) if not a.no_cost else None
        for f in [pool.submit(j) for j in jobs]:
            try:
                f.result()
            except Exception as e:  # one resource's odd shape must not hide the rest of the audit
                rep.notes.append(f'check failed: {type(e).__name__}: {e}')
        top = top.result()
        try:
            spend = spend.result() if spend else []
        except Exception as e:
            spend = [f'## COST: failed: {type(e).__name__}: {e}']

    print(f'# {t["label"]} ({tid}), last {a.days} days' + (f', resource groups containing {a.rg!r}' if a.rg else ''))
    for level, title in (('BROKEN', 'failing now'), ('RISK', 'will fail or degrade'), ('BLIND', 'no logs to investigate with')):
        groups = {}
        for kind, name, rg, text, env in rep.items[level]:
            groups.setdefault((kind, text), []).append((env, f'{name} ({rg})'))
        print(f'\n## {level}: {title} ({len(rep.items[level])})')
        rank = {e: i for i, (e, _) in enumerate(ENVS)}
        # Findings shared by several resources print once; the rest one per line, prod first.
        # Specific findings first, prod first; shared hygiene (health checks, always-on, plan sharing) last.
        hygiene = ('no health check', 'always-on off', 'shared by')
        for (kind, text), names in sorted(groups.items(), key=lambda g: (any(h in g[0][1] for h in hygiene), min(rank.get(e, 9) for e, _ in g[1]), g[0][0], sorted(g[1])[0])):
            if len(names) > 1:
                print(f'- [{kind}] {text}: {", ".join(f"{n} [{e}]" for e, n in sorted(names, key=lambda x: (rank.get(x[0], 9), x[1])))}')
            else:
                print(f'- [{names[0][0]}] [{kind}] {names[0][1]}: {text}')
        if level == 'BROKEN':
            by_rg = {}
            for kind, name, rg, text, env in rep.items[level]:
                by_rg.setdefault(rg, []).append(name)
            for rg, names in sorted(by_rg.items()):
                if len(set(names)) > 1:
                    print(f'  > {", ".join(sorted(set(names)))} share resource group {rg}: check them as one incident first')
    print(f'\n## Top exceptions ({a.days}d, App Insights, {len(ai_ws)} workspace(s))')
    for n, role, typ, msg, seen in top:
        print(f'- {role}: {typ} ({n} times): {msg} (last {seen})')
    if not top:
        print('- none recorded' if ai_ws else '- no App Insights component in scope')
    if spend:
        print('\n' + '\n'.join(spend))
    counts = ', '.join(f'{len(v)} {k.split("/")[-1]}' for k, v in sorted(by.items()))
    print(f'\nChecked: {counts or "nothing"}.' + ('' if eol else ' Runtime support dates not checked (endoflife.date unreachable).'))
    for n in rep.notes:
        print(f'  {n}')


def main():
    if any(x in ('-h', '--help') for x in sys.argv[1:]):
        print(USAGE)
        return 0
    ap = argparse.ArgumentParser(add_help=False)
    ap.error = lambda _m: (print(USAGE, file=sys.stderr), sys.exit(2))
    ap.add_argument('--tenant')
    ap.add_argument('--days', type=int, default=7)
    ap.add_argument('--rg')
    ap.add_argument('--no-cost', action='store_true')
    a = ap.parse_args()
    eol = eol_table()
    for tid, t in list_tenants(a.tenant).items():
        audit(tid, t, a, eol)
    return 0


if __name__ == '__main__':
    sys.exit(main())
