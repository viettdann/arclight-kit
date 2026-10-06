# Icons

An icon is a word set in a different alphabet: it sits in a line of text and has to match that text's size, color, and weight, or it reads as pasted in from another product. These rules hold for every profile and style; a style may choose the library, not break the rules.

Contents: library · size · color · stroke · variants · accessible names · optical alignment · RTL · state swap · checks.

## One library per surface

- One icon library per surface, chosen once and recorded in DESIGN.md. Two sets on one toolbar disagree on grid, corner shape, stroke, and terminal style, and the mix is visible even at 16px.
- A missing glyph is drawn to the library's grid (24px canvas, its stroke, its corner radius) or replaced by a word, not borrowed from another set.
- SVG only, never raster or an icon font: a font icon fails silently into a box or a letter when the font is blocked, and can't take per-path stroke rules.
- Draw at the smallest size it renders (often 16px). A set with separate 16, 20, and 24 drawings is used size for size: shrinking the 24 version to 16px puts its strokes between pixels, and they blur.

## Size in em

- An icon next to text is sized in `em`, 1em to 1.25em of the adjacent font size (`size-[1.125em]`, `width: 1.125em; height: 1.125em`). It then scales with the text under zoom, a larger label, or a denser variant; a fixed `16px` icon next to text that grew to 20px looks shrunken.
- Standalone icons (icon-only buttons, empty states) use the size tokens of the component: 16 or 20px inside a 32–40px hit area, never the icon filling the target.
- `flex-shrink: 0` on the icon, so a long label wraps instead of squeezing the icon to a sliver.

## Color

- `currentColor` for stroke and fill, so the icon follows the text color and every state (hover, active, disabled, `forced-colors`) changes it with no extra rule. Hardcoded fills (`fill="#666"`) from an imported SVG are rewritten to `currentColor`.
- An icon is the same color as its label, or one step quieter (`text-muted`) when it is decoration next to text. A colored icon beside grey text reads as a status signal it doesn't carry.
- Under `forced-colors: active`, `currentColor` follows the system text color with no extra rule; a hardcoded hex can end up near the system background and vanish.

## Stroke tracks text weight

The visible stroke matches the weight of the text beside it, measured in rendered pixels:

| Adjacent text | Rendered stroke |
| --- | --- |
| 400 (regular) | about 1.5px |
| 500–600 (medium, semibold) | about 2px |
| 700 (bold), or an emphasized standalone icon | about 2.5px |

- Stroke widths in a 24px-grid SVG scale with the icon: `stroke-width="2"` drawn at 16px paints about 1.33px, and at 24px paints 2px, so two icons on one row at different sizes show different weights. Fix the rendered width instead: Lucide's `absoluteStrokeWidth`, or `vector-effect: non-scaling-stroke` on the SVG's shapes with `stroke-width` set in px.
- Set the stroke once per context (a button variant, a nav, a table row), not per icon, so a semibold button label and its icon never drift apart.
- A library without stroke variants (filled sets) keeps its native weight; emphasis then comes from size or color, not a faux stroke.

## Outline default, filled active

- Outline is the default state in toolbars, list rows, and inline text. Filled is the selected or active state of the same glyph: the active tab, a toggled bookmark, a liked heart.
- Never mix the two as decoration. With filled icons everywhere, the active tab has no state signal left; with a filled icon that isn't active, the reader assumes it is.
- The filled variant isn't the only carrier of state: the control also has `aria-pressed`, `aria-selected`, or `aria-current`, and the label or a text cue where color and shape could be missed.

## Accessible names

- An icon-only button has an accessible name (`aria-label="Delete draft"` or visually hidden text) naming the action, not the glyph ("Close", not "X icon"). A tooltip alone is not a name: it shows on hover only and many screen readers skip it.
- The SVG inside it is `aria-hidden="true"`, so a `<title>` in the SVG isn't read on top of the button's name.
- An icon beside a visible label is decorative: `aria-hidden="true"`, no `title`. An icon that carries meaning on its own in running text (a status glyph in a table cell) gets `role="img"` and an `aria-label`.

## Optical alignment

Geometric centering is wrong for some shapes; the eye centers mass, not the bounding box.

- A play triangle centered in a circle looks left of center because its mass sits on the flat side: nudge it right by about 1px at 16px (about 6% of the icon box).
- A chevron or arrow after text (`Next →`, a disclosure chevron) sits off its box center by design; nudge it down or across about 1px so it lines up with the x-height, not the cap height.
- `align-items: center` centers the icon on the line box, which can sit a pixel off against all-caps labels or tabular numbers. Check at 2x zoom and nudge with `translate`, never with padding or margin that changes the hit area or the row height.

## RTL

Under `dir="rtl"`, mirror icons whose meaning follows reading direction and leave the rest alone.

| Mirror | Don't mirror |
| --- | --- |
| Back and forward arrows, navigation chevrons, breadcrumb separators | Clocks and anything showing clockwise time |
| Reply, undo, redo, send, external-link arrows | Checkmarks |
| Text alignment, list, and indent glyphs | Media play, pause, fast-forward (they follow tape direction, not text) |
| Progress and slider direction | Brand logos and real-world objects (cup, pencil, camera) |

- One mechanism per element: `[dir="rtl"] .icon-directional { scale: -1 1; }` or `rtl:-scale-x-100`. A flip in the component plus a flip in the page cancel back to unmirrored.
- Composite icons are judged by part: a badge or a slash keeps its position while the base arrow flips.

## State swap

- An icon that changes on an infrequent state change (copy → copied, play → pause, bookmark → bookmarked) crossfades with a slight scale and blur rather than popping, per `${CLAUDE_PLUGIN_ROOT}/skills/ui-interaction/references/motion.md`. Both icons share one grid cell so the button doesn't change width.
- Tab and navigation icon swaps, hover-revealed row actions, and decorative icons change instantly: animating a tab's icon delays the signal the user just asked for.
- Under `prefers-reduced-motion: reduce` the swap keeps only the opacity fade.

## Checks

- [ ] One icon library on the surface, SVG only, no glyph borrowed from another set.
- [ ] Icons beside text sized 1–1.25em and `flex-shrink: 0`; standalone icons use the component's size token.
- [ ] `currentColor` everywhere; no hardcoded fills; visible in `forced-colors`.
- [ ] Rendered stroke matches adjacent text weight (~1.5 / 2 / 2.5px) and is equal across icon sizes on one row (`absoluteStrokeWidth` or `non-scaling-stroke`).
- [ ] Outline by default, filled only as the active state, with ARIA state alongside.
- [ ] Every icon-only button has an accessible action name; its SVG is `aria-hidden`.
- [ ] Play triangles and trailing chevrons checked at 2x zoom and nudged where off-center.
- [ ] Under `dir="rtl"`, directional icons mirror once; clocks, checkmarks, media controls, and logos don't.
- [ ] State swaps crossfade only where infrequent; tab and nav icons change instantly.
