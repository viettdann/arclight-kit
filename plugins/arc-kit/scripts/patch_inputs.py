"""Read completed Codex patch results for advisory hooks."""
from pathlib import Path
import re
import patch_parser as PARSER

PARSER.SKIP_PATH = re.compile(r"(^|/)(node_modules|dist|build|vendor|\.git|\.venv|venv|target|coverage)/|\.gen\.|\.generated\.|\.d\.ts$|\.min\.js$|(^|/)generated/")


def changed_files(payload):
    if not isinstance(payload, dict) or payload.get("tool_name") != "apply_patch":
        return
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return
    root = Path(payload.get("cwd") or Path.cwd()).resolve()
    for source, destination, kind, hunks in PARSER.parse_patch(tool_input.get("command")):
        if kind == "Delete":
            continue
        try:
            path = (root / destination).resolve()
            relative = path.relative_to(root)
            if PARSER.SKIP_PATH.search(relative.as_posix()) or not path.is_file() or path.stat().st_size > PARSER.MAX_BYTES:
                continue
            text = path.read_text(encoding="utf-8")
            if len(text.encode("utf-8")) > PARSER.MAX_BYTES:
                continue
            lines = text.splitlines()
            added = PARSER.patch_added(lines, hunks, kind)
            before = PARSER.patch_before(lines, hunks, kind) if added else None
            if added and before is not None:
                yield path, text, added, before
        except (OSError, ValueError, UnicodeError, RuntimeError):
            continue
