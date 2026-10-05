# Profile: Marketing and Consumer

For pages that have seconds to explain something and win a decision. Concrete beats decorative: a generated page decorates because it has nothing specific to show.

Consumer-app screens (onboarding, home, progress) use Design read, Copy, Generic tells, Visual, and Avoid; Page structure, Layout rules, Pricing, Imagery, and the hero Checks apply to marketing pages only.

Contents: Design read · Page structure · Layout rules · Pricing · Imagery · Copy · Generic tells · Visual (type, radius, elevation, motion) · Avoid · Checks

## Design read

Before markup, decide one line, and open the summary with it: **page kind · audience · visual language · the one move that makes it this brand's page.** Example: "Launch page for procurement leads · calm, document-like · the product's approval trail runs down the page as the spine."

- The audience picks the language, not habit. Public-sector, regulated, or accessibility-first audiences override aesthetic ambition.
- The three default looks (design skill, Rules: cream, serif, and terracotta; near-black, one neon accent, and glow; newspaper hairlines, italic serif, and tracked mono labels) are habit too: use one only when the brief asks for it. If the product category alone predicts the look, choose again.
- The move is the page's **second-read moment**: a single unobvious but legible motif used once (an oversized number for a result the reader should remember, one material or color switch, a macro crop of the product). It must help scanning or brand recall. Restraint alone produces a clean page nobody remembers. It is also the one special element that may take a gradient, texture, glow, or style material, and the one highlighted element per view; a chosen style adds at most one more of its signature moves.
- Memory test: someone who leaves after the first viewport can describe it an hour later in concrete terms. If all they could describe is a mood, the move isn't committed yet.
- Habitual display faces (Fraunces, Playfair, Cormorant, Space Grotesk, IBM Plex, DM Serif, Instrument Sans, Inter as display) need a reason tied to this product; "the subject is warm or bookish" is not one.
- If the brief names a real design system (GOV.UK, USWDS, Carbon, Polaris, Primer, Material), use the official package instead of imitating it.

## Page structure

- Hero: the headline names the outcome, the subhead names the audience and how; one primary CTA, and any secondary action is a text link; a real product visual instead of abstract art.
- When the category has a first action people come to do (search flights by route and date, pick an open appointment slot, add to cart), the hero carries it in working form; a link to it further down doesn't count.
- Order: hero → proof → problem → how it works → proof or pricing → final CTA repeating the hero CTA exactly.
- Proof is attributable: a named person, their role, and a measurable result. Logos only if real and recognizable.
- Aggregate numbers anywhere on the page (customer counts, "median close time", "% auto-matched", "9 in 10") appear only when the user supplied them. An invented plausible stat reads as proof and ships by accident; while drafting, write a visible placeholder like `[median close time]` and list it in the notes.
- Benefits are outcomes, at most three per section. Annotate real product UI instead of an icon grid.
- Pricing follows the Pricing section below.
- The most important message goes first and last; the middle is remembered least.
- Flows end on a success screen with a next step, not a flat confirmation.

## Layout rules

- **Hero fits the first viewport** at 1280×800: headline at most 2 lines, subhead about 20 words, CTA visible without scrolling. If it doesn't fit, lower the type scale or cut copy; a 4-line headline is a font-size error. At most four text elements: optional eyebrow, headline, subhead, CTAs. Trust strips, pricing teasers, and "works with…" taglines go in the section below.
- Full-height sections use `min-height: 100dvh`, not `100vh`/`h-screen` (mobile address bars make `vh` jump).
- Navigation stays on one line at desktop, 64–72px tall. On narrow screens the links can drop away only when there are two or fewer; with three or more, a menu button opens them (closes on Esc, on a link, and on outside click) so mobile visitors can still reach every section.
- **Vary the section layouts.** Each layout family (3-up cards, image+text split, full-width quote, bento) appears once; more than two image+text splits in a row reads as a template.
- **Grids have exactly as many cells as content.** Five items → five cells (2+3, hero+4); never a blank tile to complete the grid.
- Every multi-column section states its narrow-screen layout in the same component, not "Tailwind will handle it".
- Display-size numbers are for quantities worth remembering (a result, a price), not for labels such as times, dates, or step numbers; those stay at heading size. Large type never overlaps or crowds neighboring text at any width.
- All sections share one container width and edges. A block narrower than the container (prose at 65ch) is placed deliberately, not left hugging one side with the rest empty.
- One theme for the whole page. A light section inside a dark page (or the reverse) reads as a pasted-in block unless it is one deliberate, single switch.

## Pricing

- One recommended tier, marked with more than color (border or elevation, position, a badge). The others step back by losing border and elevation, never by fading their text; prices keep full contrast.
- One badge on the page, on the recommended tier; no runner-up labels. "Most popular" is a claim about real data: use it only when the user supplied it, otherwise "Recommended".
- Feature lists show the difference: the first tier lists its 4–6 key features, each next tier opens with "Everything in Starter, plus" and lists only what it adds. A full feature matrix, if needed, goes in a comparison table below the tiers.
- One filled button, on the recommended tier; the others are secondary or outlined, and none is a gradient. CTA labels follow one pattern across tiers ("Choose Starter", "Choose Team"); a tier that goes to sales says "Talk to sales".
- The annual saving is written in money, not percent: "Save $98/year", computed from the page's own monthly and annual prices, with the billed total beside the price ("$41/mo, billed $490 yearly"). If the annual price isn't given, leave a visible placeholder like `[annual price]`. The saving label uses the accent or neutral text, never the danger color.

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
| Glass cards over a static background, glow on everything, emoji section headings | Solid surfaces, one elevation style, plain headings; glass only on layers floating over moving content, unless the brief asks for a glassy look (`materials.md`) |
| Small uppercase eyebrow above every section heading | The heading alone; at most one eyebrow per three sections |
| Numbered eyebrows (`001 · Capabilities`, `06 / How it works`), `01 / 04` on tiles | Plain topic heading, or nothing |
| Section header split into big headline left, small paragraph floating right | Headline with the paragraph directly beneath it |
| Version tags in the hero (`v0.6`, `BETA`, `Invite-only`) when it isn't a launch | Nothing |
| "Scroll to explore", bouncing chevrons | Nothing; the fold is not a problem to label |
| Stock headline openers ("Built for…", "Meet your new…", "The future of…") | The concrete outcome, in the reader's words |
| "Learn more" as a CTA label | What the click gets ("See pricing", "Read the API docs") |
| City, local time, or weather strips; `Brand · No. 01` micro-meta; build numbers in the footer | Nothing, or a real contact address once |
| Pills or credit captions laid over photos (`Plate 03 · Archive`) | The image alone, or a one-line caption below it |
| Decorative colored dots before nav items, labels, list rows | Nothing; dots only for real live state |
| "Step 1 / Step 2 / Step 3" labels | The step's verb as the label ("Connect", "Review", "Ship") |
| Hairline under every row of a long spec list | Group into 2–3 labeled clusters, or feature 3–4 specs and collapse the rest |
| Two or more marquees | At most one, where breadth is the point |

## Visual

- Body 16–18px with line-height 1.5–1.7, prose width 60–75ch. Scale ratio 1.25–1.333 with a display step; headings at least ~2× body. Weights, heading line-heights, and tracking follow `typography.md`. Italic display words with descenders (g, j, p, q, y) need line-height ≥ 1.1 or they clip.
- Generous space: section padding 64–128px on desktop; hero top padding no more than ~96px, or the content floats halfway down the viewport.
- Radius from this table, looked up per element rather than chosen by feel; an element not listed takes the row of the closest size. A style may override rows (its file says which); everything else stays. Record the result in `DESIGN.md` as tokens.

  | Element | Radius |
  |---|---|
  | Band inside the container, large panel, bottom sheet (top corners only) | 16px |
  | Card, demo window, pricing tier, modal | 12px |
  | Surface nested in padding (inner panel, media frame in a card) | outer − padding, never below 6px |
  | Button (primary and secondary), input, segmented control, popover, tooltip | 8px |
  | Chip, tag, badge, small control under 28px tall | 6px |
  | Dot, avatar, icon-only round button | full |

  A full-bleed band is square: sides flush with an edge take no radius (`radius.md`). No pills by default. A pill-shaped button, chip, or tag appears only when the chosen style lists it.
- Elevation from layered shadows, used only where lift carries meaning; glass on floating layers over moving content (`materials.md`).
- Interactive card hover: translateY(-2px to -6px) with a stronger shadow over 150–250ms `--ease-enter`. Scale media inside an `overflow: hidden` frame (at most 1.05); never scale the card itself, it shifts neighbors.
- Motion: entrances 200–300ms `--ease-enter`, exits faster with `--ease-exit`, staggers 40–60ms with a capped total. A slight spring is fine for confirmation moments, never for layout. Scroll reveals are subtle and run once, and content is never hidden by default: apply the hidden start state only after the script has run (`.js .reveal`), show everything at once under `prefers-reduced-motion` or without `IntersectionObserver`, so a script error, a blocked script, or a crawler still sees the page. Each animation needs a one-sentence reason (hierarchy, sequence, feedback, state change); "it looks alive" isn't one.
- Gradients, glow, and texture follow `materials.md`: only on the design read's move, never under body text.

## Avoid

Hero carousels, autoplaying video with sound, parallax that moves text, more than one highlighted element per view (the design read's move).

## Checks

- [ ] Design read, with its one move, stated in the summary.
- [ ] Hero fits 1280×800 with the CTA visible; nav on one line, with a menu on narrow screens when it has three or more links; no display type colliding with other text.
- [ ] Revealed content is visible without JS and under reduced motion.
- [ ] No layout family repeated; no empty grid cells.
- [ ] No div-built fake screenshots; missing images are labeled slots listed in the summary.
- [ ] Every visible string re-read; one label per CTA intent; no em dashes in copy.
- [ ] Pricing has one highlighted tier, one badge, one filled button, diff-only feature lists, and the saving in money.
- [ ] `scan_tells.py` leaves no `6-marketing` hit unexplained.
