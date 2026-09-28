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
    ("1-color", "pure black surface (near-black + layers?)", re.compile(r"(?<![\w/-])bg-black(?![\w/-])|background(?:-color)?:\s*(?:#000(?:000)?\b|black\b|rgb\(\s*0[\s,]+0[\s,]+0\s*\))")),
    ("2-decoration", "tinted tile/pill (decorative icon box or delta pill?)", re.compile(r"\bbg-(?:red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)-\d{2,3}/(?:5|10|15|20)\b")),
    ("3-hierarchy", "arbitrary font size (on the scale?)", re.compile(r"\btext-\[\d+(?:\.\d+)?(?:px|rem)\]|\bfontSize:\s*['\"]?\d")),
    ("3-hierarchy", "weight above 600", re.compile(r"\bfont-(?:bold|extrabold|black)\b|font-weight:\s*(?:[7-9]00|bold(?:er)?)\b|\bfontWeight:\s*['\"]?(?:[7-9]00|bold)")),
    ("2-decoration", "pulsing dot (signal needs silence)", re.compile(r"\banimate-ping\b|animation:\s*ping\b")),
    ("2-decoration", "zebra stripes (hairline + hover instead?)", re.compile(r"\b(?:even|odd):bg-|:nth-child\(\s*(?:even|odd|2n\+?1?)\s*\)")),
    ("4-surface", "large radius (>=16px)", re.compile(r"\brounded-(?:2xl|3xl)\b|border-radius:\s*(?:1[6-9]|[2-9]\d)px")),
    ("4-surface", "shadow (ok only on overlays)", re.compile(r"(?<![\w-])shadow(?:-(?:sm|md|lg|xl|2xl|inner))?(?![\w-])|box-shadow:")),
    ("4-surface", "all corners rounded on an edge-flush element (rounded-t-*?)", re.compile(r"^(?=.*(?<![\w:-])fixed\b)(?=.*(?<![\w:-])(?:bottom-0|inset-x-0|inset-y-0)\b)(?=.*(?<![\w:-])rounded(?:-(?:sm|md|lg|xl|2xl|3xl))?(?![\w-]))")),
    ("4-surface", "glassmorphism", re.compile(r"\bbackdrop-blur(?:-\w+)?\b|backdrop-filter:")),
    ("5-copy", "greeting / filler", re.compile(r"welcome back|good (?:morning|afternoon|evening)|here'?s what'?s happening|hello,|hi there", re.I)),
    ("5-copy", "emoji in UI text", EMOJI),
    ("5-copy", "filler verb", re.compile(r"\b(?:elevate|seamless(?:ly)?|unleash|supercharge|next-gen|revolutioni[sz]e|game-?changer)\b", re.I)),
    ("5-copy", "placeholder name/text", re.compile(r"lorem ipsum|\bjohn doe\b|\bjane doe\b|\bacme\b", re.I)),
    ("6-marketing", "numbered eyebrow / tile counter", re.compile(r">\s*0\d{1,2}\s*(?:[/·.]|&middot;)\s*\w")),
    ("6-marketing", "scroll cue", re.compile(r"scroll (?:to|down)|↓\s*scroll|>\s*scroll\s*<", re.I)),
    ("6-marketing", "saving as a percent (write it in money)", re.compile(r"\bsave\s+(?:up\s+to\s+)?\d+(?:\.\d+)?\s?%|\b\d+(?:\.\d+)?\s?%\s+off\b|>\s*[-−]\s?\d+(?:\.\d+)?\s?%\s*<", re.I)),
    ("7-code", "100vh (use min-h-dvh)", re.compile(r"(?<![\w-])h-screen\b|(?<![\w-])height:\s*100vh")),
    ("7-code", "scroll event listener", re.compile(r"addEventListener\(\s*['\"]scroll")),
    ("7-code", "random color (hash a stable id instead?)", re.compile(r"Math\.random\(\).*\b(?:colou?rs?|bg|hue|palette)\b|\b(?:colou?rs?|bg|hue|palette)\b.*Math\.random\(\)", re.I)),
    ("7-code", "hand-rolled compact number (Intl.NumberFormat notation: 'compact'?)", re.compile(r"/\s*1(?:e[369]|_?000(?:_?000){0,2})\s*\)?\s*\.toFixed\(|\.toFixed\(\d\)\s*\}?\s*\+?\s*[`'\"]?\s*[KMB]\b[`'\"]")),
    ("7-code", "clipboard write not awaited (check before it lands, no fallback?)", re.compile(r"(?<!await )(?<!return )navigator\.clipboard\.writeText\((?:[^()]|\([^()]*\))*\)(?!\s*\.(?:then|catch))")),
    ("7-code", "scroll to top (on every route change? breaks Back)", re.compile(r"\bscrollTo\(\s*(?:0\s*,\s*0|\{\s*top:\s*0\b)")),
    ("7-code", "hard-coded header offset (scroll-padding-top?)", re.compile(r"\bscroll(?:To|By)?\(.*-\s*\d{2,3}\b(?!\s*[%*/])")),
    ("7-code", "mouse events for dragging (pointer events + setPointerCapture?)", re.compile(r"addEventListener\(\s*['\"]mouse(?:move|up)['\"]")),
    ("7-code", "indeterminate as an attribute (DOM property: set it via a ref)", re.compile(r"<input\b[^>]*\bindeterminate\b")),
    ("7-code", "disabled for validity (validate on click instead?)", re.compile(r"\bdisabled=\{[^}]*(?:!\s*(?:\w+\.)*(?:is)?valid\w*|\bisValid\s*===?\s*false|!\s*\w+\s*\|\|)", re.I)),
    ("7-code", "disabled while busy (aria-busy + keep focus?)", re.compile(r"\bdisabled=\{\s*(?:\w+\.)*(?:is)?(?:loading|pending|submitting|busy|saving)\w*\s*\}", re.I)),
    ("7-code", "column hidden by viewport (container query + expandable row?)", re.compile(r"\bhidden\s+(?:[a-z0-9]+:)*(?:sm|md|lg|xl):table-cell\b")),
    ("7-code", "string cut in JS (truncate in CSS, keep the full text?)", re.compile(r"\.(?:slice|substring|substr)\(\s*0\s*,\s*\w+\s*\)\s*(?:\+\s*['\"`]|\}\s*)(?:\.\.\.|…)")),
    ("7-code", "break-all splits every word (overflow-wrap: anywhere?)", re.compile(r"(?<![\w-])break-all\b|word-break:\s*break-all")),
    ("7-code", "Enter handler without isComposing (IME users commit mid-word)", re.compile(r"^(?!.*isComposing).*\bkey\s*===?\s*['\"]Enter['\"]")),
    ("7-code", "context menu blocked page-wide (only on its own objects?)", re.compile(r"(?:document|window|document\.body)\.(?:addEventListener\(\s*['\"]contextmenu['\"]|oncontextmenu\s*=)|\boncontextmenu=['\"]\s*return false")),
    ("7-code", "escalated z-index", re.compile(r"\bz-\[\d{3,}\]|z-index:\s*\d{3,}")),
]

MARKUP_EXTS = {".html", ".htm", ".jsx", ".tsx", ".vue", ".svelte", ".astro", ".erb", ".php"}
DASH = re.compile("[\u2014\u2013]")
# A lone dash is the placeholder for a missing table value, not copy.
LONE_DASH = re.compile("(?:>|['\"`])\\s*[\u2014\u2013]\\s*(?:<|['\"`])")
COMMENT = re.compile(r"^\s*(?://|/\*|\*|<!--|#)")
EYEBROW = re.compile(r"\buppercase\b[^\"'`]*\btracking-(?:wide|wider|widest|\[)|\btracking-(?:wide|wider|widest|\[)[^\"'`]*\buppercase\b")
SECTION = re.compile(r"<section\b")
TIER_BADGE = re.compile(r">\s*(?:most popular|popular|recommended|best value)\s*<"
                        r"|\b(?:badge|label|tag)\s*[:=]\s*['\"](?:most popular|popular|recommended|best value)['\"]"
                        r"|\b(?:popular|recommended|featured|highlight(?:ed)?)\s*:\s*true\b", re.I)
CTA_INTENTS = {
    "contact": ["get in touch", "contact us", "contact sales", "let's talk", "talk to us", "reach out", "book a call"],
    "signup": ["get started", "sign up", "try free", "try it free", "start free", "start for free", "start your trial", "create account"],
    "demo": ["book a demo", "request a demo", "get a demo", "see a demo", "schedule a demo"],
}

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
    cta_seen = defaultdict(lambda: defaultdict(list))

    for path in iter_files(paths):
        try:
            with open(path, encoding="utf-8", errors="ignore") as fh:
                lines = fh.readlines()
        except OSError:
            continue
        text = "".join(lines)
        if "tabular-nums" in text or "font-variant-numeric" in text:
            tabular_files.add(path)
        markup = os.path.splitext(path)[1] in MARKUP_EXTS
        if markup:
            sections = len(SECTION.findall(text))
            eyebrows = [i for i, l in enumerate(lines, 1) if EYEBROW.search(l)]
            if sections >= 3 and len(eyebrows) > -(-sections // 3):
                hits["6-marketing"].append({"file": path, "line": eyebrows[0],
                                            "tell": f"{len(eyebrows)} uppercase tracked labels for {sections} sections (eyebrow on every section?)",
                                            "snippet": "lines " + ", ".join(map(str, eyebrows[:8]))})
            low = text.lower()
            for intent, labels in CTA_INTENTS.items():
                for lab in labels:
                    if re.search(r">\s*" + re.escape(lab) + r"\b", low):
                        cta_seen[intent][lab].append(path)
        # Tier data often lives in a .ts/.js array, so this runs on every file.
        badges = [i for i, l in enumerate(lines, 1) if TIER_BADGE.search(l)]
        if len(badges) >= 2:
            hits["6-marketing"].append({"file": path, "line": badges[0],
                                        "tell": f"{len(badges)} highlight badges (one tier only?)",
                                        "snippet": "lines " + ", ".join(map(str, badges[:8]))})
        for i, line in enumerate(lines, 1):
            snippet = line.strip()[:140]
            for principle, label, rx in RULES:
                if rx.search(line):
                    hits[principle].append({"file": path, "line": i, "tell": label, "snippet": snippet})
            if markup and DASH.search(LONE_DASH.sub("", line)) and not COMMENT.match(line):
                hits["6-marketing"].append({"file": path, "line": i, "tell": "em/en dash in copy", "snippet": snippet})
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
    for intent, labs in cta_seen.items():
        if len(labs) >= 2:
            first = next(iter(labs.values()))[0]
            hits["6-marketing"].append({"file": first, "line": 0,
                                        "tell": f"several labels for one CTA intent ({intent})", "snippet": ", ".join(sorted(labs))})
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
    print("Not detectable by grep: identical card grids (principle 3), decorative icons without tinted tiles, missing baselines/units on deltas,"
          " repeated section layouts, div-built fake screenshots, pricing tiers that repeat the same feature list,"
          " an ellipsis blocked by a flex parent without min-w-0, awkward copy.")


if __name__ == "__main__":
    main()
