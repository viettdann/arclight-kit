# Style: Print

Pages that look printed in two spot inks on uncoated paper: a dark ink for every word, a fluorescent ink for fills, overprint for the third color, and grain in the ink. Reads as made by hand and by press, like a riso zine or an art print; fails when the inks turn into a costume (fake misregistration on every heading, a flat gradient called riso) or the fluorescent ink starts carrying text.

**Fits:** "risograph", "riso", "zine", "small press", "print studio", "art print", "art book", "indie publisher", "print fair", shops and pages for printed matter, studios, and small publishers. **Profile:** marketing. Not for tool screens. **Posture:** committed.

## Decisions

- **Inks:** no black. One dark ink sets every word, rule, and icon; one fluorescent ink fills shapes, bands, and the primary action. Where the two overlap, overprint with `mix-blend-mode: multiply` makes the third color; nothing else adds a hue.
- **Text on the fill:** text on a fluorescent fill uses the `on-fill` color only, which is the paper color knocked out of the fill. Dark-ink text never sits on the fill, and the fluorescent ink is never text on paper.
- **Paper:** an uncoated off-white, warm and low in chroma, as the page ground.
- **Type:** display a heavy grotesk at 800, line-height 0.92–0.98, tracking -0.025em, sentence case; body a text serif. Labels in the body face a step smaller, sentence case, untracked. No mono.
- **Shape and depth:** radius 2px everywhere. No shadow; depth is overprint, one ink layered over the other.
- **Texture:** speck grain on fills, bands, and photographs, plus one misregistered word in the hero (`texture.md` recipes 1 and 3). Grain and misregistration count as one artifact family, so the page takes no other texture; `--texture-opacity` stays within the budget in `texture.md`, with no grain under body text.
- **Photographs:** duotone in the two inks, never full color.
- **Controls:** the primary is a fluorescent fill with `on-fill` text; beside it the secondary is a 1.5px dark-ink outline on paper. Press translates the control 1px right and down, like a sheet shifting in the drum.
- **Motion:** the misregistered word settles once on load; nothing loops. Under reduced motion it renders settled.
- **Default palette:** the brand's colors always win. When the brief and the code give no brand color, use this set instead of choosing a new one, and list it as an assumption in the summary:

  | Token | OKLCH | Text pair (measured with `scripts/contrast.mjs`) |
  |---|---|---|
  | paper | `oklch(0.97 0.011 90)` | |
  | ink | `oklch(0.40 0.165 265)` | ink on paper 8.81:1, Lc 86 |
  | fill | `oklch(0.56 0.235 356)` | |
  | on-fill | `oklch(0.97 0.011 90)` (the paper) | on-fill on fill 4.79:1, Lc −72 |

  Check every pair again with the brand's inks, and over the grain at its final `--texture-opacity`.

  The fill sits in `color.md`'s mid-lightness band, which keeps such a color off section backgrounds; print's fill is a deliberate exception because the paper (`on-fill`) passes on it. Grain on the fill uses dark specks only: light specks lower the on-fill contrast.

## Signature moves (examples)

These show the style's spirit; they are not a menu. Derive the surface's distinctive move from the product first, and use one of these only when it fits better. Never more than two per page.

- A hero headline in dark ink with one word misregistered in the fluorescent ink, settling on load.
- A fluorescent shape overprinting the edge of a duotone photograph, the overlap printing the third color.
- A colophon footer that names the inks, the paper, and the typefaces the way a printed book does.
- Product or catalogue cards ruled in dark ink on paper, each with its price set in the heavy grotesk.

## Range

- **Figures:** a number in the 800 grotesk knocked out of a grained fluorescent block in `on-fill`, its label in the body face in dark ink on the paper below.
- **Steps:** numerals in the heavy grotesk in dark ink, each step a paragraph in the text serif, separated by ink rules; a fill shape overprints the rule at the current step.
- **Rows and forms:** rows on paper ruled in dark ink, inputs with a 1.5px ink outline at 2px radius, the primary a fluorescent fill with `on-fill` text that presses 1px right and down.
- **Bands:** one grained fluorescent band with `on-fill` type, the page's committed area of brand color.

## Avoid

Black or grey ink; fluorescent ink as text on paper; misregistration on a second heading; an ungrained flat gradient standing in for riso; two duotone photograph sections back to back; dark-ink text on the fill; shadows or rounded cards.
