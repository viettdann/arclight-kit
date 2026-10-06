# Ui Check detailed instructions

Resolve all relative paths in this reference from the parent skill directory containing `SKILL.md`, not from `references/`.

## Fixing at the cause

| Check | Usual cause | Fix |
| --- | --- | --- |
| `overflow` | fixed width, unbroken string, flex item without `min-w-0`, wide table or code block | Fix the element the script names: `min-w-0`, `overflow-wrap: anywhere`, a scroll container for tables and code. Never `overflow-x: hidden` on `html` or `body`: it hides the overflow and breaks `position: sticky` (the script still finds it). |
| `clipped`, `overlap` | fixed height, `whitespace-nowrap` without truncation, absolute positioning, display line-height under 1 | Ellipsis with `min-w-0`, or let it wrap; `typography.md` (Long text) |
| `contrast` | a muted or placeholder token, a light accent, a dark theme that wasn't checked | Change the token, not one usage; verify the new pair with `../design/scripts/contrast.mjs`. Over glass: `materials.md`. |
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

Reference paths: `typography.md`, `tokens.md`, `materials.md`, and `cards.md` are in `../design/references/`; `baseline.md` and `forms.md` in `../ui-interaction/references/`.

## Limits

- It checks the first state of each page; menus, modals, and later steps need `--eval` or a URL that opens them.
- Contrast over images, gradients, and glass is measured from two screenshots of at most 20 elements (with and without the text); the rest are listed as unmeasured, and with known colors, `contrast.mjs` takes a stacked background (`"<text>|<tint> over <backdrop>"`).
- The focus check compares computed styles before and after focus; a ring drawn by a sibling element or a canvas isn't seen.
- `--perf`, `--save`, and `--compare` values come from headless loads on this machine, not field data; compare only baselines taken on the same machine and URL; layout shift covers the load only, not later interactions, and Chrome may name a parent when several children move together.
- The clickable check misses handlers delegated to a parent (React attaches them at the root); `--links` checks only links present in the first state, and treats a redirect as fine.
- It catches the common measurable failures, not everything a screen reader test or an axe audit would.

## Severity

- **P1:** breaks use or access: overflow, contrast failure (also over media), no visible focus, a control without a name, a clickable element without keyboard access, a broken image or asset, a JS exception.
- **P2:** degrades it: clipped or overlapping text, a clipped popover, text hidden after scroll, body text under 12px, targets under 24px, a distorted image, a placeholder used as the label, no page language, blocked zoom, a lazy LCP image, layout shift over 0.1 during load, console errors, failed requests, broken links, a perf regression against the baseline.
- **P3:** minor: primary-control touch targets under 44px on phones, missing alt, heading structure, missing viewport meta or favicon, contrast not measurable, the typography and layout heuristics (leading, line length, caps, tracking, edge, nested card, icon tile, heading rhythm), the LCP element (`--perf`, information only).
- **`[review]`:** a heuristic (clipped, overlap, positioned-text contrast, text-over-media contrast, the typography and layout heuristics, failed fetch calls, touch targets, layout shift, a clickable element found only by its pointer cursor). Confirm it in the screenshot first; for touch targets, report only the primary controls among those listed.
