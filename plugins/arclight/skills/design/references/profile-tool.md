# Profile: Tool

For interfaces people work in for hours. Density and speed read as competence; decoration reads as noise.

## Density and type

- Base text 13–14px (13px only with strong contrast), row height 32–40px (48px for the comfortable density), control height 28–36px. Tables expose density as a token.
- Rows keep one fixed height: content stays on one line and truncates with an ellipsis, with the full text in a tooltip or the detail view. A row never grows because its title is long.
- One family plus a monospace for ids, code, and numbers when useful. Scale ratio 1.2–1.25; weights, line-heights, and tracking follow `typography.md`.

## Depth

- Depth comes from surface value, not shadow: background levels (base, surface, raised, plus floating for a layer opened from a raised one), each one step above what it sits on, separated by a 1px hairline border at roughly 6–10% of the text color. In dark themes see `dark-mode.md`.
- Shadows are reserved for floating layers: menus, popovers, dialogs, toasts.
- Hover changes the surface value. No lift, no scale.

## Color

- Neutral UI. The accent appears on the primary button and the current selection, plus the one hero data series on a dashboard, nowhere else. Focus uses its own `focus-ring` token so "where I am" never looks like "what is chosen".
- Status is a small icon or dot plus text, not a saturated pill on every row.
- Tags and priority are neutral too: grey chips, priority as an icon rather than a colored word. Ids are monospace in muted text, not styled as links when the whole row is the link. Color is left for the one state that needs attention (urgent, overdue, error).

## Motion

- Hover response ~80–100ms, transitions 150–200ms at most, ease-out, no bounce or overshoot. The one exception is the release of a touch gesture (pull to refresh, a dismissed sheet), which carries the finger's velocity into a small settle. Nothing animates in a way that delays input.

## Layout

- App content fills the space the shell leaves (beside the sidebar, below the top bar), with consistent padding. Don't cap the main area with a centered `max-w-*` container; limit width only for prose, forms, and settings columns.
- Labels and text left-aligned, numbers right-aligned (`typography.md`), 16px icons centered on the text line, nothing centered inside tables.
- Radius scale (roles and rules in `radius.md`): `sm` 4px for chips and badges, `md` 6px for buttons, inputs, and popovers, `lg` 12px for cards, panels, and modals. No `xl`.
- Show keyboard shortcuts next to commands in menus and tooltips, and as a small key hint on the buttons for the main actions ("New issue `C`"); provide a ⌘K palette for apps with many destinations.

## Avoid

Colored pills for every status, gradient buttons, shadows on every card, spring animations, marketing-scale padding, centered layouts for data.
