#!/usr/bin/env python3
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter

from added_lines import SKIP_PATH, edit_added
from plugin_options import option

MAX_BYTES = 2_000_000
LOCK_TTL = 86400
LOCK_DIR = os.path.join(tempfile.gettempdir(), f"test-guard-{os.getuid() if hasattr(os, 'getuid') else 'user'}")
LOOKAHEAD = 3

TEST_FILE = re.compile(r"(^|[._-])(tests?|specs?)([._-]|$)|^[Tt]est(?=[A-Z0-9_.-])|(Tests?|Spec)\.[^.]+$")
PY, GO, SWIFT, PHP = {".py"}, {".go"}, {".swift"}, {".php"}
JS = {".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs", ".rb"}
ATTRIBUTED = {".cs", ".java", ".kt", ".kts", ".scala", ".rs", ".php"}
CODE_EXTS = PY | GO | SWIFT | PHP | JS | ATTRIBUTED

NAMED_CASE = [
    (PY, re.compile(r"^\s*(?:async\s+)?def\s+(test\w*)\s*\(")),
    (GO, re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?(Test(?:[A-Z0-9_]\w*)?)\s*\(")),
    (SWIFT, re.compile(r"^\s*func\s+(test\w*)\s*\(")),
    (PHP, re.compile(r"^\s*(?:(?:public|protected|private|static)\s+)*function\s+(test\w*)\s*\(")),
    (JS, re.compile(
        r"^\s*(?:it|test|specify)(?:\.(?:only|skip|each|concurrent|failing|todo|fixme|fails))*"
        r"(?:\(.*?\))?\s*\(?\s*(['\"`])(.+?)\1"
    )),
]
GO_NOT_CASES = {"TestMain"}
ATTRIBUTE_CASE = re.compile(
    r"^\s*(?:\[(?:Fact|Theory|Test|TestMethod|TestCase|DataTestMethod)\b[^\]]*\]"
    r"|@(?:Test|ParameterizedTest|RepeatedTest)\b(?:\([^)]*\))?"
    r"|#\[(?:[\w:\\]*[:\\])?[Tt]est\b[^\]]*\])"
)
STRING = re.compile(r"\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'")
DECLARED = re.compile(r"(?:fn|fun|def|void|[\w<>\[\],]+)\s+(\w+|`[^`]+`)\s*\(")


def guard_enabled():
    return option("test_guard_enabled", "true").lower() not in ("false", "0", "no", "off")


def case_name(line, ext):
    for exts, pattern in NAMED_CASE:
        m = pattern.match(line) if ext in exts else None
        if m and not (ext in GO and m.group(1) in GO_NOT_CASES):
            return m.group(m.lastindex)
    return None


def attribute_name(lines, i, ext):
    m = ATTRIBUTE_CASE.match(lines[i]) if ext in ATTRIBUTED else None
    if not m:
        return None
    for line in [lines[i][m.end():]] + lines[i + 1:i + 1 + LOOKAHEAD]:
        d = DECLARED.search(STRING.sub('""', line))
        if d:
            return d.group(1).strip("`")
    return f"test at line {i + 1}"


def cases(text, ext):
    lines = text.split("\n")
    found = []
    for i, line in enumerate(lines):
        name = case_name(line, ext) or attribute_name(lines, i, ext)
        if name:
            found.append((i, name))
    return found


def previous_text(tool, tool_input, payload, path, text):
    if tool == "Edit":
        new, old = tool_input.get("new_string", ""), tool_input.get("old_string", "")
        return text.replace(new, old) if tool_input.get("replace_all") else text.replace(new, old, 1)
    original = (payload.get("tool_response") or {}).get("originalFile")
    if isinstance(original, str):
        return original
    shown = subprocess.run(
        ["git", "-C", os.path.dirname(path) or ".", "show", f"HEAD:./{os.path.basename(path)}"],
        capture_output=True, text=True,
    )
    return shown.stdout if shown.returncode == 0 else ""


def new_cases(tool, tool_input, payload, path, text, ext):
    # Only a rise in a name's count is new, so editing, renaming, or moving an existing case never counts.
    now = cases(text, ext)
    before = cases(previous_text(tool, tool_input, payload, path, text), ext)
    extra = Counter(name for _, name in now) - Counter(name for _, name in before)
    if not extra:
        return []
    added = edit_added(text.split("\n"), text, tool_input) if tool == "Edit" else set()
    picked = []
    for name, count in extra.items():
        spots = sorted((i for i, n in now if n == name), key=lambda i: (i not in added, -i))
        picked.extend((i, name, sum(1 for j, n in now if n == name and j <= i)) for i in spots[:count])
    return sorted(picked)


def sweep_locks():
    try:
        os.makedirs(LOCK_DIR, exist_ok=True)
        now = time.time()
        for name in os.listdir(LOCK_DIR):
            stale = os.path.join(LOCK_DIR, name)
            try:
                if now - os.path.getmtime(stale) > LOCK_TTL:
                    os.remove(stale)
            except OSError:
                pass
    except OSError:
        pass


def first_seen(key):
    # Write may not carry the pre-write file, so a rewrite would otherwise re-ask about the same cases.
    try:
        lock = os.path.join(LOCK_DIR, hashlib.sha1(key.encode()).hexdigest())
        os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except FileExistsError:
        return False
    except OSError:
        return True
    return True


def main():
    if not guard_enabled():
        return 0
    payload = json.load(sys.stdin)
    tool, tool_input = payload.get("tool_name"), payload.get("tool_input") or {}
    path = tool_input.get("file_path", "")
    ext = os.path.splitext(path)[1].lower()
    if tool not in ("Edit", "Write") or SKIP_PATH.search(path):
        return 0
    if not TEST_FILE.search(os.path.basename(path)) or ext not in CODE_EXTS:
        return 0
    if tool == "Edit" and not tool_input.get("new_string"):
        return 0
    if os.path.getsize(path) > MAX_BYTES:
        return 0
    with open(path, encoding="utf-8") as f:
        text = f.read()
    found = new_cases(tool, tool_input, payload, path, text, ext)
    if not found:
        return 0
    sweep_locks()
    session = payload.get("session_id") or payload.get("transcript_path") or ""
    fresh = [(i, name) for i, name, nth in found if first_seen(f"{session}|{path}|{name}|{nth}")]
    if not fresh:
        return 0
    print("test-guard: new test cases:", file=sys.stderr)
    for i, name in fresh:
        print(f"{path}:{i + 1}: {name}", file=sys.stderr)
    print(
        "Keep a test only if you can name the plausible regression it catches: a fixed bug coming back, a branch or edge case, "
        "a public contract, an auth or security deny path, or, for a characterization test pinned before a refactor, "
        "the refactor changing current output on a path it touches.\n"
        "Junk: asserts a constant or string copied from the code, checks markup or style (a border, a class, a label), "
        "only checks that a function or command was called (exit, a mock), tests the framework or language, "
        "duplicates the type checker, passes whatever the code does, or repeats an existing test.\n"
        "The project's existing tests are not a reason to add one. Delete the junk now; for each test you keep, "
        "state in one line the regression it catches. If most of what you wrote is junk, ask whether this change "
        "needs a test at all; no test is a valid outcome.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
