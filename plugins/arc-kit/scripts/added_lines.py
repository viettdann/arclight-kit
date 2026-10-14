import os
import re
import subprocess

SKIP_PATH = re.compile(
    r"(^|/)(node_modules|dist|build|vendor|\.git|\.venv|venv|target|coverage)/"
    r"|\.gen\.|\.generated\.|\.d\.ts$|\.min\.js$|(^|/)generated/"
)


def edit_added(lines, text, tool_input):
    new, old = tool_input.get("new_string", ""), tool_input.get("old_string", "")
    old_lines = set(old.split("\n"))
    fresh = {k for k, line in enumerate(new.split("\n")) if line not in old_lines and line.strip()}
    added, start = set(), text.find(new) if new else -1
    while start != -1:
        base = text.count("\n", 0, start)
        added.update(base + k for k in fresh)
        if not tool_input.get("replace_all"):
            break
        start = text.find(new, start + len(new))
    if not added:
        wanted = {new.split("\n")[k] for k in fresh}
        added = {i for i, line in enumerate(lines) if line in wanted}
    return added


def write_added(path, lines):
    cwd = os.path.dirname(path) or "."
    tracked = subprocess.run(
        ["git", "-C", cwd, "ls-files", "--error-unmatch", "--", path],
        capture_output=True, text=True,
    )
    if tracked.returncode != 0:
        return set(range(len(lines)))
    diff = subprocess.run(
        ["git", "-C", cwd, "diff", "-U0", "--no-color", "HEAD", "--", path],
        capture_output=True, text=True,
    )
    if diff.returncode != 0:
        return set(range(len(lines)))
    added = set()
    for m in re.finditer(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", diff.stdout, re.M):
        start, count = int(m.group(1)), int(m.group(2) or "1")
        added.update(range(start - 1, start - 1 + count))
    return added
