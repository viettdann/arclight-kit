# Style: Minimal

Document-like interfaces where typography and whitespace do the work and color is scarce. Reads as calm and deliberate; fails when it turns into an empty page with nothing specific on it.

**Fits:** "minimal", "calm", "editorial", "clean like Notion/Linear", knowledge tools, docs, writing apps, B2B marketing that wants to feel quiet. **Profiles:** tool (docs, editors, settings-heavy apps) and marketing (editorial landing, changelog, about). **Posture:** restrained.

## Decisions

- **Palette:** warm or cool monochrome, chosen from the brand hue: an off-white canvas tinted a few points toward that hue, off-black text, one muted grey for secondary text. The accent appears on the primary action only (this overrides the global rule: the current selection uses a neutral fill).
- **Category color:** when items need a category (tags, labels, callouts), use tint fills (`materials.md`). Never saturated fills.
- **Type:** one sans with character for UI and body. A serif for display headings only when the product is genuinely editorial (publishing, writing, research); otherwise the sans at display size with tight tracking (-0.02 to -0.04em). Mono for shortcuts, ids, and metadata. Body line-height 1.6, prose width 60–70ch.
- **Structure:** space separates first; a 1px hairline at 6–10% of the text color goes only where space can't (table rows, a card on a surface of the same value), and `layout.md`'s line count still holds; no shadows on in-page surfaces. Radius overrides the profile's values: chips and tags 4px, buttons and inputs 6px, cards and panels 8px, no pills. Generous vertical space between groups; on marketing, content column `max-w-4xl`/`5xl`.
- **Motion:** almost invisible: 150–250ms fades and 8–12px rises, hover changes surface value, nothing loops.

## Signature moves (examples)

These show the style's spirit; they are not a menu. Derive the surface's distinctive move from the product first, and use one of these only when it fits better. Never more than two per page.

- Keyboard shortcuts rendered as keycaps (`<kbd>` with a hairline border, mono, slightly tinted background).
- A flat bento: mixed cell sizes, hairline borders, no shadows, one cell carrying a real image or product crop.
- Desaturated, warm-toned photography with generous margins around it.
- Section breaks made of space and one hairline, not headings with eyebrows.

## Range

- **Figures:** a real quantity at display size in the sans with tight tracking, in the text color, over one line of muted grey saying what it counts; the accent stays on the primary action.
- **Steps:** a numbered list read like a document: numerals in the sans, a short heading and one sentence per step, separated by space and at most one hairline.
- **Rows and forms:** table rows on hairlines at 6–10% of the text color, inputs and buttons at 6px radius, the primary button the only accent on the screen.
- **Bands:** a section break made of space and one hairline; a band is at most a neutral surface one value off the canvas, never saturated.

## Avoid

Gradients, glows, glass; pill-shaped large containers or primary buttons; saturated section backgrounds; fake OS window chrome around fake UI; filling empty space with decorative blobs instead of content.
