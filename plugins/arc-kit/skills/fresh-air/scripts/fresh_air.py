#!/usr/bin/env python3
"""fresh-air: keep project-level Claude Code skills from loading.

Writes skillOverrides / enabledPlugins (and optionally claudeMdExcludes)
entries into <project>/.claude/settings.local.json so only user-level
(personal, synced, plugin) skills stay active in that project.

Subcommands:
  scan     [DIR] [--json]            report project skills and risk signals
  apply    [DIR] [--mode off|user-only|name-only] [--claude-md sub|all] [--dry-run]
  restore  [DIR] [--dry-run]         remove every entry fresh-air adds (alias: revert)
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HOME = Path.home()
USER_SKILLS = HOME / ".claude" / "skills"
USER_COMMANDS = HOME / ".claude" / "commands"
BACKUP_DIR = HOME / ".claude" / "backups" / "fresh-air"
PRUNE_DIRS = {
    ".git", "node_modules", "vendor", "dist", "build", "target", ".venv",
    "venv", "__pycache__", ".next", ".cache", "bin", "obj",
}
MAX_DEPTH = 8
MODES = ("off", "user-invocable-only", "name-only")
MODE_ALIASES = {"user-only": "user-invocable-only"}

RISK_PATTERNS = [
    ("shell-injection", re.compile(r"!`[^`]+`")),
    ("network", re.compile(r"\b(curl|wget|nc|ncat|Invoke-WebRequest|requests\.(get|post)|urllib\.request|fetch\()", re.I)),
    # Case-sensitive on purpose: prose like "Core Exec (Worker)" must not match.
    ("obfuscation", re.compile(r"base64\s+(-d|--decode)|\beval\s*\(|\bexec\s*\(|fromCharCode|\\x[0-9a-f]{2}\\x")),
    ("destructive", re.compile(r"rm\s+-rf\s+[~/$]|mkfs|dd\s+if=|chmod\s+-R\s+777", re.I)),
    ("prompt-injection", re.compile(
        r"ignore (all |any )?(previous|prior|above) instructions|(do not|don't|never) (tell|inform|mention (this|it) to) the user"
        r"|hide (this|it) from the user|disregard (your|the) (rules|instructions)", re.I)),
    ("sensitive-paths", re.compile(r"\.ssh/|id_rsa|\.aws/credentials|ANTHROPIC_API_KEY|\.claude/settings(\.local)?\.json", re.I)),
]
SCANNED_EXT = {".md", ".sh", ".py", ".js", ".ts", ".mjs", ".cjs", ".ps1", ".rb", ".pl", ""}


def project_root(start):
    start = Path(start).resolve()
    try:
        out = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0 and out.stdout.strip():
            return Path(out.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    return start


def frontmatter_name(path):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return None
    nm = re.search(r"^name:\s*['\"]?([^'\"\n]+?)['\"]?\s*$", m.group(1), re.M)
    return nm.group(1).strip() if nm else None


def skill_dirs_under(skills_dir):
    if not skills_dir.is_dir():
        return []
    return sorted(p for p in skills_dir.iterdir() if (p / "SKILL.md").is_file())


def command_files_under(commands_dir):
    if not commands_dir.is_dir():
        return []
    result = []
    for f in sorted(commands_dir.rglob("*.md")):
        rel = f.relative_to(commands_dir).with_suffix("")
        result.append((":".join(rel.parts), f))
    return result


def find_claude_dirs(root, nested):
    """Yield every .claude dir that Claude Code may load project skills from."""
    yield root / ".claude"
    if not nested:
        return
    root_depth = len(root.parts)
    for dirpath, dirnames, _ in os.walk(root):
        depth = len(Path(dirpath).parts) - root_depth
        dirnames[:] = [d for d in dirnames if d not in PRUNE_DIRS and not (d.startswith(".") and d != ".claude")]
        if depth >= MAX_DEPTH:
            dirnames[:] = []
        if ".claude" in dirnames:
            cdir = Path(dirpath) / ".claude"
            if cdir != root / ".claude":
                yield cdir
            dirnames.remove(".claude")


def risk_signals(skill_path):
    """Return sorted set of risk labels found in a skill folder or command file."""
    files = [skill_path] if skill_path.is_file() else [
        f for f in skill_path.rglob("*") if f.is_file() and f.suffix.lower() in SCANNED_EXT
    ]
    found = set()
    for f in files[:200]:
        try:
            if f.stat().st_size > 512_000:
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for label, pat in RISK_PATTERNS:
            if pat.search(text):
                found.add(label)
        if f.name == "SKILL.md" or f.suffix == ".md":
            fm = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
            if fm and re.search(r"^allowed-tools:.*\bBash\b", fm.group(1), re.M):
                found.add("pre-approved-bash")
    if skill_path.is_dir() and (skill_path / ".claude-plugin" / "plugin.json").is_file():
        found.add("plugin-folder")
    return sorted(found)


def user_skill_names():
    """Names owned by the user: personal skills, personal commands, synced skills."""
    personal, synced = set(), set()
    for d in skill_dirs_under(USER_SKILLS):
        if d.name.lower() == "synced":
            continue
        personal.add(d.name)
        fm = frontmatter_name(d / "SKILL.md")
        if fm:
            personal.add(fm)
    for name, _ in command_files_under(USER_COMMANDS):
        personal.add(name)
    synced_root = USER_SKILLS / "synced"
    if synced_root.is_dir():
        for sk in synced_root.glob("*/*/SKILL.md"):
            synced.add(sk.parent.name)
            fm = frontmatter_name(sk)
            if fm:
                synced.add(fm.split(":")[-1])
    return personal, synced


def scan(root, nested=True, with_risk=True):
    personal, synced = user_skill_names()
    items = []
    for cdir in find_claude_dirs(root, nested):
        rel = cdir.parent.relative_to(root).as_posix()
        location = "root" if rel == "." else rel
        for d in skill_dirs_under(cdir / "skills"):
            names = {d.name}
            fm = frontmatter_name(d / "SKILL.md")
            if fm:
                names.add(fm)
            plugin_name = None
            pj = d / ".claude-plugin" / "plugin.json"
            if pj.is_file():
                try:
                    plugin_name = json.loads(pj.read_text()).get("name") or d.name
                except (OSError, ValueError):
                    plugin_name = d.name
            items.append({
                "kind": "skill", "location": location, "path": str(d.relative_to(root)),
                "names": sorted(names), "plugin": plugin_name,
                "risk": risk_signals(d) if with_risk else [],
            })
        for name, f in command_files_under(cdir / "commands"):
            items.append({
                "kind": "command", "location": location, "path": str(f.relative_to(root)),
                "names": [name], "plugin": None,
                "risk": risk_signals(f) if with_risk else [],
            })
    for it in items:
        it["shadows_personal"] = sorted(set(it["names"]) & personal)
        it["shadows_synced"] = sorted(set(it["names"]) & synced)
    project_settings = root / ".claude" / "settings.json"
    project_hooks = False
    if project_settings.is_file():
        try:
            project_hooks = bool(json.loads(project_settings.read_text()).get("hooks"))
        except (OSError, ValueError):
            pass
    return {"root": str(root), "items": items, "project_settings_has_hooks": project_hooks}


def settings_path(root):
    return root / ".claude" / "settings.local.json"


def load_settings(path):
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    try:
        data = json.loads(text)
    except ValueError as e:
        sys.exit(f"ERROR: {path} is not valid JSON ({e}). Fix it manually; nothing was changed.")
    if not isinstance(data, dict):
        sys.exit(f"ERROR: {path} top level is not an object; nothing was changed.")
    return data


def write_settings(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        # Backups live outside the repo so they can never be committed by accident.
        slug = re.sub(r"[^A-Za-z0-9]+", "-", str(path.parent.parent)).strip("-")
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        backup = BACKUP_DIR / f"{slug}-{stamp}.json"
        n = 1
        while backup.exists():
            backup = BACKUP_DIR / f"{slug}-{stamp}-{n}.json"
            n += 1
        shutil.copy2(path, backup)
        print(f"Backup: {backup}")
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def plan_targets(report):
    """Split names into ones to block and ones left alone because the user owns them."""
    block, skipped = set(), {}
    plugins = set()
    for it in report["items"]:
        for n in it["names"]:
            if n in it["shadows_personal"]:
                skipped[n] = "same name as a personal skill; personal already wins and blocking by name would hide yours"
            else:
                block.add(n)
        if it["plugin"]:
            plugins.add(f"{it['plugin']}@skills-dir")
    return sorted(block), skipped, sorted(plugins)


def cmd_scan(args):
    root = project_root(args.dir)
    report = scan(root, nested=not args.no_nested)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return
    items = report["items"]
    risky = [i for i in items if i["risk"] or i["shadows_personal"] or i["shadows_synced"]]
    print(f"Project: {root}")
    print(f"Project skills/commands found: {len(items)}  (flagged: {len(risky)})")
    if report["project_settings_has_hooks"]:
        print("NOTE: .claude/settings.json defines hooks (fresh-air does not touch hooks).")
    current = load_settings(settings_path(root)).get("skillOverrides", {})
    for it in items:
        state = ",".join(sorted({current.get(n, "on") for n in it["names"]}))
        flags = list(it["risk"])
        if it["shadows_personal"]:
            flags.append("shadows-personal:" + "/".join(it["shadows_personal"]))
        if it["shadows_synced"]:
            flags.append("shadows-synced:" + "/".join(it["shadows_synced"]))
        print(f"  [{state:>4}] {it['kind']:7} {'/'.join(it['names']):28} {it['path']}"
              + (f"  !! {' '.join(flags)}" if flags else ""))


MEMORY_FILES = ("CLAUDE.md", "AGENTS.md", ".claude/CLAUDE.md")


def git_tracked(root, path):
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files", "--error-unmatch", str(path)],
                             capture_output=True, timeout=5)
        return out.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def glob_escape(path):
    return re.sub(r"([\[\]*?{}])", r"\\\1", str(path))


def claude_md_patterns(root, scope):
    """Absolute claudeMdExcludes patterns for memory files the project ships.

    scope "sub" covers subdirectories only (root CLAUDE.md stays), "all" adds the root.
    CLAUDE.local.md is the user's own file, so it is excluded only when the repo commits it.
    """
    patterns = []
    dirs = [root] if scope == "all" else []
    root_depth = len(root.parts)
    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in PRUNE_DIRS and not (d.startswith(".") and d != ".claude")]
        if len(Path(dirpath).parts) - root_depth >= MAX_DEPTH:
            dirnames[:] = []
        if ".claude" in dirnames:
            dirnames.remove(".claude")
        if Path(dirpath) != root:
            dirs.append(Path(dirpath))
    for d in dirs:
        for name in MEMORY_FILES:
            if (d / name).is_file():
                patterns.append(glob_escape(d / name))
        local = d / "CLAUDE.local.md"
        if local.is_file() and git_tracked(root, local):
            patterns.append(glob_escape(local))
        if (d / ".claude" / "rules").is_dir():
            patterns.append(glob_escape(d / ".claude" / "rules") + "/**")
    return patterns


def drop_empty(data, *keys):
    for k in keys:
        if k in data and not data[k]:
            del data[k]


def finish(path, data, changed, dry_run, done_msg):
    if not changed:
        return False
    print(("Would change" if dry_run else "Changing") + f" {path}:")
    for c in changed:
        print("  " + c)
    if not dry_run:
        write_settings(path, data)
        print(done_msg)
    return True


def cmd_apply(args):
    root = project_root(args.dir)
    mode = MODE_ALIASES.get(args.mode, args.mode)
    report = scan(root, nested=not args.no_nested, with_risk=False)
    block, skipped, plugins = plan_targets(report)
    path = settings_path(root)
    data = load_settings(path)
    changed = []

    overrides = data.setdefault("skillOverrides", {})
    for n in block:
        if overrides.get(n) != mode:
            overrides[n] = mode
            changed.append(f"skillOverrides.{n} = {mode}")
    drop_empty(data, "skillOverrides")

    if plugins:
        enabled = data.setdefault("enabledPlugins", {})
        for p in plugins:
            if enabled.get(p) is not False:
                enabled[p] = False
                changed.append(f"enabledPlugins.{p} = false")

    if args.claude_md:
        excludes = data.setdefault("claudeMdExcludes", [])
        for pat in claude_md_patterns(root, args.claude_md):
            if pat not in excludes:
                excludes.append(pat)
                changed.append(f"claudeMdExcludes += {pat}")
        drop_empty(data, "claudeMdExcludes")

    for n, why in sorted(skipped.items()):
        print(f"SKIP {n}: {why}")
    if not block and not plugins and not args.claude_md:
        print(f"No project skills found under {root}; nothing to do.")
        return
    if not finish(path, data, changed, args.dry_run,
                  f"Done. {len(block)} project skill name(s) set to '{mode}'."):
        print(f"Already fresh: {path} is up to date.")


def cmd_restore(args):
    root = project_root(args.dir)
    report = scan(root, nested=not args.no_nested, with_risk=False)
    block, _, plugins = plan_targets(report)
    path = settings_path(root)
    if not path.exists():
        print(f"{path} does not exist; nothing to restore.")
        return
    data = load_settings(path)
    changed = []
    overrides = data.get("skillOverrides", {})
    for n in block:
        if n in overrides:
            del overrides[n]
            changed.append(f"skillOverrides -= {n}")
    drop_empty(data, "skillOverrides")
    enabled = data.get("enabledPlugins", {})
    for p in plugins:
        if enabled.get(p) is False:
            del enabled[p]
            changed.append(f"enabledPlugins -= {p}")
    drop_empty(data, "enabledPlugins")
    excludes = data.get("claudeMdExcludes", [])
    for pat in claude_md_patterns(root, "all"):
        if pat in excludes:
            excludes.remove(pat)
            changed.append(f"claudeMdExcludes -= {pat}")
    drop_empty(data, "claudeMdExcludes")
    if not finish(path, data, changed, args.dry_run, "Restored."):
        print("Nothing to restore.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("scan", "apply", "restore"):
        p = sub.add_parser(name, aliases=["revert"] if name == "restore" else [])
        p.add_argument("dir", nargs="?", default=".")
        p.add_argument("--no-nested", action="store_true", help="only the project root .claude/")
        if name == "scan":
            p.add_argument("--json", action="store_true")
        if name == "apply":
            p.add_argument("--mode", choices=MODES + tuple(MODE_ALIASES), default="off")
            p.add_argument("--claude-md", choices=("sub", "all"),
                           help="exclude project CLAUDE.md files: sub = subdirectories only, all = root too")
        if name in ("apply", "restore"):
            p.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    cmd = "restore" if args.cmd == "revert" else args.cmd
    {"scan": cmd_scan, "apply": cmd_apply, "restore": cmd_restore}[cmd](args)


if __name__ == "__main__":
    main()
