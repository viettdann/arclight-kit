# Dark Mode

A black background with white text is not a dark theme: `#000` and `#FFF` leave no room for layers, so the page has no depth and reads as a terminal. Dark mode is its own token set, built from lightness steps, alpha inks, and a calmer accent.

## Near-black, with room for layers

- The page is near-black, never `#000`: a dark neutral tinted slightly toward the brand hue (see `tokens.md`), so lighter layers have room above it.
- Surfaces step up in even OKLCH lightness increments with the same hue and chroma: page, surface, raised, floating. Pick the steps once; don't hand-pick a hex per component.
- Which step a layer takes, and why dark themes raise with lightness instead of shadow, is in `materials.md` (Lightness layers).

## Three inks from one white

- Text is white (or a brand-tinted off-white) at three alphas, never opaque `#FFF`: `text` about 87%, `text-muted` about 73%, `text-subtle` about 60%. Alpha keeps the same rank on every layer.
- The floor for readable text is about 50%; below that it fails 4.5:1 on the lighter layers. `text-disabled` (about 38%) misses 4.5:1 by design but stays above 3:1, and is for disabled controls only (`typography.md`).
- Check each ink on the darkest and the lightest surface it sits on with the design skill's `scripts/contrast.mjs` (8-digit hex for alpha: `#ffffffde|<surface>|text`).

## Calm the accent

- A saturated accent glows past its edges on dark. Keep the hue, raise the lightness, lower the chroma in OKLCH until it sits calmly on the surfaces.
- A lighter accent flips its foreground: white text on a calmed accent usually fails, so `on-accent` becomes the near-black. Verify the pair.
- Status colors follow the same rule, with text steps lighter than their fills.

## Hairlines

- Borders are alphas of one white, and input boundaries pass 3:1: `materials.md` (Solid and hairline).

## Images

- Photos are dimmed so they don't take the attention: `filter: brightness(0.8)` in the dark theme.
- Illustrations, diagrams, and logos get a dark variant, never `filter: invert()`. If the theme is set by a class or `data-theme`, swap them by that selector; `<picture media="(prefers-color-scheme: dark)">` follows only the OS setting.

## Checks

- [ ] No `#000` surface and no opaque `#FFF` text; surfaces step up in lightness by what they sit on.
- [ ] No shadow on in-page surfaces; floating layers are lighter plus a hairline.
- [ ] Three inks as alphas of one white, each passing 4.5:1 on the lightest surface it sits on.
- [ ] Accent calmed in chroma, with `on-accent` re-checked.
- [ ] Hairlines are alpha; input boundaries pass 3:1.
- [ ] Photos dimmed; illustrations and logos have dark variants.
