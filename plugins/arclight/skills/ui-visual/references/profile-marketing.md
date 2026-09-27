# Profile: Marketing and Consumer

For pages that have seconds to explain something and win a decision. Concrete beats decorative: a generated page decorates because it has nothing specific to show.

## Page structure

- Hero: the headline names the outcome, the subhead names the audience and how; one primary CTA, and any secondary action is a text link; a real product visual instead of abstract art.
- Order: hero → proof → problem → how it works → proof or pricing → final CTA repeating the hero CTA exactly.
- Proof is attributable: a named person, their role, and a measurable result. Logos only if real and recognizable.
- Aggregate numbers anywhere on the page (customer counts, "median close time", "% auto-matched", "9 in 10") appear only when the user supplied them. An invented plausible stat reads as proof and ships by accident; while drafting, write a visible placeholder like `[median close time]` and list it in the notes.
- Benefits are outcomes, at most three per section. Annotate real product UI instead of an icon grid.
- Pricing highlights one recommended plan with more than color (badge, border or elevation, position); the others stay calm and identical.
- The most important message goes first and last; the middle is remembered least.
- Flows end on a success screen with a next step, not a flat confirmation.

## Generic tells and their replacements

| Tell | Replacement |
| --- | --- |
| Gradient headline full of adjectives (supercharge, seamless, powerful) | Plain text stating a concrete outcome |
| Purple or indigo blob gradients behind everything | Neutral background; color only on the product visual and the primary CTA |
| Two equal buttons side by side | One primary button plus a text link |
| "Trusted by 10,000+" above anonymous grey logos | One attributable quote with a result and a unit |
| Three cards, icon in a circle, one word each | A product screenshot with three annotations |
| Glassmorphism, glow on everything, emoji section headings | Solid surfaces, one elevation style, plain headings |

## Visual

- Body 16–18px with line-height 1.5–1.7, prose width 60–75ch. Headings at least ~2× body, line-height 1.1–1.2, slightly tightened tracking at large sizes.
- Generous space: section padding 64–128px on desktop.
- Radius medium to large and consistent: 8–12px controls, 16–24px large cards.
- Elevation from layered shadows (a tight contact shadow plus a soft ambient one), tinted toward the background hue rather than pure black, used only where lift carries meaning.
- Interactive card hover: translateY(-2px to -6px) with a stronger shadow over 150–250ms ease-out. Scale media inside an `overflow: hidden` frame (at most 1.05); never scale the card itself, it shifts neighbors.
- Motion: entrances 200–300ms ease-out, exits faster, staggers 40–60ms with a capped total. A slight spring is fine for confirmation moments, never for layout. Scroll reveals are subtle and run once.
- Gradients stay within adjacent hues (about 60° of travel), move lightness in one direction, interpolate `in oklch`, add slight noise against banding, and never sit under body text.

## Avoid

Hero carousels, autoplaying video with sound, parallax that moves text, more than one highlighted element per view.
