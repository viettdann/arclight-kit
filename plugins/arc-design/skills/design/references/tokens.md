# Tokens

## Three layers

1. **Primitive:** raw scales named by position (`--neutral-50…950`, `--brand-50…950`, `--space-4`). Components never reference them directly.
2. **Semantic:** named by role (`--color-bg`, `--color-text-muted`, `--color-accent`, `--color-danger`). A theme switch swaps only this layer.
3. **Component (optional):** `--button-primary-bg: var(--color-accent)`. Add one only when a component must diverge from the semantic default.

## Required categories

| Category | Tokens |
| --- | --- |
| Surfaces | `bg`, `surface`, `surface-raised`, `surface-floating` (a layer opened from a raised one), `overlay` (scrim) |
| Borders | `border`, `border-strong` |
| Text | `text`, `text-muted`, `text-subtle`, `text-disabled` |
| Accent | `accent`, `accent-hover`, `accent-active`, `on-accent` (text on accent) |
| Status | `success`, `warning`, `danger`, `info`, each with `-fg`, `-bg`, `-border` |
| Focus | `focus-ring` |
| Typography | family (sans, mono), size scale, line-heights, weights, tracking (values from `typography.md`) |
| Space | 4px base: 0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96, 128, 160 (128 and 160 for marketing section padding only) |
| Radius | roles sm, md, lg, xl, full as role tokens (`--radius-chip`, `--radius-control`, `--radius-card`), never `--radius-sm/md/lg`; values per profile (`radius.md`) |
| Elevation | shadow levels 0–3 (which layers take them: `materials.md`), plus z-index layers: base, dropdown, sticky, overlay, modal, toast, tooltip |
| Motion | durations 60, 80, 100, 150, 200, 250, 300, 400ms (500–800ms only where a style lists slow motion); easings with explicit curves (below) |
| Layout | breakpoints, container widths, density (compact, default, comfortable) |

Easing curves (CSS keywords like `ease-out` are too weak to read as deliberate). Where a profile or style says "ease-out", use `--ease-enter`; a style that gives its own curve sets `--ease-enter` to it:

```css
--ease-enter: cubic-bezier(0.16, 1, 0.3, 1);
--ease-exit: cubic-bezier(0.33, 1, 0.68, 1);
--ease-move: cubic-bezier(0.65, 0, 0.35, 1);
```

- Exits ease out too, on a softer curve than the entrance, and run at 60–70% of the entrance duration (a 200ms open closes in 120–140ms). Never ease-in: an ease-in exit spends its first frames barely moving, so the UI seems slow to respond to the dismiss.
- `--ease-move` is for an element travelling between two resting positions on screen (reorder, layout change), where starting and stopping gently both read as natural.
- Which duration each element takes (press, tooltip, menu, modal) is in `../ui-interaction/references/motion.md`.

## Building color scales

Ramp spacing, which step takes which role, the brand step, status hues, token names, wide gamut, increased contrast, and auditing an existing palette: `color.md`.

- Build scales in OKLCH: keep the hue fixed, step lightness finer at the light end than mid-ramp (`color.md`, Ramps), lower chroma toward both ends.
- Tint neutrals slightly toward the brand hue (chroma around 0.005–0.015) instead of pure grey.
- Choose the accent step so `on-accent` text passes 4.5:1, then verify with the design skill's `scripts/contrast.mjs`; don't assume a `-500` step passes.
- Status colors used as text on dark backgrounds need a lighter step than the one used for fills.

## Names and frameworks

- Don't redefine a framework name (`text-sm`, `rounded-sm`, `shadow-md`, `ease-out`, `spacing` steps, palette colors): readers assume the framework's value, so the change goes unnoticed. Add new names (`rounded-control`, `ease-enter`, `text-body`), or replace the whole scale under `theme` (not `extend`) and record it in `DESIGN.md`.
- Role keys exist to be customized, so pointing them at project tokens is expected: `DEFAULT` entries (`borderColor.DEFAULT`, `ringColor.DEFAULT`, `divideColor.DEFAULT`) and `fontFamily.sans`/`serif`/`mono`.
- Components use semantic tokens or framework utilities mapped to them, never raw hex or pixel literals.
- Tailwind v4 builds class names from `@theme` names: `--color-text-muted` becomes `text-text-muted`, not `text-muted`. Name tokens for the class you will write (`--color-muted` → `text-muted`, `--color-surface` → `bg-surface`), and check that every semantic class in the markup exists.
- To keep Tailwind opacity modifiers (`bg-accent/50`) working with CSS variables, store channels (`--color-accent: 0.51 0.086 186` with `oklch(var(--color-accent) / <alpha-value>)`) or use Tailwind v4 `@theme`, which handles it natively.

## Migrating an existing project

- Keep every token or class name the codebase already uses (e.g. `brand`, `brand-dark`) working as an alias of the new semantic token, and mark it deprecated in `DESIGN.md`. Removing a name breaks every screen you didn't touch.
- Search the codebase for usages before renaming anything, and list remaining hardcoded values as follow-up rather than silently leaving them.

## Themes

- Light only (the default): `:root { color-scheme: light; }`. With a dark theme: `:root { color-scheme: light dark; }`, semantic tokens per `[data-theme="dark"]` and/or `@media (prefers-color-scheme: dark)`; `light-dark()` where supported.
- Theme the browser's own surfaces from the semantic tokens too, next to `color-scheme`: `::selection` (accent at low alpha behind `text`, or `accent` behind `on-accent`), `caret-color` and `accent-color` (native checkbox, radio, range, progress) from `accent`, `scrollbar-color` from `border-strong` on `bg`, and `text-underline-offset` on links as a token so underlines clear descenders the same way everywhere.
- Verify contrast in each theme separately.
- The dark set follows `dark-mode.md`: surfaces stepped in lightness, inks and borders as alphas of one white.

## Checks

- [ ] `color-scheme` matches the themes the page ships.
- [ ] `::selection`, `caret-color`, `accent-color`, `scrollbar-color`, and link `text-underline-offset` come from tokens, in each theme.

## Minimal example

```css
:root {
  --neutral-50: oklch(0.985 0.004 250);
  --neutral-900: oklch(0.22 0.01 250);
  --brand-600: oklch(0.52 0.16 250);

  --color-bg: var(--neutral-50);
  --color-text: var(--neutral-900);
  --color-accent: var(--brand-600);
  --color-on-accent: white;
}

[data-theme="dark"] {
  --color-bg: oklch(0.17 0.008 250);
  --color-surface: oklch(0.21 0.008 250);
  --color-text: oklch(0.98 0.003 250 / 0.87);
  --color-text-muted: oklch(0.98 0.003 250 / 0.73);
  --color-border: oklch(1 0 0 / 0.08);
}
```
