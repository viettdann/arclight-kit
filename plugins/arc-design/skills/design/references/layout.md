# Layout

How content is grouped, spaced, and rearranged as its space changes. The numbers here are defaults for a project with no spacing or density system; the project's tokens win (`tokens.md`). Narrow tables are in `${CLAUDE_PLUGIN_ROOT}/skills/ui-interaction/references/data.md`; hit areas, safe areas, and fixed bars are in `${CLAUDE_PLUGIN_ROOT}/skills/ui-interaction/references/baseline.md`.

Contents: Grouping · Control clearance · Container queries · Adapting across widths · Hidden content · Responsive images · Print · Checks

## Grouping

- Group with space first, a surface tint second, and a line last. A divider is only for places where space can't hold the structure (table rows, a long settings list, a dense tool panel), because every line is one more edge the eye has to read past.
- The gap between groups is at least twice the gap inside a group: 8px inside means 16px or more between, 16px inside means 32px between. With equal gaps, a label attaches to the wrong field and a heading floats between two sections (`typography.md`, Space around headings).

## Control clearance

- When neither `DESIGN.md` nor the theme defines a density token, start from these gaps: 12px between adjacent bordered or filled controls, 24px between the visible glyphs of borderless icon or text buttons (their own padding counts toward it), and 24px or more between unrelated control groups (a toolbar's edit set and its view set). Borderless controls need the larger gap because nothing else shows where one ends.
- A project's density scale replaces these numbers. Go tighter only while hit areas don't overlap (`${CLAUDE_PLUGIN_ROOT}/skills/ui-interaction/references/baseline.md`, Pointer and touch) and each control still reads as separate.

## Container queries

- A reusable component (card, media object, form row, stat block, list item) adapts to its own width through a container query, not a viewport breakpoint, because the same card can sit in a 320px sidebar on a 1440px screen. Put the container on the component's root wrapper (`@container`, `container-type: inline-size`) so the component works wherever it is placed.
- Put the breakpoint where the content stops fitting: resize the container, not the window, and add the query at the width where the layout breaks (`@[34rem]:`), never at a device width.
- A container query styles descendants only. An element can't query its own size, so `@container` plus an `@md:` variant on the same element queries some outer container instead. `container-type: inline-size` on a shrink-to-fit box (a flex item with no basis, an inline-block, an absolute box with no width) collapses it to zero width, so give the box a definite width first.
- When migrating `sm:`/`md:` classes, never map `md:` to `@md:` one to one: `md` is 48rem of viewport, `@md` is 28rem of container. Find the width again in the narrowest real slot (sidebar, drawer, small grid cell).
- Keep viewport media queries for what depends on the window: the shell grid, whether a sidebar exists, the navigation pattern, fixed and sticky bars, and the global type scale.
- Tailwind v4 has container queries in core; v3 needs `@tailwindcss/container-queries`. Check the version before writing `@` variants.

## Adapting across widths

- When there is room for both (about 48rem and up: tablet landscape, a desktop window), a list with a detail view shows them side by side: the list at a fixed width, the detail filling the rest, the selected row marked. On narrower screens the detail is its own route or a sheet, and Back returns to the list at its scroll position (`${CLAUDE_PLUGIN_ROOT}/skills/ui-interaction/references/navigation.md`, Scroll position in client-side routing).

## Hidden content

- A horizontally scrolling row (cards, a shelf, chips) shows 16–32px of the next item at its edge; a row whose items end exactly at the edge looks complete, so nobody scrolls it. Use native scroll: `scroll-snap-type: x mandatory` on the track, `scroll-snap-align: start` on the items, and scroll padding equal to the page margin (`scroll-px-4`) so a snapped item lines up with the content above. An edge fade (`${CLAUDE_PLUGIN_ROOT}/skills/ui-interaction/references/data.md`, Filters) can sit over the peeking item.
- A collapsed or paged group says what it hides and how much ("Show 12 more results", "Show all 48 files"), never a bare "More" or a lone chevron, so the user can judge whether opening it is worth it.

## Responsive images

- A content image shown at different widths gets `srcset` with width descriptors and a `sizes` that states its real layout width (`(min-width: 64rem) 33vw, 100vw`), or the framework's image component with `sizes` set (`next/image`, Astro `<Image>`). Without `sizes` the browser assumes 100vw, so a 300px thumbnail downloads the full-width file.
- Use `<picture>` with `<source media>` only for art direction (a different crop on phones), and `<source type="image/avif">` for format fallback. Reserving the box stays in `${CLAUDE_PLUGIN_ROOT}/skills/ui-interaction/references/baseline.md`, Layout stability.

## Print

- Pages people print (docs, invoices, receipts, order confirmations, reports, tickets) get an `@media print` block; app screens don't need one.
- Hide what does nothing on paper (navigation, sidebars, toolbars, toasts, cookie banners, video, controls that only work interactively) and let the content take the full page width.
- Print on the light token set with backgrounds off, so a dark theme prints as light. Keep color only where it carries meaning (status), using `print-color-adjust: exact` on those elements.
- Links in prose print their URL (`a[href^="http"]::after { content: " (" attr(href) ")" }`). Use `break-inside: avoid` on cards, figures, and table rows and `break-after: avoid` on headings, and repeat the table header on each page (`thead` as `table-header-group`, the default).

## Checks

- [ ] Groups are separated by space, the gap between groups is at least twice the gap inside them, and dividers appear only where space can't carry the structure.
- [ ] Control spacing comes from the project's density scale or the defaults here, and no hit areas overlap.
- [ ] Reusable components adapt through container queries on their own wrapper, no element carries both `@container` and an `@` variant, and viewport queries are used only for page-level layout.
- [ ] Horizontal rows show part of the next item, and every disclosure says what it hides and how many.
- [ ] Content images have `srcset` and `sizes`, and pages people print have a print block.
