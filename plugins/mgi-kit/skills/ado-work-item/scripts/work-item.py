#!/usr/bin/env python3
"""One work item as plain text: fields, rich-text fields, test steps, parent chain, links, PRs, attachments, comments; read-only.
APIs: https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/work-items/get-work-item?view=azure-devops-rest-7.1
      https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/comments/get-comments?view=azure-devops-rest-7.1"""

import argparse
import json
import os
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

# Shares the REST and credential helpers of ado-pipelines-advisor, installed alongside in mgi-kit.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'ado-pipelines-advisor' / 'scripts' / 'lib'))
import ado  # noqa: E402

USAGE = """Usage:
  work-item.py --org ORG --id ID [--comments N] [--parent-chars N] [--download DIR]

--id also takes a work item URL. --comments: newest N comments, printed oldest first (default 30).
--parent-chars: description excerpt per ancestor (default 1500, 0 for titles only).
--download DIR: save attached files and inline images there (only from the organization's host), to Read them."""

SCOPE = 'vso.work (Work Items: Read), plus vso.code (Code: Read) for pull request titles'
# Fields shown elsewhere in the output, or bookkeeping that says nothing about the work.
SKIP = re.compile(r'^(System\.|WEF_|Microsoft\.VSTS\.Common\.(StateChange|Activated|Resolved|Closed|StackRank|BacklogPriority)'
                  r'|Microsoft\.VSTS\.TCM\.(TestSuiteAudit|TestSuiteTypeId|LocalDataSource|Parameters))')
TEXT_KEEP = {'System.Description'}
LINK_NAMES = {'System.LinkTypes.Hierarchy-Reverse': 'Parent', 'System.LinkTypes.Hierarchy-Forward': 'Child'}


class _Text(HTMLParser):
    BLOCK = {'p', 'div', 'br', 'tr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'table', 'pre', 'blockquote'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.images = [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in self.BLOCK:
            self.out.append('\n')
        elif tag == 'li':
            self.out.append('\n- ')
        elif tag == 'td' or tag == 'th':
            self.out.append(' | ')
        elif tag == 'img' and a.get('src'):
            self.images.append(a['src'])
            name = urllib.parse.parse_qs(urllib.parse.urlsplit(a['src']).query).get('fileName', [a['src'][-40:]])[0]
            self.out.append(f'[image: {name}]')

    def handle_endtag(self, tag):
        if tag in self.BLOCK or tag == 'li':
            self.out.append('\n')

    def handle_data(self, data):
        self.out.append(data)


def html_text(s, images=None):
    p = _Text()
    p.feed(s or '')
    if images is not None:
        images.extend(p.images)
    text = re.sub(r'[ \t ]+\n', '\n', ''.join(p.out))
    # <li><p>x</p></li> leaves "- " alone on its line and blank lines between items.
    text = re.sub(r'^- *\n+', '- ', text, flags=re.M)
    text = re.sub(r'\n\s*\n(?=- )', '\n', text)
    return re.sub(r'\n{3,}', '\n\n', text).strip()


def test_steps(xml, images):
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return html_text(xml, images)
    lines = []
    for n, step in enumerate(root.iter('step'), 1):
        parts = [html_text(ps.text or '', images) for ps in step.findall('parameterizedString')]
        lines.append(f'{n}. {parts[0] if parts else ""}' + (f'\n   expected: {parts[1]}' if len(parts) > 1 and parts[1] else ''))
    for ref in root.iter('compref'):
        lines.append(f'(shared steps work item {ref.get("ref")})')
    return '\n'.join(lines)


def who(v):
    return v.get('displayName') if isinstance(v, dict) else v


def main():
    if any(a in ('-h', '--help') for a in sys.argv[1:]):
        print(USAGE)
        return 0
    p = argparse.ArgumentParser(add_help=False)
    p.error = lambda _msg: (print(USAGE, file=sys.stderr), sys.exit(2))
    p.add_argument('--org', default=os.environ.get('ADO_ORG'))
    p.add_argument('--id')
    p.add_argument('--comments', type=int, default=30)
    p.add_argument('--parent-chars', type=int, default=1500)
    p.add_argument('--download')
    a = p.parse_args()
    m = re.search(r'(\d+)\D*$', a.id or '')
    if not m:
        p.error('')
    if not a.org and a.id and '://' in a.id:
        a.org = re.match(r'(https://dev\.azure\.com/[^/]+|https://[^/]+\.visualstudio\.com)', a.id).group(1)
    wid = m.group(1)
    org = ado.org_url(a.org)
    client = ado.Client(org)
    wit = f'{org}/_apis/wit'

    w = client.get_json(f'{wit}/workitems/{wid}?$expand=all&api-version={ado.API_VERSION}', SCOPE)
    f = w['fields']
    project = f['System.TeamProject']
    images = []
    print(f"#{wid} [{f['System.WorkItemType']}] {f['System.Title']}")
    print(f"  state {f['System.State']} ({f.get('System.Reason')})  assigned {who(f.get('System.AssignedTo')) or '-'}  "
          f"created {f['System.CreatedDate'][:10]} by {who(f.get('System.CreatedBy'))}  changed {f['System.ChangedDate'][:10]} by {who(f.get('System.ChangedBy'))}")
    print(f"  area {f.get('System.AreaPath')}  iteration {f.get('System.IterationPath')}" + (f"  tags {f['System.Tags']}" if f.get('System.Tags') else ''))
    print(f"  {org}/{ado.uri(project)}/_workitems/edit/{wid}")

    short, long = [], []
    for k, v in f.items():
        if v in (None, '') or (SKIP.match(k) and k not in TEXT_KEEP):
            continue
        if k == 'Microsoft.VSTS.TCM.Steps':
            long.append(('Test steps', test_steps(v, images)))
        elif isinstance(v, str) and (len(v) > 80 or '<' in v):
            long.append((k.rsplit('.', 1)[-1], html_text(v, images)))
        else:
            short.append(f"{k.rsplit('.', 1)[-1]}={who(v)}")
    if short:
        print('  ' + '  '.join(short))
    for name, text in long:
        print(f'\n== {name}\n{text}')

    rels = w.get('relations') or []
    linked, prs, other, files = {}, [], {}, []
    for r in rels:
        name = (r.get('attributes') or {}).get('name') or LINK_NAMES.get(r['rel']) or r['rel']
        if r['rel'] == 'AttachedFile':
            files.append((r['attributes'].get('name'), r['attributes'].get('resourceSize'), r['url']))
        elif r['url'].startswith(f'{org}/') and '/_apis/wit/workItems/' in r['url']:
            linked.setdefault(name, []).append(int(r['url'].rsplit('/', 1)[1]))
        elif name == 'Pull Request':
            prs.append(urllib.parse.unquote(r['url'].rsplit('/', 1)[1]).split('/'))
        else:
            other.setdefault(name, []).append(r['url'])

    ids = sorted({i for v in linked.values() for i in v})
    info = {}
    for i in range(0, len(ids), 200):
        batch = client.request('POST', f'{wit}/workitemsbatch?api-version={ado.API_VERSION}', {
            'ids': ids[i:i + 200], 'errorPolicy': 'omit',
            'fields': ['System.WorkItemType', 'System.Title', 'System.State', 'System.AssignedTo']})
        if batch[0] == 200:
            for x in json.loads(batch[1])['value']:
                if x:
                    info[x['id']] = x['fields']

    def line(i):
        x = info.get(i)
        return f'#{i} [{x["System.WorkItemType"]}] {x["System.Title"]} ({x["System.State"]}, {who(x.get("System.AssignedTo")) or "-"})' if x else f'#{i} (no access)'

    parent = (linked.get('Parent') or [None])[0]
    depth = 0
    while parent and depth < 3:
        pw = client.get_json(f'{wit}/workitems/{parent}?$expand=relations&api-version={ado.API_VERSION}', SCOPE)
        pf = pw['fields']
        print(f"\n== {'Parent' if depth == 0 else 'Ancestor'} #{parent} [{pf['System.WorkItemType']}] {pf['System.Title']} ({pf['System.State']})")
        chars = a.parent_chars if depth == 0 else min(a.parent_chars, 200)
        if chars > 0:
            text = html_text(pf.get('System.Description') or pf.get('Microsoft.VSTS.Common.AcceptanceCriteria') or '')
            print(text[:chars] + (' [...]' if len(text) > chars else ''))
        parent = next((int(r['url'].rsplit('/', 1)[1]) for r in pw.get('relations') or []
                       if r['rel'] == 'System.LinkTypes.Hierarchy-Reverse'), None)
        depth += 1

    for name, group in linked.items():
        if name == 'Parent':
            continue
        print(f'\n== {name} ({len(group)})')
        for i in group:
            print(f'- {line(i)}')

    if not prs:
        print('\n== Pull requests: none linked (a fix may still be named in comments)')
    else:
        print(f'\n== Pull requests ({len(prs)})')
        for proj_id, repo_id, pr_id in sorted(prs, key=lambda x: -int(x[2]))[:10]:
            code, raw = client.request('GET', f'{org}/{proj_id}/_apis/git/repositories/{repo_id}/pullrequests/{pr_id}?api-version={ado.API_VERSION}')
            if code == 200:
                pr = json.loads(raw)
                print(f"- !{pr_id} {pr['status']} {pr['repository']['name']}: {pr['title']}  "
                      f"{pr['sourceRefName'].removeprefix('refs/heads/')} -> {pr['targetRefName'].removeprefix('refs/heads/')}")
            else:
                print(f'- !{pr_id} (HTTP {code})')
        if len(prs) > 10:
            print(f'- ... {len(prs) - 10} older')
    for name, urls in other.items():
        shown = [urllib.parse.unquote(u.rsplit('/', 1)[-1]).split('/')[-1] for u in urls]
        if name in ('Fixed in Commit', 'Commit'):
            shown = [x[:10] for x in shown]
        print(f'\n== {name} ({len(urls)})\n- ' + '\n- '.join(shown[-10:]))

    if files:
        print(f'\n== Attachments ({len(files)})')
        for name, size, _ in files:
            print(f'- {name} ({size or "?"} bytes)')

    if a.comments > 0 and f.get('System.CommentCount'):
        c = client.get_json(f'{org}/{ado.uri(project)}/_apis/wit/workItems/{wid}/comments?$top={a.comments}&order=desc'
                            f'&api-version=7.1-preview.4', SCOPE)
        shown = list(reversed(c.get('comments') or []))
        print(f"\n== Comments ({len(shown)} of {c.get('totalCount')}, oldest first)")
        for x in shown:
            print(f"\n-- {who(x['createdBy'])} {x['createdDate'][:16].replace('T', ' ')}"
                  + (f" (edited {x['modifiedDate'][:10]})" if x.get('modifiedDate', '')[:16] != x['createdDate'][:16] else ''))
            print(html_text(x.get('text') or '', images))

    if images and not a.download:
        print(f'\n({len(images)} inline image(s); --download DIR to fetch them)')
    if a.download:
        out = Path(a.download)
        out.mkdir(parents=True, exist_ok=True)
        host = urllib.parse.urlsplit(org).hostname
        targets = [(n, u) for n, _, u in files]
        for u in images:
            q = urllib.parse.parse_qs(urllib.parse.urlsplit(u).query)
            targets.append((q.get('fileName', [u.rsplit('/', 1)[-1][:40] + '.png'])[0], u))
        print(f'\n== Downloaded to {out}')
        for n, (name, url) in enumerate(targets, 1):
            if urllib.parse.urlsplit(url).hostname != host:
                print(f'- skipped {name}: not on {host}')
                continue
            code, raw = client.request('GET', url)
            if code != 200:
                print(f'- {name}: HTTP {code}')
                continue
            dest = out / f'{n:02d}-{re.sub(r"[^\w.-]", "_", name or "file")}'
            dest.write_bytes(raw)
            print(f'- {dest} ({len(raw)} bytes)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
