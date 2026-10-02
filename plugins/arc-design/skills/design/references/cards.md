# Cards, Panels, Sections

Generated UI uses the card as a default wrapper for any group of content, so every page becomes boxes inside boxes. A card means something specific; everything else is a section or a panel.

## What is a card

- One card is one entity: a title that names it, a subject line (client, owner, the key value), and one destination (its detail view).
- A group without an entity of its own (a settings group, a form section, a region of a page) is a section: a heading plus dividers or spacing, no box. A settings page is one surface with sections, not three cards.
- A block with several actions and no single destination is a panel: it can have a surface, but it doesn't take hover or click as a whole.

## Edge treatment follows the background

Pick one edge per card from what it sits on, and use the same one for every card in that context:

| Card sits on | Treatment |
| --- | --- |
| A background of the same value (white on white) | 1px border |
| A tinted canvas (card lighter than the page) | Tool profile: 1px border. Marketing profile: one soft shadow, no border |
| A panel, modal, drawer, or any other surface | Flat: no border, no shadow; separated by dividers or spacing |

Never a full-strength border and a shadow together; the two edges read as a double outline. The materials themselves (hairline values, layered shadow) are in `materials.md`.

## Never nest

- A card never contains a card, and a panel, modal, or drawer never contains boxed groups. Inside a surface, groups are separated by a heading and a divider. The one exception is a settings danger zone (ui-interaction `settings.md`).
- Each inner box stacks another round of padding and radius, eating width and adding lines that say nothing.

## Media

- All cards in one grid share one aspect ratio (16:9 or 1:1, chosen per grid). Media fills its frame with `object-fit: cover` (`aspect-video object-cover`); never stretched to fit. The frame clips it or insets it with a reduced radius (`radius.md`).
- A card without media keeps an empty frame with a neutral placeholder, so rows stay aligned.
- Cards in a grid share one structure, with the footer pinned to the bottom (`flex flex-col`, footer `mt-auto`), so rows end flush.

## Checks

- [ ] Every card has one entity and one destination; groups without either are sections.
- [ ] No card or boxed group inside another surface.
- [ ] One edge treatment per context, never border plus shadow.
- [ ] One media ratio per grid, nothing stretched.
