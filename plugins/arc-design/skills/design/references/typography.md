# Typography

One family (plus a monospace where useful) used as a system: every size, weight, ink, line-height, and tracking comes from a small set, so hierarchy reads the same on every screen. The profile sets the base size and ratio; a style may override rows and says which.

## Size scale

- Build the scale from the base size and one ratio, not hand-picked values: tool 1.2–1.25, marketing 1.25–1.333. At 1.25 from 13px: 13, 16, 20, 25, 32.
- Round each step to a whole pixel. About five steps for a tool, plus one display step for marketing. A size between steps is off-scale.
- Size ranks blocks (page title, section heading, body). Inside a block or a row, rank with ink and weight instead of another size; a metric's value is its own step and may be larger than its label.

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

## Line-height and tracking

Line-height drops as size rises; tracking moves only at the extremes.

| Size | Line-height | Tracking |
| --- | --- | --- |
| Body and small (up to 16px) | 1.5 | 0 |
| ~20px | 1.35 | 0 |
| ~25px | 1.2 | -0.01em |
| 32px and up | 1.1 | -0.02em |
| Uppercase label under 16px | as its size | +0.04 to +0.06em |

## Measure

- Prose runs 45–75 characters per line (`max-width: 65ch`, `max-w-prose`).
- Cap the text element, not the container: the page keeps its full width, and tables, cards, and grids still fill it.

## Long text

Real content is longer than the sample: a 40-character name, an email on a long domain, a URL with no spaces. Every text slot either truncates or wraps, and that has to actually happen.

- Truncate with CSS, never by cutting the string (`name.slice(0, 20) + "…"`): the DOM keeps the full text for screen readers, find-in-page, and copy, and the cut follows the real width. The full value stays reachable in a tooltip or the detail view.
- An ellipsis inside a flex or grid item never fires by default. A flex item has `min-width: auto`, so it stays as wide as its content and pushes its siblings out of the card instead of truncating. Put `min-w-0` on every flex item between the container and the `truncate` element (an item that is itself `truncate` already shrinks, since `overflow: hidden` drops that minimum), use `minmax(0, 1fr)` instead of `1fr` in grid columns, and `shrink-0` on the siblings that must keep their size (avatar, badge, actions).
- Cut the middle when both ends carry meaning: an email (name and domain), a file name (its extension), a path, an id compared by its last characters. Split it into two spans in a `flex min-w-0` row, the start `truncate` and the end `shrink-0`: `dan.le.quarterly…@company.com`, `report-2026-q3-fi….pdf`. The DOM still holds the whole string.
- A string with no spaces (URL, hash, token, a long user name) has no break opportunity and forces its container wider, often into a sideways page scroll. Containers of user content get `overflow-wrap: anywhere` (Tailwind v4.1 `wrap-anywhere`, otherwise `[overflow-wrap:anywhere]`): unlike `break-word`, it also lowers the minimum width, so it holds inside flex, grid, and tables. Never `word-break: break-all`, which splits ordinary words too.
- Where a URL or path is the content itself (a settings value, a log line), add `<wbr>` after each `/` so it breaks between segments before `anywhere` has to split one.

## Numbers

- Numbers that stack (columns, lists, stat groups) or change in place (counters, timers, prices, badges) use `font-variant-numeric: tabular-nums`: proportional digits give "1" and "0" different widths, so equal-length numbers end at different edges and a live counter jitters. Check that the family has tabular figures; running text keeps proportional ones.
- Numbers right-aligned, text left-aligned, so the eye compares straight down the last digit.
- Decimals line up through one precision per column plus tabular figures; CSS can't align on the decimal point, so never mix `9.9` and `9.99` in one column.
- In a money column the symbol is pinned, not glued: either in the header ("Amount, USD") with bare numbers in the cells, or in its own left-aligned slot of the cell with the number right-aligned. A column mixing currencies shows the code on every row.
- Negatives use a real minus (`−`, U+2212) or the locale's accounting format, never a hyphen.
- Big numbers are compact where they summarize (stat cards, charts, counts in nav): `Intl.NumberFormat(locale, { notation: "compact", maximumFractionDigits: 1 })` gives "3.4M", never a hand-rolled `/ 1000 + "K"`. Below 10,000 show the exact value. The exact value stays reachable (a tooltip on a focusable element, or `aria-label`), since hover alone misses touch and keyboard.
- Exact where people compare, reconcile, or pay: table columns, invoices, balances, anything they typed.
- Past events read as relative under a day ("just now", "5m ago", "2h ago") and absolute after that ("Mar 3", with the year when it isn't the current one), in `<time datetime>` with the full timestamp on hover. Relative labels refresh on a timer. Due dates, scheduled times, and dates people reconcile (booked, posted, invoiced) stay absolute.

## Checks

- [ ] Every font size is a step of the scale; no arbitrary sizes.
- [ ] Two weights, 400 and 600, unless the style lists another.
- [ ] Rank inside a row comes from ink, and all three inks pass 4.5:1.
- [ ] Line-height drops as size rises; tracking only from ~25px up and on uppercase labels.
- [ ] Prose is capped at 45–75ch.
- [ ] Every text slot holds a long value and an unbroken string: it truncates in CSS (middle when both ends matter, the full value reachable) or wraps, and nothing pushes past its container.
- [ ] Stacked and live numbers are tabular with one precision per column; compact only where it summarizes, with the exact value reachable; relative time only under a day.
