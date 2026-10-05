---
name: ui-check
description: "Measure rendering defects on a running page or static file at phone to wide widths: horizontal overflow and its cause, clipped or overlapping text, contrast per theme, focus without a visible state, unnamed controls, clickable elements a keyboard can't reach, targets under 24px, broken images, missing page language, blocked zoom, a lazy LCP image, JS errors and failed requests; optionally layout shifts, load timings and bytes against a baseline, and broken same-origin links. Use when the user asks to check, QA, or verify how a page renders (\"check the UI\", \"is anything broken\", \"kiểm tra giao diện\"), or before shipping a UI change; restyle and redesign run it last. Reports by impact, fixes only when asked. Not for taste (restyle), a new direction (redesign), component behavior (ui-interaction), or a control that does the wrong thing (state-check)."
argument-hint: "[url or file] [fix]"
---

# UI check

A page can pass every rule in its code and still break when it renders: a table pushes the page sideways at 375px, a label lands on a heading at 768px, a muted grey fails contrast only in the dark theme, a custom button loses its focus ring. These are measurable, so measure them instead of eyeballing a screenshot. This skill reports defects, not taste; taste is restyle's job.

## Workflow

1. **Target.** The URL of a dev server or staging site that is already running, or a static HTML file. With no target given, use a dev-server URL from the conversation or terminal output; otherwise ask for it. Don't start a server or install anything unless the user asks; if the page needs a server that isn't running, say so and stop. A production URL is checked read-only. For a page behind login, ask for a session cookie or token and pass it with `--cookie` or `--header`; never log in with the user's password. As in the design skills, read only the current working tree (`${CLAUDE_PLUGIN_ROOT}/skills/design/SKILL.md`, Sources).
2. **Run the check**, with screenshots in a temp dir:
   ```bash
   d=$(mktemp -d) && node ${CLAUDE_SKILL_DIR}/scripts/ui_check.mjs <url-or-file> --shot "$d/shot.png"
   ```
   It loads the page at 375, 768, 1280, and 1920px (`--width` to change), light theme by default, and walks the first 40 Tab stops at 1280. Add `--scheme light,dark` when the project has a dark theme through `prefers-color-scheme`; a theme set by a class needs a second run with `--eval "document.documentElement.classList.add('dark')"`. Use `--wait-for <css>` for content that arrives after load (charts, fetched lists), `--eval "js"` to open the state to check (a tab, a modal, a later step), `--root <site-root>` for a local file that uses root-relative assets, `--full` for whole-page shots, `--perf` to add the largest-contentful-paint element and the elements that shift during load and print TTFB, FCP, LCP, long tasks and their blocking time (over 50ms each), JS and CSS bytes, and request count of one uncached load (lab values from this machine), `--save base.json` to store those numbers (median of 3 uncached loads) and the console messages as a baseline, `--compare base.json` to flag a timing up more than 50% and 500ms or JS or CSS bytes up more than 25% and 1 KB against it (same `--header` set in both runs) and report only console messages the baseline doesn't have and that appear in at least two loads, `--links` to request every same-origin link once (no fragments, mailto, tel, or logout, delete, cancel, or unsubscribe paths; at most 200) and report 4xx, 5xx, and failures, allowed only on localhost, a private IP, a docker service name, or a local file, `--cookie name=value` (repeatable or comma list) and `--header "Name: value"` (repeatable) for a page behind login, sent only to the target's origin, `--stress` to lengthen the text ~40% and inject unbroken strings, emoji, and CJK before checking (`--stress=rtl` also sets `dir=rtl`), `--json` for the full list. One run per URL and theme. Exit 0 means nothing at P1 or P2, 1 findings at P1 or P2, 2 the check couldn't run (no Node 22+, no Chrome, Chromium, or Edge, page unreachable); on 2, say what is missing and stop.
3. **Look at the screenshots** of every width for what the script can't measure. First impression: in the widest shot, name the first three things the eye lands on and confirm the primary action or content is among them; when it isn't, report it as P2 with what draws the eye instead. Then: elements detached from what they describe, large empty areas, a primary action off screen at 375px, sections in the wrong order. Confirm each `[review]` finding in the shot before reporting it, and drop it when it's intended (a badge meant to sit over an avatar, a caption positioned over a photo). For a hover state, use `node ${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/screenshot.mjs <url> out.png --hover <css>`.
4. **Report** in this shape, at most about ten lines, ordered by severity and then by how many users meet it:
   ```
   P1 overflow · 375, 768 · `table.invoices`: right edge 120px past the viewport → wrap it in an overflow-x: auto container
   P1 contrast · dark · `p.muted` "Due in 3 days": 2.9:1 (#6b6b6b on #18181b) → raise text-muted in the dark tokens
   ```
   One cause is one line, even when it shows at several widths or on several elements. End with one line naming what wasn't checked (no dark run, a page behind login without `--cookie` or `--header`, states not opened, no `--links`). No taste notes ("could use more whitespace"), no praise, no list of passed checks.
5. **Fix only when asked** (the `fix` argument, or the user asks after the report), then re-run the same command and report what is fixed and what remains. Fix the defects, nothing else: no restyle or redesign on the way.

## Fixing at the cause

| Check | Usual cause | Fix |
| --- | --- | --- |
| `overflow` | fixed width, unbroken string, flex item without `min-w-0`, wide table or code block | Fix the element the script names: `min-w-0`, `overflow-wrap: anywhere`, a scroll container for tables and code. Never `overflow-x: hidden` on `html` or `body`: it hides the overflow and breaks `position: sticky` (the script still finds it). |
| `clipped`, `overlap` | fixed height, `whitespace-nowrap` without truncation, absolute positioning, display line-height under 1 | Ellipsis with `min-w-0`, or let it wrap; `typography.md` (Long text) |
| `contrast` | a muted or placeholder token, a light accent, a dark theme that wasn't checked | Change the token, not one usage; verify the new pair with `${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/contrast.mjs`. Over glass: `materials.md`. |
| `text-over-media-contrast`, `contrast-unmeasured` | text over an image, gradient, or glass (measured from screenshots for the first 20, the rest unmeasured) | Add a scrim or a solid surface behind the text; check unmeasured ones in the shot |
| `content-hidden-at-rest` | a reveal-on-scroll animation that never ran (wrong selector, observer threshold, JS error) | Start content visible and animate only when JS and motion allow it |
| `tiny-text`, `tight-leading`, `line-length`, `all-caps-body`, `wide-tracking`, `edge-flush-text` | body text under 12px (controls under 11px), line-height under 1.3, lines over 80ch, uppercase or tracking over 0.05em on running text, text under 16px from the viewport edge | `typography.md`: fix the type token or the container's max-width and padding |
| `nested-card`, `icon-tile`, `heading-rhythm` | a card inside a card, a framed icon square above each heading, a heading with less space above than below | Flatten the inner card to a divider or plain group, drop the tile frame, more space above the heading than below (restyle) |
| `clipped-popover` | a menu, popover, or tooltip inside an `overflow: hidden` container | Render it in a portal or the top layer (`popover`, `<dialog>`), or move the overflow off its ancestors |
| `clickable` | a `div` or `span` with `onclick`, a click listener, or `cursor: pointer` and no role or `tabindex` | Make it a `<button>` (an action) or `<a href>` (navigation); only when that is impossible, add a role, `tabindex="0"`, and Enter and Space handling |
| `focus` | `outline: none` without a replacement | A `:focus-visible` ring from the `focus-ring` token (`tokens.md`), drawn per `baseline.md` |
| `name`, `placeholder-label` | icon button without a label, field labelled by its placeholder | `aria-label` on icon buttons, a visible `<label>` above fields (ui-interaction `forms.md`) |
| `target`, `target-touch` | small icon buttons, default browser controls, tight links | Pad the hit area to 24px (44px for primary controls on phones) without changing the visual size (`baseline.md`) |
| `broken-image`, `distorted`, `alt` | wrong path, `object-fit` missing, no alt | Fix the path, `object-fit: cover` in a fixed-ratio frame (`cards.md`), `alt` text or `alt=""` for decoration |
| `js-error`, `console`, `request-asset`, `request` | a runtime error or a missing file | Report it with the message; fix only when the cause is in the UI code being checked |
| `heading`, `viewport`, `favicon` | structure | One `h1`, no skipped levels, `<meta name="viewport" content="width=device-width, initial-scale=1">` |
| `lang`, `zoom-blocked` | no `lang` on `<html>`; `maximum-scale=1` or `user-scalable=no` in the viewport meta | `<html lang="…">` with the page's language; drop the zoom limits |
| `broken-link` | a renamed or deleted route, a typo in a hard-coded path | Fix the `href` or restore the route; check the router for the same path elsewhere |
| `perf-regression` | a new dependency or an unsplit bundle, a blocking request added before render, an uncompressed asset, a slower server | Compare the request list of both versions; split, defer, or drop what was added. Re-run `--compare` a second time before reporting: one machine's timings vary |
| `lcp-lazy`, `lcp` | `loading="lazy"` on the image the page opens with | Remove `loading="lazy"` from it and add `fetchpriority="high"`; lazy-load only what starts below the fold |
| `layout-shift` | content above the shifted element that arrived late: an image without `width`/`height`, a banner or embed injected after load, a web font swap | Reserve the space (`width`/`height`, `aspect-ratio`, a min-height slot), or insert late content below the viewport (`baseline.md`, Layout stability) |

Reference paths: `typography.md`, `tokens.md`, `materials.md`, and `cards.md` are in `${CLAUDE_PLUGIN_ROOT}/skills/design/references/`; `baseline.md` and `forms.md` in `${CLAUDE_PLUGIN_ROOT}/skills/ui-interaction/references/`.

## Severity

- **P1:** breaks use or access: overflow, contrast failure (also over media), no visible focus, a control without a name, a clickable element without keyboard access, a broken image or asset, a JS exception.
- **P2:** degrades it: clipped or overlapping text, a clipped popover, text hidden after scroll, body text under 12px, targets under 24px, a distorted image, a placeholder used as the label, no page language, blocked zoom, a lazy LCP image, layout shift over 0.1 during load, console errors, failed requests, broken links, a perf regression against the baseline.
- **P3:** minor: primary-control touch targets under 44px on phones, missing alt, heading structure, missing viewport meta or favicon, contrast not measurable, the typography and layout heuristics (leading, line length, caps, tracking, edge, nested card, icon tile, heading rhythm), the LCP element (`--perf`, information only).
- **`[review]`:** a heuristic (clipped, overlap, positioned-text contrast, text-over-media contrast, the typography and layout heuristics, failed fetch calls, touch targets, layout shift, a clickable element found only by its pointer cursor). Confirm it in the screenshot first; for touch targets, report only the primary controls among those listed.

## Limits

- It checks the first state of each page; menus, modals, and later steps need `--eval` or a URL that opens them.
- Contrast over images, gradients, and glass is measured from two screenshots of at most 20 elements (with and without the text); the rest are listed as unmeasured, and with known colors, `contrast.mjs` takes a stacked background (`"<text>|<tint> over <backdrop>"`).
- The focus check compares computed styles before and after focus; a ring drawn by a sibling element or a canvas isn't seen.
- `--perf`, `--save`, and `--compare` values come from headless loads on this machine, not field data; compare only baselines taken on the same machine and URL; layout shift covers the load only, not later interactions, and Chrome may name a parent when several children move together.
- The clickable check misses handlers delegated to a parent (React attaches them at the root); `--links` checks only links present in the first state, and treats a redirect as fine.
- It catches the common measurable failures, not everything a screen reader test or an axe audit would.
