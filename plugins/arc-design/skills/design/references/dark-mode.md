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

- Light text on dark reads thinner and tighter than the same text on light: raise body line-height by about 0.05–0.1, add about 0.01em tracking, and go one weight step up if the face looks spindly.

## Calm the accent

- A saturated accent glows past its edges on dark. Keep the hue, raise the lightness, lower the chroma in OKLCH until it sits calmly on the surfaces.
- A lighter accent flips its foreground: white text on a calmed accent usually fails, so `on-accent` becomes the near-black. Verify the pair.
- Status colors follow the same rule, with text steps lighter than their fills.

## Hairlines

- Borders are alphas of one white, and input boundaries pass 3:1: `materials.md` (Solid and hairline).

## Images

- Photos are dimmed so they don't take the attention: `filter: brightness(0.8)` in the dark theme.
- Illustrations, diagrams, and logos get a dark variant, never `filter: invert()`. If the theme is set by a class or `data-theme`, swap them by that selector; `<picture media="(prefers-color-scheme: dark)">` follows only the OS setting.

## Theme on load, switching, and native UI

- A stored theme (`localStorage`, a cookie) applied in `useEffect` or after hydration flashes the wrong theme on every load. Set the class or `data-theme` from a small blocking inline script in `<head>`, before first paint; with React SSR, add `suppressHydrationWarning` to `<html>`. A theme the server renders from a cookie needs no script.
- Switching themes at runtime fires every color transition on the page at once, so buttons, borders, and backgrounds fade over at different speeds. Suppress them for the switch: append a `<style>` with `*, *::before, *::after { transition: none !important; }`, flip the class, force a reflow (`getComputedStyle(document.body).opacity` or `document.body.offsetHeight`), and remove the style in the next `requestAnimationFrame`. Without the forced reflow the browser applies the flip and the removal together, and the transitions still run. next-themes does this with `disableTransitionOnChange`.
- `color-scheme: light` and `color-scheme: dark` on the root of each theme, so scrollbars, form controls, and the default canvas follow it.
- `<meta name="theme-color">` matching the page background, one per scheme (`media="(prefers-color-scheme: dark)"`); when a class sets the theme, update the meta with it.
- Native `<select>` gets explicit `background-color` and `color`; Windows otherwise draws its dropdown in system colors that can clash with or vanish against the dark theme.

## Default palette for a tool without a brand

For a tool-profile dark theme when the project, the brief, and the chosen style give no palette. Technical and glass use their own default palettes (`styles/technical.md`, `styles/glass.md`). Chroma climbs slightly per layer (0.007 to 0.011) on purpose, against the same-chroma rule above, so the raised layers don't grey out.

| Layer | Value | For |
| --- | --- | --- |
| sunken | `oklch(0.135 0.007 250)` | Code, logs, changed rows: one step below the page |
| page | `oklch(0.17 0.008 250)` | The app background |
| surface | `oklch(0.21 0.009 250)` | Panels, cards, the sidebar |
| raised | `oklch(0.25 0.010 250)` | Controls and layers on a surface |
| floating | `oklch(0.29 0.011 250)` | Menus, popovers, dialogs |

- **Accent** `oklch(0.80 0.11 250)`, **on-accent** `oklch(0.18 0.04 250)`: on-accent on the accent 10.09:1 (Lc 68); the accent as text on floating 7.57:1 (Lc −63).
- **Inks** are white at three alphas set for these layers: `text` `#ffffffde` (87%) 15.02:1 on sunken, 11.05:1 on floating; `text-muted` `#ffffffc7` (78%) 12.06:1 on sunken, 9.19:1 on floating; `text-subtle` `#ffffffb0` (69%) 9.49:1 on sunken, 7.54:1 on floating. Each passes with no `warn`; the alphas sit above the general ones (Three inks from one white) because APCA rates muted light-on-dark text lower than WCAG 2 does.
- **Hairlines** follow the alpha rules above (Hairlines).
- **No in-page shadow:** layers are told apart by lightness and hairlines; floating layers keep only an optional overlap shadow (`materials.md`, Lightness layers).
- **Mono only for measured values and ids** (durations, sizes, hashes, keys); labels and running text stay in the UI face.

Ratios measured with `scripts/contrast.mjs` (`"#ffffffb0|oklch(0.29 0.011 250)|text"`); remeasure any value you change.

## Checks

- [ ] The stored theme is applied before first paint; no flash on reload; switching themes suppresses transitions for that frame.
- [ ] `color-scheme` set per theme; `theme-color` matches the page; native selects readable in dark.
- [ ] No `#000` surface and no opaque `#FFF` text; surfaces step up in lightness by what they sit on.
- [ ] No shadow on in-page surfaces (glass-style panes excepted, `styles/glass.md`); floating layers are lighter plus a hairline.
- [ ] Three inks as alphas of one white, each passing 4.5:1 on the lightest surface it sits on; body text on dark has slightly more line-height and tracking.
- [ ] Accent calmed in chroma, with `on-accent` re-checked.
- [ ] Hairlines are alpha; input boundaries pass 3:1.
- [ ] Photos dimmed; illustrations and logos have dark variants.
