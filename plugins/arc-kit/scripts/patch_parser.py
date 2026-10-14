"""Bounded apply_patch parser shared with arc-kit; keep parser behavior in sync."""
MAX_BYTES = 2_000_000
MAX_MATCH_STATES = 256
MAX_MATCH_WORK = 4_000_000

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


def patch_before(lines, hunks, kind):
    if kind == "Add":
        return ""
    previous, cursor = [], 0
    for body, anchor, eof in hunks:
        expected = [row[1:] for row in body if row[0] != "-"]
        if not expected:
            return None
        search_start = cursor
        if anchor is not None:
            anchors = matching_starts(lines, [anchor], cursor, False)
            if len(anchors) != 1:
                return None
            search_start = anchors[0] + 1
        append = not any(row[0] in " -" for row in body)
        starts = matching_starts(lines, expected, search_start, eof or append)
        if len(starts) != 1:
            return None
        start = starts[0]
        previous.extend(lines[cursor:start])
        previous.extend(row[1:] for row in body if row[0] != "+")
        cursor = start + len(expected)
    previous.extend(lines[cursor:])
    return "\n".join(previous)
