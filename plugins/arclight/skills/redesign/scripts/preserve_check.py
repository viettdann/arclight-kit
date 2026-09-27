#!/usr/bin/env python3
"""List hooks that existed before a redesign and are gone after it.

Compares hrefs, ids, form field names, form actions, data-* attributes,
<title>, and meta descriptions between two files or two directories.
Heuristic regex extraction: works on HTML, JSX/TSX, Vue, Svelte, Astro.

Usage: preserve_check.py <old-file-or-dir> <new-file-or-dir> [--json]
Exits 1 if anything is missing.
"""
import argparse
import json
import os
import re
import sys

EXTS = {".html", ".htm", ".jsx", ".tsx", ".js", ".ts", ".vue", ".svelte", ".astro", ".erb", ".php"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out", "coverage", "vendor", ".turbo"}

ATTR = r"""\s*=\s*(?:"([^"]*)"|'([^']*)'|\{\s*["'`]([^"'`]*)["'`]\s*\})"""
PATTERNS = {
    "href": re.compile(r"\bhref" + ATTR),
    "id": re.compile(r"\bid" + ATTR),
    "name": re.compile(r"\bname" + ATTR),
    "action": re.compile(r"\baction" + ATTR),
    "data-*": re.compile(r"\b(data-[\w-]+)" + ATTR),
}
TITLE = re.compile(r"<title>(.*?)</title>", re.S | re.I)
META_DESC = re.compile(r"<meta[^>]+name=[\"']description[\"'][^>]+content=[\"']([^\"']*)", re.I)


def files(path):
    if os.path.isfile(path):
        yield path
        return
    for root, dirs, fs in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in fs:
            if os.path.splitext(f)[1] in EXTS:
                yield os.path.join(root, f)


def extract(path):
    found = {k: set() for k in [*PATTERNS, "title", "meta description"]}
    for f in files(path):
        try:
            text = open(f, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        for kind, rx in PATTERNS.items():
            for m in rx.finditer(text):
                if kind == "data-*":
                    value = next(g for g in m.groups()[1:] if g is not None)
                    found[kind].add(f"{m.group(1)}={value}")
                else:
                    value = next((g for g in m.groups() if g is not None), "")
                    if value and "{" not in value and "$" not in value:
                        found[kind].add(value)
        found["title"].update(t.strip() for t in TITLE.findall(text))
        found["meta description"].update(META_DESC.findall(text))
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    old, new = extract(args.old), extract(args.new)
    missing = {k: sorted(old[k] - new[k]) for k in old if old[k] - new[k]}
    if args.json:
        json.dump({"missing": missing}, sys.stdout, indent=2, ensure_ascii=False)
        print()
    elif not missing:
        total = sum(len(v) for v in old.values())
        print(f"All {total} hooks from the original are still present.")
    else:
        print("Present before, missing after (restore, or report as an intentional change):\n")
        for kind, values in missing.items():
            print(f"== {kind} ==")
            for v in values:
                print(f"  {v}")
            print()
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
