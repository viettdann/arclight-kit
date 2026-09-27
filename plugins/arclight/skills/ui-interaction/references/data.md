# Tables, Lists, Search, Filters

## Tables

- Choose columns by task, not by schema: what the user scans for and what they act on. Usually 4–7 columns; the rest goes to a detail view or a column picker.
- Numeric columns are right-aligned with `font-variant-numeric: tabular-nums`; text is left-aligned; dates use one consistent format.
- The header is sticky on vertical scroll; the first column is frozen on horizontal scroll.
- Sort cycles ascending → descending → original order, exposed with `aria-sort`.
- Row density is a token (for example compact 32px, default 40px, comfortable 48px), not per-screen guesswork.
- When a row opens a detail, the whole row is the target; checkboxes and row menus inside it don't trigger the row.
- Use real `<table>` semantics; use `role="grid"` only when cells are interactive, and then implement its full keyboard model.

## Selection and bulk actions

- The header checkbox has three states: none, some (indeterminate), all. Clicking the indeterminate state selects all.
- Scope is explicit: "25 selected on this page · Select all 247 matching". The count re-reads when filters change.
- Selection is a set of ids in application state, so it survives paging and re-render. Shift-click selects a range.
- Bulk actions echo the count ("Archive 12 invoices"); destructive bulk actions follow `destructive.md`.

## Pagination

- Use cursor pagination for data that changes, offset only for static data.
- Page or cursor, filters, sort, and search live in the URL so refresh and shared links reproduce the view.
- Returning from a detail view restores the list's scroll position and state.
- Numbered pagination shows first, last, current, and its neighbors, with ellipses for gaps. Infinite scroll is for feeds only; anything with a footer or a need to find an item again uses "Load more" or numbers.

## Search

- The placeholder names what is searchable ("Search by name, email, or invoice #").
- Persistent search bars show recent searches on focus.
- Debounce input (about 200–300ms), show pending inline, cancel stale requests (`AbortController`), and drop responses that arrive out of order.
- Zero results never dead-end: echo the query, offer to clear it, and suggest spelling fixes, related filters, or popular items.
- Suggestions rank by relevance or popularity, not alphabetically. Arrows, Enter, and Escape work; combobox semantics use `aria-activedescendant`.

## Filters

- Chips have distinct idle, active (filled plus check), and disabled (would give no results) states.
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

Four different cases, each with its own copy and one next action:

| Case | Content |
| --- | --- |
| First run | What this area is for, one primary create action, optionally a preview of a filled state |
| No results | The query echoed, a clear action, suggestions |
| Filtered out | Which filters hide the items, "Clear filters" |
| Error | What failed, retry (see `feedback.md`) |

## Checks

- [ ] Every table column is justified by a task.
- [ ] Numbers are tabular and right-aligned.
- [ ] Reloading the URL reproduces page, filters, sort, and search, and Back/Forward restores the previous view (`popstate` or the router's equivalent).
- [ ] A search with no match offers a way out.
- [ ] Selection survives a page change, and its scope is stated in numbers.
