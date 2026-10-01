#!/usr/bin/env python3
"""List hooks that existed before a redesign and are gone after it.

Compares hrefs, ids, form field names, form actions, data-* attributes,
<title>, and meta descriptions between two files or two directories.
Heuristic regex extraction: works on HTML, JSX/TSX, Vue, Svelte, Astro.

Usage: preserve_check.py <old-file-or-dir> <new-file-or-dir> [--json]
Exits 1 if anything is missing, 2 if a path is missing or the original has no hooks.
"""
import argparse
import json
import os
import re
import sys

EXTS = {".html", ".htm", ".jsx", ".tsx", ".js", ".ts", ".vue", ".svelte", ".astro", ".mdx", ".erb", ".php"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out", "coverage", "vendor", ".turbo"}

VALUE = r"""\s*=\s*(?:"([^"]*)"|'([^']*)'|\{\s*["'`]([^"'`]*)["'`]\s*\})"""
# Skip longer names (data-id), Vue/Svelte bindings (:href, bind:name), and JS assignments (const name = "x", el.id = "x").
LEAD = r"(?<![\w:.@-])(?<!const )(?<!let )(?<!var )"
PATTERNS = {
    "href": re.compile(LEAD + r"href" + VALUE),
    "id": re.compile(LEAD + r"id" + VALUE),
    "name": re.compile(LEAD + r"name" + VALUE),
    "action": re.compile(LEAD + r"action" + VALUE),
    "data-*": re.compile(LEAD + r"(data-[\w-]+)" + VALUE),
}
REGISTER = re.compile(r"""\bregister\(\s*["'`]([^"'`$]+)["'`]""")  # react-hook-form field names
TITLE = re.compile(r"<title>(.*?)</title>", re.S | re.I)
SVG = re.compile(r"<svg\b.*?</svg>", re.S | re.I)
META = re.compile(r"<meta\b[^>]*>", re.I)
TAG_ATTR = re.compile(r"""([\w:-]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|\{\s*["'`]([^"'`]*)["'`]\s*\})""")
META_API = re.compile(r"\b(?:export\s+const\s+metadata|generateMetadata|useHead|useSeoMeta|definePageMeta)\b")
META_FIELD = re.compile(r"""\b(title|description)\s*:\s*(["'`])((?:(?!\2)[^\\]|\\.)*)\2""")


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
            with open(f, encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
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
        found["name"].update(REGISTER.findall(text))
        found["title"].update(" ".join(t.split()) for t in TITLE.findall(SVG.sub("", text)))
        for tag in META.findall(text):
            attrs = {m.group(1).lower(): next(g for g in m.groups()[1:] if g is not None) for m in TAG_ATTR.finditer(tag)}
            if attrs.get("name", "").lower() == "description" and "content" in attrs:
                found["meta description"].add(attrs["content"])
        if META_API.search(text):
            for field, _, value in META_FIELD.findall(text):
                found["title" if field == "title" else "meta description"].add(value)
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    for p in (args.old, args.new):
        if not os.path.exists(p):
            ap.error(f"no such file or directory: {p}")

    old, new = extract(args.old), extract(args.new)
    total = sum(len(v) for v in old.values())
    if total == 0:
        print(f"No hooks found in {args.old}: is it the snapshot of the source folder?", file=sys.stderr)
        sys.exit(2)
    missing = {k: sorted(old[k] - new[k]) for k in old if old[k] - new[k]}
    if args.json:
        json.dump({"missing": missing}, sys.stdout, indent=2, ensure_ascii=False)
        print()
    elif not missing:
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
