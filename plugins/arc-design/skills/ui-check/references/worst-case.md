# Worst-case data

`--stress` lengthens the text a page already shows. It can't show what happens with no rows, one row, five thousand rows, a missing avatar, or a total that came back `null`. Those come from the data, so test them by changing the data and running ui-check on each state.

## Where to inject

- At the data boundary only: a fixture file, a mock handler (MSW, a route stub), story args, or the props a test renders with. Never by editing the markup or the component; the point is to see what the component does with data it didn't choose.
- One state per run: an empty list, a single item, the typical case, the huge case, each value set below. Open it with a URL, a story, or `--eval`, then run the usual command and look at the shots.
- Keep the harness out of production: delete it after, or keep it behind a dev-only flag or in stories and test fixtures. It is never the default data a build ships with.

## Take the limits from the schema

The worst case is the longest value the system accepts, not a guess. Read it from:

- Validation schemas: Zod `.max()`, `.min()`, `.int()`, Yup `max`, enum and union members.
- Database migrations and models: `varchar(n)`, `CHECK` constraints, nullable columns, numeric precision and scale.
- `maxLength`, `min`, `max`, and `pattern` on the form fields that create the value.
- Backend DTO validation: `[MaxLength]`, `[Range]`, class-validator decorators, OpenAPI `maxLength` and `enum`.

When the front end and the back end disagree (the form allows 100 characters, the column holds 255, an import path skips the form entirely), test at the larger limit and report the mismatch: data written by another client or an older version reaches the UI at the back end's limit.

## Quantity

| Count | What to look at |
| --- | --- |
| 0 | An empty state exists, explains why, and offers the next action; totals, averages, and percentages don't divide by zero |
| 1 | Singular copy ("1 item", not "1 items"); a grid or carousel with one card doesn't look broken; "1 of 1" paging |
| Typical | The count real accounts have; the layout the design was drawn for |
| Page size and page size + 1 | Off-by-one in "Showing 20 of 20", an empty last page |
| 1,000+ | Pagination or virtualization exists, render and scroll stay responsive, counts get thousands separators, select-all says what it selects |

## Container

- 320px: the narrowest phone, where every long value overflows at once.
- Squeezed by a sibling: the component in a sidebar, a split pane, or next to an open detail panel, often 280 to 400px inside a wide window. ui-check widths don't catch this; render it in the narrow slot or set the container width with `--eval`.
- Very wide: 1920px and up, where lines run too long and short content strands on one side.

## Values

Use values a real user could produce, at the schema's real limit. Domains in emails and URLs are `example.com` or `.test`.

| Kind | Values to try |
| --- | --- |
| Names | One at the full column length with a hyphen and diacritics; a two-letter name (`Jo`); CJK with no spaces (`王秀英`); RTL Arabic or Hebrew; an emoji ZWJ sequence first (`👩🏽‍💻 Priya`), which `.charAt(0)` or `.slice` splits; a suffix (`III`, `Jr.`); no name at all, only an email |
| Emails, URLs, IDs | A 60-character email; a long URL with a path and query; a UUID or hash; a file name where the version and extension sit at the end. None has a space to wrap at |
| Numbers | `0`; a negative; `0.1 + 0.2` unrounded; a huge count (`1284000`); `NaN`, `null`, `undefined`; a currency amount with many digits (`12345678.90`); a percentage past 100 |
| Dates and times | `1970-01-01` (a zero timestamp); a far-future date; a time near midnight that lands on another day in the viewer's timezone; a time inside a DST change; "now" and a date years ago for relative-time thresholds |
| Media | An image URL that 404s; no image at all; a 4000×200 or 200×4000 image; an image that loads slowly (throttle it in the mock) |
| States | Every enum or status value in one list at once; disabled, archived, or deleted items; the current user in the list; a role without permission for the row actions; an optional field filled on some rows and empty on others |

## Truncation, per field

- Decide per field, not once for the component. A name can end-truncate; a value whose distinguishing part is at the end (file names, hashes, paths, IDs that share a prefix) truncates in the middle, keeping the start and the end.
- Never truncate a number, an amount, or a date: a cut `$1,284,5…` reads as another value. Give the column room, or use a compact form (`1.3M`) only where precision doesn't matter.
- The full value stays reachable: a `title` or tooltip, an expand, or the detail view. A truncated value nobody can read in full is lost data.

## Symptoms

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Page scrolls sideways | an email, URL, or ID with no break point; a flex child without `min-w-0` | `min-w-0` on the flex child, `overflow-wrap: anywhere` on the value, or truncation with the full value reachable |
| Text cut off mid-glyph or mid-line | a fixed height or `overflow: hidden` sized for one line of typical text | Let it wrap, or clamp with an ellipsis and expose the full value |
| Layout jumps when data or images arrive | images without dimensions, a skeleton that doesn't match the final row, numbers without `tabular-nums` | Reserve the space (`width`/`height`, `aspect-ratio`, a min-height), match the skeleton to the row |
| "1 items", "0 result(s)" | hand-built plurals | `Intl.PluralRules` or the i18n library's plural forms |
| "NaN", "null", "undefined", "Invalid Date" on screen | a missing value formatted without a guard | A placeholder (`—`) for missing values, formatting through `Intl.NumberFormat` and `Intl.DateTimeFormat` |
| Broken-image icon in place of an avatar | no fallback for a failed or missing URL | An `onerror` fallback to initials or a neutral shape at the same size |
| Numbers in a column don't line up | proportional digits, mixed alignment, varying decimal places | `tabular-nums`, right alignment, a fixed number of decimals per column |
| Badges or rows of uneven width | status labels of different lengths | A min-width or fixed column for the badge; check the longest enum value |

## Rules

- Every value is plausible for a real user or sits exactly at the schema's limit. Random strings and lorem ipsum find nothing a real user would hit.
- Report each defect at the data that caused it: the field, the value, and the limit it came from.
- The fixture, mock, or flag is removed, or kept only for development and tests; it never becomes the data a build ships.
