#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import os
import re
import sys

from plugin_options import option

DEFAULT_WIDTH = 150
WRAP_MIN = 60
MAX_BYTES = 2_000_000
MAX_MATCH_STATES = 256
MAX_MATCH_WORK = 4_000_000

def option(key, default):
    return os.environ.get(f"ARC_{key}", "").strip() or default


def lint_enabled():
    return option("comment_lint_enabled", "true").lower() not in ("false", "0", "no", "off")


def lint_width():
    try:
        return max(int(float(option("COMMENT_LINT_WIDTH", str(DEFAULT_WIDTH)))), WRAP_MIN)
    except (ValueError, OverflowError):
        return DEFAULT_WIDTH


WIDTH = lint_width()

SLASH_EXTS = {
    ".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs", ".go", ".rs",
    ".java", ".kt", ".kts", ".scala", ".cs", ".c", ".h", ".cc", ".cpp", ".hpp", ".swift", ".php",
}
HASH_EXTS = {".py", ".sh", ".bash", ".zsh", ".yml", ".yaml", ".toml", ".rb", ".tf", ".ps1"}
MD_EXTS = {".md", ".mdx"}

SKIP_PATH = re.compile(
    r"(^|/)(node_modules|dist|build|vendor|\.git|\.venv|venv|target|coverage)/"
    r"|\.gen\.|\.generated\.|\.d\.ts$|\.min\.js$|(^|/)generated/"
)
DIRECTIVE = re.compile(
    r"^(biome-ignore|@ts-|eslint|prettier|noqa|type:|pylint|nolint|go:|#|shellcheck|spdx|"
    r"istanbul|c8|-\*-|fmt:|isort|pragma|region|endregion|@vitest|@jest|jsx|<reference)",
    re.I,
)
URL = re.compile(r"https?://")
DIVIDER = re.compile(r"[-=*#/~_─━═]{4,}")
SENTENCE_END = re.compile(r"[.!?:]$")
LIST_ITEM = re.compile(r"^([-*•]|\d+[.)]|@\w)")
NARRATIVE_HEADING = re.compile(r"^#{1,6}\s+(rationale|background|alternatives)\b", re.I)
BLOCK_START = re.compile(r"^\s*/\*")
LICENSE = re.compile(r"license|copyright", re.I)


def line_comment(line, marker):
    pattern = r"^(\s*)//(?!/)\s?(.*)$" if marker == "//" else r"^(\s*)#(?![!#])\s?(.*)$"
    m = re.match(pattern, line)
    if not m or DIRECTIVE.match(m.group(2).strip()):
        return None
    return m.group(1), m.group(2).rstrip()


def parse_patch(command):
    """Read the apply_patch grammar; reject incomplete or unexpected input."""
    if not isinstance(command, str) or len(command.encode("utf-8")) > MAX_BYTES:
        return []
    rows = command.strip().splitlines()
    if len(rows) < 2 or rows[0] != "*** Begin Patch" or rows[-1] != "*** End Patch":
        return []
    operations, i = [], 1
    while i < len(rows) - 1:
        header = rows[i]
        kind = next((k for k in ("Add", "Update", "Delete") if header.startswith(f"*** {k} File: ")), None)
        if not kind:
            return []
        path = header.split(": ", 1)[1]
        i += 1
        if not path:
            return []
        if kind == "Delete":
            operations.append((path, path, kind, []))
            continue
        destination = path
        if kind == "Update" and rows[i].startswith("*** Move to: "):
            destination = rows[i][len("*** Move to: "):]
            i += 1
        hunks, body, anchor, eof = [], [], None, False
        while i < len(rows) - 1 and not rows[i].startswith(("*** Add File: ", "*** Update File: ", "*** Delete File: ")):
            row = rows[i]
            if kind == "Update" and (row == "@@" or row.startswith("@@ ")):
                if body:
                    hunks.append((body, anchor, eof))
                body, anchor, eof = [], row[3:] if row.startswith("@@ ") else None, False
            elif kind == "Update" and row == "*** End of File":
                eof = True
            elif not eof and (row and row[0] in ("+" if kind == "Add" else " +-") or not row and kind == "Update"):
                body.append(row or " ")
            else:
                return []
            i += 1
        if body:
            hunks.append((body, anchor, eof))
        operations.append((path, destination, kind, hunks))
    return operations


def matching_starts(lines, expected, start, eof):
    last = len(lines) - len(expected)
    candidates = [last] if eof else range(start, last + 1)
    if len(candidates) * len(expected) > MAX_MATCH_WORK:
        return []
    for normalize in (lambda s: s, str.rstrip, str.strip):
        matches = [
            i for i in candidates if i >= start
            and all(normalize(lines[i + j]) == normalize(row) for j, row in enumerate(expected))
        ]
        if matches:
            return matches
    return []


def patch_added(lines, hunks, kind):
    if kind == "Add":
        expected = [row[1:] for body, _, _ in hunks for row in body]
        return set(range(len(lines))) if lines == expected else set()
    # Intersect all valid placements: repeated context must not implicate old comments.
    states = {0: set()}
    for body, anchor, eof in hunks:
        expected = [row[1:] for row in body if row[0] != "-"]
        offsets = {j for j, row in enumerate(row for row in body if row[0] != "-") if row[0] == "+"}
        if not expected:
            continue
        next_states = {}
        for cursor, added in states.items():
            if anchor is not None:
                anchors = matching_starts(lines, [anchor], cursor, False)
                if not anchors:
                    continue
                cursor = anchors[0] + 1
            append = not any(row[0] in " -" for row in body)
            for start in matching_starts(lines, expected, cursor, eof or append):
                end = start + len(expected)
                located = added | {start + j for j in offsets}
                if end in next_states:
                    next_states[end] &= located
                else:
                    next_states[end] = located
                if len(next_states) > MAX_MATCH_STATES:
                    return set()
        states = next_states
        if not states:
            return set()
    return set.intersection(*states.values()) if states else set()


def read_source(root, name):
    if not isinstance(name, str) or not name:
        return None
    try:
        path = (root / name).resolve()
        relative = path.relative_to(root)
        ext = path.suffix.lower()
        if SKIP_PATH.search(relative.as_posix()) or ext not in SLASH_EXTS | HASH_EXTS | MD_EXTS:
            return None
        if not path.is_file() or path.stat().st_size > MAX_BYTES:
            return None
        with path.open(encoding="utf-8") as source:
            content = source.read(MAX_BYTES + 1)
        if len(content.encode("utf-8")) > MAX_BYTES:
            return None
        return path, ext, content.splitlines()
    except (OSError, ValueError, UnicodeError, RuntimeError):
        return None


def excerpt(text, limit=50):
    text = re.sub(r"^[\s/*#]+", "", text).strip()
    return text if len(text) <= limit else text[:limit].rstrip() + "..."


def check_code(lines, added, marker):
    found = []
    parsed = [line_comment(line, marker) for line in lines]
    for i in sorted(added):
        if i >= len(lines) or not parsed[i]:
            continue
        body, cols = parsed[i][1], len(lines[i].expandtabs(2))
        if cols > WIDTH and not URL.search(lines[i]):
            found.append((i, i, f"comment {cols} cols > {WIDTH}", excerpt(body)))
        if DIVIDER.search(body):
            found.append((i, i, "banner or divider comment", excerpt(body)))
    wraps = []
    for i in sorted({j for k in added for j in (k - 1, k)}):
        if i < 0 or i + 1 >= len(lines) or not parsed[i] or not parsed[i + 1]:
            continue
        (indent_a, body_a), (indent_b, body_b) = parsed[i], parsed[i + 1]
        if (
            indent_a == indent_b
            and len(lines[i].expandtabs(2)) >= WRAP_MIN
            and body_a
            and body_b
            and not SENTENCE_END.search(body_a)
            and not LIST_ITEM.match(body_b)
            and not body_b.startswith(" ")
            and not DIVIDER.search(body_a + body_b)
        ):
            if wraps and wraps[-1][1] == i:
                wraps[-1][1] = i + 1
            else:
                wraps.append([i, i + 1])
    found += [(a, b, "wrapped comment", excerpt(parsed[a][1])) for a, b in wraps]
    if marker == "//":
        i = 0
        while i < len(lines):
            if BLOCK_START.match(lines[i]) and "*/" not in lines[i]:
                end = next((j for j in range(i + 1, len(lines)) if "*/" in lines[j]), len(lines) - 1)
                block = lines[i : end + 1]
                if added & set(range(i, end + 1)) and not LICENSE.search("\n".join(block)):
                    text = next((excerpt(line) for line in block if excerpt(line)), "")
                    found.append((i, end, "multi-line block comment", text))
                i = end + 1
            else:
                i += 1
    return found


def check_markdown(lines, added):
    return [
        (i, i, "narrative section heading", excerpt(lines[i]))
        for i in sorted(added)
        if i < len(lines) and NARRATIVE_HEADING.match(lines[i])
    ]


def report(path, ext, lines, added):
    found = check_markdown(lines, added) if ext in MD_EXTS else check_code(lines, added, "//" if ext in SLASH_EXTS else "#")
    for start, end, message, text in sorted(found):
        span = f"{start + 1}-{end + 1}" if end > start else f"{start + 1}"
        print(f'{path}:{span}: {message} "{text}"', file=sys.stderr)
    return bool(found)


def main():
    parser = argparse.ArgumentParser(description="Lint comments added by a Codex apply_patch hook, or entire explicit workspace files.")
    parser.add_argument("--files", nargs="+", help="Lint all lines in these files, relative to the current directory; no Git diff is used.")
    args = parser.parse_args()
    if not lint_enabled():
        return 0
    violations = False
    if args.files:
        root = Path.cwd().resolve()
        for name in args.files:
            source = read_source(root, name)
            if source:
                path, ext, lines = source
                violations |= report(path, ext, lines, set(range(len(lines))))
    else:
        try:
            raw = sys.stdin.read(MAX_BYTES + 1)
            if len(raw.encode("utf-8")) > MAX_BYTES:
                return 0
            payload = json.loads(raw)
        except (ValueError, UnicodeError):
            return 0
        if not isinstance(payload, dict) or payload.get("tool_name") != "apply_patch":
            return 0
        tool_input, cwd = payload.get("tool_input"), payload.get("cwd")
        if not isinstance(tool_input, dict) or not isinstance(cwd, str) or not cwd or not Path(cwd).is_absolute():
            return 0
        try:
            root = Path(cwd).resolve()
        except (OSError, ValueError, RuntimeError):
            return 0
        operations = parse_patch(tool_input.get("command"))
        for _, destination, kind, hunks in operations:
            if kind == "Delete":
                continue
            source = read_source(root, destination)
            if source:
                path, ext, lines = source
                violations |= report(path, ext, lines, patch_added(lines, hunks, kind))
    if not violations:
        return 0
    print(
        f"Join each flagged comment onto one physical line (never wrap it; up to {WIDTH} columns is fine) "
        "stating the invariant, or delete it; drop narrative doc sections. Ignore false positives.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
