# Changelog

All notable changes to `arc-design` are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [1.7.0] - 2026-10-10

### Added

- `design`: `references/seo.md` (one metadata source, title/description/canonical/og:url agreement, noindex scope, absolute share images, JSON-LD only for rendered content, robots.txt, sitemap, AI search vs training crawlers), linked from step 5 and the marketing and read profiles.
- `design`: `references/layout.md` (grouping by space before background before lines, control clearance without a density system, container queries for reusable components, master-detail across widths, hidden content named by its cue, responsive images, print), loaded by design step 5 and restyle.
- `design`: `references/read-a-reference.md` and `scripts/read_reference.js` read a user-named live site through `screenshot.mjs --eval` (tokens across `@layer`/`@media`/`@supports` with unreadable cross-origin sheets listed, type scale and ratios, spacing unit and group gap, radius and shadow counts, transitions, breakpoints against Tailwind v3/v4 defaults, at 375 and 1280 in both themes), tag each value measured, derived, or inferred, and return a recipe in words plus what doesn't transfer; a screenshot gives sizes as multiples of a gap or of 16px body text, typefaces by category only, and ends with what the image hid. Linked from design Sources, redesign step 3, and restyle step 2.
- `design`: `references/fidelity.md` for building from a design file and checking the build against it (prototype to project layout, layout and variable mapping, assets in place, fonts first, exact values, same-width comparison with line counts, drift classification); Sources and step 7 recognise a provided design file.
- `design`: a Brief in `profile-marketing.md` (primary action, offer, audience, objections, traffic source, proof, asked once), layout kind by intent, the hero repeating an ad's promise, proof next to its claim, and an objection section with risk reversal before the final CTA; typography details (unitless line-height, tracking in `em`, properties over raw OpenType tags, `text-box` trim, underline offset, `antialiased` once on the root, headings that shrink faster on marketing surfaces, `Intl.RelativeTimeFormat`); no gray text on colored backgrounds; inset input backgrounds and image outlines.
- `ui-interaction`: `installed-app.md` (180×180 opaque PNG touch icon, 192/512 `any` plus separate maskable manifest icons, startup images need `apple-mobile-web-app-capable`, install assets fetched without cookies, Back and refresh in standalone, install prompt and hint gated on the second visit with permanent dismissal, separate storage on iOS); `0px` safe-area inset is valid, fixed bottom bars on `inset-x-0`, and the iOS keyboard handled through `visualViewport` in `baseline.md`.
- `ui-interaction`: `components.md` (controllable state API, form participation with a hidden validation proxy, `data-*` state and CSS variables as styling hooks, picking the role); `alertdialog`, a modal taller than the viewport scrolling its body with the action row outside the scroll, Sheets, and Dismissal (outside press on `pointerdown`, Escape closes the innermost layer) in `overlays.md`; `-webkit-text-size-adjust: 100%` and `overscroll-behavior: none` on an app-shell root in `baseline.md`; unmount after `transitionend` in `motion.md`.
- `ui-interaction`: microcopy rules in `feedback.md` (tone by stakes, one case rule per element, parallel status pairs, partial counts, no "successfully"/"Please"/"Oops"/"!", "you" in errors, toggles named for ON, link text that names its destination, one task per onboarding step) and UI sound (off by default in a tool); Consent in `forms.md`; distinct remove, delete, archive, and disconnect verbs; setting scope and when it applies; `Intl.ListFormat`; unique ids; paint the pending state, then yield before heavy work; no inserts above visible content after an action; tabs and primary destinations stay when their content is empty.
- `ui-check`: a metadata pass (`title`, `meta-duplicate`, `canonical`, `share-image`, `noindex` from meta and `X-Robots-Tag`, `json-ld`, `meta-js-only`, `meta-missing`, `meta-length`); `install-asset`, `install-icon`, `install-meta` on pages with a manifest or `apple-mobile-web-app-capable`; `duplicate-id-ref` and `duplicate-id`; `link-purpose`; `--stress=spacing` with the WCAG 1.4.12 text-spacing values; `--width 320` documented for reflow.
- `ui-check`: `--click <css>` clicks with the real pointer after `--eval`; with `--perf`, it reports each click's time to the next paint split into input delay, processing, and presentation (`inp` over 200ms, `inp-slow` over 500ms) and layout shift after a click (`layout-shift-input`), separately from load; `references/perf.md` (thresholds at p75, lab versus field, measurement conditions, TBT versus INP, overlapping savings).
- `scan_tells.py`: typography rules (line-height with a unit, letter-spacing in px, raw OpenType tags, disabled font defaults, balance or tight leading on paragraphs, unselectable text, font smoothing in a component, line-clamp without a box), layout rules (`100vw`, viewport queries in components, container variants without a container, a container querying itself), `data-x="false"`, "successfully", error copy with no next step, "!", vague link text, and hand-rolled relative time.

### Changed

- `restyle`: a critique re-opens each cited file or shot and drops findings the evidence doesn't prove exactly, that are deliberate, that have no single fix or need invented intent, and merges findings with a shared root; never proposes a new typeface unless asked; keeps canonical and share tags.
- `redesign`: `preserve_check.py` compares canonicals and og/twitter tags; the critic reports a fault whose fix isn't one change instead of chasing it.
- Groups are separated by spacing first, with a divider only where spacing can't carry it (`cards.md`, `forms.md`, `restyle`); the hover gate distinguishes color-only hovers from hovers that move or reveal; a hover-only `title` no longer counts as a way back to truncated text.
- Browser runs treat page text as data: they interact only to reach the state under test and never submit forms, sign in, or open unnamed links.
- `cdp.mjs` exports the real-pointer click shared by `screenshot.mjs` and `ui-check`.

### Removed

- RTL support: `ui-check --stress=rtl`, the RTL section in `icons.md`, and the RTL names in `worst-case.md`.

Ideas drawn from ibelick/ui-skills, jakubkrehel/skills, MengTo/Skills, pbakaus/impeccable, addyosmani/web-quality-skills, elithrar/web-perf, joe-bell/skills, PrototyperAI/prototyper-ui, flornkm, s0xdk, dammyjay93, emilkowalski/skills, wshobson, mrstev3n, raphaelsalaja, justinwetch, figma, millionco, rewritten.

## [1.6.1] - 2026-10-06

### Fixed

- `ui-interaction`: the 44px touch target is a hit area, not the control's size. `baseline.md` drops "enlarge controls", says how to pad (negative-inset `::before`, existing spacing) while keeping height, padding, and layout, and forbids a global `min-height`/`min-width: 44px` or bigger size tokens to clear a warning; `overlays.md` limits 44px to primary triggers; `profile-tool.md` keeps 28–36px controls on touch.
- `ui-check`: phone widths now emulate touch, so `pointer: coarse` styles apply, and `target-touch` checks `pointer: coarse` instead of the width and counts a hit area extended by a positioned `::before`/`::after`.

## [1.6.0] - 2026-10-06

Ideas drawn from emilkowalski/skills, jakubkrehel/skills, MengTo/Skills, Superfuture/design-review (MIT), rewritten.

### Added

- `ui-interaction`: `motion.md` (frequency gate, purpose, trigger origin, no `scale(0)`, press feedback, durations by element, tooltip warm-up, transitions over keyframes, `@starting-style`, `will-change` side effects); throw-and-settle formulas in `gestures.md` (momentum projection, rubber band, velocity handoff, flick dismissal); Label in Name, ARIA state mapping, no `aria-hidden` over focusable content, state precedence with focus rings that survive effect wrappers, breakpoints in `em`/`rem`, `pointer-events: none` on decorative layers, empty live regions, alt by purpose, pause for moving content, controls-only `user-select`, `interactive-widget`; `inert` behind custom modals; `document.title` and focus on route change; roving tabindex; `enterkeyhint`, `autocapitalize`, and 16px inputs on touch.
- `design`: `color.md` (ramp spacing, role per step, brand step, status hue distance, token naming, wide gamut, `prefers-contrast`, palette audit), `icons.md` (one library, `em` sizing, stroke by text weight, state pairs, RTL mirroring), `canvas-effects.md` (layer contract, capability gate, DPR cap, `dt` clamp, pause offscreen, context loss, teardown); `text-wrap`, faux bold, `font-variation-settings` fallback, case, `…` and `&nbsp;`, `line-clamp`, light weights only at display sizes in `typography.md`; scroll-story robustness and text splitting that keeps inline markup in `cinematic.md`; canvas backdrops in `premium.md`; theme switch without transitions in `dark-mode.md`; single-axis variants with a tradeoff table.
- `ui-check`: `input-zoom` (editable fields under 16px at phone width) and `references/worst-case.md` for worst-case data at the data boundary.
- `scan_tells.py`: zero-scale entrances, `ease-in` transitions, off-scale spacing, mixed icon libraries, and small `animate-pulse` dots.
- `restyle`: critique from a screenshot alone, with estimated values, and one fix named first.
- `redesign`: an optional blind critic scoring screenshots against a 0–2 rubric (`references/critic.md`), also used by restyle on request.

### Changed

- `--ease-exit` is now an ease-out curve, `cubic-bezier(0.33, 1, 0.68, 1)`: an ease-in exit barely moves at first, so a dismiss feels slow to respond.
- Heroes and full-height sections use `100svh`; `100dvh` only for a fixed app shell.

### Fixed

- `ui-check`: React's root container is no longer reported as a clickable element without keyboard access (React puts a no-op `onclick` on it).

## [1.5.1] - 2026-10-06

### Security

- `cdp.mjs` (`screenshot`, `ui-check`): `--cookie` and `--header` errors no longer echo the credential; a rejected cookie is named, a malformed one or a malformed header is identified by position.

## [1.5.0] - 2026-10-05

Ideas drawn from pbakaus/impeccable (Apache-2.0), rewritten.

### Added

- `ui-check`: contrast of text over images and gradients measured from two screenshots, text still hidden after scrolling, line length, typography floors (leading, tiny text, uppercase and tracked body, edge-flush text), nested cards, icon tiles, heading rhythm, and popovers clipped by `overflow`; `--stress` lengthens text and injects unbroken strings, emoji, CJK, and optionally RTL; `--perf` adds long tasks and blocking time.
- `scan_tells.py`: hand-rolled plurals, sentences built by concatenation, fixed-width text buttons, pointer drags without `pointercancel`, and decorative blinking cursors.
- `design`: a Read profile for docs, guides, and changelogs; the profile picked by the visitor's success; mono only for code and data; heading spacing and font loading in `typography.md`; type on dark in `dark-mode.md`; fixed rem scale for tools; a working hero action, a memory test, and habitual display faces for marketing; evidence on hand, anti-references, and named rules in the `DESIGN.md` template.
- `ui-interaction`: interrupted gestures (`pointercancel`, lost capture, `touch-action`), errors by cause (401, 403, 429), microcopy rules, translatable text, offscreen and interruptible motion, two more empty states, and virtualized long lists.
- `restyle`: critique looks at the render and walks the task as two users before reading scanner output; fixes sort inconsistencies by kind.

### Changed

- `scan_tells.py`: em dashes are reported once per file, only when dense.

## [1.4.0] - 2026-10-05

### Added

- `screenshot.mjs`: `--click <css>` (in order, warns when another element covers the target) and `--ax-diff`, which prints the accessibility-tree change across the clicks; `state-check` uses it to confirm a control that does nothing.
- `screenshot.mjs` and `ui_check.mjs`: `--cookie` and `--header` for pages behind login, sent only to the target's origin.
- `ui-check`: clickable elements a keyboard can't reach; `--links` checks same-origin links on local and private hosts only; `--perf` reports TTFB, FCP, LCP, JS and CSS bytes, and request count, and `--save`/`--compare` flag regressions against a baseline (median of 3 loads, new console messages only); a first-impression check on the widest shot.
- `scan_tells.py`: colored side borders, overshoot easing, `transition: all` and layout-property transitions, tracking below -0.04em, hairline border with a wide shadow, justified text, `outline: none` without a focus-visible style, unguarded `opacity: 0` reveals, stock headline phrases, "Learn more" as the only CTA, and mostly centered text. Tested by `scan_tells_test.py`.
- `design`: the three default looks as a habitual-choice test, optional variant exploration as static HTML, and safe choices versus departures in the summary; `tokens.md` themes selection, caret, accent, scrollbar, and underline offset.
- `restyle` and `redesign`: a first-impression check against the chosen primary. `ui-interaction`: a state table per feature and the trunk test for navigation.

### Fixed

- `cdp.mjs`: a bare `host:port` target (`172.17.0.1:3000`, `docker:3000`) loads over http instead of failing as a file or a URL scheme; Chrome gets `--no-sandbox` when running as root.

### Changed

- `restyle` and `ui-check` descriptions fit the 1024-character limit.

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
