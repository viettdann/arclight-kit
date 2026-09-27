# Style: Editorial Minimal

Document-like interfaces where typography and whitespace do the work and color is scarce. Reads as calm and deliberate; fails when it turns into an empty page with nothing specific on it.

**Fits:** "minimal", "calm", "editorial", "clean like Notion/Linear", knowledge tools, docs, writing apps, B2B marketing that wants to feel quiet. **Profiles:** tool (docs, editors, settings-heavy apps) and marketing (editorial landing, changelog, about).

## Decisions

- **Palette:** warm or cool monochrome, chosen from the brand hue: an off-white canvas tinted a few points toward that hue, off-black text, one muted grey for secondary text. The accent appears on the primary action only.
- **Category color:** when items need a category (tags, labels, callouts), use washed-out tints: a very light background of the hue plus a dark text step of the same hue, at 4.5:1. Never saturated fills.
- **Type:** one sans with character for UI and body. A serif for display headings only when the product is genuinely editorial (publishing, writing, research); otherwise the sans at display size with tight tracking (-0.02 to -0.04em). Mono for shortcuts, ids, and metadata. Body line-height 1.6, prose width 60–70ch.
- **Structure:** 1px hairline borders at 6–10% of the text color separate everything; no shadows on in-page surfaces. Radius 4–6px on controls, 8–12px on panels. Generous vertical space between groups; on marketing, content column `max-w-4xl`/`5xl`.
- **Motion:** almost invisible: 150–250ms fades and 8–12px rises, hover changes surface value, nothing loops.

## Signature moves (pick one or two)

- Keyboard shortcuts rendered as keycaps (`<kbd>` with a hairline border, mono, slightly tinted background).
- A flat bento: mixed cell sizes, hairline borders, no shadows, one cell carrying a real image or product crop.
- Desaturated, warm-toned photography with generous margins around it.
- Section breaks made of space and one hairline, not headings with eyebrows.

## Avoid

Gradients, glows, glass; pill-shaped large containers or primary buttons; saturated section backgrounds; fake OS window chrome around fake UI; filling empty space with decorative blobs instead of content.
