#!/usr/bin/env python3
import json
from pathlib import Path
import re
import sys

SKILL = Path(__file__).resolve().parents[1] / "skills" / "arc" / "SKILL.md"
INVOKED = re.compile(r"(?<![\w$])\$arc(?![\w-])|\barc-kit:arc(?![\w-])|<name>arc</name>")


def user_texts(record):
    payload = record.get("payload", record) if isinstance(record, dict) else None
    if not isinstance(payload, dict):
        return
    if payload.get("type") == "user_message" and isinstance(payload.get("message"), str):
        yield payload["message"]
    if payload.get("role") == "user" and isinstance(payload.get("content"), list):
        for part in payload["content"]:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                yield part["text"]


def invoked(transcript):
    with transcript.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if any(INVOKED.search(text) for text in user_texts(record)):
                return True
    return False


def defaults():
    text = SKILL.read_text(encoding="utf-8")
    body = "\n".join(line for line in text[text.index("# Arc"):].splitlines() if not line.startswith("On invocation:"))
    return re.sub(r"\n{3,}", "\n\n", body).strip()


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    path = event.get("transcript_path") if isinstance(event, dict) else None
    if not isinstance(path, str) or not Path(path).is_file() or not invoked(Path(path)):
        return 0
    print("Arc daily defaults ($arc, invoked earlier in this session) still apply:\n")
    print(defaults())
    return 0


if __name__ == "__main__":
    sys.exit(main())
