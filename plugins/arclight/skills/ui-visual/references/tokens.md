# Tokens

## Three layers

1. **Primitive:** raw scales named by position (`--neutral-50…950`, `--brand-50…950`, `--space-4`, `--radius-md`). Components never reference them directly.
2. **Semantic:** named by role (`--color-bg`, `--color-text-muted`, `--color-accent`, `--color-danger`). A theme switch swaps only this layer.
3. **Component (optional):** `--button-primary-bg: var(--color-accent)`. Add one only when a component must diverge from the semantic default.

## Required categories

| Category | Tokens |
| --- | --- |
| Surfaces | `bg`, `surface`, `surface-raised`, `overlay` (scrim) |
| Borders | `border`, `border-strong` |
| Text | `text`, `text-muted`, `text-subtle`, `text-disabled` |
| Accent | `accent`, `accent-hover`, `accent-active`, `on-accent` (text on accent) |
| Status | `success`, `warning`, `danger`, `info`, each with `-fg`, `-bg`, `-border` |
| Focus | `focus-ring` |
| Typography | family (sans, mono), size scale, line-heights, weights, tracking |
| Space | 4px base: 0, 4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96 |
| Radius | none, sm, md, lg, xl, full; values per profile |
| Elevation | shadow levels 0–3, plus z-index layers: base, dropdown, sticky, overlay, modal, toast, tooltip |
| Motion | durations 100, 150, 200, 300, 400ms; easings with explicit curves (below) |
| Layout | breakpoints, container widths, density (compact, default, comfortable) |

Easing curves (CSS keywords like `ease-out` are too weak to read as deliberate):

```css
--ease-out: cubic-bezier(0.16, 1, 0.3, 1);
--ease-in: cubic-bezier(0.7, 0, 0.84, 0);
--ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
```

## Building color scales

- Build scales in OKLCH: keep the hue fixed, step lightness evenly, lower chroma toward both ends.
- Tint neutrals slightly toward the brand hue (chroma around 0.005–0.015) instead of pure grey.
- Choose the accent step so `on-accent` text passes 4.5:1, then verify with `scripts/contrast.mjs`; don't assume a `-500` step passes.
- Status colors used as text on dark backgrounds need a lighter step than the one used for fills.

## Names and frameworks

- Don't redefine a framework name (`text-sm`, `rounded-sm`, `shadow-md`, `ease-out`, `spacing` steps, palette colors): readers assume the framework's value, so the change goes unnoticed. Add new names (`rounded-control`, `ease-enter`, `text-body`), or replace the whole scale under `theme` (not `extend`) and record it in `DESIGN.md`.
- Role keys exist to be customized, so pointing them at project tokens is expected: `DEFAULT` entries (`borderColor.DEFAULT`, `ringColor.DEFAULT`, `divideColor.DEFAULT`) and `fontFamily.sans`/`serif`/`mono`.
- Components use semantic tokens or framework utilities mapped to them, never raw hex or pixel literals.
- To keep Tailwind opacity modifiers (`bg-accent/50`) working with CSS variables, store channels (`--color-accent: 0.51 0.086 186` with `oklch(var(--color-accent) / <alpha-value>)`) or use Tailwind v4 `@theme`, which handles it natively.

## Migrating an existing project

- Keep every token or class name the codebase already uses (e.g. `brand`, `brand-dark`) working as an alias of the new semantic token, and mark it deprecated in `DESIGN.md`. Removing a name breaks every screen you didn't touch.
- Search the codebase for usages before renaming anything, and list remaining hardcoded values as follow-up rather than silently leaving them.

## Themes

- `:root { color-scheme: light dark; }`; semantic tokens per `[data-theme="dark"]` and/or `@media (prefers-color-scheme: dark)`; `light-dark()` where supported.
- Verify contrast in each theme separately.

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
  --color-text: oklch(0.93 0.005 250);
}
```
