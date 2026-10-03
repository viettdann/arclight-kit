# Changelog

All notable changes to `arc-design` are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

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
