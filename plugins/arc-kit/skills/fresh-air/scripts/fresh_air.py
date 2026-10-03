#!/usr/bin/env python3
"""Disable repository Codex skills through supported user-config entries.

Python 3.11+. Only this script's verified marker block is changed. Repository
files are never modified. Disabling a path affects every session using the
same CODEX_HOME; restart Codex after changing the configuration.
"""

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import tomllib


class Conflict(Exception):
    """Configuration or ownership cannot safely be determined."""


def project_root(directory):
    start = Path(directory).expanduser().resolve(strict=True)
    if not start.is_dir():
        raise Conflict(f"Not a directory: {start}")
    try:
        result = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5, check=False,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip()).resolve(strict=True)
    except (OSError, subprocess.SubprocessError):
        pass
    return start


def protected_roots(codex_home):
    return tuple(path.resolve() for path in (
        Path.home() / ".agents" / "skills", codex_home / "skills",
        Path("/etc/codex/skills"),
    ))


def validate_root(root, protected):
    home = Path.home().resolve()
    if home.is_relative_to(root):
        raise Conflict("Choose a project directory, not your home or its ancestors.")
    if any(root.is_relative_to(path) for path in protected):
        raise Conflict("A personal or system skills directory is not a project.")


def discover(root, protected):
    """Find nested .agents/skills, following skill links only inside this repo."""
    found, skipped = set(), set()

    def failed_walk(error):
        raise error

    def permitted(path):
        resolved = path.resolve()
        if not resolved.is_relative_to(root):
            skipped.add(f"{path}: symlink target outside project")
            return False
        if any(resolved.is_relative_to(item) for item in protected):
            skipped.add(f"{path}: personal or system skills")
            return False
        return True

    def walk_skills(directory):
        seen = set()
        for current, dirs, files in os.walk(directory, followlinks=True, onerror=failed_walk):
            path = Path(current)
            resolved = path.resolve()
            if not permitted(path) or resolved in seen:
                dirs[:] = []
                continue
            seen.add(resolved)
            dirs[:] = sorted(d for d in dirs if d != ".git" and permitted(path / d))
            if "SKILL.md" in files and permitted(path / "SKILL.md"):
                if (path / "SKILL.md").is_file():
                    found.add((path / "SKILL.md").resolve())
                else:
                    skipped.add(f"{path / 'SKILL.md'}: missing or non-file skill")

    for current, dirs, _ in os.walk(root, followlinks=False, onerror=failed_walk):
        path = Path(current)
        if ".agents" in dirs:
            skills = path / ".agents" / "skills"
            if skills.is_dir() and permitted(skills):
                walk_skills(skills)
            dirs.remove(".agents")
        retained = []
        for name in sorted(dirs):
            candidate = path / name
            if name == ".git":
                continue
            if candidate.is_symlink():
                skipped.add(f"{candidate}: linked project directory not traversed")
            elif permitted(candidate):
                retained.append(name)
        dirs[:] = retained
    return sorted(found), sorted(skipped)


def parse_config(raw):
    try:
        return tomllib.loads(raw.decode("utf-8"))
    except (UnicodeError, tomllib.TOMLDecodeError) as error:
        raise Conflict(f"Invalid config.toml; nothing changed: {error}") from error


def configured_skills(raw):
    data = parse_config(raw)
    skills = data.get("skills", {})
    if not isinstance(skills, dict):
        raise Conflict("Existing 'skills' configuration is not a table.")
    entries = skills.get("config", [])
    if not isinstance(entries, list):
        raise Conflict("Existing 'skills.config' is not an array of tables.")
    result = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise Conflict("Existing skills.config entry has no string path.")
        if "enabled" in entry and not isinstance(entry["enabled"], bool):
            raise Conflict("Existing skills.config entry has a non-boolean enabled value.")
        path = Path(entry["path"]).expanduser()
        if not path.is_absolute():
            # Relative paths can vary with config source. Never guess and risk
            # adding an override for the same skill.
            raise Conflict("Existing skills.config uses a relative path; resolve it before running fresh-air.")
        path = path.resolve()
        if path in result:
            raise Conflict(f"Duplicate existing skill configuration: {path}")
        result[path] = entry.get("enabled", True)
    return result


def marker_id(root):
    return hashlib.sha256(os.fsencode(root)).hexdigest()[:24]


def make_block(root, paths):
    body = f"# Repository: {json.dumps(str(root), ensure_ascii=False)}\n"
    for path in sorted(paths):
        body += f"[[skills.config]]\npath = {json.dumps(str(path), ensure_ascii=False)}\nenabled = false\n"
    payload = body.encode("utf-8")
    key = marker_id(root)
    digest = hashlib.sha256(payload).hexdigest()
    return (
        f"\n# >>> fresh-air {key} {digest}\n".encode() + payload
        + f"# <<< fresh-air {key}\n".encode()
    )


def split_owned(raw, root):
    key = marker_id(root).encode()
    start_token = b"# >>> fresh-air " + key
    end_token = b"# <<< fresh-air " + key
    if start_token not in raw and end_token not in raw:
        return raw, set(), b""
    pattern = re.compile(
        rb"\n# >>> fresh-air " + key + rb" ([0-9a-f]{64})\n(.*?)# <<< fresh-air " + key + rb"\n",
        re.DOTALL,
    )
    matches = list(pattern.finditer(raw))
    if len(matches) != 1 or raw.count(start_token) != 1 or raw.count(end_token) != 1:
        raise Conflict("Managed markers changed or duplicated; nothing changed.")
    match = matches[0]
    if hashlib.sha256(match[2]).hexdigest().encode() != match[1]:
        raise Conflict("Managed block was edited; restore its original contents before retrying.")
    paths = configured_skills(match[2])
    if not paths or any(paths.values()) or make_block(root, paths) != match[0]:
        raise Conflict("Managed block does not match the expected repository/format.")
    actual = configured_skills(raw)
    if any(path not in actual or actual[path] is not False for path in paths):
        raise Conflict("Managed markers are not active disabled skill entries; nothing changed.")
    base = raw[:match.start()] + raw[match.end():]
    configured_skills(base)
    return base, set(paths), match[0]


@contextmanager
def config_lock(config_path):
    """Fail fast if another fresh-air operation owns this config's lock."""
    config_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock = config_path.with_name(".fresh-air.lock")
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as error:
        raise Conflict(f"Configuration locked: {lock}. If a previous process crashed, remove this lock after confirming it has stopped.") from error
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(str(os.getpid()) + "\n")
        yield
    finally:
        lock.unlink()


def read_config(path):
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return b""


def atomic_write(path, previous, replacement, existed):
    parse_config(replacement)
    mode = stat.S_IMODE(path.stat().st_mode) if existed else 0o600
    fd, temporary = tempfile.mkstemp(prefix=".fresh-air-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            os.chmod(temporary, mode)
            stream.write(replacement)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists() != existed or read_config(path) != previous:
            raise Conflict("Config changed during this operation; nothing overwritten. Retry after other config edits finish.")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def operate(command, root, config_path, protected, dry_run=False):
    existed = config_path.exists()
    raw = read_config(config_path)
    configured_skills(raw)
    base, owned, old_block = split_owned(raw, root)
    for entry in parse_config(raw).get("skills", {}).get("config", []):
        if Path(entry["path"]).expanduser().resolve() in owned and set(entry) != {"path", "enabled"}:
            raise Conflict("A managed skill entry has extra user fields; nothing changed.")
    existing = configured_skills(base)
    if owned & existing.keys():
        raise Conflict("Managed skill paths also have user entries; resolve the duplicate configuration first.")
    paths, skipped = discover(root, protected) if command != "restore" else ([], [])
    report = {
        "project": str(root), "config": str(config_path), "command": command,
        "discovered": [str(path) for path in paths],
        "managed": [str(path) for path in sorted(owned)],
        "preserved_user_entries": [
            {"path": str(path), "enabled": existing[path]}
            for path in paths if path in existing
        ],
        "skipped": skipped, "changed": False, "dry_run": dry_run,
    }
    if command == "status":
        return report
    if command == "off":
        owned.update(path for path in paths if path not in existing)
        block = make_block(root, owned) if owned else b""
        # Keep the original block location on repeated calls, including when
        # the user has appended unrelated tables after it.
        replacement = raw if block == old_block else base + block
    else:
        replacement = base
        owned.clear()
    report["managed"] = [str(path) for path in sorted(owned)]
    report["changed"] = replacement != raw
    parse_config(replacement)
    if report["changed"] and not dry_run:
        atomic_write(config_path, raw, replacement, existed)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("off", "restore", "status"))
    parser.add_argument("directory", nargs="?", default=".")
    parser.add_argument("--dry-run", action="store_true", help="preview without writing config or a lock")
    parser.add_argument("--json", action="store_true", help="print machine-readable results")
    args = parser.parse_args(argv)
    try:
        codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser().resolve()
        config_path = (codex_home / "config.toml").resolve()
        root = project_root(args.directory)
        protected = protected_roots(codex_home)
        validate_root(root, protected)
        if args.command == "status" or args.dry_run:
            report = operate(args.command, root, config_path, protected, args.dry_run)
        else:
            with config_lock(config_path):
                report = operate(args.command, root, config_path, protected)
    except (Conflict, OSError, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Project: {report['project']}\nConfig: {report['config']}")
        print(f"Discovered: {len(report['discovered'])}; managed disabled paths: {len(report['managed'])}")
        for path in report["discovered"]:
            print(f"SKILL: {path}")
        for entry in report["preserved_user_entries"]:
            print(f"PRESERVED: {entry['path']} (enabled={str(entry['enabled']).lower()})")
        for message in report["skipped"]:
            print(f"SKIP: {message}")
        if args.command != "status":
            print("Would change config." if args.dry_run and report["changed"] else "Config changed." if report["changed"] else "No changes.")
            if report["changed"] and not args.dry_run:
                print("Restart Codex sessions using this CODEX_HOME to load the change.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
