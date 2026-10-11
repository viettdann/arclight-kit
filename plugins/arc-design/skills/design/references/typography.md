# Typography

One family (plus a monospace where useful) used as a system: every size, weight, ink, line-height, and tracking comes from a small set, so hierarchy reads the same on every screen. The profile sets the base size and ratio; a style may override rows and says which.

## Size scale

- Build the scale from the base size and one ratio, not hand-picked values: tool 1.2–1.25, marketing 1.25–1.333. At 1.25 from 13px: 13, 16, 20, 25, 32.
- Round each step to a whole pixel. About five steps for a tool, plus one display step for marketing. A size between steps is off-scale.
- Size ranks blocks (page title, section heading, body). Inside a block or a row, rank with ink and weight instead of another size; a metric's value is its own step and may be larger than its label.
- Heading sizes descend with level within a section (`h2` larger than `h3`), and no heading is smaller than body text; a deliberate overline is the one exception.
- Font sizes are in `rem`, so they follow the user's browser text size; `px` sizes ignore it.
- Across widths, large steps shrink more than small ones: body keeps its size while a 48px display drops to about 28–32px on a phone. Step down by switching to a smaller ratio below the breakpoint (marketing 1.333 to 1.2), or by a `clamp()` on display and heading steps only, never one factor applied to every size. Padding on large containers tightens the same way while control padding stays. Tool surfaces keep fixed steps (`profile-tool.md`).

## Ink

Three text inks carry the hierarchy within a line:

| Token | Role | Example |
| --- | --- | --- |
| `text` | What the user scans for | Amount, name, title |
| `text-muted` | Supporting, still read | Invoice id, secondary label |
| `text-subtle` | Present but quiet | Date, metadata, caption |

All three pass 4.5:1 on every surface they sit on; check them with the design skill's `scripts/contrast.mjs`. `text-disabled` is for disabled controls only, never a way to make text quiet, and still reaches 3:1 so the label of an unavailable action can be read.

## Weight

- Two weights: 400 to read (body, cells, descriptions), 600 to scan (headings, key values, the label that anchors a row).
- Weight marks single elements. A bold paragraph, a bold table, or bold on every label leaves nothing to find.
- No 500, and nothing above 600 unless the chosen style lists it.
- A style that uses light weights (100–300) keeps them to display sizes of about 28px and up: below that the thin strokes break up on screen and fall under contrast even when the color passes.
- Set weight with `font-weight`, never `font-variation-settings: "wght" 600`: the variation setting does nothing on a static fallback font, so the heading silently renders at 400 when the variable file fails to load.
- Raw `font-variation-settings` and `font-feature-settings` tags are only for features no CSS property covers (a stylistic set such as `"ss01"`, a custom axis such as `"GRAD"`). Weight, width, slant, optical size, figures, and small caps have their own properties (`font-weight`, `font-stretch`, `font-style`, `font-optical-sizing`, `font-variant-numeric`, `font-variant-caps`); a raw declaration replaces the element's whole tag list, so one added tag silently drops the others it inherited.

## Line-height and tracking

Line-height drops as size rises; tracking moves only at the extremes.

| Size | Line-height | Tracking |
| --- | --- | --- |
| Body and small (up to 18px) | 1.5; marketing prose 1.5–1.7 | 0 |
| ~20px | 1.35 | 0 |
| ~25px | 1.2 | -0.01em |
| 32px and up | 1.1 (a style may go to 0.9 for uppercase or caseless display with no descenders) | -0.02em |
| Uppercase label under 16px | as its size | +0.04 to +0.06em |

- Line-height is unitless (`1.5`, or Tailwind's named `leading-tight`/`leading-normal`): a hand-written or arbitrary `px` or `rem` line-height (`leading-[24px]`) is inherited as a fixed length, so a larger child inherits a line-height too tight for it.
- Text that can wrap to three or more lines gets at least 1.4, even inside a row with a fixed height; give the row room or truncate instead of tightening the lines.
- Tracking is in `em`, never `px`, so it scales with the size it sits on.
- `font-kerning: none` is never a fix: a pair that looks wrong is a font or size choice, and turning kerning off breaks every other pair.

## Space around headings

A heading belongs to the text below it: the space above a heading is larger than the space below it, so the heading groups with its section instead of floating between two.

## Loading fonts

- Load only the families and weights the scale uses, `font-display: swap`, and preload the one file the first viewport needs.
- Load every weight and style the page actually renders, italic included: a missing one makes the browser smear or slant the nearest file into a faux bold or italic with wrong spacing. `font-synthesis: none` during review turns each missing file into a visible plain-weight fallback instead.
- Match the fallback's metrics (`size-adjust`, `ascent-override`, or the framework's font loader such as `next/font`) so the swap doesn't reflow the page; ui-check reports that reflow as layout shift.
- Font smoothing (`antialiased`, `-webkit-font-smoothing`) is set once on the root (`html` or `body`), never per component, so text doesn't change weight from one component to the next.

## Measure

- Prose runs 45–75 characters per line (`max-width: 65ch`, `max-w-prose`).
- Cap the text element, not the container: the page keeps its full width, and tables, cards, and grids still fill it.
- Headings get `text-wrap: balance`, so a two-line title splits into even lines instead of one full line and a dangling word; Chromium balances only up to about 6 lines, so it does nothing on long text. Body text gets `text-wrap: pretty`, which avoids a single word alone on the last line of a paragraph. Neither goes on a container of user content or a live-editing field, where the extra layout pass costs on every change.

## Characters and case

- Store text in its natural case and apply uppercase or small caps with `text-transform`: a string typed in capitals is read letter by letter by some screen readers, copies as capitals, and forces translators to keep the case.
- Use the real ellipsis `…` (U+2026), not three periods, which can break across lines and space unevenly.
- A number and its unit, or a short word that must stay with the next one, are joined by a non-breaking space (`10&nbsp;km`, `5&nbsp;MB`, `Mar&nbsp;3`; U+00A0 in strings), so a line never ends on "10" with "km" starting the next.

## Details

- In buttons and badges, `text-box: trim-both cap alphabetic` trims the space above the cap height and below the baseline, so the label sits in the optical center of its padding. It is progressive enhancement: the padding must still look right in browsers that ignore it.
- Underlines are placed with `text-underline-offset` (or `text-decoration-thickness: from-font`), never by turning off `text-decoration-skip-ink`, which runs the line through descenders. A dotted underline marks a defined term (an `<abbr>` or a term with a definition on focus), not a link.
- `user-select: none` only on controls and on drag and gesture surfaces, never on text people may want to copy (`${CLAUDE_PLUGIN_ROOT}/skills/ui-interaction/references/baseline.md`, Mobile web and locale).

## Long text

Real content is longer than the sample: a 40-character name, an email on a long domain, a URL with no spaces. Every text slot either truncates or wraps, and that has to actually happen.

- Truncate with CSS, never by cutting the string (`name.slice(0, 20) + "…"`): the DOM keeps the full text for screen readers, find-in-page, and copy, and the cut follows the real width. The full value stays reachable by keyboard and touch: the detail view, an expand control, or a tooltip on a focusable element, never a `title` alone.
- An ellipsis inside a flex or grid item never fires by default. A flex item has `min-width: auto`, so it stays as wide as its content and pushes its siblings out of the card instead of truncating. Put `min-w-0` on every flex item between the container and the `truncate` element (an item that is itself `truncate` already shrinks, since `overflow: hidden` drops that minimum), use `minmax(0, 1fr)` instead of `1fr` in grid columns, and `shrink-0` on the siblings that must keep their size (avatar, badge, actions).
- Cut the middle when both ends carry meaning: an email (name and domain), a file name (its extension), a path, an id compared by its last characters. Split it into two spans in a `flex min-w-0` row, the start `truncate` and the end `shrink-0`: `dan.le.quarterly…@company.com`, `report-2026-q3-fi….pdf`. The DOM still holds the whole string.
- A string with no spaces (URL, hash, token, a long user name) has no break opportunity and forces its container wider, often into a sideways page scroll. Containers of user content get `overflow-wrap: anywhere` (Tailwind v4.1 `wrap-anywhere`, otherwise `[overflow-wrap:anywhere]`): unlike `break-word`, it also lowers the minimum width, so it holds inside flex, grid, and tables. Never `word-break: break-all`, which splits ordinary words too.
- Where a URL or path is the content itself (a settings value, a log line), add `<wbr>` after each `/` so it breaks between segments before `anywhere` has to split one.
- A multi-line preview (a card description, a comment excerpt) is cut with `display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 3; overflow: hidden` (Tailwind `line-clamp-3`; the unprefixed `line-clamp` isn't shipped in every engine yet), never by character count, which cuts mid-word and ignores the real width. The full text stays reachable through the detail view or an expand control.

## Numbers

- Numbers that stack (columns, lists, stat groups) or change in place (counters, timers, prices, badges) use `font-variant-numeric: tabular-nums` (not `font-feature-settings: "tnum"`): proportional digits give "1" and "0" different widths, so equal-length numbers end at different edges and a live counter jitters. Check that the family has tabular figures; running text keeps proportional ones.
- Numbers right-aligned, text left-aligned, so the eye compares straight down the last digit.
- Decimals line up through one precision per column plus tabular figures; CSS can't align on the decimal point, so never mix `9.9` and `9.99` in one column.
- In a money column the symbol is pinned, not glued: either in the header ("Amount, USD") with bare numbers in the cells, or in its own left-aligned slot of the cell with the number right-aligned. A column mixing currencies shows the code on every row.
- Negatives use a real minus (`−`, U+2212) or the locale's accounting format, never a hyphen.
- Big numbers are compact where they summarize (stat cards, charts, counts in nav): `Intl.NumberFormat(locale, { notation: "compact", maximumFractionDigits: 1 })` gives "3.4M", never a hand-rolled `/ 1000 + "K"`. Below 10,000 show the exact value. The exact value stays reachable (a tooltip on a focusable element, or `aria-label`), since hover alone misses touch and keyboard.
- Exact where people compare, reconcile, or pay: table columns, invoices, balances, anything they typed.
- Past events read as relative under a day ("just now", "5m ago", "2h ago") and absolute after that ("Mar 3", with the year when it isn't the current one), in `<time datetime>` with the full timestamp in a tooltip on focus and hover. Format them with `Intl.RelativeTimeFormat` (`style: "narrow"` gives "5m ago", `numeric: "auto"` gives "yesterday"), never `${n}m ago` by hand, which can't be translated; "just now" stays a product string for anything under one minute, since the API only offers "now". Relative labels refresh on a timer. Due dates, scheduled times, and dates people reconcile (booked, posted, invoiced) stay absolute.

## Checks

- [ ] Every font size is a step of the scale, in `rem`; no arbitrary sizes; headings descend with level and none is smaller than body.
- [ ] On marketing surfaces, display and heading steps shrink more than body on narrow screens; tool surfaces keep fixed steps.
- [ ] Two weights, 400 and 600, unless the style lists another.
- [ ] Rank inside a row comes from ink, and all three inks pass 4.5:1.
- [ ] Line-height drops as size rises, is unitless, and is at least 1.4 on text that wraps to three or more lines; tracking in `em`, only from ~25px up and on uppercase labels.
- [ ] Raw OpenType tags only for features with no property; no `font-kerning: none` or `text-decoration-skip-ink: none`; smoothing set once on the root; `user-select: none` only on controls and drag surfaces.
- [ ] Prose is capped at 45–75ch; headings use `text-wrap: balance` and body text `text-wrap: pretty`.
- [ ] Weight comes from `font-weight`, every rendered weight and style has its file (no faux bold or italic with `font-synthesis: none`), and weights under 400 appear only at about 28px and up.
- [ ] Case comes from `text-transform`, ellipses are `…`, and numbers stay on the line with their units.
- [ ] Space above each heading is larger than below it.
- [ ] Only used weights load, and the fallback is metric-matched.
- [ ] Every text slot holds a long value and an unbroken string: it truncates in CSS (middle when both ends matter, the full value reachable by keyboard and touch) or wraps, and nothing pushes past its container.
- [ ] Stacked and live numbers are tabular with one precision per column; compact only where it summarizes, with the exact value reachable; relative time only under a day, formatted with `Intl.RelativeTimeFormat`.
