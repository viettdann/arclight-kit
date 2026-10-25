#!/usr/bin/env python3
"""List hooks that existed before a redesign and are gone after it.

Compares two files or two directories; every file under a path is pooled,
so an item that moved between files counts as kept.
Wiring (FAIL): hrefs, ids, form field names, form actions, data-* attributes,
<title>, meta descriptions, canonical URLs, og:/twitter: share tags, event
handlers bound to a named function (`event=identifier`; arrow functions are
checked by hand), <script> srcs, and static DOM query selector strings.
Content (WARN): heading text, <img>/<Image> srcs, and currency or percent
figures in text.
Heuristic regex extraction: works on HTML, JSX/TSX, Vue, Svelte, Astro.
Skipped as presentation: anything inside <svg> (except handlers), `name` on
icon components, and <link> hrefs for stylesheets, fonts, preloads, and icons.

Usage: preserve_check.py <old-file-or-dir> <new-file-or-dir> [--json]
Exits 1 if wiring is missing, 0 if only content changed (still listed),
2 if a path is missing or the original has no wiring.
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
LINK = re.compile(r"<link\b[^>]*>", re.I)
TAG_ATTR = re.compile(r"""([\w:-]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|\{\s*["'`]([^"'`]*)["'`]\s*\})""")
META_API = re.compile(r"\b(?:export\s+const\s+metadata|generateMetadata|useHead|useSeoMeta|definePageMeta)\b")
META_LINK = re.compile(r"""\brel\s*:\s*["'`]canonical["'`]\s*,\s*href\s*:\s*(["'`])((?:(?!\1)[^\\]|\\.)*)\1""")
META_FIELD = re.compile(r"""\b(title|description|canonical)\s*:\s*(["'`])((?:(?!\2)[^\\]|\\.)*)\2""")
HANDLERS = [
    re.compile(r"\bon([A-Z]\w*)=\{\s*([\w.$]+)\s*\}"),  # JSX
    re.compile(r'(?<![\w:-])(?:@|v-on:)([\w:-]+)(?:\.[\w-]+)*="\s*([\w.$]+)\s*[("]'),  # Vue: a name or the function called
    re.compile(r"(?<![\w:-])on:([\w-]+)(?:\|[\w-]+)*=\{\s*([\w.$]+)\s*\}"),  # Svelte 4, modifiers allowed
    re.compile(r"(?<![\w:.-])on([a-z]+)=\{\s*([\w.$]+)\s*\}"),  # Svelte 5
    re.compile(r'\bon([a-z]+)="\s*(?:return\s+|void\s+)?([\w.$]+)\s*\('),  # HTML: the first function called
]
NOT_HANDLERS = {"true", "false", "null", "undefined"}
SCRIPT = re.compile(r"<script\b[^>]*>", re.I)
IMAGE = re.compile(r"<(?:img|Image)\b[^>]*>")
SELECTOR = re.compile(r"""\b(?:querySelector(?:All)?|getElementById|closest|matches)\(\s*(["'`])((?:(?!\1)[^\\]|\\.)*)\1\s*\)""")
HEADING = re.compile(r"<h([1-6])\b[^>]*>(.*?)</h\1\s*>", re.S | re.I)
INNER_TAG = re.compile(r"<[^>]*>")
TEXT_NODE = re.compile(r">([^<>]+)<")
FIGURES = [re.compile(r"[$€£¥]\s?\d[\d,.]*"), re.compile(r"\d[\d,.]*\s?%")]
WARN_KINDS = {"heading", "image", "figure"}
TAG_NAME = re.compile(r"<([\w.:-]+)")
CANONICAL_REL = re.compile(r"""\brel\s*=\s*["'{`]*\s*canonical\b""", re.I)
ASSET_REL = re.compile(r"""\brel\s*=\s*["'{`]*\s*(?:stylesheet|preconnect|preload|modulepreload|prefetch|dns-prefetch|(?:apple-touch-|mask-|shortcut )?icon)\b""", re.I)


def enclosing_tag(text, pos):
    """The tag name (lowercased) and source of the tag around pos, or (None, "")."""
    start = text.rfind("<", 0, pos)
    if start < 0:
        return None, ""
    end = text.find(">", pos)
    tag = text[start:end + 1 if end >= 0 else len(text)]
    m = TAG_NAME.match(tag)
    return (m.group(1).lower(), tag) if m else (None, "")


def presentation(text, pos, kind):
    """True for a match that is styling, not a hook: an icon component's name, an asset <link>'s href."""
    if kind not in ("name", "href"):
        return False
    name, tag = enclosing_tag(text, pos)
    if name is None:
        return False
    if kind == "name":
        return "icon" in name
    return name == "link" and bool(ASSET_REL.search(tag))


def canonical_link(text, pos):
    """True for the href of <link rel="canonical">, which is compared as `canonical`, not `href`."""
    name, tag = enclosing_tag(text, pos)
    return name == "link" and bool(CANONICAL_REL.search(tag))


def tag_attrs(tag):
    return {m.group(1).lower(): next(g for g in m.groups()[1:] if g is not None) for m in TAG_ATTR.finditer(tag)}


def static(value):
    return bool(value) and "{" not in value and "$" not in value


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
    kinds = [*PATTERNS, "title", "meta description", "canonical", "share tags", "handler", "script", "selector", "heading", "image", "figure"]
    found = {k: set() for k in kinds}
    for f in files(path):
        try:
            with open(f, encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
        except OSError:
            continue
        markup = SVG.sub("", text)
        for kind, rx in PATTERNS.items():
            for m in rx.finditer(markup):
                if presentation(markup, m.start(), kind) or (kind == "href" and canonical_link(markup, m.start())):
                    continue
                if kind == "data-*":
                    value = next(g for g in m.groups()[1:] if g is not None)
                    found[kind].add(f"{m.group(1)}={value}")
                else:
                    value = next((g for g in m.groups() if g is not None), "")
                    if static(value):
                        found[kind].add(value)
        found["name"].update(REGISTER.findall(text))
        found["title"].update(" ".join(t.split()) for t in TITLE.findall(SVG.sub("", text)))
        for tag in META.findall(text):
            attrs = tag_attrs(tag)
            if attrs.get("name", "").lower() == "description" and "content" in attrs:
                found["meta description"].add(attrs["content"])
            key = attrs.get("property") or attrs.get("name") or ""
            if key.lower().startswith(("og:", "twitter:")) and static(attrs.get("content", "")):
                found["share tags"].add(f"{key}={attrs['content']}")
        for tag in LINK.findall(markup):
            attrs = tag_attrs(tag)
            if CANONICAL_REL.search(tag) and static(attrs.get("href", "")):
                found["canonical"].add(attrs["href"])
        if META_API.search(text):
            for field, _, value in META_FIELD.findall(text):
                found[{"title": "title", "description": "meta description"}.get(field, "canonical")].add(value)
            for _, value in META_LINK.findall(text):
                found["canonical"].add(value)
        for rx in HANDLERS:
            for event, value in rx.findall(text):
                if value not in NOT_HANDLERS:
                    found["handler"].add(f"{event.lower()}={value}")
        for tag in SCRIPT.findall(markup):
            src = tag_attrs(tag).get("src", "")
            if static(src):
                found["script"].add(src)
        for quote, value in SELECTOR.findall(text):
            if value and not (quote == "`" and "${" in value):
                found["selector"].add(value)
        for _, inner in HEADING.findall(markup):
            heading = " ".join(INNER_TAG.sub(" ", inner).split())
            if heading and "{" not in heading:
                found["heading"].add(heading)
        for tag in IMAGE.findall(markup):
            src = tag_attrs(tag).get("src", "")
            if static(src):
                found["image"].add(src)
        for node in TEXT_NODE.findall(markup):
            if "{" not in node:
                # A sentence-final period or comma is punctuation, not part of the figure.
                found["figure"].update(m.rstrip(".,") for rx in FIGURES for m in rx.findall(node))
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
    if not any(old[k] for k in old if k not in WARN_KINDS):
        print(f"No hooks found in {args.old}: is it the snapshot of the source folder?", file=sys.stderr)
        sys.exit(2)
    total = sum(len(v) for v in old.values())
    lost = {k: sorted(old[k] - new[k]) for k in old if old[k] - new[k]}
    missing = {k: v for k, v in lost.items() if k not in WARN_KINDS}
    warn = {k: v for k, v in lost.items() if k in WARN_KINDS}
    kept = {k: [len(old[k] & new[k]), len(old[k])] for k in old if old[k]}
    if args.json:
        json.dump({"missing": missing, "warn": warn, "kept": kept}, sys.stdout, indent=2, ensure_ascii=False)
        print()
    else:
        for kind, (n, m) in kept.items():
            print(f"Kept {n}/{m} {kind}")
        print()
        if not lost:
            print(f"All {total} hooks from the original are still present.")
        for header, group in (("Present before, missing after (restore, or report as an intentional change):", missing),
                              ("Changed content (check each is intended):", warn)):
            if not group:
                continue
            print(header + "\n")
            for kind, values in group.items():
                print(f"== {kind} ==")
                for v in values:
                    print(f"  {v}")
                print()
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
