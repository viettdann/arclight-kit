# Style: Playful

Bright, friendly interfaces: saturated color, chunky type, illustration, and motion with some bounce. Reads as warm and confident; fails when it turns into a toy (every color at once, everything bouncing) or a rainbow template.

**Fits:** "playful", "fun", "friendly", "bold", "colorful", "neo-brutalism", Duolingo, Gumroad, Figma-like, consumer apps, education, games, creator tools, communities, family products. **Profiles:** marketing and consumer-app screens (onboarding, home, progress). Not for dense tool screens.

## Pick one mode and commit

| | Bubbly | Neo-brutal |
| --- | --- | --- |
| Canvas | White or a pale tint of the brand | Off-white or a flat bright color |
| Shape | Rounded: cards 16–20px, primary buttons pill | Radius 0–8px, 2–3px solid borders in the ink color |
| Depth | Solid lip under buttons and cards (`materials.md`) | Hard offset shadow in the ink color (`materials.md`) |
| Type | Rounded or geometric sans | Grotesk or quirky display, tight |
| Motion | Springy | Snappy, near-instant |

Never mix the two modes on one surface.

## Decisions

- **Palette (overrides the one-accent rule):** 3–5 saturated hues from the brand, each with a role (categories, illustration, section bands), plus one action color used only for the primary action, so "act here" still reads. Large areas take tints, small ones the saturated value. Text on each fill is the dark ink or white, whichever passes 4.5:1 for that fill; yellow, lime, and cyan almost always need the dark ink. Check every fill.
- **Type:** display 700–800 (overrides the 400/600 weights for display only); body stays 400/600 at 16–18px. Headlines are short and can be big.
- **Illustration:** one consistent style (stroke, fill, palette from the tokens) for spot art, mascots, and empty states; stickers and doodles sit around real content, never replace it. Icons from one library, filled or duotone in the palette. Warmth comes from illustration and copy, not emoji in headings.
- **Motion:** spring on press, toggles, completion, and celebration (fast, overshoot at most ~10%); layout changes and page transitions keep `--ease-enter` (marketing profile). Neo-brutal swaps springs for a 60–100ms offset press. Celebration (confetti, a mascot reaction) only for real milestones, once, skippable, and off under `prefers-reduced-motion: reduce`.
- **Access:** color never carries meaning alone (categories also get a label or icon). Products for children: 48px targets, plain words, no time pressure.

## Signature moves (examples)

These show the style's spirit; they are not a menu. Derive the surface's distinctive move from the product first, and use one of these only when it fits better. Never more than two per page.

- A sticker-like badge or callout, rotated -2 to -4°, on one element per section.
- Section bands alternating flat brand hues, each with type in the ink that passes on it.
- Neo-brutal cards with an ink border and a hard shadow that collapses on press.
- A bubbly primary button with a solid lip that the press removes.
- Real product UI in a playful frame (a sticker outline, a hand-drawn arrow pointing at the one feature).

## Avoid

Every hue in every section (a band uses one hue plus ink); rainbow gradients; rotating or bouncing everything, or springs on layout; mixing bubbly and neo-brutal; emoji headings; white text on yellow, lime, or cyan; illustrations in several styles; confetti on routine actions.
