# Style: Technical

Engineered, evidence-first pages for a technical buyer: a dark layered canvas, one warm accent, small radii, flat surfaces, and measured numbers as the hero content. Reads as precise and honest; fails when the numbers have no source, or when the look turns into a costume (mono everywhere, fake terminals, neon glow).

**Fits:** "technical", "engineered", "precise", "benchmark-led", "numbers-first", "spec sheet", CoralBricks-like pages, for APIs, infrastructure, inference, databases, and developer platforms whose claim can be measured. **Profile:** marketing (landing, pricing, model or plan pages). Not for tool screens; when the product's app takes this style, apply its palette, type, and radius on top of the tool profile (design skill, step 4).

Differs from cinematic dark tech: no light source, no glow, no viewport-scale type, no scroll story. The proof carries the page, not the atmosphere.

## Decisions

- **Canvas:** dark by default; this overrides the light-by-default rule, because the style's audience compares it with their editor and terminal and the brief chose the style for that. A light canvas when the brand is light or the brief asks. Dark is built per `dark-mode.md`: a near-black tinted toward the brand hue, surfaces stepped in lightness, alpha inks and hairlines.
- **Accent:** one warm or saturated brand hue that is not neon (coral, vermilion, amber, signal green are typical; cyan or magenta on black is the habitual look (b) in the design rules and needs the brief to ask). Spent on the primary CTA, the hero's measured numbers, and the accented half of a headline. Calm it per `dark-mode.md` until `on-accent` text passes; never a glow.
- **Neutrals against the accent:** the neutrals take a hue roughly opposite the accent (cool blue-grey under a warm accent, warm grey under a green or blue one), overriding `tokens.md`'s tint toward the brand hue: the accent stands out by hue contrast alone, which is what lets the page skip glow. Chroma stays low, rising slightly with lightness.
- **Layer steps (dark):** one large step from canvas to the first surface, then small ones, so cards read as objects and nested layers stay quiet:

  | Role | OKLCH lightness | Chroma |
  |---|---|---|
  | canvas | 0.15–0.17 | 0.010–0.012 |
  | surface (cards, tiles, bands) | canvas + 0.08–0.09 | ~0.020 |
  | raised (inputs, secondary buttons, hover) | surface + 0.02–0.04 | ~0.025 |
  | secondary button border (its label identifies it) | 0.44–0.46 | ~0.014 |
  | input border (must pass 3:1 on surface and raised) | 0.58 or above | ~0.014 |

- **Accent as text:** a mid-lightness accent (L about 0.58) on the canvas sits near 4.2:1, which passes only for large text. Accent text below the large size (24px, or 18.7px bold) either takes a lighter step of the accent that passes 4.5:1, or stays in the ink color. Check both pairs, accent on canvas and `on-accent` on the accent, with `scripts/contrast.mjs`.
- **Default palette:** the brand's colors always win. When the brief and the code give no brand color, use this set (from CoralBricks) instead of choosing a new one, and list it as an assumption in the summary:

  | Token | OKLCH | Hex |
  |---|---|---|
  | canvas | `oklch(0.155 0.011 268)` | `#0A0C11` |
  | surface | `oklch(0.243 0.021 264)` | `#1B202A` |
  | raised | `oklch(0.281 0.027 267)` | `#232937` |
  | secondary button border | `oklch(0.445 0.014 264)` | `#50545C` (2.15:1 on surface, decorative only) |
  | input border | `oklch(0.58 0.014 264)` | (3.81:1 on surface, 3.39:1 on raised) |
  | accent | `oklch(0.584 0.189 32)` | `#D44027` |
  | on-accent | white | `#FFFFFF` (4.60:1) |
  | ink | white at the `dark-mode.md` alphas | `#FDFDFD` base |
  | light band canvas | `oklch(0.985 0.002 264)` | |
  | light band border | `oklch(0.904 0.007 269)` | `#DDDFE4` |

  The accent measures 4.25:1 on the canvas and 4.41:1 on the light band: large text only on both, per the rule above.
- **Type:** one neo-grotesk sans for display and body, display 56–72px at weight 500–600, tracking -0.02 to -0.03em, line-height 1.0–1.05; body 17–18px. Mono (with `tabular-nums`) only for measured values, prices, model or API ids, and code, which this style has a lot of; never for headings, labels, or eyebrows.
- **Accented headline:** a two-clause headline with the second clause in the accent ("Faster and **cheaper tokens.**"). In the hero and in the final CTA that repeats it; not on every section heading, where it becomes a formula.
- **Radius:** small and tight. Use the marketing profile's radius table with these overrides; every other row stays as the profile sets it:

  | Element | Override |
  |---|---|
  | Band inside the container, large panel | 12px |
  | Card, stat tile, demo window, pricing tier, modal | 10px |
  | Chip, tag, badge | 4px |

  No pills, including the primary CTA and the nav.
- **Depth:** flat. Surfaces separate by lightness steps and alpha hairlines (`materials.md`, Lightness layers). The primary button takes the **lit edge** (`materials.md`, Style materials); one floating object per page (the demo panel or playground) may take the profile's shadow. Nothing else lifts on hover; hover changes surface lightness or the hairline.
- **Proof:** every number on the page is measured and sourced. A stat tile is the value (mono, accent or full ink), one line saying what it measures with its unit, and a muted source line (sample size, date, or "listed rate, Oct 8, 2026"). Only numbers the user supplied; otherwise a visible placeholder (`[p50 TTFT]`) per the marketing profile. Stat tiles sit beside the claim they prove, in a grid with exactly as many cells as numbers.
- **Code:** the integration is shown as real, copyable code (a base URL and a key, a `curl`, a config block) with a copy button (`../ui-interaction/references/feedback.md`), not as a screenshot or a div-built terminal.
- **Space:** section padding 96–128px on desktop; grids on the profile's container; one light band at most, as the page's single deliberate theme switch (marketing profile, Layout rules), placed where the reader compares (models, plans, pricing).
- **Motion:** fast and functional: 150–250ms `--ease-enter`, fades and 8px rises run once. Numbers never count up: the reader must see the real value at first paint and under reduced motion. Live motion is reserved for a real demo (a streamed answer, a running request) and the one canvas effect.

## Signature moves (examples)

These show the style's spirit; they are not a menu. Derive the surface's distinctive move from the product first, and use one of these only when it fits better. Never more than two per page.

- **An illustrated scene drawn from the brand name** behind the hero (CoralBricks: a coral reef whose fish scatter on click), as a canvas effect per `canvas-effects.md`: one per page, a static poster first, paused offscreen, still under reduced motion, text checked against its brightest frame. The interaction is a small reward, never required to read the page.
- **A working demo in the first two sections:** a real prompt box, request builder, or query that runs against the product, with the primary action inside it.
- **A measured-number grid** right after the hero: three or four stat tiles with their sources, the page's proof in one glance.
- **A rate card:** model or plan cards whose prices are mono and right-aligned with a dated source line, comparable at a glance.

## Avoid

Glow, gradients on text or buttons, neon accents on black; mono as a costume on headings and labels; fake terminals or dashboards built from `div`s; numbers without a source line, or count-up animations; the accented headline on every section; more than one marquee (logos and testimonials both scrolling is the common slip: let one sit still); more than one light band; pill buttons; benchmark claims ("fastest", "lowest") in the headline without a measured number on the same screen.
