# ui_check.mjs options

Every option beyond the defaults in step 2 of the workflow:

- `--wait-for <css>` for content that arrives after load (charts, fetched lists)
- `--eval "js"` to open the state to check (a tab, a modal, a later step)
- `--click <css>` (repeatable, in order) to click with the real pointer after `--eval` and check the state it opens; with `--perf`, it also reports each click's time to the next paint, split into input delay, processing, and presentation, plus layout shift more than 500ms after the click
- `--root <site-root>` for a local file that uses root-relative assets
- `--full` for whole-page shots
- `--perf` to add the largest-contentful-paint element and the elements that shift during load and print TTFB, FCP, LCP, long tasks and their blocking time (over 50ms each), JS and CSS bytes, and request count of one uncached load (lab values from this machine)
- `--save base.json` to store those numbers (median of 3 uncached loads) and the console messages as a baseline
- `--compare base.json` to flag a timing up more than 50% and 500ms or JS or CSS bytes up more than 25% and 1 KB against it (same `--header` set in both runs) and report only console messages the baseline doesn't have and that appear in at least two loads
- `--links` to request every same-origin link once (no fragments, mailto, tel, or logout, delete, cancel, or unsubscribe paths; at most 200) and report 4xx, 5xx, and failures, allowed only on localhost, a private IP, a docker service name, or a local file
- `--cookie name=value` (repeatable or comma list) and `--header "Name: value"` (repeatable) for a page behind login, sent only to the target's origin
- `--stress` to lengthen the text ~40% and inject unbroken strings, emoji, and CJK before checking
- `--stress=spacing` to apply the WCAG 1.4.12 text-spacing overrides instead (line-height 1.5, paragraphs 2em apart, letter-spacing 0.12em, word spacing 0.16em), so a `clipped`, `overlap`, or `overflow` it adds is content lost to user spacing settings (`--stress=text,spacing` for both)
- `--json` for the full list
