# Profile: Tool

For interfaces people work in for hours. Density and speed read as competence; decoration reads as noise.

## Density and type

- Base text 13–14px (13px only with strong contrast), row height 32–40px, control height 28–36px. Tables expose density as a token.
- One family plus a monospace for ids, code, and numbers when useful. Weights 400/500/600. Negative letter-spacing only on headings of 20px and up.

## Depth

- Depth comes from surface value, not shadow: three background levels (base, surface, raised) separated by a 1px hairline border at roughly 6–10% of the text color.
- Shadows are reserved for floating layers: menus, popovers, dialogs, toasts.
- Hover changes the surface value. No lift, no scale.

## Color

- Neutral UI. The accent appears on the primary button, the current selection, and focus, nowhere else.
- Status is a small icon or dot plus text, not a saturated pill on every row.

## Motion

- Hover response ~80–100ms, transitions 150–200ms at most, ease-out, no bounce or overshoot. Nothing animates in a way that delays input.

## Layout

- Labels and text left-aligned, numbers and dates right-aligned with `tabular-nums`, 16px icons centered on the text line, nothing centered inside tables.
- Radius small to medium: 4–6px on controls, 8–12px on panels.
- Show keyboard shortcuts next to commands in menus and tooltips; provide a ⌘K palette for apps with many destinations.

## Avoid

Colored pills for every status, gradient buttons, shadows on every card, spring animations, marketing-scale padding, centered layouts for data.
