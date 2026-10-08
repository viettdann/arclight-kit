#!/usr/bin/env python3
"""Snapshot, backup, check, and diff for arc-kit:supervise, so the skill runs the same under bash, zsh, and macOS."""
import argparse
import contextlib
import difflib
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile


def git(root, *args):
    r = subprocess.run(["git", "-C", root, *args], capture_output=True)
    return r.stdout.decode("utf-8", "surrogateescape") if r.returncode == 0 else None


def repo_root(cwd="."):
    out = git(cwd, "rev-parse", "--show-toplevel")
    return os.path.realpath(out.strip()) if out else None


def digest(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha1(f.read()).hexdigest()
    except (FileNotFoundError, IsADirectoryError):
        return None


def state(root):
    names = set()
    for args in (("ls-files", "-z", "-m", "-o", "--exclude-standard"), ("diff", "-z", "--name-only", "--no-renames", "--cached")):
        names.update(n for n in (git(root, *args) or "").split("\0") if n)
    head = git(root, "rev-parse", "-q", "--verify", "HEAD")
    return {
        "head": head.strip() if head else None,
        "stash": (git(root, "stash", "list", "--format=%H") or "").split(),
        "files": {n: digest(os.path.join(root, n)) for n in sorted(names)},
    }


def load(run, name, default):
    try:
        with open(os.path.join(run, name)) as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def save(run, name, data):
    with open(os.path.join(run, name), "w") as f:
        json.dump(data, f, indent=1)


def relative(root, path):
    # realpath on both sides: macOS /tmp and /var/folders are symlinks into /private, and git reports the resolved root.
    full = path if os.path.isabs(path) else os.path.join(root, path)
    rel = os.path.relpath(os.path.join(os.path.realpath(os.path.dirname(full)), os.path.basename(full)), root)
    if rel.startswith(".."):
        raise SystemExit(f"snapshot: {path} is outside {root}")
    return rel


def take(args):
    root = repo_root()
    run = args.run or tempfile.mkdtemp(prefix="supervise-")
    os.makedirs(run, exist_ok=True)
    if root:
        save(run, "snapshot.json", {"root": root, "git": True, **state(root)})
    else:
        save(run, "snapshot.json", {"root": os.path.realpath(os.getcwd()), "git": False})
        print("snapshot: not a git repository; nothing to check later, but backup and diff work", file=sys.stderr)
    print(run)
    return 0


def run_root(run):
    root = load(run, "snapshot.json", {}).get("root")
    if not root:
        raise SystemExit(f"snapshot: {run} has no snapshot.json; run `take` first")
    return root


@contextlib.contextmanager
def locked(run):
    # Parallel backups would otherwise lose each other's owned.json entries.
    with open(os.path.join(run, ".lock"), "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        yield


def backup(args):
    root = run_root(args.run)
    dest = os.path.join(args.run, args.group)
    rels = [relative(root, p) for p in args.paths]
    dirs = [r for r in rels if os.path.isdir(os.path.join(root, r))]
    if dirs:
        print(f"snapshot: {', '.join(dirs)} is a directory; list its files", file=sys.stderr)
        return 2
    with locked(args.run):
        owned = load(args.run, "owned.json", {})
        paths = owned.setdefault(args.group, [])
        for rel in rels:
            # A path this group already owns keeps its first backup, or its absence: a later call must not adopt the worker's edits as the baseline.
            if rel in paths:
                continue
            source = os.path.join(root, rel)
            if os.path.isfile(source):
                os.makedirs(os.path.dirname(os.path.join(dest, rel)), exist_ok=True)
                shutil.copy2(source, os.path.join(dest, rel))
            paths.append(rel)
        os.makedirs(dest, exist_ok=True)
        save(args.run, "owned.json", owned)
    print(dest)
    return 0


def check(args):
    snap = load(args.run, "snapshot.json", None)
    if snap is None:
        print("snapshot: no snapshot.json in the run directory", file=sys.stderr)
        return 2
    if not snap.get("git"):
        print("skipped: not a git repository")
        return 0
    now = state(snap["root"])
    owned = {p for paths in load(args.run, "owned.json", {}).values() for p in paths}
    findings = []
    if now["head"] != snap["head"]:
        findings.append(f"head-moved {snap['head']} -> {now['head']}")
    if now["stash"] != snap["stash"]:
        findings.append(f"stash-changed {len(snap['stash'])} -> {len(now['stash'])} entries")
    for path, before in snap["files"].items():
        if path not in owned and now["files"].get(path, digest(os.path.join(snap["root"], path))) != before:
            findings.append(f"foreign-changed {path}")
    for path in now["files"]:
        if path not in owned and path not in snap["files"]:
            findings.append(f"stray {path}")
    print("\n".join(findings) if findings else "clean")
    return 1 if findings else 0


def read(path):
    try:
        with open(path, "rb") as f:
            return f.read()
    except (FileNotFoundError, IsADirectoryError):
        return None


def unified(before, after, old_label, new_label):
    if b"\0" in (before or b"") or b"\0" in (after or b""):
        return [f"Binary files {old_label} and {new_label} differ\n".encode()] if before != after else []
    old = (before or b"").decode("utf-8", "surrogateescape").splitlines(keepends=True)
    new = (after or b"").decode("utf-8", "surrogateescape").splitlines(keepends=True)
    out = []
    for line in difflib.unified_diff(old, new, old_label, new_label):
        if not line.endswith("\n"):
            line += "\n\\ No newline at end of file\n"
        out.append(line.encode("utf-8", "surrogateescape"))
    return out


def diff(args):
    root = run_root(args.run)
    owned = load(args.run, "owned.json", {}).get(args.group)
    if owned is None:
        print(f"snapshot: no group {args.group} in {args.run}", file=sys.stderr)
        return 2
    base = os.path.join(args.run, args.group)
    for rel in owned:
        before, after = read(os.path.join(base, rel)), read(os.path.join(root, rel))
        old_label = f"a/{rel}" if before is not None else "/dev/null"
        new_label = f"b/{rel}" if after is not None else "/dev/null"
        # Bytes straight to stdout: a strict UTF-8 stdout (macOS) would reject non-UTF-8 content.
        sys.stdout.buffer.writelines(unified(before, after, old_label, new_label))
    sys.stdout.buffer.flush()
    return 0


def main():
    parser = argparse.ArgumentParser(prog="snapshot")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("take", help="record HEAD, the stash list, and hashes of uncommitted files; print the run directory")
    p.add_argument("--run", help="retake into an existing run directory")
    p.set_defaults(func=take)
    p = sub.add_parser("backup", help="copy a group's owned files into <run>/<group>/ and record the ownership")
    p.add_argument("run")
    p.add_argument("group")
    p.add_argument("paths", nargs="+")
    p.set_defaults(func=backup)
    p = sub.add_parser("check", help="compare the worktree with the snapshot, ignoring every owned file; exit 1 on findings")
    p.add_argument("run")
    p.set_defaults(func=check)
    p = sub.add_parser("diff", help="unified diff of a group's owned files against its backup")
    p.add_argument("run")
    p.add_argument("group")
    p.set_defaults(func=diff)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
