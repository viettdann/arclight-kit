# Style: Gallery

Quiet pages that hang like a show: limewash paper, a light serif at display size, wall labels, card stock with a fibre wash, and one cool slate used sparingly. Reads as curated and unhurried; fails when it slides into the habitual cream-and-serif look, or when every block becomes a framed card and nothing is left on the wall.

**Fits:** "art gallery", "museum", "exhibition", "atelier", "fragrance", "ceramics", "furniture", "architecture studio", "boutique hotel", "lookbook", collections and objects sold or shown one piece at a time. **Profile:** marketing. Not for tool screens. **Posture:** restrained.

## Decisions

- **Palette:** a limewash neutral paper (chroma 0.010 or less), a deep umber ink for text, and one cool slate accent (chroma 0.09 or less) covering under 4% of the screen: link underlines, a drop cap, and the focus ring.
- **Action accent:** the ink. The primary control is ink-filled with paper text; slate never fills a control.
- **Type:** display a light serif at 300, roman, line-height 1.02–1.1, sentence case. A small serif at 400 for `h3` and names, never under 16px. Body a grotesk at 400, line-height 1.6. Labels are wall labels: the body face a step smaller, sentence case, untracked.
- **Card stock:** cards are card stock with a fibre wash (`texture.md` recipe 6), an inset lit edge top left, a warm layered shadow, radius 0–2px, and an inner hairline frame inset 14px. The shadow belongs to card stock only. The fibre wash is the page's one texture family, within the budget in `texture.md`, and stays at 0.05 or none under body text.
- **Rows:** hairline rows; a table opens on an ink rule.
- **Photographs:** on a thin mat, with a wall label beneath (title, material, year, or price).
- **Controls:** the primary is ink-filled with paper text at 3px radius; the secondary a hairline ink outline at 3px radius; links take a slate underline.
- **Motion:** one opacity fade of the page after fonts load; nothing else moves. Under reduced motion, no motion at all.
- **Default palette:** the brand's colors always win. When the brief and the code give no brand color, use this set instead of choosing a new one, and list it as an assumption in the summary:

  | Token | OKLCH | Text pairs (measured with `scripts/contrast.mjs`) |
  |---|---|---|
  | paper | `oklch(0.945 0.010 76)` | paper on ink (primary label) 15.77:1, Lc −95 |
  | ink | `oklch(0.19 0.024 52)` | ink on paper 15.77:1, Lc 94; ink on card 17.29:1, Lc 100 |
  | accent (slate) | `oklch(0.41 0.075 248)` | slate on paper 7.48:1, Lc 79; slate on card 8.20:1, Lc 85 |
  | card | `oklch(0.976 0.007 82)` | |

  Check every pair again with the brand's colors, and on card stock with the fibre wash applied.

## Signature moves (examples)

These show the style's spirit; they are not a menu. Derive the surface's distinctive move from the product first, and use one of these only when it fits better. Never more than two per page.

- One sentence of the brief at display size across nine or ten columns, over a wall-text paragraph that opens on a slate drop cap.
- The collection as a ruled index under an ink rule: name in the small serif, wall label beside it.
- The inquiry or booking form as a card-stock card with ruled lines to write on.

## Range

- **Figures:** a number in the light serif at 300 in ink, a wall label beneath it saying what it counts; slate stays off figures.
- **Steps:** a ruled index under an ink rule, each step a hairline row with its name in the small serif and one wall-label line.
- **Rows and forms:** hairline rows and a table opening on an ink rule; the form a card-stock card with ruled lines, the primary ink-filled with paper text.
- **Bands:** a card-stock panel with its fibre wash and inner hairline frame on the paper ground; never a colored band.

## Avoid

A warm or terracotta accent; a cream paper with a high-contrast serif (habitual look (a) in the design rules); italic or colored accent words in headings; tracked-caps or mono labels (habitual look (c)); serif running text; a flat white card; glass; two still lifes side by side at one size.
