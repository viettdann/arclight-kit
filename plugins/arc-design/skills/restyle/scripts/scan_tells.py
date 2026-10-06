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
QUOTED = re.compile(r"[\"'`]([^\"'`]*)[\"'`]")


class Check:
    """A rule matcher built from a function, for conditions one regex can't express."""
    def __init__(self, fn):
        self.search = fn


def same_string(*patterns):
    """True when every pattern hits inside one quoted string, i.e. on one element's class list."""
    rxs = [re.compile(p) for p in patterns]
    return lambda line: any(all(rx.search(s) for rx in rxs) for s in QUOTED.findall(line))


SIDE_TW = same_string(r"(?<![\w-])border-[lrse]-(?:[2-8]|\[[2-8]px\])(?![\w-])",
                      # A color under 40% alpha is a structural line, not an accent.
                      r"(?<![\w-])border-(?:[lrse]-)?(?:" + COLORS + r"-\d{2,3}|primary|accent|brand)(?![\w-]|/[1-3]?\d(?!\d))")
SIDE_CSS = re.compile(r"border-(?:left|right|inline-start|inline-end):\s*['\"]?[2-8]px\s+solid\s+([^;'\"}]+)", re.I)
NEUTRAL_COLOR = re.compile(r"transparent|currentcolor|inherit|gr[ae]y|silver|black|white|neutral|zinc|slate|stone|border|divider|muted|subtle|line", re.I)
HEX = re.compile(r"#([0-9a-f]{3,8})\b", re.I)
RGB = re.compile(r"rgba?\(\s*(\d+)[\s,]+(\d+)[\s,]+(\d+)")


def colored_side_border(line):
    if SIDE_TW(line):
        return True
    m = SIDE_CSS.search(line)
    if not m or NEUTRAL_COLOR.search(m[1]):
        return False
    h, rgb = HEX.search(m[1]), RGB.search(m[1])
    if h:
        s = h[1] if len(h[1]) > 4 else "".join(c * 2 for c in h[1])
        rgb = [int(s[k:k + 2], 16) for k in (0, 2, 4)]
    elif rgb:
        rgb = [int(v) for v in rgb.groups()]
    # Channels this close together are a grey hairline, not an accent.
    return not rgb or max(rgb) - min(rgb) >= 30


BEZIER = re.compile(r"cubic-bezier\(([^)]*)\)")


def overshoot_easing(line):
    for m in BEZIER.finditer(line):
        parts = m[1].replace("_", " ").split(",")
        try:
            y1, y2 = float(parts[1]), float(parts[3])
        except (IndexError, ValueError):
            continue
        if not (0 <= y1 <= 1 and 0 <= y2 <= 1):
            return True
    return False


# Only a scale-0 that animates is an entrance; a bare one hides an element for good.
ZERO_SCALE_TW = re.compile(r"(?<![\w-])(?:[\w\[\]=&-]+:)+scale-0(?![\w.-])")
BARE_SCALE_TW = [re.compile(r"(?<![\w:-])scale-0(?![\w.-])"), re.compile(r"(?<![\w-])(?:transition|animate-|duration-)")]
# `scale: 0 1` grows one axis (an underline), so only an all-zero value counts.
ZERO_SCALE = re.compile(r"(?<![\w-])scale\(\s*0(?:\.0+)?\s*(?:,\s*0(?:\.0+)?\s*)?\)|(?<![\w-])scale:\s*['\"]?0(?:\s+0)?(?![\w.%])(?!\s+[\w.-])")


def zero_scale(line):
    if "scale" not in line:
        return False
    if ZERO_SCALE.search(line):
        return True
    return any(ZERO_SCALE_TW.search(s) or all(rx.search(s) for rx in BARE_SCALE_TW) for s in QUOTED.findall(line))


SPACING_TW = re.compile(r"(?<![\w-])-?(?:p[xytrblse]?|m[xytrblse]?|gap(?:-[xy])?|space-[xy])-\[(\d+(?:\.\d+)?)px\]")
# The value ends at a quote, comma, or tag edge too, so a one-line JSX style object or HTML attribute doesn't run into the next declaration.
SPACING_CSS = re.compile(r"(?<![\w-])(?:padding|margin|gap|row-gap|column-gap)(?:-(?:top|right|bottom|left|inline|block)(?:-(?:start|end))?)?:\s*['\"`]?((?:[^;{}'\"`,<>()]|\([^()]*\))+)")
PX = re.compile(r"(?<![\w.])-?(\d+(?:\.\d+)?)px\b")


def off_grid(v):
    v = float(v)
    return v not in (1, 2) and v % 4 != 0


def off_scale_spacing(line):
    if any(off_grid(v) for v in SPACING_TW.findall(line)):
        return True
    return any(off_grid(v) for m in SPACING_CSS.finditer(line) for v in PX.findall(m[1]))


SMALL = r"(?:0\.5|1|1\.5|2|2\.5|3)"
# A skeleton bar is also round and pulsing; only a dot small on both axes is a status dot.
DOT_SIZE = (r"(?<![\w-])size-" + SMALL + r"(?![\w.-])|^(?=.*(?<![\w-])h-" + SMALL + r"(?![\w.-]))(?=.*(?<![\w-])w-" + SMALL + r"(?![\w.-]))")
PULSE_DOT = same_string(r"(?<![\w-])animate-pulse(?![\w-])", r"(?<![\w-])rounded-full(?![\w-])", DOT_SIZE)


def pulsing_dot(line):
    if re.search(r"\banimate-ping\b|animation:\s*ping\b", line):
        return True
    return "animate-pulse" in line and PULSE_DOT(line)


WIDE_SHADOW_TW = r"(?<![\w-])shadow-(?:xl|2xl)(?![\w-])|(?<![\w-])shadow-\[(?:-?[\d.]+(?:px)?_){2}(?:2[4-9]|[3-9]\d|\d{3})px"
HAIRLINE_SHADOW_TW = same_string(r"(?<![\w:-])border(?![\w-])", WIDE_SHADOW_TW)
WIDE_SHADOW_CSS = re.compile(r"box-?[sS]hadow:\s*['\"]?(?:inset\s+)?(?:-?[\d.]+(?:px|rem)?\s+){2}(?:2[4-9]|[3-9]\d|\d{3})px")
NEG_EM = r"-(?:0?\.(?:04\d*[1-9]|0[5-9]|[1-9])\d*|[1-9]\d*(?:\.\d+)?)em"
STOCK = r"\b(?:built for|meet your new|the future of)\b"

RULES = [
    # (principle, label, regex or Check)
    ("1-color", "gradient", re.compile(r"\bbg-gradient-to-\w+|\bbg-(?:linear|radial|conic)(?:-[\w\[]|\b)|(?:linear|radial|conic)-gradient\(|\bbg-clip-text\b")),
    ("1-color", "glow/colored shadow", re.compile(r"\bshadow-(?:[a-z]+)-\d{3}(?:/\d+)?\b|drop-shadow-\[|\bshadow-\[0_0_[1-9]|(?<!\d\s)\b0 0 [1-9]\d*px\s+(?:rgba?\(|hsla?\(|#|oklch\()")),
    ("1-color", "pure black surface (near-black + layers?)", re.compile(r"^(?!.*(?<![\w-])(?:bg-)?opacity-\d).*?(?<![\w/-])bg-black(?![\w/-])|(?:background(?:-color)?:\s*|backgroundColor:\s*['\"]|bg-\[)(?:#000(?:000)?\b|black\b|rgb\(\s*0[\s,]+0[\s,]+0\s*\))")),
    ("2-decoration", "tinted tile/pill (decorative icon box or delta pill?)", re.compile(r"\bbg-" + COLORS + r"-\d{2,3}/(?:[5-9]|1\d|20)\b|\bbg-" + COLORS + r"-(?:50|100)\b(?=[^\"'`]*\btext-" + COLORS + r"-[4-8]00\b)")),
    ("3-hierarchy", "arbitrary font size (on the scale?)", re.compile(r"\btext-\[(?:\d+(?:\.\d+)?|\.\d+)(?:px|rem|em)\]|\bfontSize:\s*['\"]?\.?\d")),
    ("3-hierarchy", "off the spacing scale (4px grid: p-3, gap-4, or a spacing token?)", Check(off_scale_spacing)),
    ("3-hierarchy", "weight above 600", re.compile(r"\bfont-(?:bold|extrabold|black)\b|font-weight:\s*(?:[7-9]00|bold(?:er)?)\b|\bfontWeight:\s*['\"]?(?:[7-9]00|bold)")),
    ("3-hierarchy", "weight other than 400/600 (500 or thin weights)", re.compile(r"\bfont-(?:thin|extralight|light|medium)\b|font-weight:\s*(?:[1-3]00|500)\b|\bfontWeight:\s*['\"]?(?:[1-3]00|500)\b")),
    ("3-hierarchy", "display tracking tighter than -0.04em", re.compile(r"(?<![\w-])tracking-tighter\b|(?<![\w-])tracking-\[" + NEG_EM + r"\]|letter-?[sS]pacing:\s*['\"]?" + NEG_EM)),
    ("3-hierarchy", "justified text (uneven word gaps; left-align?)", re.compile(r"text-align:\s*justify\b|(?<![\w-])text-justify(?![\w-])|textAlign:\s*['\"]justify")),
    ("2-decoration", "colored side border (accent bar on a card or block?)", Check(colored_side_border)),
    ("2-decoration", "pulsing dot (pulse only for real live state)", Check(pulsing_dot)),
    ("2-decoration", "blinking cursor (decorative typing effect)", re.compile(r"(?<![\w-])animate-(?:blink|caret|cursor)\b|(?<![\w-])animate-pulse\b[^<>]*>\s*(?:\||▍|▌|█|_|&#124;|\{['\"`][|▍▌█_]['\"`]\})\s*<|animation(?:-name)?:\s*['\"]?(?:blink|caret|cursor)[\w-]*")),
    ("2-decoration", "zebra stripes (hairline + hover instead?)", re.compile(r"\b(?:even|odd):bg-|(?:\btr|\brow\w*|&)[^{,\s]*:nth-(?:child|of-type)\(\s*(?:even|odd|2n(?:\s*\+\s*1)?)\s*\)")),
    ("4-surface", "large radius (>=16px)", re.compile(r"\brounded(?:-[trblse]{1,2})?-(?:[2-4]xl|\[(?:1[6-9]|[2-9]\d)px\])(?![\w-])|border-radius:\s*(?:(?:1[6-9]|[2-9]\d)px|(?:1(?:\.\d+)?|[2-9](?:\.\d+)?)rem)")),
    ("4-surface", "shadow (ok only on overlays)", re.compile(r"(?<![\w-])shadow(?:-(?:2xs|xs|sm|md|lg|xl|2xl|inner))?(?![\w-])|box-shadow:(?!\s*none\b)|\bboxShadow:")),
    ("4-surface", "hairline border plus a large shadow (double edge: keep one)", Check(lambda l: HAIRLINE_SHADOW_TW(l) or bool(WIDE_SHADOW_CSS.search(l)))),
    ("4-surface", "all corners rounded on an edge-flush element (rounded-t-*?)", re.compile(r"^(?=.*(?<![\w:-])fixed\b)(?=.*(?<![\w:-])(?:bottom-0|inset-x-0|inset-y-0)\b)(?=.*(?<![\w:-])rounded(?:-(?:sm|md|lg|xl|2xl|3xl))?(?![\w-]))")),
    ("4-surface", "glass on an in-page surface? (fine on fixed, sticky, or overlay layers)", re.compile(r"\bbackdrop-blur(?:-\w+)?\b|backdrop-filter:")),
    ("5-copy", "greeting / filler", re.compile(r"welcome back|good (?:morning|afternoon|evening)|here'?s what'?s happening|\bhello,|hi there|>\s*(?:hi|hey|hello)\b[\s,!]", re.I)),
    ("5-copy", "emoji in UI text", EMOJI),
    ("5-copy", "filler verb", re.compile(r"\b(?:elevate|seamless(?:ly)?|unleash|supercharge|next-gen|revolutioni[sz]e|game-?changer)\b", re.I)),
    ("5-copy", "placeholder name/text", re.compile(r"lorem ipsum|\bjohn doe\b|\bjane doe\b|(?<![@\w/-])acme\b(?![/-])", re.I)),
    ("6-marketing", "stock headline phrase (state the concrete outcome)", re.compile(STOCK, re.I)),
    ("6-marketing", "'Learn more' as the CTA label (name what the click gets)", re.compile(r">\s*learn more\s*(?:→|&rarr;|›|&rsaquo;|»|&raquo;|&gt;)?\s*<|\b(?:label|text|cta|title)\s*[:=]\s*['\"`]learn more['\"`]", re.I)),
    ("6-marketing", "numbered eyebrow / tile counter", re.compile(r">\s*0\d{1,2}\s*(?:[/·.]|&middot;)\s*[A-Za-z]")),
    ("6-marketing", "scroll cue", re.compile(r"\bscroll\s+(?:down|to\s+(?:explore|discover|learn|see|continue|begin|start|view))\b|↓\s*scroll|>\s*scroll\s*<", re.I)),
    ("6-marketing", "saving as a percent (write it in money)", re.compile(r"\bsave\s+(?:up\s+to\s+)?\d+(?:\.\d+)?\s?%|\b\d+(?:\.\d+)?\s?%\s+off\b|>\s*[-−]\s?\d{1,2}\s?%\s*<", re.I)),
    ("7-code", "100vh (h-dvh for a fixed app shell, min-h-svh for a full-height section)", re.compile(r"(?<![\w-])(?:min-|max-)?h-(?:screen\b|\[100vh\])|(?<![\w-])(?:min-|max-)?height:\s*100vh")),
    ("7-code", "scroll event listener", re.compile(r"addEventListener\(\s*['\"]scroll|\bonscroll\s*=")),
    ("7-code", "random color (hash a stable id instead?)", re.compile(r"(?:colou?r|\bbg\b|\bhue\b|palette|hsl|['\"`]#)[^;]*Math\.random\(\)|Math\.random\(\)[^;]*(?:colou?r|\bbg\b|\bhue\b|palette)", re.I)),
    ("7-code", "hand-rolled compact number (Intl.NumberFormat notation: 'compact'?)", re.compile(r"/\s*1(?:e[369]|_?000(?:_?000){0,2})\s*\)?\s*\.toFixed\(\d?\)\s*\}?\s*\+?\s*[`'\"]?\s*[KMBkmb](?![A-Za-z])|\.toFixed\(\d\)\s*\}?\s*\+?\s*[`'\"]?\s*[KMB](?![A-Za-z])")),
    ("7-code", "hand-rolled plural (Intl.PluralRules or the i18n library's plural)", re.compile(r"\?\s*(['\"`])s\1\s*:\s*(['\"`])\2|\?\s*(['\"`])\3\s*:\s*(['\"`])s\4|(?:[!=]==?|[<>]=?)\s*\d\s*\?\s*(['\"`])([A-Za-z][\w ]*?)\5\s*:\s*(['\"`])\6e?s\7|(?:[!=]==?|[<>]=?)\s*\d\s*\?\s*(['\"`])([A-Za-z][\w ]*?)e?s\8\s*:\s*(['\"`])\9\10")),
    # Both literals carry words and face the variable with a space, so keys, paths, and class lists don't match.
    ("7-code", "sentence built by concatenation (one translatable string with placeholders)", re.compile(r"^(?!.*\b(?:console|throw|Error|log(?:ger)?)\b).*(['\"])[^'\"]*[A-Za-z]{2}[^'\"]*\s\1\s*\+\s*[\w.$()\[\]]+\s*\+\s*(['\"])\s[^'\"]*[A-Za-z]{2}")),
    ("7-code", "fixed width on a text button (longer labels and translations overflow; min-w + padding?)", re.compile(r"<[Bb]utton\b[^<>]*?(?:(?<![\w-])w-\d+(?:\.5)?(?![\w-])|(?<![\w-])width:\s*['\"]?\d+(?:px)?\b)[^<>]*>\s*[^<>{}\s]*[A-Za-z]{2}[^<>]*<")),
    ("7-code", "pointer drag without pointercancel (a stolen gesture leaves it stuck mid-drag)", re.compile(r"^(?!.*removeEventListener).*pointer-?move", re.I)),
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
    ("7-code", "transition: all (list the properties)", re.compile(r"(?<![\w-])transition-all(?![\w-])|transition(?:-property)?:\s*['\"]?all\b|transitionProperty:\s*['\"]all\b")),
    ("7-code", "transition on a layout property (transform, or grid-template-rows for a collapse?)", re.compile(r"(?:transition(?:-property)?:|transitionProperty:)\s*['\"]?[^;'\"}]*?(?<![\w-])(?:max-|min-)?(?:width|height|top|left|right|bottom)\b|(?<![\w-])transition-\[[^\]]*?(?<![\w-])(?:max-|min-)?(?:width|height|top|left|right|bottom)\b")),
    ("7-code", "entrance from zero scale (enter from ~0.95 with opacity 0, see ui-interaction/references/motion.md)", Check(zero_scale)),
    ("7-code", "ease-in on a UI transition (delays the response: ease-out, --ease-exit for exits)", re.compile(r"(?<![\w-])(?:[\w\[\]=&-]+:)*ease-in(?![\w-])(?=[^\"'`]*[\"'`])|transition(?:-timing-function)?:[^;{}]*?(?<![\w-])ease-in(?![\w-])|transitionTimingFunction:\s*['\"]ease-in['\"]")),
    ("7-code", "bounce or overshoot easing (cubic-bezier y outside 0-1)", Check(overshoot_easing)),
    ("7-code", "outline removed with no focus-visible style in the file", re.compile(r"(?<![\w:-])outline-none(?![\w-])|(?<![\w-])outline:\s*['\"]?(?:none|0)(?![\w.-])")),
    ("7-code", "hidden reveal start state without a JS guard (blank if the script fails)", re.compile(r"(?<![\w-])opacity:\s*['\"]?0(?![\w.%])|(?<![\w:-])opacity-0(?![\w-])")),
    ("7-code", "escalated z-index", re.compile(r"\bz-\[\d{3,}\]|z-index:\s*\d{3,}|\bzIndex:\s*\d{3,}")),
]

# 7-code hits that change handlers or behavior; the rest are presentation fixes.
BEHAVIOR = ("scroll event listener", "clipboard write", "scroll to top", "hard-coded header offset", "mouse events for dragging",
            "indeterminate as an attribute", "disabled for validity", "disabled while busy", "column hidden by viewport",
            "Enter handler", "context menu blocked", "pointer drag")

FLOATING = re.compile(r"(?<![\w-])(?:fixed|sticky|absolute)\b|position:\s*['\"]?(?:fixed|sticky|absolute)")

# Context checks: (label prefix, regex, lines before, lines after, scope: False nearby lines, True a stylesheet hit's rule block, "file" the whole file).
SUPPRESS_NEAR = [
    ("Enter handler", re.compile(r"isComposing|keyCode\s*===?\s*229"), 6, 1, False),
    ("clipboard write", re.compile(r"^\s*\.(?:then|catch)\b"), 0, 1, False),
    # Glass on a layer that floats over moving content is the legitimate use (design materials.md).
    ("glass on", FLOATING, 0, 0, True),
    # A side border marking the current item or a quote is information, not an accent bar.
    ("colored side border", re.compile(r"aria-current|\bactive\b|isActive|selected|\bcurrent\b|blockquote"), 1, 0, True),
    # Floating layers (menus, dialogs, toasts) may pair a hairline with their shadow.
    ("hairline border plus", re.compile(FLOATING.pattern + r"|z-\[|z-index|\b(?:popover|menu|dropdown|dialog|modal|toast|tooltip)", re.I), 0, 0, True),
    # Overlay containers take programmatic focus and need no ring; list rows show focus as their highlighted state.
    ("outline removed", re.compile(r"\bfixed\b|tabIndex|tabindex|role=|origin-\[|shadow-(?:lg|xl|2xl)|animate-in|data-(?:open|closed)\b|data-\[state=|\bactive\b|highlighted|selected"), 0, 1, False),
    ("stock headline", re.compile(r"(?://|/\*|^\s*\*|<!--|^\s*#).*" + STOCK, re.I), 0, 0, False),
    # Keyframe start states are animations that run without JS.
    ("hidden reveal", re.compile(r"@keyframes|(?:^|[\s{])(?:from|to|\d+%)\s*\{"), 0, 0, True),
    ("outline removed", re.compile(r"focus-visible|focus(?:-within)?:(?:ring|border|shadow|bg-|text-|underline|outline-(?!none))|data-\[?highlighted|:focus\b[^{]*\{[^}]*(?:box-shadow|outline:(?!\s*(?:none|0\b)))"), 0, 0, "file"),
    ("pointer drag", re.compile(r"pointer-?cancel|lostpointercapture", re.I), 0, 0, "file"),
    # The marketing profile's guard: the hidden start state applies only once a script marked the page (`.js .reveal`).
    ("hidden reveal", re.compile(r"(?:^|[\s,{>~+])(?:html|:root|body)?\.js(?=[\s.,{:>\[])|\.no-js\b|\[data-js\]|<noscript\b|classList\.(?:add|remove|replace|toggle)\(\s*['\"](?:no-)?js['\"]", re.M), 0, 0, "file"),
]
REQUIRE_NEAR = [
    ("scroll to top", re.compile(r"pathname|location|router|\$route|\bnavigat(?:e|ion)\b|afterEach|useEffect|watch\(", re.I), 4, 1, False),
    ("hairline border plus", re.compile(r"(?<![\w:.-])border(?=[\s\"'`]|$)|border(?:-width)?:\s*['\"]?(?:1px|thin|0?\.5px)\b"), 0, 0, True),
    ("hidden reveal", re.compile(r"[Rr]eveal|(?<![a-z])in-?view|InView|data-aos|animate-on-scroll|scroll-?(?:anim|reveal|trigger)|data-animate|IntersectionObserver"), 1, 3, True),
    ("pointer drag", re.compile(r"pointer-?down", re.I), 0, 0, "file"),
    # A blink keyframe also drives busy indicators; only a caret or typing element makes it a cursor.
    ("blinking cursor", re.compile(r"caret|cursor(?!\s*:)|typ(?:ing|ewriter)|animate-"), 0, 0, True),
]
FILE_CHECKS = [rx for table in (SUPPRESS_NEAR, REQUIRE_NEAR) for _, rx, _, _, scope in table if scope == "file"]
# label -> [(skip the hit when the context check returns this value, regex, before, after, scope)]
CONTEXT = {label: [(want, rx, b, a, scope) for want, table in ((True, SUPPRESS_NEAR), (False, REQUIRE_NEAR))
                   for k, rx, b, a, scope in table if label.startswith(k)] for _, label, _ in RULES}

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
# A few dashes are punctuation; a file thick with them reads as generated, so only saturation is flagged.
DASH_MIN, DASH_MAX_CHARS = 8, 500
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

# Attribute values may hold ">" inside quotes or one level of nested JSX braces; a bare "<" and one-line quotes keep a stray "<" (a < b) from scanning to the end of the file.
TAG = re.compile(r"<(/?)([A-Za-z][\w.:-]*)((?:[^<>\"'{]|\"[^\"\n]*\"|'[^'\n]*'|\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})*?)(/?)>")
TEXT_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "figcaption", "dt", "dd"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
CENTER = re.compile(r"(?<![\w-])text-center(?![\w-])|text-align:\s*['\"]?center|textAlign:\s*['\"]center")
# Any explicit other alignment, at any breakpoint, counts as not centered.
NOT_CENTER = re.compile(r"(?<![\w-])text-(?:left|start|right|end|justify)(?![\w-])|text-align:\s*['\"]?(?:left|start|right|end|justify)|textAlign:\s*['\"](?:left|start|right|end|justify)")
CENTER_MIN_BLOCKS = 8


def centered_share(text):
    """(centered, total) text blocks in a markup file; a block inherits centering from its nearest aligned ancestor."""
    stack, centered, total = [], 0, 0
    for close, name, attrs, self_close in TAG.findall(text):
        name = name.lower()
        if close:
            k = next((k for k in range(len(stack) - 1, -1, -1) if stack[k][0] == name), None)
            if k is not None:
                del stack[k:]
            continue
        own = False if NOT_CENTER.search(attrs) else True if CENTER.search(attrs) else None
        here = own if own is not None else bool(stack and stack[-1][1])
        if name in TEXT_TAGS:
            total += 1
            centered += here
        if not self_close and name not in VOID_TAGS:
            stack.append((name, here))
    return centered, total


# react-icons bundles unrelated sets (fa, md, hi), so each subpath counts as its own library.
ICON_IMPORT = re.compile(r"""(?:\bfrom|\bimport|\brequire\()\s*\(?\s*['"](lucide-react|react-icons/\w+|@heroicons/react|@radix-ui/react-icons|@tabler/icons-react|@phosphor-icons/react|react-feather|@fortawesome|@mui/icons-material|iconoir-react)(?:/[^'"]*)?['"]""")


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


def skip_hit(label, lines, i, style, file_found):
    for want, rx, before, after, scope in CONTEXT[label]:
        if scope == "file":
            found = file_found[rx]
        else:
            found = bool(rx.search(css_block(lines, i))) if scope and style else near(lines, i, rx, before, after)
        if found == want:
            return True
    return False


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
        file_found = {rx: bool(rx.search(text)) for rx in FILE_CHECKS}
        if markup:
            agg = dir_sections[os.path.dirname(path)]
            agg[0] += len(SECTION.findall(text))
            agg[1] += [(path, i) for i, l in enumerate(lines, 1) if EYEBROW.search(l) and not NOT_EYEBROW.search(l)]
            centered, blocks = (0, 0) if any(len(l) > MAX_LINE for l in lines) else centered_share(text)
            if blocks >= CENTER_MIN_BLOCKS and centered > 0.6 * blocks:
                hits["3-hierarchy"].append({"file": path, "line": 0,
                                            "tell": f"{centered} of {blocks} text blocks centered (left-align body, lists, and long copy?)", "snippet": ""})
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
        icon_libs = {}
        # The file-level icon hit is reported ahead of this file's per-line hits, so output order stays stable.
        icon_at = len(hits.get("2-decoration", ()))
        dashes = []
        for i, line in enumerate(lines, 1):
            if len(line) > MAX_LINE:
                skipped += 1
                continue
            for lib in ICON_IMPORT.findall(line):
                icon_libs.setdefault(lib, i)
            snippet = line.strip()[:140]
            for principle, label, rx in RULES:
                if rx.search(line):
                    if skip_hit(label, lines, i, ext in STYLE_EXTS, file_found):
                        continue
                    if principle == "7-code":
                        label = ("behavior: " if label.startswith(BEHAVIOR) else "presentation: ") + label
                    hits[principle].append({"file": path, "line": i, "tell": label, "snippet": snippet})
            if markup and DASH.search(line) and not COMMENT.match(line):
                dashes += [i] * len(DASH.findall(RANGE_DASH.sub("", LONE_DASH.sub("", INLINE_COMMENT.sub("", line)))))
            if ext not in STYLE_EXTS:
                for d in DELTA.findall(line):
                    key = d.replace(" ", "").replace("−", "-")
                    deltas[key] += 1
                    delta_locs[key].append(f"{path}:{i}")
            if markup and NUMERIC_HINT.search(line):
                numeric_files.add(path)
        if len(icon_libs) >= 2:
            hits["2-decoration"].insert(icon_at, {"file": path, "line": min(icon_libs.values()),
                                                  "tell": f"{len(icon_libs)} icon libraries in one file (one library per surface, see design/references/icons.md)",
                                                  "snippet": ", ".join(sorted(icon_libs))})
        if len(dashes) >= DASH_MIN and len(text) <= DASH_MAX_CHARS * len(dashes):
            hits["6-marketing"].append({"file": path, "line": dashes[0], "tell": f"{len(dashes)} em/en dashes in copy, one per {len(text) // len(dashes)} chars (separators?)",
                                        "snippet": "lines " + ", ".join(map(str, sorted(set(dashes))[:8]))})

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
