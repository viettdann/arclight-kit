---
name: ui-check
description: "Measure rendering defects on a running page or static file at phone to wide widths: horizontal overflow and its cause, clipped or overlapping text, contrast per theme, focus without a visible state, unnamed controls, clickable elements a keyboard can't reach, targets under 24px, broken images, missing page language, blocked zoom, a lazy LCP image, JS errors and failed requests; optionally layout shifts, load timings and bytes against a baseline, and broken same-origin links. Use when the user asks to check, QA, or verify how a page renders (\"check the UI\", \"is anything broken\", \"kiểm tra giao diện\"), or before shipping a UI change; restyle and redesign run it last. Reports by impact, fixes only when asked. Not for taste (restyle), a new direction (redesign), component behavior (ui-interaction), or a control that does the wrong thing (state-check)."
---

# UI check

Before running checks, read `references/remediation-and-limits.md` for interpretation limits and remediation guidance. This skill reports findings; it fixes only when asked.

Resolve reference and script paths relative to this `SKILL.md`. Before running a helper from the project directory, replace its relative path with the absolute installed path; keep the project working directory so target paths resolve correctly. Read applicable `AGENTS.md` instructions first. Use the session’s available shell, file-editing, and image-viewing tools; load only the references needed for the task.

A page can pass every rule in its code and still break when it renders: a table pushes the page sideways at 375px, a label lands on a heading at 768px, a muted grey fails contrast only in the dark theme, a custom button loses its focus ring. These are measurable, so measure them instead of eyeballing a screenshot. This skill reports defects, not taste; taste is restyle's job.

## Workflow

1. **Target.** The URL of a dev server or staging site that is already running, or a static HTML file. With no target given, use a dev-server URL from the conversation or terminal output; otherwise ask for it. For an authorized local UI check, start the project's existing dev command when needed and stop only the process you started afterward. If dependencies or credentials are missing, report that limitation and continue static checks. A production URL is checked read-only. For a page behind login, ask for a session cookie or token and pass it with `--cookie` or `--header`; never log in with the user's password. As in the design skills, read only the current working tree (`../design/SKILL.md`, Sources).
2. **Run the check**, with screenshots in a temp dir:
   ```bash
   d=$(mktemp -d) && node ./scripts/ui_check.mjs <url-or-file> --shot "$d/shot.png"
   ```
   It loads the page at 375, 768, 1280, and 1920px (`--width` to change), light theme by default, and walks the first 40 Tab stops at 1280. Add `--scheme light,dark` when the project has a dark theme through `prefers-color-scheme`; a theme set by a class needs a second run with `--eval "document.documentElement.classList.add('dark')"`. Use `--wait-for <css>` for content that arrives after load (charts, fetched lists), `--eval "js"` to open the state to check (a tab, a modal, a later step), `--root <site-root>` for a local file that uses root-relative assets, `--full` for whole-page shots, `--perf` to add the largest-contentful-paint element and the elements that shift during load and print TTFB, FCP, LCP, long tasks and their blocking time (over 50ms each), JS and CSS bytes, and request count of one uncached load (lab values from this machine), `--save base.json` to store those numbers (median of 3 uncached loads) and the console messages as a baseline, `--compare base.json` to flag a timing up more than 50% and 500ms or JS or CSS bytes up more than 25% and 1 KB against it (same `--header` set in both runs) and report only console messages the baseline doesn't have and that appear in at least two loads, `--links` to request every same-origin link once (no fragments, mailto, tel, or logout, delete, cancel, or unsubscribe paths; at most 200) and report 4xx, 5xx, and failures, allowed only on localhost, a private IP, a docker service name, or a local file, `--cookie name=value` (repeatable or comma list) and `--header "Name: value"` (repeatable) for a page behind login, sent only to the target's origin, `--stress` to lengthen the text ~40% and inject unbroken strings, emoji, and CJK before checking (`--stress=rtl` also sets `dir=rtl`), `--json` for the full list. One run per URL and theme. Exit 0 means nothing at P1 or P2, 1 findings at P1 or P2, 2 the check couldn't run (no Node 22+, no Chrome, Chromium, or Edge, page unreachable); on 2, say what is missing and stop.
3. **Look at the screenshots** of every width for what the script can't measure. First impression: in the widest shot, name the first three things the eye lands on and confirm the primary action or content is among them; when it isn't, report it as P2 with what draws the eye instead. Then: elements detached from what they describe, large empty areas, a primary action off screen at 375px, sections in the wrong order. Confirm each `[review]` finding in the shot before reporting it, and drop it when it's intended (a badge meant to sit over an avatar, a caption positioned over a photo). For a hover state, use `node ../design/scripts/screenshot.mjs <url> out.png --hover <css>`.
4. **Report** in this shape, at most about ten lines, ordered by severity and then by how many users meet it:
   ```
   P1 overflow · 375, 768 · `table.invoices`: right edge 120px past the viewport → wrap it in an overflow-x: auto container
   P1 contrast · dark · `p.muted` "Due in 3 days": 2.9:1 (#6b6b6b on #18181b) → raise text-muted in the dark tokens
   ```
   One cause is one line, even when it shows at several widths or on several elements. End with one line naming what wasn't checked (no dark run, a page behind login without `--cookie` or `--header`, states not opened, no `--links`). No taste notes ("could use more whitespace"), no praise, no list of passed checks.
5. **Fix only when asked** (the `fix` argument, or the user asks after the report), then re-run the same command and report what is fixed and what remains. Fix the defects, nothing else: no restyle or redesign on the way.

## Fixing at the cause

For confirmed findings, use the cause-based remediation guidance in `references/remediation-and-limits.md`. Report first; fix only when asked.

## Severity

Rank findings P1–P3 using the severity definitions in `references/remediation-and-limits.md`; keep review candidates and checks that could not run explicit.

## Limits

Apply the measurement and interpretation limits in `references/remediation-and-limits.md`; distinguish measured failures from checks the environment could not run.
