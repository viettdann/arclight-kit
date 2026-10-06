# Overlays and Menus

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
- Native `<dialog>` opened with `showModal()` makes the rest of the page inert on its own. A custom modal (a `div` with `role="dialog"` and `aria-modal="true"`, a modal drawer or sheet) sets `inert` on the page content outside it while open and removes it on close: a focus trap alone stops Tab, but a screen reader's virtual cursor and a pointer can still reach the page behind. Render the overlay outside the element that gets `inert`, or it disables itself.
- Initial focus goes to the first field, or to the least destructive button in a confirmation.
- A scrim click closes only if there is no unsaved input.

## Menus and dropdowns

- The trigger looks interactive: a caret, a hover state, a target of at least 24px (44px under `pointer: coarse`).
- Collision aware: flips or shifts to stay inside the viewport (Floating UI or CSS anchor positioning).
- Arrows move, Enter selects, Escape closes one level, letters jump to matching items, Home/End work.
- Items are grouped by intent with separators; the destructive item is last and set apart.
- Submenus tolerate diagonal movement toward them with a safe triangle: its tip is the pointer, its base the near edge of the open submenu, recomputed on each pointer move. While the pointer stays inside, hovering a sibling item doesn't switch submenus; leaving it (or resting on a sibling for about 100ms) does. A submenu flips to the left when there's no room on the right, and the triangle follows.
- Past about 10 options, make it a searchable combobox.
- Opens in about 120–150ms, closes faster.

### Context menus

- **Measure, then open.** The menu anchors to the pointer, not the element: a zero-size virtual anchor at `clientX`/`clientY` (Floating UI's virtual element; CSS anchor positioning needs a real element). Render it hidden, measure it, place it, then show it, so it never flashes at the wrong spot.
- **Collide by mirroring.** No room below: it opens upward, bottom edge at the cursor. No room on the right: it opens to the left, right edge at the cursor. Still too tall: shift inside the viewport with an 8px margin and scroll within the menu.
- **Scope.** Take over `contextmenu` only on the objects the menu is for. Text fields, selected text, and ordinary links keep the browser's menu.
- **Target.** Right-clicking an item outside the selection selects it first; right-clicking inside a selection acts on all of it, and the labels say so ("Delete 3 files").
- **Contents.** Grouped like any menu (open, edit, share, destructive last). The order is the same for every object of a type; an action that doesn't apply right now stays in place and explains itself (`baseline.md`), one that never applies to this type is left out. Shortcuts show on the right.
- **Keyboard.** Shift+F10 and the Menu key open it at the focused element; focus goes to the first item and returns to the element on close. It also closes on click outside, scroll, resize, and window blur.
- **Two triggers, one list.** A visible "…" button opens the same menu. On touch, a long press (about 500ms) opens the same actions in a bottom sheet headed by the target ("roadmap-v2.png · 8.1 MB"). Cancel the press if the finger moves more than about 10px (it's a scroll), suppress the native callout (`-webkit-touch-callout: none`) and the click on release, and open once even where the browser also fires `contextmenu` for the press. Define the actions once and render them in both.

## Tooltips

- Appears after about 300–500ms of hover and immediately on keyboard focus; hides on pointer leave, blur, and Escape.
- An arrow points at the trigger; it flips near viewport edges; width is capped around 280–320px, one sentence.
- Never put essential information or interactive content in a tooltip.

## Checks

- [ ] Every overlay closes with Escape and returns focus; a custom modal makes the background `inert` while open.
- [ ] Menus, popovers, and tooltips never clip at viewport edges.
- [ ] A context menu opens at the pointer and mirrors at the edges, takes over only its own objects, opens from the keyboard, and has a visible "…" and a long press with the same actions.
