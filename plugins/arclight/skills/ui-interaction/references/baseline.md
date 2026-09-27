# Baseline (always applies)

## Semantics

- Interactive elements are real elements: `<button>` for actions, `<a href>` for navigation, native inputs for input. No `div` or `span` with a click handler acting as a button.
- Prefer native primitives when they fit: `<dialog>` with `showModal()`, `<details>`/`<summary>`, `popover` attribute, `<input type="date">` on mobile.

## Keyboard and focus

- Never remove the outline without a replacement. Focus ring: 2px thick, 2px offset, at least 3:1 against the adjacent colors, visible in every theme. Use `:focus-visible` so mouse clicks don't show it.
- The focus ring color differs from the selected or active color, otherwise keyboard users can't tell "where I am" from "what is chosen".
- DOM order matches visual order. Don't reorder focusable content with CSS `order` or grid placement.
- Dialogs trap focus, close on Escape, and return focus to the element that opened them.
- Pages with navigation start with a skip link that is visible on focus.

## Pointer and touch

- Touch targets are at least 44×44px for primary controls, never below 24×24px. Pad the hit area, the visible glyph can stay 16–20px.
- Hover styles live under `@media (hover: hover)`; enlarge controls under `@media (pointer: coarse)`. Never branch on user agent.
- Hover may reveal extras only. Every primary action is reachable by tap and keyboard without hover.

## Color and text

- Contrast: 4.5:1 for body text, 3:1 for large text (24px, or 18.66px bold) and for UI boundaries, icons, and focus rings.
- Never carry meaning by color alone: pair it with an icon, text, or shape.

## Motion

- Honor `prefers-reduced-motion: reduce` for every animation and every transition that moves or scales (`transform`, `translate`, `scale`, position): replace the movement with an opacity change or nothing. Color and opacity transitions may stay.
- Press/tap feedback appears within 100ms.
- Exits are faster than entrances, roughly 60–70% of the entrance duration.

## Platform CSS worth using

- `:has()` for state that already lives in the DOM (checked, open, invalid, child count) instead of mirroring it into JS state, e.g. `.plan:has(:checked)`, `form:has(:user-invalid)`, `.grid:has(> :nth-child(n + 5))`.
- `:user-invalid` instead of `:invalid`, so errors don't show on first render.
- `body:has(dialog[open]) { overflow: hidden; }` for scroll lock without cleanup code.
- Animate to `height: auto` with `grid-template-rows: 0fr → 1fr` (or `interpolate-size: allow-keywords` where supported).
- `z-index` only works on positioned elements or flex/grid children, and only ranks siblings inside one stacking context. Put `isolation: isolate` on components with internal layers; never escalate to 9999, find the stacking context instead.
- `animation-timeline: scroll()` / `view()` for scroll-linked effects, wrapped in `@supports` with a static fallback.

## Checks

- [ ] Every interactive element is focusable in a logical order and has a visible `:focus-visible` style.
- [ ] No clickable `div`/`span`.
- [ ] No action depends on hover, right-click, or swipe alone.
- [ ] Every moving animation or transition has a `prefers-reduced-motion: reduce` override.
- [ ] No state is conveyed by color alone.
