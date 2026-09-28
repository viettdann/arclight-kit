# Profile: Marketing and Consumer

For pages that have seconds to explain something and win a decision. Concrete beats decorative: a generated page decorates because it has nothing specific to show.

## Design read

Before markup, write one line in the summary: **page kind · audience · visual language · the one move that makes it this brand's page.** Example: "Launch page for procurement leads · calm, document-like · the product's approval trail runs down the page as the spine."

- The audience picks the language, not habit. Public-sector, regulated, or accessibility-first audiences override aesthetic ambition.
- Pick one **second-read moment**: a single unobvious but legible motif used once (an oversized number for a result the reader should remember, one material or color switch, a macro crop of the product). It must help scanning or brand recall. Restraint alone produces a clean page nobody remembers.
- If the brief names a real design system (GOV.UK, USWDS, Carbon, Polaris, Primer, Material), use the official package instead of imitating it.

## Page structure

- Hero: the headline names the outcome, the subhead names the audience and how; one primary CTA, and any secondary action is a text link; a real product visual instead of abstract art.
- Order: hero → proof → problem → how it works → proof or pricing → final CTA repeating the hero CTA exactly.
- Proof is attributable: a named person, their role, and a measurable result. Logos only if real and recognizable.
- Aggregate numbers anywhere on the page (customer counts, "median close time", "% auto-matched", "9 in 10") appear only when the user supplied them. An invented plausible stat reads as proof and ships by accident; while drafting, write a visible placeholder like `[median close time]` and list it in the notes.
- Benefits are outcomes, at most three per section. Annotate real product UI instead of an icon grid.
- Pricing highlights one recommended plan with more than color (badge, border or elevation, position); the others stay calm and identical.
- The most important message goes first and last; the middle is remembered least.
- Flows end on a success screen with a next step, not a flat confirmation.

## Layout rules

- **Hero fits the first viewport** at 1280×800: headline at most 2 lines, subhead about 20 words, CTA visible without scrolling. If it doesn't fit, lower the type scale or cut copy; a 4-line headline is a font-size error. At most four text elements: optional eyebrow, headline, subhead, CTAs. Trust strips, pricing teasers, and "works with…" taglines go in the section below.
- Full-height sections use `min-height: 100dvh`, not `100vh`/`h-screen` (mobile address bars make `vh` jump).
- Navigation stays on one line at desktop, 64–72px tall.
- **Vary the section layouts.** Each layout family (3-up cards, image+text split, full-width quote, bento) appears once; more than two image+text splits in a row reads as a template.
- **Grids have exactly as many cells as content.** Five items → five cells (2+3, hero+4); never a blank tile to complete the grid.
- Every multi-column section states its narrow-screen layout in the same component, not "Tailwind will handle it".
- Display-size numbers are for quantities worth remembering (a result, a price), not for labels such as times, dates, or step numbers; those stay at heading size. Large type never overlaps or crowds neighboring text at any width.
- All sections share one container width and edges. A block narrower than the container (prose at 65ch) is placed deliberately, not left hugging one side with the rest empty.
- One theme for the whole page. A light section inside a dark page (or the reverse) reads as a pasted-in block unless it is one deliberate, single switch.

## Imagery

A marketing page is a visual product; text plus a gradient blob is a placeholder, not a hero.

1. If an image-generation tool is available, generate section-specific assets at the section's aspect ratio.
2. Otherwise use real assets from the brief, or seeded placeholders (`https://picsum.photos/seed/<section-context>/1600/1000`).
3. If neither fits, leave labeled slots (`<!-- hero product photo, 1600×1000 -->`) and list them in the summary.

Never draw a fake product screenshot from styled `div`s (fake task lists, dashboards, terminals). Use a real screenshot, a generated image, or an actual working mini version of the component. Logo walls use real SVG logos (Simple Icons, devicon) and nothing else, no category label under each logo.

## Copy

- Re-read every visible string before finishing: headings, buttons, captions, alt text, footer. Rewrite anything grammatically off, with unclear referents, or "cute" wordplay that doesn't track. Plain functional copy beats clever AI copy.
- One label per intent across the page: if the CTA is "Book a demo", the nav and footer don't say "Let's talk" or "Get in touch".
- One register per page: don't mix terminal-style metadata, editorial prose, and ad punchlines unless the brand voice is that.
- No em dashes (—) or en dashes used as separators in page copy; they are the most recognizable generated-copy fingerprint. Use a period, comma, colon, or hyphen.

## Generic tells and their replacements

| Tell | Replacement |
| --- | --- |
| Gradient headline full of adjectives (supercharge, seamless, powerful) | Plain text stating a concrete outcome |
| Purple or indigo blob gradients behind everything | Neutral background; color only on the product visual and the primary CTA |
| Two equal buttons side by side | One primary button plus a text link |
| "Trusted by 10,000+" above anonymous grey logos | One attributable quote with a result and a unit |
| Three cards, icon in a circle, one word each | A product screenshot with three annotations |
| Glassmorphism, glow on everything, emoji section headings | Solid surfaces, one elevation style, plain headings |
| Small uppercase eyebrow above every section heading | The heading alone; at most one eyebrow per three sections |
| Numbered eyebrows (`001 · Capabilities`, `06 / How it works`), `01 / 04` on tiles | Plain topic heading, or nothing |
| Section header split into big headline left, small paragraph floating right | Headline with the paragraph directly beneath it |
| Version tags in the hero (`v0.6`, `BETA`, `Invite-only`) when it isn't a launch | Nothing |
| "Scroll to explore", bouncing chevrons | Nothing; the fold is not a problem to label |
| City, local time, or weather strips; `Brand · No. 01` micro-meta; build numbers in the footer | Nothing, or a real contact address once |
| Pills or credit captions laid over photos (`Plate 03 · Archive`) | The image alone, or a one-line caption below it |
| Decorative colored dots before nav items, labels, list rows | Nothing; dots only for real live state |
| "Step 1 / Step 2 / Step 3" labels | The step's verb as the label ("Connect", "Review", "Ship") |
| Hairline under every row of a long spec list | Group into 2–3 labeled clusters, or feature 3–4 specs and collapse the rest |
| Two or more marquees | At most one, where breadth is the point |

## Visual

- Body 16–18px with line-height 1.5–1.7, prose width 60–75ch. Headings at least ~2× body, line-height 1.1–1.2, slightly tightened tracking at large sizes. Italic display words with descenders (g, j, p, q, y) need line-height ≥ 1.1 or they clip.
- Generous space: section padding 64–128px on desktop; hero top padding no more than ~96px, or the content floats halfway down the viewport.
- Radius medium to large and consistent: 8–12px controls, 16–24px large cards. One documented rule, applied everywhere.
- Elevation from layered shadows (a tight contact shadow plus a soft ambient one), tinted toward the background hue rather than pure black, used only where lift carries meaning.
- Interactive card hover: translateY(-2px to -6px) with a stronger shadow over 150–250ms ease-out. Scale media inside an `overflow: hidden` frame (at most 1.05); never scale the card itself, it shifts neighbors.
- Motion: entrances 200–300ms ease-out, exits faster, staggers 40–60ms with a capped total. A slight spring is fine for confirmation moments, never for layout. Scroll reveals are subtle and run once. Each animation needs a one-sentence reason (hierarchy, sequence, feedback, state change); "it looks alive" isn't one.
- Gradients stay within adjacent hues (about 60° of travel), move lightness in one direction, interpolate `in oklch`, add slight noise against banding, and never sit under body text.

## Avoid

Hero carousels, autoplaying video with sound, parallax that moves text, more than one highlighted element per view.

## Checks

- [ ] Design read and second-read moment stated in the summary.
- [ ] Hero fits 1280×800 with the CTA visible; nav on one line; no display type colliding with other text.
- [ ] No layout family repeated; no empty grid cells.
- [ ] No div-built fake screenshots; missing images are labeled slots listed in the summary.
- [ ] Every visible string re-read; one label per CTA intent; no em dashes in copy.
- [ ] `scan_tells.py` leaves no `6-marketing` hit unexplained.
