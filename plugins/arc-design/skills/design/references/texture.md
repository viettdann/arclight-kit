# Texture

A texture is an analog artifact laid over flat color: grain, halftone, misregistration, scanlines, a deckled edge. It makes a surface read as made rather than rendered, and it costs contrast and attention, so a page gets one family and a small dose of it. Where a texture may sit, and that the tool profile takes none, is in `materials.md` (Texture); this file holds the budget and the recipes. Styles choose the family (cinematic film grain, brutalist analog texture, print speck grain plus one misregistered word, gallery fibre wash).

Contents: budget · overlay · recipes (grain, halftone, misregistration, scanline, deckle, fibre wash) · overrides · accessibility · checks.

## Budget

- **One artifact family per page:** grain, halftone, misregistration, scanline, or deckle. Two families compete, and the page reads as a filter preset instead of a surface. The print style's grain and misregistration count as one family; gallery's fibre wash is grain-family.
- **`--texture-opacity`** sets the strength: at most 0.05 (or none) wherever body text sits under the texture, a page-wide overlay included; where no body text sits under it, at most 0.08 for a page-wide overlay and at most 0.15 inside one plate (a band, a photograph, a fill, one card).
- **CSS or a data-URI SVG only.** No texture image to download, no canvas, no script: the texture renders with the first paint and costs no request.
- **Every overlay** is `aria-hidden="true"` and `pointer-events: none`, so it is never announced and never sits between a pointer and a link.
- **Motion:** a texture that moves (flicker, rolling scanlines, grain that shifts) is frozen or removed under `prefers-reduced-motion: reduce`.
- **Increased contrast:** every texture is removed under `prefers-contrast: more`.

## Overlay

A page-wide or plate-wide texture is one empty element, placed last in its container, that every recipe below styles.

```html
<div class="texture" aria-hidden="true"></div>
```

```css
:root { --texture-opacity: 0.05; }
.texture { position: absolute; inset: 0; pointer-events: none; opacity: var(--texture-opacity); }
.texture--page { position: fixed; z-index: 1; }
```

The plate holding a `.texture` is `position: relative; isolation: isolate`, so the overlay stays inside it and any blend mode stops at its edge.

## Recipes

### 1. Grain

Discrete specks, not a fog. `feTurbulence` at a high `baseFrequency` (0.85) makes fine noise; the `feColorMatrix` alpha row `0 0 0 9 -4` multiplies its alpha by 9 and subtracts 4, which thresholds the noise into separate specks with clear ground between them. Dark specks on light grounds (RGB rows 0), white specks on dark grounds (RGB offsets 1).

```css
.texture--grain {
  background-size: 160px 160px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='g'%3E%3CfeTurbulence baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 9 -4'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23g)'/%3E%3C/svg%3E");
}
/* Dark ground: same SVG with the RGB rows set to '0 0 0 0 1' so the specks are white. */
```

Grain on a fill, band, or photograph sits inside that plate at up to 0.15; page-wide grain stays at 0.05 over body text and reaches 0.08 only where no body text sits under it.

### 2. Halftone

A dot screen for bands, fills, and photographs; never under type, where the dots break letter edges.

```css
.texture--halftone {
  --halftone-size: 6px;
  --halftone-dot: var(--ink);
  background-image: radial-gradient(circle, var(--halftone-dot) 28%, transparent 30%);
  background-size: var(--halftone-size) var(--halftone-size);
}
```

A larger `--halftone-size` reads as print at a distance; under 4px it turns into a grey tint and moiré on phones.

### 3. Misregistration

One focal word per page, in the hero: a copy of the word in the second ink, offset 1–3px, as if the second plate slipped. A second misregistered heading makes it a font effect.

```html
<h1>Prints that <span class="misregister" data-text="ship">ship</span> this week</h1>
```

```css
.misregister { position: relative; }
.misregister::after {
  content: attr(data-text) / "";
  position: absolute; inset: 0; z-index: 1; pointer-events: none;
  color: var(--ink-2); mix-blend-mode: multiply;
  transform: translate(2px, 1px);
  animation: misregister-settle 700ms var(--ease-enter) 1 both;
}
@keyframes misregister-settle { from { transform: translate(6px, 4px); } }
```

The copy sits above the word and multiplies with it, so where the two inks overlap they overprint into a third color; the span takes no `isolation`, and the copy never goes behind the word, or multiply has nothing to blend with. `content: attr(data-text) / ""` gives the copy an empty alternative text, so a screen reader reads the word once. The offset settles at most once on load and then holds; nothing loops.

### 4. Scanline

A fixed overlay of horizontal lines for a screen-like surface. The line color carries the strength, so the overlay itself stays at full opacity.

```css
.texture--scanline {
  position: fixed; opacity: 1;
  background-image: repeating-linear-gradient(to bottom, rgb(0 0 0 / 0.06) 0 1px, transparent 1px 3px);
}
```

Use white at 0.06 on dark grounds. Rolling scanlines are a moving texture: under reduced motion they stop.

### 5. Deckle

A torn-paper edge on one element class per page (the photographs, or the cards, never both): a `mask-image` from a displaced rectangle.

```css
.deckle {
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100' preserveAspectRatio='none'%3E%3Cfilter id='d'%3E%3CfeTurbulence baseFrequency='0.08' numOctaves='3'/%3E%3CfeDisplacementMap in='SourceGraphic' scale='3'/%3E%3C/filter%3E%3Crect x='2' y='2' width='96' height='96' fill='white' filter='url(%23d)'/%3E%3C/svg%3E");
  mask-size: 100% 100%;
}
```

Keep text inside the 2% inset, or the torn edge eats letters.

### 6. Fibre wash (grain family)

Card stock: a soft continuous wash of low-frequency noise with no threshold, so it reads as fibre in the paper rather than specks on it. `fractalNoise` at `baseFrequency` 0.02 or lower, and the `feColorMatrix` alpha row `0 0 0 0.5 0` halves the noise alpha without cutting it off.

```css
.texture--fibre {
  background-size: 400px 400px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400'%3E%3Cfilter id='f'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.02' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 0.3  0 0 0 0 0.25  0 0 0 0 0.2  0 0 0 0.5 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23f)'/%3E%3C/svg%3E");
}
```

Set the RGB offsets toward the ink's hue. On a card that holds body text or a form the wash stays at 0.05 or below.

## Overrides

These two blocks come after every recipe rule in the stylesheet: they match the recipes' specificity, so a recipe rule later in source (the misregistered copy's `animation`, the deckle's `mask-image`) would win over them.

```css
@media (prefers-contrast: more) {
  .texture, .misregister::after { display: none; }
  .deckle { mask-image: none; }
}
@media (prefers-reduced-motion: reduce) {
  .texture, .misregister::after { animation: none; }
}
```

## Accessibility

- Contrast is measured on the textured result, not only on the flat ground. Measure the text on the flat ground and on the texture composited as a layer over it, and keep the lower ratio: dark specks lower it for light text, light specks for dark text. Dark specks at 0.05 over a ground are `#0000000d over <ground>`, as in `node ${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/contrast.mjs "<text>|#0000000d over <ground>|text"`. Light specks under light text on a dark ground are measured the same way with white.
- Under `prefers-contrast: more` every texture goes (overlay, misregistered copy, deckle mask); under `prefers-reduced-motion: reduce` a moving one freezes or goes. Both are in Overrides above, after the recipes.
- An overlay never captures the pointer or focus, and never holds content; a texture that carries meaning is not a texture.

## Checks

- [ ] One artifact family on the page (print's grain plus misregistration and gallery's fibre wash each count as one).
- [ ] `--texture-opacity` 0.05 or none under body text (page-wide included); otherwise at most 0.08 page-wide, 0.15 inside one plate.
- [ ] CSS or data-URI SVG only; every overlay `aria-hidden="true"` and `pointer-events: none`.
- [ ] Removed under `prefers-contrast: more`; frozen or removed under reduced motion if it moves.
- [ ] Text contrast measured on the flat ground and with the texture composited over it; the lower ratio passes.
- [ ] Misregistration on one word in the hero, settling at most once; halftone never under type; deckle on one element class.
