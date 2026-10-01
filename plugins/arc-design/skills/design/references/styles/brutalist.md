# Style: Brutalist

Raw, mechanical interfaces: visible grids, extreme type scale, zero ornament. Reads as honest and technical; fails when the raw look becomes costume (fake scanlines, decorative crosshairs) over content that isn't structured.

**Fits:** "brutalist", "Swiss", "raw", "terminal", "technical", "blueprint", developer tools, infrastructure, data products, portfolios and editorial sites that want edge. **Profiles:** tool (terminal mode suits dense data) and marketing.

## Pick one mode and commit

| | Swiss print | Terminal |
| --- | --- | --- |
| Canvas | Light newsprint off-white | Near-black (dark by nature: choose it only when the brief wants dark) |
| Type | Heavy grotesk display, uppercase, huge | Mono everywhere, sans only for long prose |
| Accent | One signal color (red is classic) used for alerts and the main action | One phosphor-like color (green, amber, or the brand's) at readable contrast |
| Density | Asymmetric, lots of negative space | High, tabular |

Never mix the two modes on one surface.

## Decisions

- **Type (overrides `typography.md` for display):** display weight 700–900, `clamp(3rem, 8vw, 10rem)`, tracking -0.03 to -0.05em, line-height 0.9, uppercase. Micro labels in mono 11–13px with +0.05em tracking. Body text stays readable: at least 14px mono or 16px sans, 4.5:1.
- **Grid:** the grid is visible: 1–2px solid rules between cells and sections, aligned to real columns. Lines organize content; a line that separates nothing is removed.
- **Shape and depth:** radius 0 everywhere except the `full` roles (avatars, dots, toggles); no shadows, no gradients, no blur. Depth comes from rules and inversion (a black block with light text).
- **Numbers:** large numerals only for real quantities (metrics, prices, counts), tabular.
- **Motion:** none, instant state changes, or stepped transitions (`steps()`), never soft easing.

## Signature moves (examples)

These show the style's spirit; they are not a menu. Derive the surface's distinctive move from the product first, and use one of these only when it fits better. Never more than two per page.

- A viewport-bleeding headline or numeral that the grid is built around.
- Bracketed labels (`[ STATUS ]`, `> run`) in terminal mode, for real commands and states only.
- Inverted blocks (solid text-color background) for the one thing that matters on the screen.
- Analog texture (halftone, dither, scanlines) as a fixed `pointer-events: none` overlay, subtle, never under body text, removed under `prefers-reduced-motion` and `prefers-contrast: more`.

## Avoid

Rounded corners, soft shadows, pastel tints; decorative crosshairs, fake coordinates, and version stamps that carry no information; low-contrast grey mono body text; making every label uppercase mono so nothing stands out.
