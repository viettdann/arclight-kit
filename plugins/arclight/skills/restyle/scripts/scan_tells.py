#!/usr/bin/env python3
"""Heuristic scanner for "AI tells" in UI code.

Prints candidates grouped by principle. It is a grep, not a verdict:
shadows on modals/popovers are correct, semantic status colors can be fine.

Usage: scan_tells.py <path> [<path> ...] [--json]
"""
import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

EXTS = {".html", ".htm", ".jsx", ".tsx", ".js", ".ts", ".vue", ".svelte", ".astro", ".css", ".scss", ".erb", ".php"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out", "coverage", "vendor", ".turbo"}

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")

RULES = [
    # (principle, label, regex)
    ("1-color", "gradient", re.compile(r"\bbg-gradient-to-\w+|\bbg-linear-to-\w+|linear-gradient\(|radial-gradient\(|\bbg-clip-text\b")),
    ("1-color", "glow/colored shadow", re.compile(r"\bshadow-(?:[a-z]+)-\d{3}(?:/\d+)?\b|drop-shadow-\[|0 0 \d+px rgba")),
    ("2-decoration", "tinted tile/pill (decorative icon box or delta pill?)", re.compile(r"\bbg-(?:red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-\d{2,3}/(?:5|10|15|20)\b")),
    ("4-surface", "large radius (>=16px)", re.compile(r"\brounded-(?:2xl|3xl)\b|border-radius:\s*(?:1[6-9]|[2-9]\d)px")),
    ("4-surface", "shadow (ok only on overlays)", re.compile(r"(?<![\w-])shadow(?:-(?:sm|md|lg|xl|2xl|inner))?(?![\w-])|box-shadow:")),
    ("4-surface", "glassmorphism", re.compile(r"\bbackdrop-blur(?:-\w+)?\b|backdrop-filter:")),
    ("5-copy", "greeting / filler", re.compile(r"welcome back|good (?:morning|afternoon|evening)|here'?s what'?s happening|hello,|hi there", re.I)),
    ("5-copy", "emoji in UI text", EMOJI),
]

DELTA = re.compile(r"[+\-−]\s?\d+(?:\.\d+)?%")
NUMERIC_HINT = re.compile(r"\$\s?\d[\d,]*(?:\.\d+)?|\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b")


def iter_files(paths):
    for p in paths:
        if os.path.isfile(p):
            yield p
            continue
        for root, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for f in files:
                if os.path.splitext(f)[1] in EXTS:
                    yield os.path.join(root, f)


def scan(paths):
    hits = defaultdict(list)
    deltas = Counter()
    delta_locs = defaultdict(list)
    tabular_files, numeric_files = set(), set()

    for path in iter_files(paths):
        try:
            with open(path, encoding="utf-8", errors="ignore") as fh:
                lines = fh.readlines()
        except OSError:
            continue
        text = "".join(lines)
        if "tabular-nums" in text or "font-variant-numeric" in text:
            tabular_files.add(path)
        for i, line in enumerate(lines, 1):
            snippet = line.strip()[:140]
            for principle, label, rx in RULES:
                if rx.search(line):
                    hits[principle].append({"file": path, "line": i, "tell": label, "snippet": snippet})
            for d in DELTA.findall(line):
                key = d.replace(" ", "").replace("−", "-")
                deltas[key] += 1
                delta_locs[key].append(f"{path}:{i}")
            if NUMERIC_HINT.search(line):
                numeric_files.add(path)

    for key, n in deltas.items():
        if n >= 3:
            hits["5-copy"].append({"file": delta_locs[key][0].rsplit(":", 1)[0], "line": int(delta_locs[key][0].rsplit(":", 1)[1]),
                                   "tell": f"identical delta '{key}' x{n} (placeholder?)", "snippet": ", ".join(delta_locs[key][:5])})
    for f in sorted(numeric_files - tabular_files):
        hits["5-copy"].append({"file": f, "line": 0, "tell": "numbers without tabular-nums", "snippet": ""})
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    hits = scan(args.paths)
    if args.json:
        json.dump(hits, sys.stdout, indent=2, ensure_ascii=False)
        print()
        return
    if not hits:
        print("No heuristic tells found. Still review hierarchy (identical cards) and copy by reading the code.")
        return
    total = sum(len(v) for v in hits.values())
    print(f"{total} candidate(s). Heuristic only: verify each (overlay shadows and real status colors are fine).\n")
    for principle in sorted(hits):
        print(f"== {principle} ==")
        for h in hits[principle]:
            loc = f"{h['file']}:{h['line']}" if h["line"] else h["file"]
            print(f"  {loc}  [{h['tell']}]  {h['snippet']}")
        print()
    print("Not detectable by grep: identical card grids (principle 3), decorative icons without tinted tiles, missing baselines/units on deltas.")


if __name__ == "__main__":
    main()
