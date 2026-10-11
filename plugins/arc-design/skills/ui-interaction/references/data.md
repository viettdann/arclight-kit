# Tables, Lists, Cards, Search, Filters

## Tables

- Width follows content: short fixed-format columns (status, date, amount) get room for their longest value plus padding, and spare width is spread across columns (table-auto, or proportional widths) rather than handed to a single name column that ends in empty space.
- Choose columns by task, not by schema: what the user scans for and what they act on. Usually 4–7 columns; the rest goes to a detail view or a column picker.
- Numeric columns are right-aligned with `font-variant-numeric: tabular-nums` and one precision per column (`$86.00`, not `$86`), so the column reads like a receipt; text is left-aligned; dates use one consistent format. Number formatting (currency symbol, compact values, relative time) follows the design skill's `typography.md`.
- Numbers never truncate or wrap; long text truncates with an ellipsis and shows in full in a tooltip on the focusable cell or in the row's detail, so the text column is the one that gives way. Emails and file names truncate in the middle (the design skill's `typography.md`, Long text).
- Rows are separated by one hairline, and hover changes the row's surface. Zebra stripes only for rows so wide the eye loses the line.
- The header is sticky on vertical scroll. In wide layouts the identity columns (checkbox, id or name) are pinned on horizontal scroll, with a border or shadow on the pinned edge only while scrolled; narrow widths switch to rows instead (below).
- Sort cycles ascending → descending → original order, exposed with `aria-sort`. The arrow shows on the active column only; other sortable headers show it on hover and focus.
- Row density is a token that scales with the base text size (for tool tables at 13–14px: compact 32px, default 40px, comfortable 48px), not per-screen guesswork. Pick it by task: compact for operations and triage, default for everyday work, comfortable for review and careful reading.
- An empty cell is a question, so answer it: missing data shows a muted dash with "No value" for screen readers, zero shows `0` or `$0.00`, loading shows a skeleton in the cell. Never a blank cell.
- When a row opens a detail, the whole row is the target; checkboxes and row menus inside it don't trigger the row.
- Per-row actions don't repeat on every row. They appear on row hover and focus (`opacity-0 group-hover:opacity-100 group-focus-within:opacity-100`, never `hidden`, which removes them from the keyboard), and their column keeps its width so nothing shifts. Gate the hover reveal with `(hover: hover) and (pointer: fine)` (`baseline.md`, Pointer and touch); elsewhere a kebab menu stays visible.
- Editable cells follow "Inline edit" in `forms.md`: a click selects, it doesn't write.
- Use real `<table>` semantics; use `role="grid"` only when cells are interactive, and then implement its full keyboard model.

## Tables on narrow widths

- The table owns its breakpoint: switch layouts with a container query on the table's wrapper (`@container`, Tailwind `@[Npx]:`), not a viewport media query, so the same table in a 400px side panel on desktop gets the narrow form too. N is the width the full column set needs, measured, not a device width.
- Below N, don't shrink type to fit and don't scroll sideways: each record becomes a two-line row. Type stays at the profile's base size.
- Rank fields by use, not column order. Line 1: identity on the left (name), the value on the right (amount). Line 2: state and one key date. Everything else (id, notes, secondary dates) moves to the expanded row.
- The value keeps one slot: the right edge of line 1, right-aligned with `tabular-nums`, so amounts line up down the list. Nothing else takes that slot.
- There is no header row, so label what is ambiguous: a date gets its meaning ("Due Mar 04"), while a currency amount explains itself. Sort moves into the toolbar ("Sort · Due date").
- Hidden isn't deleted. A chevron on the right shows the row expands; tapping it opens the row inline with the hidden fields and the row's actions. The full record opens in a bottom sheet (`overlays.md`), never a separate page, so the list keeps its place.
- The row is a disclosure (`<button aria-expanded>`) and the actions sit in the expanded region, outside the button. The whole row is the touch target, about 64–72px tall.
- Wide rows stay one line and truncate; narrow rows are two lines by design.

## Clickable cards

- A clickable card has one destination, and the whole surface is the target: a real link on the title stretched over the card (`after:absolute after:inset-0` on the `<a>`, `relative` on the card), never `onClick` on a `div`.
- Secondary actions go in one overflow menu (⋯) raised above the stretched link (`relative z-10`); never a `<button>` inside the `<a>`.
- Hover and focus style the whole card, and the focus ring wraps the card (`has-[:focus-visible]:ring-2`), not just the title.
- A card with two or more actions and no single destination is a panel: not clickable as a whole, each action its own button.

## Selection and bulk actions

- The header checkbox has three states: none, some (indeterminate), all. Partial is a state, not a bug: clicking it selects all, never clears; only the checked state clears. On a native checkbox `indeterminate` is a DOM property set through a ref, not an attribute; a custom one uses `aria-checked="mixed"`.
- The header checkbox covers the rows on screen. Name the number, not "all": "6 selected" plus a text link "Select all 247 matching", which becomes "All 247 selected · Clear selection".
- "Matching" follows the active filters, and the numbers say so ("Select all 96 on Pro"). Select-all-matching is stored as the filter plus excluded ids, not a fetched list of ids, so unticking one row works and the bulk action sends the filter to the server.
- When a filter hides selected rows, the count says so ("12 selected, 3 hidden by filters") and the bulk action applies only to what the count states.
- Selection is a set of ids in application state, so it survives paging and re-render. Shift-click selects the range from the last clicked row and applies that row's new state; Shift+Space does the same from the keyboard.
- While anything is selected, a bar shows the count, the bulk actions, and "Clear".
- Bulk actions echo the count ("Archive 12 invoices") and so does the result ("247 members deleted · Undo"). A reversible bulk action runs at once with an undo toast instead of an "Are you sure?" dialog, which adds friction without recovery; irreversible ones follow `destructive.md`.

## Pagination

- Use cursor pagination for data that changes, offset only for static data.
- Page or cursor, filters, sort, and search live in the URL so refresh and shared links reproduce the view.
- Returning from a detail view restores the list's scroll position and state (see "Scroll position in client-side routing" in `navigation.md`).
- Numbered pagination shows first, last, current, and its neighbors, with ellipses for gaps. Infinite scroll is for feeds only; anything with a footer or a need to find an item again uses "Load more" or numbers.
- A list that renders more than about 1,000 rows at once is virtualized (TanStack Virtual, or the grid's built-in), keeping row height fixed so the scrollbar doesn't jump.

## Search

- The placeholder names what is searchable ("Search by name, email, or invoice #").
- Persistent search bars show recent searches on focus.
- Debounce input (about 200–300ms), show pending inline, cancel stale requests (`AbortController`), and drop responses that arrive out of order.
- Zero results never dead-end: echo the query, offer to clear it, and suggest spelling fixes, related filters, or popular items.
- Suggestions rank by relevance or popularity, not alphabetically. Arrows, Enter, and Escape work; combobox semantics use `aria-activedescendant`.

## Filters

- Chips have distinct idle, active (filled plus check), and empty states: an option with no results stays focusable and shows its `0` count.
- The logic is visible: OR within a group, AND across groups.
- The result count updates in the same frame as the change.
- Whenever a filter is active there is a single "Clear all" and a visible summary of what is applied.
- On narrow screens overflowing chips stay in one horizontally scrolling row with an edge fade, never a multi-row wall above the results.

## Command palette

- Fuzzy subsequence matching ("stg" finds Settings, Staging).
- Opens with recent and suggested commands, never a blank box. Results are grouped (Recent, Actions, Pages), each shows its shortcut.
- Fully keyboard driven; async commands load inline without freezing; nested commands have a breadcrumb and Escape goes back one level.
- It is an accelerator, never the only path to a feature.

## Empty states for collections

Distinct cases, each with its own copy and one next action:

| Case | Content |
| --- | --- |
| First run | What this area is for, one primary create action, optionally a preview of a filled state |
| No results | The query echoed, a clear action, suggestions |
| Filtered out | Which filters hide the items, "Clear filters" |
| Error | What failed, retry (see `feedback.md`) |
| No permission | That items may exist but this user can't see them, and who grants access |
| Cleared by the user | Confirmation that it's done ("Inbox zero"), no create prompt pushed |

## Checks

- [ ] Every table column is justified by a task.
- [ ] Numbers are tabular and right-aligned.
- [ ] No blank cells: missing, zero, and loading each look different.
- [ ] Below the width its columns need, the table becomes two-line rows via a container query, with no sideways scroll, no shrunken type, and every hidden field reachable by expanding the row.
- [ ] Clickable cards are one link over the whole surface, with secondary actions in a menu above it.
- [ ] Reloading the URL reproduces page, filters, sort, and search, and Back/Forward restores the previous view (`popstate` or the router's equivalent).
- [ ] A search with no match offers a way out.
- [ ] Selection survives a page change, and its scope is stated in numbers.
- [ ] Clicking the partial header box selects all; select-all-matching is a filter plus exclusions; bulk results echo the count with Undo.
