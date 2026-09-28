# Overlays, Menus, Navigation

## Picking the surface

| Need | Surface |
| --- | --- |
| A decision must be made before anything else (destructive confirmation, required step) | Modal dialog |
| A contextual task on mobile | Bottom sheet: page visible behind, snap points, drag handle, drag to dismiss |
| Navigation or a side task while the page stays usable | Drawer or side panel |
| A few contextual options | Popover or menu anchored to its trigger |
| A short label explaining a control | Tooltip |

Never stack modals. Never put primary navigation in a blocking overlay. Reach for a modal only when a popover, sheet, or inline expansion can't do the job.

## Modal

- Beyond the baseline focus rules: scrim behind, body scroll locked, titled via `aria-labelledby`.
- Initial focus goes to the first field, or to the least destructive button in a confirmation.
- A scrim click closes only if there is no unsaved input.

## Menus and dropdowns

- The trigger looks interactive: a caret, a hover state, a target of 40–44px.
- Collision aware: flips or shifts to stay inside the viewport (Floating UI or CSS anchor positioning).
- Arrows move, Enter selects, Escape closes one level, letters jump to matching items, Home/End work.
- Items are grouped by intent with separators; the destructive item is last and set apart.
- Submenus tolerate diagonal movement toward them (safe triangle or close delay).
- Past about 10 options, make it a searchable combobox.
- Opens in about 120–150ms, closes faster.
- A right-click menu has an equivalent visible trigger ("…") and a long press on touch.

## Tooltips

- Appears after about 300–500ms of hover and immediately on keyboard focus; hides on pointer leave, blur, and Escape.
- An arrow points at the trigger; it flips near viewport edges; width is capped around 280–320px, one sentence.
- Never put essential information or interactive content in a tooltip. Never attach one to a disabled element: it receives no pointer events.

## Tabs

- `tablist`/`tab`/`tabpanel` roles; arrows move between tabs, Home/End jump, Tab moves into the panel.
- The active indicator slides rather than jumping; panel switches don't shift the layout.
- Overflow scrolls horizontally with edge fades (plus chevrons on desktop), never wraps to a second row.
- On mobile use a segmented control for up to 4–5 options; beyond that, a scrolling row or a select/sheet.
- When tabs are views, the active tab is in the URL.

## Accordion

- The header is a `<button>` with `aria-expanded` and `aria-controls`, or use `<details>`/`<summary>`.
- One-open-at-a-time for sequential content, many-open for FAQs.
- Chevron rotation and panel height share one duration and easing.
- The tapped header stays anchored when a lower item expands.

## Navigation

- Mobile: bottom tabs for 3–5 primary destinations. Desktop: a persistent sidebar for 5+ sections, a top bar for fewer.
- A hamburger holds secondary items on mobile only, never desktop primary navigation.
- Breadcrumbs only for hierarchies deeper than two levels.
- The current location is marked with `aria-current="page"`.

## Drag and drop

- Pickup shows a lift (shadow, slight scale); the drop target is indicated before release (insertion line between items, highlight for a container); items snap to valid slots.
- A non-drag alternative exists (move up/down, "Move to…" menu, keyboard reordering).
- Every drop can be undone for a few seconds.

## Swipe

- Swipe is never the only path: the same actions exist in a menu or detail view.
- Show an affordance for discovery. At most two actions per side, with consistent direction semantics across the app.
- A destructive swipe reveals a button to tap, or commits on full swipe with an undo toast.

## Checks

- [ ] Every overlay closes with Escape and returns focus.
- [ ] Menus, popovers, and tooltips never clip at viewport edges.
