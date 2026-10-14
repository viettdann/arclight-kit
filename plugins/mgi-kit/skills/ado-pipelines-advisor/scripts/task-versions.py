#!/usr/bin/env python3
"""Checks task references in pipeline YAML against references/task-versions.md, and refreshes that table from Learn or an organization."""

import argparse
import os
import re
import shutil
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'lib'))
import ado  # noqa: E402

TABLE = HERE.parent / 'references' / 'task-versions.md'
INDEX_URL = 'https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/?view=azure-pipelines&accept=text/markdown'
SHORTCUTS = ('script', 'bash', 'pwsh', 'powershell')

USAGE = """Usage:
  task-versions.py refresh                     Latest major of every task in the Learn task index (Azure DevOps Services), as TSV.
  task-versions.py check FILE.yml...           Tasks below the latest major, deprecated, renamed inputs, unlisted tasks, script shortcuts.
  task-versions.py check --markdown FILE.md... Same, over every fenced ```yaml block.
  task-versions.py org --org ORG [--all]       Tasks installed in the organization with majors and deprecated/preview flags.

check reads the table in references/task-versions.md, so it runs offline. Exit code 1 when a finding or parse error exists."""


def load_yaml_module():
    try:
        import yaml
        return yaml
    except ImportError:
        pass
    # Re-run once under uv with PyYAML instead of asking the user to install it.
    if shutil.which('uv') and not os.environ.get('TASK_VERSIONS_UV'):
        os.environ['TASK_VERSIONS_UV'] = '1'
        os.execvp('uv', ['uv', 'run', '--quiet', '--no-project', '--with', 'pyyaml', 'python3', __file__, *sys.argv[1:]])
    ado.die('PyYAML is required: pip install pyyaml (or install uv)', 2)


def load_table():
    """name -> (name, latest, older, status, replacement, renamed); names are case-insensitive in Azure Pipelines."""
    if not TABLE.is_file():
        ado.die(f'table not found: {TABLE}')
    rows = {}
    for line in TABLE.read_text().splitlines():
        cells = line.split('|')
        if len(cells) <= 7:
            continue
        f = [c.replace('`', '').strip() for c in cells[1:8]]
        if re.fullmatch(r'[A-Za-z0-9]+@[0-9]+', f[1]):
            rows.setdefault(f[0].lower(), f[:6])
    if not rows:
        ado.die(f'no rows parsed from {TABLE}')
    return rows


def walk(node, path, yaml):
    """Pre-order over mappings, yielding (mapping node, dict of key -> value node, path of keys)."""
    if isinstance(node, yaml.MappingNode):
        m = {}
        for k, v in node.value:
            if isinstance(k, yaml.ScalarNode):
                m.setdefault(k.value, v)
        yield node, m, path
        for k, v in node.value:
            yield from walk(v, path + [k.value if isinstance(k, yaml.ScalarNode) else '?'], yaml)
    elif isinstance(node, yaml.SequenceNode):
        for i, v in enumerate(node.value):
            yield from walk(v, path + [str(i)], yaml)


class Checker:
    def __init__(self, yaml, table):
        self.yaml, self.table, self.findings = yaml, table, 0

    def report(self, label, kind, msg):
        print(f'{label}\t{kind}\t{msg}')
        self.findings += 1

    def check_text(self, text, label, offset=0):
        yaml = self.yaml
        try:
            docs = list(yaml.compose_all(text))
        except yaml.YAMLError as e:
            mark = getattr(e, 'problem_mark', None)
            line = offset + (mark.line + 1 if mark else 1)
            self.report(label, 'parse-error', f"yaml at line {line}: {' '.join(x for x in (getattr(e, 'context', None), getattr(e, 'problem', None)) if x) or e}")
            return
        tasks, shortcuts = [], []
        for doc in docs:
            for node, m, path in walk(doc, [], yaml):
                line = node.start_mark.line + 1 + offset
                if 'task' in m:
                    inputs = m.get('inputs')
                    keys = [k.value for k, _ in inputs.value if isinstance(k, yaml.ScalarNode)] if isinstance(inputs, yaml.MappingNode) else []
                    tasks.append((getattr(m['task'], 'value', ''), keys, line))
                elif 'inputs' not in path:
                    # A same-named key under inputs: is a task input, not a step.
                    shortcuts += [(k, line) for k in m if k in SHORTCUTS]
        for ref, inputs, line in tasks:
            self.check_task(label, re.sub(r'\s', '', str(ref)), inputs, f'line {line}')
        for key, line in shortcuts:
            self.report(label, 'shortcut', f"'{key}:' step at line {line}: write it as Bash@3 (targetType: inline) or CmdLine@2")

    def check_task(self, label, ref, inputs, where):
        if not ref:
            return
        name, _, major = ref.rpartition('@') if '@' in ref else (ref, '', '')
        if not major.isdigit():
            self.report(label, 'no-major', f'{ref} at {where}: pin a major, e.g. {name}@N')
            return
        row = self.table.get(name.lower())
        if not row:
            self.report(label, 'unlisted', f'{ref} at {where}: not in task-versions.md; look it up on its task reference page and add a row')
            return
        _, latest, _, status, replacement, renamed = row
        if status.lower().startswith('deprecated'):
            self.report(label, 'deprecated', f"{ref} at {where}: deprecated, use {replacement or 'the replacement in task-versions.md'}")
            return
        latest_major = int(latest.rpartition('@')[2])
        if int(major) < latest_major:
            self.report(label, 'outdated', f'{ref} at {where}: latest is {latest}')
        elif int(major) > latest_major:
            self.report(label, 'unknown-major', f'{ref} at {where}: table only knows up to {latest}; refresh the table')
        # Renamed inputs are listed as old->new and apply to the latest major.
        if renamed and renamed != '-' and int(major) == latest_major:
            for pair in renamed.split(','):
                old, _, new = pair.partition('->')
                old, new = old.strip(), new.strip()
                if old in inputs:
                    if new == '(removed)':
                        self.report(label, 'removed-input', f"{ref} at {where}: input '{old}' does not exist in {latest}")
                    else:
                        self.report(label, 'renamed-input', f"{ref} at {where}: input '{old}' is '{new}' in {latest}")


def yaml_blocks(text):
    """(fence line number, block text) for every fenced yaml block; the fence line is the offset to source lines."""
    blocks, start, buf = [], None, []
    for n, line in enumerate(text.splitlines(), 1):
        if start is None and re.fullmatch(r'[ \t]*```[ \t]*(yaml|yml)[ \t]*', line):
            start, buf = n, []
        elif start is not None and re.fullmatch(r'[ \t]*```[ \t]*', line):
            blocks.append((start, '\n'.join(buf) + '\n'))
            start = None
        elif start is not None:
            buf.append(line)
    return blocks


def cmd_check(args):
    checker = Checker(load_yaml_module(), load_table())
    for f in args.files:
        p = Path(f)
        if not p.is_file():
            ado.die(f'not a file: {f}')
        text = p.read_text()
        if args.markdown:
            for offset, block in yaml_blocks(text):
                checker.check_text(block, f, offset)
        else:
            checker.check_text(text, f)
    print(f'{checker.findings} finding(s)', file=sys.stderr)
    return 1 if checker.findings else 0


def cmd_refresh(_args):
    try:
        with urllib.request.urlopen(INDEX_URL) as r:
            md = r.read().decode().replace('\r', '')
    except OSError as e:
        ado.die(f'could not fetch {INDEX_URL}: {e}')
    order, label, note, majors, page = [], {}, {}, {}, {}
    on = done = False
    # The page repeats its tables per product version; the azure-pipelines moniker is the Services one.
    for line in md.splitlines():
        if not done and '::: moniker range="azure-pipelines"' in line:
            on = True
            continue
        if on and line.startswith('::: moniker-end'):
            on, done = False, True
        if not (on and line.startswith('| **')):
            continue
        cell = line.split('|')
        display = re.sub(r'^ *\*\*', '', cell[1])
        name = display.split('**')[0]
        # One display name can hold two task names, e.g. UseNode@1 and NodeTool@0; each is its own row.
        for task, major, slug in re.findall(r'\[([A-Za-z0-9]+)@([0-9]+)\]\(([a-z0-9-]+)\)', display):
            page[f'{task}@{major}'] = slug
            if task not in label:
                order.append(task)
                label[task], note[task] = name, cell[2]
            majors.setdefault(task, []).append(int(major))
    print('task\tlatest\tolder\tdisplay\turl\tdescription')
    for t in order:
        hi = max(majors[t])
        older = ','.join(str(v) for v in majors[t] if v != hi)
        url = f'https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/{page[f"{t}@{hi}"]}?view=azure-pipelines'
        print(f'{t}\t{t}@{hi}\t{older}\t{label[t]}\t{url}\t{note[t].strip(" ")}')
    return 0


def tsv(v):
    if isinstance(v, bool):
        v = 'true' if v else 'false'
    return str(v).replace('\\', '\\\\').replace('\t', '\\t').replace('\n', '\\n').replace('\r', '\\r')


def cmd_org(args):
    client = ado.Client()
    data = client.get_json(f'{ado.org_url(args.org or os.environ.get("ADO_ORG"))}/_apis/distributedtask/tasks?api-version={ado.API_VERSION}',
                           'vso.agentpools (Agent Pools: Read)')
    groups = {}
    for t in data['value']:
        v = t['version']
        groups.setdefault(t['name'].lower(), []).append({
            'name': t['name'], 'major': v['major'], 'ver': (v['major'], v['minor'], v['patch']),
            'deprecated': bool(t.get('deprecated')), 'preview': bool(t.get('preview')), 'msg': t.get('deprecationMessage') or ''})
    # The endpoint returns every installed version; keep the highest per major.
    tasks = []
    for key in sorted(groups):
        best = {}
        for e in groups[key]:
            if e['major'] not in best or e['ver'] >= best[e['major']]['ver']:
                best[e['major']] = e
        tasks.append((groups[key][0]['name'], [best[m] for m in sorted(best, reverse=True)]))
    if args.all:
        print('task\tmajor\tversion\tdeprecated\tpreview\tmessage')
        for name, ms in tasks:
            for e in ms:
                print('\t'.join(tsv(x) for x in (name, e['major'], '.'.join(map(str, e['ver'])), e['deprecated'], e['preview'], e['msg'])))
    else:
        print('task\tlatest\tmajors\tdeprecated_majors\tlatest_preview')
        for name, ms in tasks:
            print('\t'.join(tsv(x) for x in (name, f"{name}@{ms[0]['major']}", ','.join(str(e['major']) for e in ms),
                                                ','.join(str(e['major']) for e in ms if e['deprecated']), ms[0]['preview'])))
    return 0


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(USAGE)
        return 0
    p = argparse.ArgumentParser(usage=USAGE, add_help=False)
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('refresh', add_help=False)
    c = sub.add_parser('check', add_help=False)
    c.add_argument('--markdown', action='store_true')
    c.add_argument('files', nargs='+')
    o = sub.add_parser('org', add_help=False)
    o.add_argument('--org')
    o.add_argument('--all', action='store_true')
    args = p.parse_args()
    return {'refresh': cmd_refresh, 'check': cmd_check, 'org': cmd_org}[args.cmd](args)


if __name__ == '__main__':
    sys.exit(main())
