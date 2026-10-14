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

MAX_BYTES = 2_000_000
LOCK_TTL = 86400
LOCK_DIR = os.path.join(tempfile.gettempdir(), f"dotnet-guard-{os.getuid() if hasattr(os, 'getuid') else 'user'}")
SKIP_PATH = re.compile(r"(^|/)(bin|obj|node_modules|\.git|packages)/|\.g\.cs$|\.g\.i\.cs$|\.generated\.cs$|\.Designer\.cs$")
TEST_FILE = re.compile(r"(Tests?|Specs?)\.cs$|(^|/)[^/]*\.(Unit|Integration|Functional|E2E)?Tests?/", re.I)

CS_RULES = [
    ("skipped test", re.compile(r"\[\s*(?:Fact|Theory|SkippableFact|SkippableTheory)\s*\([^\]]*\bSkip\s*=|[\[,]\s*(?:Ignore|Explicit)\s*[(\],]|\bAssert\.(?:Inconclusive|Ignore)\s*\(")),
    ("warning suppressed", re.compile(r"^\s*#pragma\s+warning\s+disable\b|\[\s*(?:assembly:\s*)?(?:System\.Diagnostics\.CodeAnalysis\.)?SuppressMessage(?:Attribute)?\s*\(|^\s*#nullable\s+disable\b")),
]
CS_TEST_RULES = [
    ("sleep in a test", re.compile(r"\bThread\.Sleep\s*\(|\bTask\.Delay\s*\(")),
]
EMPTY_CATCH = re.compile(r"\bcatch\b\s*(?:\([^)]*\))?\s*(?:when\s*\((?:[^()]|\([^()]*\))*\))?\s*\{(?:\s|//[^\n]*)*\}")
MSBUILD_RULES = [
    ("warning suppressed", re.compile(r"<NoWarn\b|\bNoWarn\s*=|<WarningsNotAsErrors\b|<TreatWarningsAsErrors>\s*false|<Nullable>\s*(?:disable|warnings)\b|<(?:RunAnalyzers|EnableNETAnalyzers|RunAnalyzersDuringBuild)>\s*false|<AnalysisMode>\s*None", re.I)),
    ("central package version bypassed", re.compile(r"\bVersionOverride\s*=|<ManagePackageVersionsCentrally>\s*false", re.I)),
]
EDITORCONFIG_RULES = [
    ("analyzer severity lowered", re.compile(r"^\s*dotnet_diagnostic\.[\w.-]+\.severity\s*=\s*(?:none|silent|suggestion)\b|^\s*dotnet_analyzer_diagnostic\.[\w.-]+\s*=\s*(?:none|silent)\b", re.I)),
]


def guard_enabled():
    value = os.environ.get("ARC_DOTNET_GUARD_ENABLED", "").strip() or "true"
    return value.lower() not in ("false", "0", "no", "off")


def rules_for(path):
    name = os.path.basename(path).lower()
    if name.endswith(".cs"):
        return CS_RULES + (CS_TEST_RULES if TEST_FILE.search(path) else []), True
    if name.endswith((".csproj", ".fsproj", ".vbproj", ".props", ".targets")):
        return MSBUILD_RULES, False
    if name in (".editorconfig", ".globalconfig") or name.endswith(".globalconfig"):
        return EDITORCONFIG_RULES, False
    return None, False


def findings(text, rules, csharp):
    found = []
    lines = text.split("\n")
    for i, line in enumerate(lines):
        for what, pattern in rules:
            if pattern.search(line):
                found.append((i, what, line.strip()))
    if csharp:
        for m in EMPTY_CATCH.finditer(text):
            i = text.count("\n", 0, m.start())
            found.append((i, "empty catch", " ".join(m.group(0).split())))
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


def added_findings(now, before):
    # Only a rise in an identical line's count is new, so moving or re-indenting an existing suppression never counts.
    extra = Counter((what, line) for _, what, line in now) - Counter((what, line) for _, what, line in before)
    picked = []
    for (what, line), count in extra.items():
        spots = sorted((i for i, w, l in now if w == what and l == line), reverse=True)
        picked.extend((i, what, line) for i in spots[:count])
    return sorted(picked)


def first_seen(key):
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
        lock = os.path.join(LOCK_DIR, hashlib.sha1(key.encode()).hexdigest())
        os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except FileExistsError:
        return False
    except OSError:
        return True
    return True


def legacy_main(payload):
    if not guard_enabled():
        return 0
    tool, tool_input = payload.get("tool_name"), payload.get("tool_input") or {}
    path = tool_input.get("file_path", "")
    if tool not in ("Edit", "Write") or not path or SKIP_PATH.search(path.replace(os.sep, "/")):
        return 0
    rules, csharp = rules_for(path)
    if rules is None or (tool == "Edit" and not tool_input.get("new_string")):
        return 0
    if not os.path.isfile(path) or os.path.getsize(path) > MAX_BYTES:
        return 0
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    now = findings(text, rules, csharp)
    if not now:
        return 0
    before = findings(previous_text(tool, tool_input, payload, path, text), rules, csharp)
    session = payload.get("session_id") or payload.get("transcript_path") or ""
    fresh = [f for f in added_findings(now, before) if first_seen(f"{session}|{path}|{f[1]}|{f[2]}")]
    if not fresh:
        return 0
    print("dotnet-guard: this edit hides a failure instead of fixing it:", file=sys.stderr)
    for i, what, line in fresh:
        print(f"{path}:{i + 1}: {what}: {line[:160]}", file=sys.stderr)
    print(
        "Undo each line and fix the cause: make the test pass, fix the warning, handle or rethrow the exception, "
        "wait on the condition instead of sleeping, align the central package version. "
        "Keep one only when the user asked for it or the cause is outside this code (a third-party analyzer bug, "
        "a test blocked by an external service); then add a comment on it with the reason and the tracking item, "
        "and tell the user in one line which one you kept and why.",
        file=sys.stderr,
    )
    return 2


def main():
    if not guard_enabled():
        return 0
    payload = json.load(sys.stdin)
    if payload.get("tool_name") != "apply_patch":
        return legacy_main(payload)
    from patch_inputs import changed_files
    session = payload.get("session_id") or payload.get("transcript_path") or ""
    reported = False
    for path, text, added, before in changed_files(payload):
        if SKIP_PATH.search(path.as_posix()):
            continue
        rules, csharp = rules_for(str(path))
        if rules is None:
            continue
        found = findings(text, rules, csharp)
        if csharp:
            for match in EMPTY_CATCH.finditer(text):
                start = text.count("\n", 0, match.start())
                end = text.count("\n", 0, match.end())
                if any(i in added for i in range(start, end + 1)):
                    added.add(start)
        extra = Counter((what, line) for _, what, line in added_findings(found, findings(before, rules, csharp)))
        for i, what, line in found:
            if i not in added or extra[(what, line)] <= 0 or not first_seen(f"{session}|{path}|{what}|{line}"):
                continue
            extra[(what, line)] -= 1
            if not reported:
                print("dotnet-guard: this edit hides a failure instead of fixing it:", file=sys.stderr)
            reported = True
            print(f"{path}:{i + 1}: {what}: {line[:160]}", file=sys.stderr)
    if reported:
        print("Fix the cause instead of suppressing it. Keep an exception only when authorized or blocked by an external cause; record the reason and tracking item.", file=sys.stderr)
    return 2 if reported else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
