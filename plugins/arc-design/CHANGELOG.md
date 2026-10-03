# Changelog

All notable changes to `arc-design` are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [1.3.0] - 2026-10-03

### Added

- `ui-check` flags a missing `<html lang>`, a viewport meta that blocks zoom, and a lazy-loaded LCP image; `--perf` adds the LCP element and the elements that shift during load (lab values, layout shift over 0.1 as a `[review]` finding).
- `dark-mode.md`: the stored theme applied by a blocking inline script before first paint, `color-scheme` per theme, `theme-color` per scheme, and explicit colors on native `<select>`.
- `baseline.md`: mobile web and locale rules (`touch-action`, overscroll containment on overlays, safe-area insets, `translate="no"`, `Intl` for dates and numbers, no `transition: all`, no blocked paste), drawn from vercel-labs/web-interface-guidelines (MIT).
- `state-check`: stale copy (`useState(prop)`) and effect chain patterns.

## [1.2.0] - 2026-10-03

### Added

- `ui-interaction`: generated content rules in `feedback.md` (streaming, output-shaped skeleton, named steps, output as an editable draft, actions on a selection, confirmation for risky proposed actions, growing prompt box, partial text kept on failure); no repeated entry across a multi-step form (WCAG 3.3.7) in `forms.md`; text that survives 200% zoom and reserved sizes for images, videos, and iframes in `baseline.md`.

## [1.1.0] - 2026-10-03

### Added

- `state-check`: maps every state writer in scope (store actions and the fields they reset, effects, query cache, URL), traces each control's handler call by call against what its label promises, and reports sequential undo, effect undo, read after set, stale closure, async race, missing transition, dead path, teardown, and double fire. P1 and P2 findings are confirmed with a failing test or a reproduction; fixes go to the writer, not the handler, and only when asked (the `fix` argument, or after the report). A dead control is first checked for a handler that never runs; report-only runs delete their confirming tests.
- `contrast.mjs` reads `hsl()` and `hsla()`.
- `scan_tells.py` tags each `7-code` hit `presentation` or `behavior`; restyle and redesign fix presentation hits and flag behavior ones.

### Changed

- `restyle` and `redesign` verify with one `ui_check.mjs --shot` run at 1280 and 390, confirming `[review]` findings in the shots before fixing them. Screenshot options live once, in design step 7.
- `design`: a style's stated values win over the profile, everything else stays; style signals are words about the look, not page types; a style named for a profile it doesn't list keeps the profile's space and motion. A marketing page that opens gets one render run for its hero and nav checks.
- References agree: space scale to 160 and durations 60-800ms, easings named by token, role radius tokens, `color-scheme: light` when light-only, body line-height up to 18px, display line-height 0.9 only without descenders, the design read's move as the one special element, media frames and double bezels allowed inside cards, hard offset shadow exempt from the border-plus-shadow rule, premium's floating glass nav inside the glass budget.
- `preserve_check.py` skips SVG internals, icon names, and asset `<link>`s; redesign states which metadata it reads and snapshots several folders when needed.
- `ui-check`: asks for a target when none is known, runs once per URL and theme, and folds phone touch targets under 44px into one `[review]` line listing the smallest, so only primary controls get reported.
- Triggers: design gains Vietnamese phrases, restyle is scoped to the look, ui-check and ui-interaction point dead controls to state-check.

## [1.0.1] - 2026-10-03

### Changed

- `design`: a brief that asks for a glassy look gets visible glass on the hero and key panels, not only on floating layers.
- `design` (marketing): scroll reveals keep content visible without JS and under reduced motion; a nav with three or more links gets a menu on narrow screens.

### Fixed

- `screenshot.mjs` and `ui_check.mjs` also find the Chromium downloaded by Playwright (`$PLAYWRIGHT_BROWSERS_PATH` or the default `ms-playwright` cache, newest build first) when no browser is on PATH, so they run on CI runners and containers without `CHROME` set.

## [1.0.0] - 2026-10-03

First release.

### Added

- `design`: new UI from a profile (tool or marketing) plus an optional style (`minimal`, `premium`, `brutalist`, `cinematic`, `playful`). Always loads tokens, typography, radius, and `materials.md` (solid and hairline, lightness layers, shadow, glass for layers floating over moving content, scrim, gradient and glow, texture, tint fill); cards, avatars, and dark mode on demand. Writes the project's `DESIGN.md`. Scripts: `contrast.mjs` (WCAG pairs, stacked backgrounds such as `"<tint> over <backdrop>"`) and `screenshot.mjs` (any width, light or dark, emulated media, `--wait-for`, `--eval`, keyboard `--focus`, real `--hover`, one element with `--selector`, exit 1 on horizontal overflow).
- `redesign`: a new visual language for an existing product, keeping content, information architecture, URLs, and behavior; snapshots the source first and checks what it preserved with `preserve_check.py`.
- `restyle`: removes AI tells from a generated-looking UI while keeping the layout; `scan_tells.py` finds them in code, and critique-only mode reports at most three findings by user impact.
- `ui-check`: loads a running page at 375, 768, 1280, and 1920px and reports measured defects by severity: the element causing horizontal overflow, clipped and overlapping text, contrast per text element in each theme, focus with no visible change, controls without an accessible name, small targets, broken or distorted images, heading structure, JS errors, and failed requests. Fixes only when asked; `restyle` and `redesign` run it to verify.
- `ui-interaction`: behavior and state rules for forms, tables, overlays, navigation, feedback, destructive actions, and settings, used alongside the other design skills.
