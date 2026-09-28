# Radius

Rounded corners everywhere don't make a system: one radius on everything, or a value picked per element by feel, and nothing lines up. Radius is a scale with roles, and a few geometric rules.

## One scale, every element on a role

| Role | Elements |
| --- | --- |
| `sm` | Chip, tag, badge, small control under 28px tall |
| `md` | Button, input, select, segmented control, popover, menu, tooltip |
| `lg` | Card, panel, modal, dialog |
| `xl` | Large panel, band inside the container, bottom sheet (top corners) |
| `full` | Avatar, dot, toggle, icon-only round button |

- Values come from the profile: tool `sm` 4px, `md` 6px, `lg` 12px, no `xl` (a bottom sheet takes `lg`); marketing from its radius table. A style may override rows.
- Radius grows with size: a larger element never gets a smaller step than a smaller element beside it.
- Elements that sit side by side at one height share a step: a button next to an input, a select next to a search field.

## Nested corners share one center

- Inner radius = outer radius − padding (card 12, padding 8, inner 4), so both curves are concentric. The same inner radius as the outer looks pinched, a larger one looks bloated.
- If the result falls below the smallest step, use the smallest step (marketing sets its own floor).

## Rings go outward

- A ring or selection outline outside an element: ring radius = element radius + gap (8 in, 2px gap, 10 out).
- `outline` with `outline-offset` and `box-shadow` spread (Tailwind `ring`) grow the radius on their own. The pinch happens when the ring is its own element (a pseudo-element, wrapper, or absolute `div`) that copies the element's radius; give it radius + gap.

## Full is a shape, not a number

- `rounded-full` (or 9999px) is for elements that are exactly one line at a fixed height.
- Anything that can wrap or grow (tooltip, toast, textarea, a long badge, a card) takes a number from the scale; a pill on two lines becomes a lozenge.
- This limits where a pill can appear; it doesn't make pills a default (the profile and style decide that).

## Touching an edge, no corner there

A corner needs space beyond it. A side flush with the viewport or its container has square corners on that side:

- Bottom sheet flush to the bottom: `rounded-t-*` only.
- Sidebar at the left edge: square.
- Toast flush to the bottom on mobile: top corners only.
- Full-bleed band edge to edge: square; the band's radius applies only when it sits inside the container.

## Media in a rounded frame

Two correct ways, never an image with square corners poking out of a rounded card:

- **Full-bleed:** the media fills the edge and the frame clips it (`overflow-hidden` with the frame's radius). Put the clip on the media frame, or on a card with no menus or popovers inside, because `overflow-hidden` also cuts off children's popovers and focus rings.
- **Inset:** the media sits inside the padding with radius = outer − padding (card 12, inset 8, image 4).

## Checks

- [ ] Every radius is a role from the scale; side-by-side controls share one.
- [ ] Nested corners are outer − padding; outer rings are radius + gap.
- [ ] `rounded-full` only on one-line, fixed-height elements.
- [ ] No rounded corner on a side flush with an edge.
- [ ] Media is clipped by its frame or inset with the reduced radius.
