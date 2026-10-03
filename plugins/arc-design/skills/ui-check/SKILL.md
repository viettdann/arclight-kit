---
name: ui-check
description: "Measure rendering defects on a page that runs (dev server, staging, or a static file) at phone, tablet, desktop, and wide widths: horizontal overflow and its cause, clipped or overlapping text, contrast in each theme, focus without a visible state, unnamed controls, targets under 24px, broken or distorted images, missing page language, blocked zoom, a lazy LCP image, JS errors, failed requests, and optionally the LCP element and layout shifts. Use to check, QA, test, or verify how a UI renders (\"check the UI\", \"is anything broken\", \"test it on mobile\", \"kiểm tra giao diện\", \"xem có lỗi hiển thị không\") or before shipping a UI change; restyle and redesign run it last. Reports by impact; fixes only when asked. Not for taste (restyle), a new direction (redesign), component behavior (ui-interaction), or a control that does nothing (state-check)."
---

# UI check

Resolve reference and script paths relative to this `SKILL.md`. Before running a helper from the project directory, replace its relative path with the absolute installed path; keep the project working directory so target paths resolve correctly. Read applicable `AGENTS.md` instructions first. Use the session’s available shell, file-editing, and image-viewing tools; load only the references needed for the task.

A page can pass every rule in its code and still break when it renders: a table pushes the page sideways at 375px, a label lands on a heading at 768px, a muted grey fails contrast only in the dark theme, a custom button loses its focus ring. These are measurable, so measure them instead of eyeballing a screenshot. This skill reports defects, not taste; taste is restyle's job.

## Workflow

1. **Target.** The URL of a dev server or staging site that is already running, or a static HTML file. With no target given, use a dev-server URL from the conversation or terminal output; otherwise ask for it. For an authorized local UI check, start the project's existing dev command when needed and stop only the process you started afterward. If dependencies or credentials are missing, report that limitation and continue static checks. A production URL is checked read-only. As in the design skills, read only the current working tree (`../design/SKILL.md`, Sources).
2. **Run the check**, with screenshots in a temp dir:
   ```bash
   d=$(mktemp -d) && node ./scripts/ui_check.mjs <url-or-file> --shot "$d/shot.png"
   ```
   It loads the page at 375, 768, 1280, and 1920px (`--width` to change), light theme by default, and walks the first 40 Tab stops at 1280. Add `--scheme light,dark` when the project has a dark theme through `prefers-color-scheme`; a theme set by a class needs a second run with `--eval "document.documentElement.classList.add('dark')"`. Use `--wait-for <css>` for content that arrives after load (charts, fetched lists), `--eval "js"` to open the state to check (a tab, a modal, a later step), `--root <site-root>` for a local file that uses root-relative assets, `--full` for whole-page shots, `--perf` to add the largest-contentful-paint element and the elements that shift during load (lab values from this machine), `--json` for the full list. One run per URL and theme. Exit 0 means nothing at P1 or P2, 1 findings at P1 or P2, 2 the check couldn't run (no Node 22+, no Chrome, Chromium, or Edge, page unreachable); on 2, say what is missing and stop.
3. **Look at the screenshots** of every width for what the script can't measure: elements detached from what they describe, large empty areas, a primary action off screen at 375px, sections in the wrong order. Confirm each `[review]` finding in the shot before reporting it, and drop it when it's intended (a badge meant to sit over an avatar, a caption positioned over a photo). For a hover state, use `node ../design/scripts/screenshot.mjs <url> out.png --hover <css>`.
4. **Report** in this shape, at most about ten lines, ordered by severity and then by how many users meet it:
   ```
   P1 overflow · 375, 768 · `table.invoices`: right edge 120px past the viewport → wrap it in an overflow-x: auto container
   P1 contrast · dark · `p.muted` "Due in 3 days": 2.9:1 (#6b6b6b on #18181b) → raise text-muted in the dark tokens
   ```
   One cause is one line, even when it shows at several widths or on several elements. End with one line naming what wasn't checked (no dark run, a page behind login, states not opened). No taste notes ("could use more whitespace"), no praise, no list of passed checks.
5. **Fix only when asked** (the `fix` argument, or the user asks after the report), then re-run the same command and report what is fixed and what remains. Fix the defects, nothing else: no restyle or redesign on the way.

## Fixing at the cause

| Check | Usual cause | Fix |
| --- | --- | --- |
| `overflow` | fixed width, unbroken string, flex item without `min-w-0`, wide table or code block | Fix the element the script names: `min-w-0`, `overflow-wrap: anywhere`, a scroll container for tables and code. Never `overflow-x: hidden` on `html` or `body`: it hides the overflow and breaks `position: sticky` (the script still finds it). |
| `clipped`, `overlap` | fixed height, `whitespace-nowrap` without truncation, absolute positioning, display line-height under 1 | Ellipsis with `min-w-0`, or let it wrap; `typography.md` (Long text) |
| `contrast` | a muted or placeholder token, a light accent, a dark theme that wasn't checked | Change the token, not one usage; verify the new pair with `../design/scripts/contrast.mjs`. Over glass: `materials.md`. |
| `contrast-unmeasured` | text over an image, gradient, or glass | Check it in the shot; add a scrim or a solid surface behind the text if it fails |
| `focus` | `outline: none` without a replacement | A `:focus-visible` ring from the `focus-ring` token (`tokens.md`), drawn per `baseline.md` |
| `name`, `placeholder-label` | icon button without a label, field labelled by its placeholder | `aria-label` on icon buttons, a visible `<label>` above fields (ui-interaction `forms.md`) |
| `target`, `target-touch` | small icon buttons, default browser controls, tight links | Pad the hit area to 24px (44px for primary controls on phones) without changing the visual size (`baseline.md`) |
| `broken-image`, `distorted`, `alt` | wrong path, `object-fit` missing, no alt | Fix the path, `object-fit: cover` in a fixed-ratio frame (`cards.md`), `alt` text or `alt=""` for decoration |
| `js-error`, `console`, `request-asset`, `request` | a runtime error or a missing file | Report it with the message; fix only when the cause is in the UI code being checked |
| `heading`, `viewport`, `favicon` | structure | One `h1`, no skipped levels, `<meta name="viewport" content="width=device-width, initial-scale=1">` |
| `lang`, `zoom-blocked` | no `lang` on `<html>`; `maximum-scale=1` or `user-scalable=no` in the viewport meta | `<html lang="…">` with the page's language; drop the zoom limits |
| `lcp-lazy`, `lcp` | `loading="lazy"` on the image the page opens with | Remove `loading="lazy"` from it and add `fetchpriority="high"`; lazy-load only what starts below the fold |
| `layout-shift` | content above the shifted element that arrived late: an image without `width`/`height`, a banner or embed injected after load, a web font swap | Reserve the space (`width`/`height`, `aspect-ratio`, a min-height slot), or insert late content below the viewport (`baseline.md`, Layout stability) |

Reference paths: `typography.md`, `tokens.md`, `materials.md`, and `cards.md` are in `../design/references/`; `baseline.md` and `forms.md` in `../ui-interaction/references/`.

## Severity

- **P1:** breaks use or access: overflow, contrast failure, no visible focus, a control without a name, a broken image or asset, a JS exception.
- **P2:** degrades it: clipped or overlapping text, targets under 24px, a distorted image, a placeholder used as the label, no page language, blocked zoom, a lazy LCP image, layout shift over 0.1 during load, console errors, failed requests.
- **P3:** minor: primary-control touch targets under 44px on phones, missing alt, heading structure, missing viewport meta or favicon, contrast not measurable, the LCP element (`--perf`, information only).
- **`[review]`:** a heuristic (clipped, overlap, positioned-text contrast, failed fetch calls, touch targets, layout shift). Confirm it in the screenshot first; for touch targets, report only the primary controls among those listed.

## Limits

- It checks the first state of each page; menus, modals, and later steps need `--eval` or a URL that opens them.
- Contrast over images, gradients, and glass isn't measured; with known colors, `contrast.mjs` takes a stacked background (`"<text>|<tint> over <backdrop>"`).
- The focus check compares computed styles before and after focus; a ring drawn by a sibling element or a canvas isn't seen.
- `--perf` values come from one headless load on this machine, not field data; layout shift covers the load only, not later interactions, and Chrome may name a parent when several children move together.
- It catches the common measurable failures, not everything a screen reader test or an axe audit would.
