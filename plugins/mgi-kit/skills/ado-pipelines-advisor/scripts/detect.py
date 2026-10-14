#!/usr/bin/env python3
"""Inventories a repository before writing or reviewing a pipeline: project roots, package managers, version pins, lockfiles, Docker, IaC and existing pipelines."""

import argparse
import fnmatch
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path, PurePosixPath

USAGE = """Usage: detect.py [DIR] [--json]

Scans DIR (default: current directory). Inside a git work tree it reads tracked and untracked-but-not-ignored files, which is what a pipeline checkout sees; otherwise it walks the tree.
WARN lines need an answer from the user before writing YAML; INFO lines state the default that applies."""

PRUNE = {'node_modules', '.git', 'bin', 'obj', 'dist', 'build', 'out', '.next', '.nuxt', '.turbo', '.cache', 'coverage', 'vendor', 'target',
         '.venv', 'venv', '__pycache__', '.pnpm-store', '.terraform', '.angular', '.svelte-kit', '.output', '.parcel-cache', '.gradle', '.idea', '.vs'}
GIT_PRUNE = {'node_modules', 'vendor', 'bower_components', '.yarn'}
FIXTURE_DIRS = {'fixtures', 'test-fixtures', '__fixtures__', 'testdata', 'test-data'}
NODE_LOCKS = {'package-lock.json': 'npm', 'npm-shrinkwrap.json': 'npm', 'yarn.lock': 'yarn', 'pnpm-lock.yaml': 'pnpm', 'bun.lock': 'bun', 'bun.lockb': 'bun'}
PY_LOCKS = {'uv.lock': 'uv', 'poetry.lock': 'poetry', 'Pipfile.lock': 'pipenv', 'pdm.lock': 'pdm'}
OTHER = {'go.mod': 'go', 'Cargo.toml': 'rust', 'pom.xml': 'maven', 'build.gradle': 'gradle', 'build.gradle.kts': 'gradle', 'composer.json': 'php', 'Gemfile': 'ruby'}
INSTALL = {'npm': 'npm ci', 'yarn': 'yarn install --frozen-lockfile', 'yarn-berry': 'yarn install --immutable', 'pnpm': 'pnpm install --frozen-lockfile',
           'bun': 'bun install --frozen-lockfile'}
PIPELINE_DIRS = {'.azure', '.azuredevops', '.azure-pipelines', 'pipelines', '.pipelines'}
ROOT_KEYS = re.compile(r'^(trigger|pr|schedules|resources|extends|pool|name|lockBehavior|appendCommitMessageToRunName):', re.M)
BODY_KEYS = re.compile(r'^(stages|jobs|steps|parameters|variables):', re.M)


def list_files(root):
    try:
        out = subprocess.run(['git', '-C', str(root), 'ls-files', '-co', '--exclude-standard', '-z'], capture_output=True, check=True).stdout
        files = [f for f in out.decode().split('\0') if f]
        source = 'git'
    except (OSError, subprocess.CalledProcessError):
        files, source = [], 'walk'
        stack = [root]
        while stack:
            d = stack.pop()
            try:
                entries = list(d.iterdir())
            except OSError:
                continue
            for e in entries:
                if e.is_symlink():
                    continue
                if e.is_dir():
                    if e.name not in PRUNE:
                        stack.append(e)
                else:
                    files.append(e.relative_to(root).as_posix())
    # Tracked build output is what a checkout sees, so git mode only drops vendored dependency trees.
    prune = GIT_PRUNE if source == 'git' else PRUNE
    files = [f for f in files if not prune.intersection(PurePosixPath(f).parts[:-1])]
    return sorted(files), source


def read(root, rel, limit=512 * 1024):
    p = root / rel
    try:
        if p.stat().st_size > limit:
            return ''
        return p.read_text(errors='replace')
    except OSError:
        return ''


def head(root, rel, n=4096):
    try:
        with open(root / rel, errors='replace') as fh:
            return fh.read(n)
    except OSError:
        return ''


def read_json(root, rel):
    try:
        return json.loads(read(root, rel))
    except ValueError:
        return None


def parent(rel):
    return PurePosixPath(rel).parent.as_posix()


def ancestors(d):
    p = PurePosixPath(d)
    return [p.as_posix()] + [a.as_posix() for a in p.parents]


class Repo:
    def __init__(self, root):
        self.root = root
        self.files, self.source = list_files(root)
        self.files = [f for f in self.files if not FIXTURE_DIRS.intersection(PurePosixPath(f).parts[:-1])]
        self.by_dir = {}
        for f in self.files:
            self.by_dir.setdefault(parent(f), set()).add(PurePosixPath(f).name)
        self.notes = []

    def note(self, level, code, path, msg):
        self.notes.append({'level': level, 'code': code, 'path': path, 'message': msg})

    def has(self, d, name):
        return name in self.by_dir.get(d, ())

    def rel(self, d, name):
        return name if d == '.' else f'{d}/{name}'

    def nearest(self, d, names):
        """Closest file among names in d or an ancestor, as (dir, name)."""
        for a in ancestors(d):
            for n in names:
                if self.has(a, n):
                    return a, n
        return None


def workspace_patterns(repo, d, pkg):
    ws = pkg.get('workspaces') if isinstance(pkg, dict) else None
    pats = ws if isinstance(ws, list) else (ws or {}).get('packages', []) if isinstance(ws, dict) else []
    if repo.has(d, 'pnpm-workspace.yaml'):
        text = read(repo.root, repo.rel(d, 'pnpm-workspace.yaml'))
        block = re.search(r'^packages:\s*\n((?:[ \t]+-.*\n?)+)', text, re.M)
        if block:
            pats += [m.strip().strip('\'"') for m in re.findall(r'-\s*(.+)', block.group(1))]
    return [p.rstrip('/') for p in pats if isinstance(p, str)]


def node_version(repo, d, pkg):
    for a in ancestors(d):
        for n in ('.nvmrc', '.node-version'):
            if repo.has(a, n):
                return read(repo.root, repo.rel(a, n)).strip(), repo.rel(a, n)
    if isinstance(pkg, dict):
        if (pkg.get('volta') or {}).get('node'):
            return pkg['volta']['node'], 'volta.node'
        if (pkg.get('engines') or {}).get('node'):
            return pkg['engines']['node'], 'engines.node'
    return None, None


def detect_node(repo):
    dirs = sorted(d for d, names in repo.by_dir.items() if 'package.json' in names)
    pkgs = {d: read_json(repo.root, repo.rel(d, 'package.json')) or {} for d in dirs}
    workspaces = {d: workspace_patterns(repo, d, pkgs[d]) for d in dirs}
    workspaces = {d: p for d, p in workspaces.items() if p}

    def owner(d):
        for w, pats in workspaces.items():
            if w == d:
                continue
            base = '' if w == '.' else w + '/'
            if not (d + '/').startswith(base) and w != '.':
                continue
            sub = d[len(base):] if base else d
            if any(fnmatch.fnmatch(sub, p) or fnmatch.fnmatch(sub, p.replace('/**', '/*')) for p in pats if not p.startswith('!')):
                return w
        return None

    out = []
    for d in dirs:
        pkg = pkgs[d]
        locks = sorted({n for n in NODE_LOCKS if repo.has(d, n)})
        member_of = owner(d)
        if member_of is not None:
            if locks:
                repo.note('WARN', 'W4', d, f'workspace member of {member_of} has its own {", ".join(locks)}; ask whether it is installed separately or the file is stale')
            out.append({'path': d, 'kind': 'node', 'member_of': member_of, 'name': pkg.get('name')})
            continue
        lock_pms = sorted({NODE_LOCKS[n] for n in locks})
        declared = pkg.get('packageManager') if isinstance(pkg.get('packageManager'), str) else None
        declared_pm, _, declared_ver = (declared or '').partition('@')
        pm = declared_pm or (lock_pms[0] if len(lock_pms) == 1 else None)
        if pm == 'yarn' and (repo.has(d, '.yarnrc.yml') or '__metadata:' in head(repo.root, repo.rel(d, 'yarn.lock'))):
            pm = 'yarn-berry'
        if len(lock_pms) > 1:
            repo.note('WARN', 'W1', d, f'lockfiles of {len(lock_pms)} package managers ({", ".join(locks)}); ask which one is used and which lockfile to delete')
        elif not locks:
            repo.note('WARN', 'W2', d, f'package.json without a lockfile; ask whether to commit one (`{INSTALL.get(pm or "npm")}` needs it) or install without')
        if declared_pm and lock_pms and declared_pm not in lock_pms:
            repo.note('WARN', 'W3', d, f'packageManager is {declared} but the lockfile is {", ".join(locks)}; ask which is right')
        ver, ver_src = node_version(repo, d, pkg)
        if not ver:
            repo.note('INFO', 'I1', d, 'no Node version pin; use UseNode@1 version 24.x')
        tools = [t for t in ('turbo.json', 'nx.json', 'lerna.json') if repo.has(d, t)]
        npmrc = read(repo.root, repo.rel(d, '.npmrc')) if repo.has(d, '.npmrc') else ''
        if 'pkgs.dev.azure.com' in npmrc or 'pkgs.visualstudio.com' in npmrc:
            repo.note('INFO', 'I2', d, '.npmrc points at Azure Artifacts; add npmAuthenticate@0 before install')
        out.append({'path': d, 'kind': 'node', 'name': pkg.get('name'), 'pm': pm, 'pm_source': 'packageManager' if declared_pm else 'lockfile' if pm else None,
                    'pm_version': declared_ver.split('+')[0] or None, 'install': INSTALL.get(pm) if pm else None, 'lockfiles': locks,
                    'node': ver, 'node_source': ver_src, 'workspace': workspaces.get(d), 'tools': tools,
                    'members': sorted(m for m in dirs if m != d and owner(m) == d)})
    return out


def detect_dotnet(repo):
    slns = [f for f in repo.files if f.endswith(('.sln', '.slnx'))]
    projs = [f for f in repo.files if f.endswith(('.csproj', '.fsproj', '.vbproj'))]
    out, roots, claimed = [], {}, set()
    for d in sorted({parent(s) for s in slns}, key=lambda d: (d.count('/'), d)):
        here = sorted(PurePosixPath(s).name for s in slns if parent(s) == d)
        top = next((r for r in roots if r == '.' or d.startswith(r + '/')), None)
        if top is not None:
            roots[top]['nested_solutions'] += [f'{d}/{n}' for n in here]
            continue
        if len(here) > 1:
            repo.note('WARN', 'W5', d, f'{len(here)} solutions ({", ".join(here)}); ask which one the pipeline builds')
        mine = [p for p in projs if d == '.' or p.startswith(d + '/')]
        claimed.update(mine)
        roots[d] = dotnet_entry(repo, d, here, mine)
        out.append(roots[d])
    # Projects outside any solution group under the folder that holds their src/ or tests/ directory.
    loose = {}
    for p in sorted(set(projs) - claimed):
        parts = PurePosixPath(p).parts
        cut = next((i for i, x in enumerate(parts[:-1]) if x in ('src', 'tests', 'test')), len(parts) - 1)
        loose.setdefault(PurePosixPath(*parts[:cut]).as_posix() if cut else '.', []).append(p)
    for d, ps in loose.items():
        out.append(dotnet_entry(repo, d, [], ps))
    return out


def dotnet_entry(repo, d, slns, projs):
    tfms = set()
    for p in projs:
        for m in re.findall(r'<TargetFrameworks?>([^<]+)</TargetFrameworks?>', read(repo.root, p)):
            tfms.update(t.strip() for t in m.split(';') if t.strip())
    sdk = rollforward = gj_path = None
    found = repo.nearest(d, ['global.json'])
    if found:
        gj_path = repo.rel(*found)
        gj = read_json(repo.root, gj_path) or {}
        sdk, rollforward = (gj.get('sdk') or {}).get('version'), (gj.get('sdk') or {}).get('rollForward')
    if not sdk:
        repo.note('INFO', 'I3', d, f'no SDK pin in global.json; UseDotNet@2 takes the version from the target framework ({", ".join(sorted(tfms)) or "unknown"})')
    feeds = []
    nc = repo.nearest(d, ['nuget.config', 'NuGet.config', 'NuGet.Config'])
    if nc:
        feeds = re.findall(r'<add\s+key="[^"]*"\s+value="(https?://[^"]+)"', read(repo.root, repo.rel(*nc)))
        if any('pkgs.dev.azure.com' in f or 'pkgs.visualstudio.com' in f for f in feeds):
            repo.note('INFO', 'I4', d, 'nuget.config has an Azure Artifacts feed; add NuGetAuthenticate@1 before restore')
    locked = any(repo.has(parent(p), 'packages.lock.json') for p in projs)
    return {'path': d, 'kind': 'dotnet', 'solutions': slns, 'nested_solutions': [], 'projects': len(projs), 'target_frameworks': sorted(tfms), 'sdk': sdk,
            'roll_forward': rollforward, 'global_json': gj_path, 'central_packages': bool(repo.nearest(d, ['Directory.Packages.props'])),
            'feeds': feeds, 'restore': 'dotnet restore --locked-mode' if locked else 'dotnet restore'}


def detect_python(repo):
    out = []
    for d in sorted(d for d, n in repo.by_dir.items() if n & {'pyproject.toml', 'Pipfile', 'setup.py'} or any(x.startswith('requirements') and x.endswith('.txt') for x in n)):
        names = repo.by_dir[d]
        locks = sorted(n for n in PY_LOCKS if n in names)
        pyproject = {}
        if 'pyproject.toml' in names:
            try:
                pyproject = tomllib.loads(read(repo.root, repo.rel(d, 'pyproject.toml')))
            except tomllib.TOMLDecodeError:
                pass
        pms = sorted({PY_LOCKS[n] for n in locks})
        pm = pms[0] if len(pms) == 1 else None
        if not pms:
            tool = pyproject.get('tool', {})
            pm = 'poetry' if 'poetry' in tool else 'uv' if 'uv' in tool else 'pdm' if 'pdm' in tool else 'pipenv' if 'Pipfile' in names else 'pip'
        if len(pms) > 1:
            repo.note('WARN', 'W1', d, f'Python lockfiles of {len(pms)} tools ({", ".join(locks)}); ask which one is used')
        ver = read(repo.root, repo.rel(d, '.python-version')).strip() if '.python-version' in names else pyproject.get('project', {}).get('requires-python')
        out.append({'path': d, 'kind': 'python', 'pm': pm, 'lockfiles': locks, 'python': ver or None,
                    'requirements': sorted(n for n in names if n.startswith('requirements') and n.endswith('.txt'))})
    return out


def detect_other(repo):
    out = []
    for d, names in sorted(repo.by_dir.items()):
        for n, kind in OTHER.items():
            if n in names:
                out.append({'path': d, 'kind': kind, 'manifest': n})
    return out


def detect_pipelines(repo):
    out = []
    for f in repo.files:
        p = PurePosixPath(f)
        if p.suffix not in ('.yml', '.yaml'):
            continue
        if not (p.name.startswith('azure-pipelines') or PIPELINE_DIRS.intersection(p.parts[:-1])):
            continue
        text = read(repo.root, f)
        if ROOT_KEYS.search(text):
            out.append({'path': f, 'role': 'pipeline'})
        elif BODY_KEYS.search(text):
            out.append({'path': f, 'role': 'template'})
    return out


def main():
    if any(a in ('-h', '--help') for a in sys.argv[1:]):
        print(USAGE)
        return 0
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument('dir', nargs='?', default='.')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    root = Path(a.dir).resolve()
    if not root.is_dir():
        print(f'error: not a directory: {a.dir}', file=sys.stderr)
        return 2
    repo = Repo(root)
    projects = detect_node(repo) + detect_dotnet(repo) + detect_python(repo) + detect_other(repo)
    f = repo.files
    extras = {
        'dockerfiles': [x for x in f if re.fullmatch(r'(.*\.)?Dockerfile(\..*)?', PurePosixPath(x).name)],
        'bake': [x for x in f if re.fullmatch(r'docker-bake(\..*)?\.(hcl|json)', PurePosixPath(x).name)],
        'compose': [x for x in f if re.fullmatch(r'(docker-)?compose(\..*)?\.ya?ml', PurePosixPath(x).name)],
        'bicep': sorted({parent(x) for x in f if x.endswith(('.bicep', '.bicepparam'))}),
        'terraform': sorted({parent(x) for x in f if x.endswith('.tf')}),
        'github_workflows': [x for x in f if x.startswith('.github/workflows/') and x.endswith(('.yml', '.yaml'))],
    }
    pipelines = detect_pipelines(repo)
    counts = {
        'sln': sum(x.endswith('.sln') for x in f), 'slnx': sum(x.endswith('.slnx') for x in f),
        'csproj': sum(x.endswith(('.csproj', '.fsproj', '.vbproj')) for x in f),
        **{n: sum(PurePosixPath(x).name == n for x in f) for n in (*NODE_LOCKS, *PY_LOCKS)},
        'package.json': sum(PurePosixPath(x).name == 'package.json' for x in f),
        'Dockerfile': len(extras['dockerfiles']), 'pipelines': sum(p['role'] == 'pipeline' for p in pipelines),
        'templates': sum(p['role'] == 'template' for p in pipelines),
    }
    result = {'root': str(root), 'source': repo.source, 'files': len(f), 'counts': {k: v for k, v in counts.items() if v},
              'projects': projects, 'pipelines': pipelines, **extras, 'notes': repo.notes}
    if a.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    print(f"root: {root} ({repo.source}, {len(f)} files)")
    for p in projects:
        if p['kind'] == 'node':
            if p.get('member_of') is not None:
                continue
            bits = [f"{p['pm']} ({p['pm_source']})" if p['pm'] else 'pm?', p['install'] or '',
                    f"node {p['node']} ({p['node_source']})" if p['node'] else 'node unpinned',
                    ','.join(p['lockfiles']) or 'no lockfile', f"workspace: {len(p['members'])} members" if p['workspace'] else '', ' '.join(p['tools'])]
        elif p['kind'] == 'dotnet':
            bits = [', '.join(p['solutions']) or 'no solution', f"{p['projects']} projects", f"{len(p['nested_solutions'])} nested solutions" if p['nested_solutions'] else '', ','.join(p['target_frameworks']),
                    f"sdk {p['sdk']} ({p['global_json']})" if p['sdk'] else 'sdk unpinned', 'CPM' if p['central_packages'] else '', p['restore']]
        elif p['kind'] == 'python':
            bits = [p['pm'], ','.join(p['lockfiles']) or ','.join(p['requirements']) or 'no lockfile', f"python {p['python']}" if p['python'] else '']
        else:
            bits = [p['manifest']]
        print(f"{p['path']:<32} {p['kind']:<7} {'  '.join(b for b in bits if b)}")
    for k in ('dockerfiles', 'bake', 'compose', 'bicep', 'terraform', 'github_workflows'):
        if extras[k]:
            print(f"{k}: {', '.join(extras[k][:15])}{' ...' if len(extras[k]) > 15 else ''}")
    for role in ('pipeline', 'template'):
        items = [p['path'] for p in pipelines if p['role'] == role]
        if items:
            print(f"{role}s: {', '.join(items[:20])}{' ...' if len(items) > 20 else ''}")
    print('counts: ' + ', '.join(f'{k} {v}' for k, v in result['counts'].items()))
    grouped = {}
    for n in repo.notes:
        grouped.setdefault((n['level'], n['code'], n['message']), []).append(n['path'])
    for (level, code, msg), paths in sorted(grouped.items(), key=lambda kv: (kv[0][0] != 'WARN', kv[0][1])):
        where = paths[0] if len(paths) == 1 else f"{len(paths)} roots: {', '.join(paths[:5])}{' ...' if len(paths) > 5 else ''}"
        print(f'{level} {code} {where}: {msg}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
