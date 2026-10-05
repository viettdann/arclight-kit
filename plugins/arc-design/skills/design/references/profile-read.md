# Profile: Read

For pages people read through or come back to look something up: docs, guides, help center, changelog, blog posts. The text is the product; the page's job is to keep the reader oriented and out of the way.

## Wayfinding

- The reader always knows where they are and where to go next: section navigation (sidebar or top), a breadcrumb or section label above the title, and previous/next links at the end of each page.
- Long pages get an on-page table of contents from their `h2`/`h3`, with the current section marked while scrolling. Every heading has an anchor link.
- Search is in the same place on every page; on docs with many pages, `/` or ⌘K focuses it.

## Column and type

- One reading column of 60–75ch, body 16–18px, line-height 1.6–1.7, weights and tracking from `typography.md`. Navigation and the table of contents sit beside the column, never inside it.
- Running text is never monospace. Code, commands, file names, and identifiers are; code blocks scroll on their own axis and have a copy button (`ui-interaction/references/feedback.md`, Copy to clipboard).
- Tables, callouts, and code blocks may run wider than the prose column, but share its left edge.
- Callouts are rare and typed (note, warning) by a label plus a hairline or tint, not a colored side bar.

## Brand

The brand lives in the frame (masthead, navigation, how code, tables, and links are set), not in the text column. No hero, no imagery between paragraphs unless it explains something, no display type below the page title.

## Changelog

Newest first, each entry with a `<time datetime>` date and a version, grouped by kind (added, changed, fixed). Each entry links to the relevant docs page.

## Checks

- [ ] Section nav, current location, and previous/next present on every page; headings have anchors.
- [ ] Prose column 60–75ch; no monospace running text; code blocks scroll and copy.
- [ ] Brand only in the frame; no decoration inside the text column.
