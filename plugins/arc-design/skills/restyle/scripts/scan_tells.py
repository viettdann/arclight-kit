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

EXTS = {".html", ".htm", ".jsx", ".tsx", ".js", ".ts", ".mjs", ".cjs", ".vue", ".svelte", ".astro", ".mdx",
        ".css", ".scss", ".sass", ".less", ".erb", ".php", ".twig", ".liquid", ".njk", ".hbs", ".ejs", ".cshtml", ".razor"}
SKIP_DIRS = {"node_modules", "dist", "build", "out", "coverage", "vendor", "storybook-static", "__generated__"}
MAX_LINE = 2000  # longer lines are minified or generated; skip them

EMOJI = re.compile("[\U0001F1E6-\U0001F1FF\U0001F300-\U0001FAFF☀-➿⭐⭕⌚⌛⏩-⏳⏸-⏺]")
COLORS = r"(?:red|orange|amber|yellow|lime|green|emerald|teal|cyan|sky|blue|indigo|violet|purple|fuchsia|pink|rose)"
DISABLED = r"(?<![\w-])(?:v-bind)?:?disabled=[{\"]"

RULES = [
    # (principle, label, regex)
    ("1-color", "gradient", re.compile(r"\bbg-gradient-to-\w+|\bbg-(?:linear|radial|conic)(?:-[\w\[]|\b)|(?:linear|radial|conic)-gradient\(|\bbg-clip-text\b")),
    ("1-color", "glow/colored shadow", re.compile(r"\bshadow-(?:[a-z]+)-\d{3}(?:/\d+)?\b|drop-shadow-\[|\bshadow-\[0_0_[1-9]|(?<!\d\s)\b0 0 [1-9]\d*px\s+(?:rgba?\(|hsla?\(|#|oklch\()")),
    ("1-color", "pure black surface (near-black + layers?)", re.compile(r"^(?!.*(?<![\w-])(?:bg-)?opacity-\d).*?(?<![\w/-])bg-black(?![\w/-])|(?:background(?:-color)?:\s*|backgroundColor:\s*['\"]|bg-\[)(?:#000(?:000)?\b|black\b|rgb\(\s*0[\s,]+0[\s,]+0\s*\))")),
    ("2-decoration", "tinted tile/pill (decorative icon box or delta pill?)", re.compile(r"\bbg-" + COLORS + r"-\d{2,3}/(?:[5-9]|1\d|20)\b|\bbg-" + COLORS + r"-(?:50|100)\b(?=[^\"'`]*\btext-" + COLORS + r"-[4-8]00\b)")),
    ("3-hierarchy", "arbitrary font size (on the scale?)", re.compile(r"\btext-\[(?:\d+(?:\.\d+)?|\.\d+)(?:px|rem|em)\]|\bfontSize:\s*['\"]?\.?\d")),
    ("3-hierarchy", "weight above 600", re.compile(r"\bfont-(?:bold|extrabold|black)\b|font-weight:\s*(?:[7-9]00|bold(?:er)?)\b|\bfontWeight:\s*['\"]?(?:[7-9]00|bold)")),
    ("3-hierarchy", "weight other than 400/600 (500 or thin weights)", re.compile(r"\bfont-(?:thin|extralight|light|medium)\b|font-weight:\s*(?:[1-3]00|500)\b|\bfontWeight:\s*['\"]?(?:[1-3]00|500)\b")),
    ("2-decoration", "pulsing dot (signal needs silence)", re.compile(r"\banimate-ping\b|animation:\s*ping\b")),
    ("2-decoration", "zebra stripes (hairline + hover instead?)", re.compile(r"\b(?:even|odd):bg-|(?:\btr|\brow\w*|&)[^{,\s]*:nth-(?:child|of-type)\(\s*(?:even|odd|2n(?:\s*\+\s*1)?)\s*\)")),
    ("4-surface", "large radius (>=16px)", re.compile(r"\brounded(?:-[trblse]{1,2})?-(?:[2-4]xl|\[(?:1[6-9]|[2-9]\d)px\])(?![\w-])|border-radius:\s*(?:(?:1[6-9]|[2-9]\d)px|(?:1(?:\.\d+)?|[2-9](?:\.\d+)?)rem)")),
    ("4-surface", "shadow (ok only on overlays)", re.compile(r"(?<![\w-])shadow(?:-(?:2xs|xs|sm|md|lg|xl|2xl|inner))?(?![\w-])|box-shadow:(?!\s*none\b)|\bboxShadow:")),
    ("4-surface", "all corners rounded on an edge-flush element (rounded-t-*?)", re.compile(r"^(?=.*(?<![\w:-])fixed\b)(?=.*(?<![\w:-])(?:bottom-0|inset-x-0|inset-y-0)\b)(?=.*(?<![\w:-])rounded(?:-(?:sm|md|lg|xl|2xl|3xl))?(?![\w-]))")),
    ("4-surface", "glass on an in-page surface? (fine on fixed, sticky, or overlay layers)", re.compile(r"\bbackdrop-blur(?:-\w+)?\b|backdrop-filter:")),
    ("5-copy", "greeting / filler", re.compile(r"welcome back|good (?:morning|afternoon|evening)|here'?s what'?s happening|\bhello,|hi there|>\s*(?:hi|hey|hello)\b[\s,!]", re.I)),
    ("5-copy", "emoji in UI text", EMOJI),
    ("5-copy", "filler verb", re.compile(r"\b(?:elevate|seamless(?:ly)?|unleash|supercharge|next-gen|revolutioni[sz]e|game-?changer)\b", re.I)),
    ("5-copy", "placeholder name/text", re.compile(r"lorem ipsum|\bjohn doe\b|\bjane doe\b|(?<![@\w/-])acme\b(?![/-])", re.I)),
    ("6-marketing", "numbered eyebrow / tile counter", re.compile(r">\s*0\d{1,2}\s*(?:[/·.]|&middot;)\s*[A-Za-z]")),
    ("6-marketing", "scroll cue", re.compile(r"\bscroll\s+(?:down|to\s+(?:explore|discover|learn|see|continue|begin|start|view))\b|↓\s*scroll|>\s*scroll\s*<", re.I)),
    ("6-marketing", "saving as a percent (write it in money)", re.compile(r"\bsave\s+(?:up\s+to\s+)?\d+(?:\.\d+)?\s?%|\b\d+(?:\.\d+)?\s?%\s+off\b|>\s*[-−]\s?\d{1,2}\s?%\s*<", re.I)),
    ("7-code", "100vh (h-dvh for a fixed app shell, min-h-dvh for a full-height section)", re.compile(r"(?<![\w-])(?:min-|max-)?h-(?:screen\b|\[100vh\])|(?<![\w-])(?:min-|max-)?height:\s*100vh")),
    ("7-code", "scroll event listener", re.compile(r"addEventListener\(\s*['\"]scroll|\bonscroll\s*=")),
    ("7-code", "random color (hash a stable id instead?)", re.compile(r"(?:colou?r|\bbg\b|\bhue\b|palette|hsl|['\"`]#)[^;]*Math\.random\(\)|Math\.random\(\)[^;]*(?:colou?r|\bbg\b|\bhue\b|palette)", re.I)),
    ("7-code", "hand-rolled compact number (Intl.NumberFormat notation: 'compact'?)", re.compile(r"/\s*1(?:e[369]|_?000(?:_?000){0,2})\s*\)?\s*\.toFixed\(\d?\)\s*\}?\s*\+?\s*[`'\"]?\s*[KMBkmb](?![A-Za-z])|\.toFixed\(\d\)\s*\}?\s*\+?\s*[`'\"]?\s*[KMB](?![A-Za-z])")),
    ("7-code", "clipboard write not awaited (check before it lands, no fallback?)", re.compile(r"^(?!.*\b(?:await|return)\s+(?:window\.)?navigator\.clipboard\.writeText).*?\bnavigator\.clipboard\.writeText\((?:[^()]|\([^()]*\))*\)(?!\s*\.(?:then|catch))")),
    ("7-code", "scroll to top (on every route change? breaks Back)", re.compile(r"\bscrollTo\(\s*(?:0\s*,\s*0|\{[^}]*\btop:\s*0\b)")),
    ("7-code", "hard-coded header offset (scroll-padding-top?)", re.compile(r"\bscroll(?:To|By)?\([^;]*-\s*\d{2,3}\b(?!\s*[%*/])")),
    ("7-code", "mouse events for dragging (pointer events + setPointerCapture?)", re.compile(r"addEventListener\(\s*['\"]mouse(?:move|up)['\"]")),
    ("7-code", "indeterminate as an attribute (DOM property: set it via a ref)", re.compile(r"<input\b(?:[^>]|=>)*?(?<![:\w-])indeterminate\b")),
    ("7-code", "disabled for validity (validate on click instead?)", re.compile(DISABLED + r"[^}\"]*(?:!\s*(?:\w+\.)*\w*valid\w*|\bisValid\s*===?\s*false|!\s*\w+\s*\|\||!\s*(?:\w+\.)*can\w+)", re.I)),
    ("7-code", "disabled while busy (aria-busy + keep focus?)", re.compile(DISABLED + r"\s*(?:\w+\.)*(?:is)?(?:loading|pending|submitting|busy|saving)\w*\s*(?:[}\"]|\|\|)", re.I)),
    ("7-code", "column hidden by viewport (container query + expandable row?)", re.compile(r"(?<![\w:-])hidden\b(?=[^\"'`]*?(?<![\w-])(?:[\w-]+:)*(?:sm|md|lg|xl|2xl):table-cell\b)|(?<![\w-])max-(?:sm|md|lg|xl|2xl):hidden\b(?=[^\"'`]*\btable-cell\b)|<t[dh]\b[^>]*(?<![\w-])max-(?:sm|md|lg|xl|2xl):hidden\b")),
    ("7-code", "string cut in JS (truncate in CSS, keep the full text?)", re.compile(r"\.(?:slice|substring|substr)\(\s*0\s*,\s*[\w.]+(?:\s*[-+]\s*\d+)?\s*\)\s*(?:\+\s*['\"`]\s?|\}\s*)(?:\.\.\.|…)")),
    ("7-code", "break-all splits every word (overflow-wrap: anywhere?)", re.compile(r"(?<![\w-])break-all\b|word-break:\s*break-all")),
    ("7-code", "Enter handler without isComposing (IME users commit mid-word)", re.compile(r"^(?!.*isComposing).*(?:\bkey\s*===?\s*['\"]Enter['\"]|['\"]Enter['\"]\s*===?\s*(?:\w+\.)*key\b|@key(?:down|up|press)\.enter\b|\bcase\s+['\"]Enter['\"])")),
    ("7-code", "context menu blocked page-wide (only on its own objects?)", re.compile(r"(?:document|window|document\.body)\.(?:addEventListener\(\s*['\"]contextmenu['\"]|oncontextmenu\s*=)|\boncontextmenu=['\"]\s*return false")),
    ("7-code", "escalated z-index", re.compile(r"\bz-\[\d{3,}\]|z-index:\s*\d{3,}|\bzIndex:\s*\d{3,}")),
]

# 7-code hits that change handlers or behavior; the rest are presentation fixes.
BEHAVIOR = ("scroll event listener", "clipboard write", "scroll to top", "hard-coded header offset", "mouse events for dragging",
            "indeterminate as an attribute", "disabled for validity", "disabled while busy", "column hidden by viewport",
            "Enter handler", "context menu blocked")

FLOATING = re.compile(r"(?<![\w-])(?:fixed|sticky|absolute)\b|position:\s*['\"]?(?:fixed|sticky|absolute)")

# Context checks on nearby lines: (label prefix, regex, lines before, lines after).
SUPPRESS_NEAR = [
    ("Enter handler", re.compile(r"isComposing|keyCode\s*===?\s*229"), 6, 1),
    ("clipboard write", re.compile(r"^\s*\.(?:then|catch)\b"), 0, 1),
    # Glass on a layer that floats over moving content is the legitimate use (design materials.md).
    # Markup is checked on its own line; a stylesheet by its rule block (see css_block).
    ("glass on", FLOATING, 0, 0),
]
REQUIRE_NEAR = [
    ("scroll to top", re.compile(r"pathname|location|router|\$route|\bnavigat(?:e|ion)\b|afterEach|useEffect|watch\(", re.I), 4, 1),
]
# label -> (skip the hit when the context check returns this value, regex, before, after)
CONTEXT = {label: (want, rx, b, a) for _, label, _ in RULES
           for want, table in ((True, SUPPRESS_NEAR), (False, REQUIRE_NEAR)) for k, rx, b, a in table if label.startswith(k)}

MARKUP_EXTS = {".html", ".htm", ".jsx", ".tsx", ".vue", ".svelte", ".astro", ".mdx", ".erb", ".php",
               ".twig", ".liquid", ".njk", ".hbs", ".ejs", ".cshtml", ".razor"}
STYLE_EXTS = {".css", ".scss", ".sass", ".less"}
DASH = re.compile("[—–]|&[mn]dash;|&#821[12];")
# A lone dash is the placeholder for a missing table value, not copy.
LONE_DASH = re.compile("(?:>|['\"`])\\s*(?:[—–]|&[mn]dash;)\\s*(?:<|['\"`])")
# An unspaced en dash between two words or numbers is a range (Mon–Fri, 2020–2024), not a separator.
RANGE_DASH = re.compile(r"(?<=\w)(?:–|&ndash;|&#8211;)(?=\w)")
INLINE_COMMENT = re.compile(r"\{/\*.*?\*/\}|/\*.*?\*/|<!--.*?-->|(?<![:\"'])//.*$")
COMMENT = re.compile(r"^\s*(?://|/\*|\*|<!--|#|\{/\*)")
EYEBROW = re.compile(r"\buppercase\b[^\"'`]*\btracking-(?:wide|wider|widest|\[)|\btracking-(?:wide|wider|widest|\[)[^\"'`]*\buppercase\b")
NOT_EYEBROW = re.compile(r"<(?:th|td|dt|label|button|legend)\b", re.I)
SECTION = re.compile(r"<section\b")
TIER_CATEGORIES = [
    re.compile(r">\s*(?:most popular|popular|recommended|best value)\s*<", re.I),
    re.compile(r"\b(?:badge|label|tag)\s*[:=]\s*['\"](?:most popular|popular|recommended|best value)['\"]", re.I),
    re.compile(r"\b(?:popular|recommended|featured|highlight(?:ed)?)\s*:\s*true\b", re.I),
]
PRICING = re.compile(r"\b(?:prices?|pricing|tiers?|plans?)\b", re.I)
CTA_INTENTS = {
    "contact": ["get in touch", "contact us", "contact sales", "let's talk", "talk to us", "reach out", "book a call"],
    "signup": ["get started", "sign up", "try free", "try it free", "start free", "start for free", "start your trial", "create account"],
    "demo": ["book a demo", "request a demo", "get a demo", "see a demo", "schedule a demo"],
}

DELTA = re.compile(r"(?<![\w(,.\-])(?<!,\s)[+\-−]\s?\d+(?:\.\d+)?%(?!\s*[,)])")
NUMERIC_HINT = re.compile(r"\$\s?\d[\d,]*(?:\.\d+)?|\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b")


def iter_files(paths):
    for p in paths:
        if os.path.isfile(p):
            yield p
            continue
        for root, dirs, files in os.walk(p):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
            for f in files:
                if os.path.splitext(f)[1].lower() in EXTS and ".min." not in f:
                    yield os.path.join(root, f)


def near(lines, i, rx, before, after):
    return any(rx.search(l) for l in lines[max(0, i - 1 - before):i + after])


def css_block(lines, i):
    """The declarations of the rule that holds line i (1-based): from the last "{" above it to the next "}"."""
    start = next((j for j in range(i - 1, -1, -1) if "{" in lines[j]), i - 1)
    end = next((j for j in range(i - 1, len(lines)) if "}" in lines[j]), i - 1)
    return "".join(lines[start:end + 1])


def scan(paths):
    hits = defaultdict(list)
    deltas = Counter()
    delta_locs = defaultdict(list)
    tabular_files, numeric_files = set(), set()
    cta_seen = defaultdict(lambda: defaultdict(list))
    dir_sections = defaultdict(lambda: [0, []])
    skipped = 0

    for path in iter_files(paths):
        try:
            with open(path, encoding="utf-8", errors="ignore") as fh:
                lines = fh.readlines()
        except OSError:
            continue
        text = "".join(lines)
        ext = os.path.splitext(path)[1].lower()
        if "tabular-nums" in text or "font-variant-numeric" in text:
            tabular_files.add(path)
        markup = ext in MARKUP_EXTS
        if markup:
            agg = dir_sections[os.path.dirname(path)]
            agg[0] += len(SECTION.findall(text))
            agg[1] += [(path, i) for i, l in enumerate(lines, 1) if EYEBROW.search(l) and not NOT_EYEBROW.search(l)]
            low = text.lower()
            for intent, labels in CTA_INTENTS.items():
                for lab in labels:
                    if re.search(r">\s*" + re.escape(lab) + r"\b(?!\s+for\s+(?:our|the|updates|news))", low):
                        cta_seen[intent][lab].append(path)
        # Tier data often lives in a .ts/.js array, so this runs on every file.
        if PRICING.search(text):
            for rx in TIER_CATEGORIES:
                badges = [i for i, l in enumerate(lines, 1) if rx.search(l)]
                if len(badges) >= 2:
                    hits["6-marketing"].append({"file": path, "line": badges[0],
                                                "tell": f"{len(badges)} highlight badges (one tier only?)",
                                                "snippet": "lines " + ", ".join(map(str, badges[:8]))})
                    break
        for i, line in enumerate(lines, 1):
            if len(line) > MAX_LINE:
                skipped += 1
                continue
            snippet = line.strip()[:140]
            for principle, label, rx in RULES:
                if rx.search(line):
                    ctx = CONTEXT.get(label)
                    if ctx and near(lines, i, *ctx[1:]) == ctx[0]:
                        continue
                    if label.startswith("glass on") and ext in STYLE_EXTS and FLOATING.search(css_block(lines, i)):
                        continue
                    if principle == "7-code":
                        label = ("behavior: " if label.startswith(BEHAVIOR) else "presentation: ") + label
                    hits[principle].append({"file": path, "line": i, "tell": label, "snippet": snippet})
            if markup and DASH.search(line) and not COMMENT.match(line):
                copy = RANGE_DASH.sub("", LONE_DASH.sub("", INLINE_COMMENT.sub("", line)))
                if DASH.search(copy):
                    hits["6-marketing"].append({"file": path, "line": i, "tell": "em/en dash in copy", "snippet": snippet})
            if ext not in STYLE_EXTS:
                for d in DELTA.findall(line):
                    key = d.replace(" ", "").replace("−", "-")
                    deltas[key] += 1
                    delta_locs[key].append(f"{path}:{i}")
            if markup and NUMERIC_HINT.search(line):
                numeric_files.add(path)

    for d, (sections, eyebrows) in dir_sections.items():
        if sections >= 3 and len(eyebrows) > -(-sections // 3):
            hits["6-marketing"].append({"file": eyebrows[0][0], "line": eyebrows[0][1],
                                        "tell": f"{len(eyebrows)} uppercase tracked labels for {sections} sections (eyebrow on every section?)",
                                        "snippet": ", ".join(f"{os.path.basename(p)}:{i}" for p, i in eyebrows[:8])})
    for key, n in deltas.items():
        if n >= 3:
            hits["5-copy"].append({"file": delta_locs[key][0].rsplit(":", 1)[0], "line": int(delta_locs[key][0].rsplit(":", 1)[1]),
                                   "tell": f"identical delta '{key}' x{n} (placeholder?)", "snippet": ", ".join(delta_locs[key][:5])})
    for intent, labs in cta_seen.items():
        if len(labs) >= 2:
            first = next(iter(labs.values()))[0]
            hits["6-marketing"].append({"file": first, "line": 0,
                                        "tell": f"several labels for one CTA intent ({intent})",
                                        "snippet": "; ".join(f"{lab}: {', '.join(sorted(set(fs)))}" for lab, fs in sorted(labs.items()))})
    for f in sorted(numeric_files - tabular_files):
        hits["5-copy"].append({"file": f, "line": 0, "tell": "numbers without tabular-nums", "snippet": ""})
    if skipped:
        print(f"note: skipped {skipped} line(s) over {MAX_LINE} characters (minified or generated code)", file=sys.stderr)
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()
    missing = [p for p in args.paths if not os.path.exists(p)]
    if missing:
        ap.error("no such file or directory: " + ", ".join(missing))

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
