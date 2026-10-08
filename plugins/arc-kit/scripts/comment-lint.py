#!/usr/bin/env python3
import json
import os
import re
import sys
import tempfile
import time

from added_lines import SKIP_PATH, edit_added, write_added
from plugin_options import option

DEFAULT_WIDTH = 150
WRAP_MIN = 60
MAX_BYTES = 2_000_000
LOCK_TTL = 3600
LOCK_DIR = os.path.join(tempfile.gettempdir(), f"comment-lint-{os.getuid() if hasattr(os, 'getuid') else 'user'}")


def lint_enabled():
    return option("comment_lint_enabled", "true").lower() not in ("false", "0", "no", "off")


def lint_width():
    try:
        return max(int(float(option("comment_lint_width", str(DEFAULT_WIDTH)))), WRAP_MIN)
    except ValueError:
        return DEFAULT_WIDTH


WIDTH = lint_width()

SLASH_EXTS = {
    ".ts", ".tsx", ".mts", ".cts", ".js", ".jsx", ".mjs", ".cjs", ".go", ".rs",
    ".java", ".kt", ".kts", ".scala", ".cs", ".c", ".h", ".cc", ".cpp", ".hpp", ".swift", ".php",
}
HASH_EXTS = {".py", ".sh", ".bash", ".zsh", ".yml", ".yaml", ".toml", ".rb", ".tf", ".ps1"}
MD_EXTS = {".md", ".mdx"}

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


def claim(tool_use_id):
    if not tool_use_id:
        return True
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
        lock = os.path.join(LOCK_DIR, re.sub(r"[^\w-]", "_", tool_use_id))
        os.close(os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except FileExistsError:
        return False
    except OSError:
        return True
    return True


def main():
    if not lint_enabled():
        return 0
    payload = json.load(sys.stdin)
    tool, tool_input = payload.get("tool_name"), payload.get("tool_input") or {}
    path = tool_input.get("file_path", "")
    ext = os.path.splitext(path)[1].lower()
    if tool not in ("Edit", "Write") or SKIP_PATH.search(path):
        return 0
    if ext not in SLASH_EXTS | HASH_EXTS | MD_EXTS:
        return 0
    if os.path.getsize(path) > MAX_BYTES:
        return 0
    if not claim(payload.get("tool_use_id")):
        return 0
    with open(path, encoding="utf-8") as f:
        text = f.read()
    lines = text.split("\n")
    added = edit_added(lines, text, tool_input) if tool == "Edit" else write_added(path, lines)
    if not added:
        return 0
    if ext in MD_EXTS:
        found = check_markdown(lines, added)
    else:
        found = check_code(lines, added, "//" if ext in SLASH_EXTS else "#")
    if not found:
        return 0
    for start, end, message, text in sorted(found):
        span = f"{start + 1}-{end + 1}" if end > start else f"{start + 1}"
        print(f'{path}:{span}: {message} "{text}"', file=sys.stderr)
    print(
        f"Join each flagged comment onto one physical line (never wrap it; up to {WIDTH} columns is fine) "
        "stating the invariant, or delete it; drop narrative doc sections. Ignore false positives.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
