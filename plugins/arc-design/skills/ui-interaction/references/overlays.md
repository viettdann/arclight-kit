# Overlays and Menus

## Picking the surface

| Need | Surface |
| --- | --- |
| A decision must be made before anything else (destructive confirmation, required step) | Modal dialog |
| A contextual task on mobile | Bottom sheet: page visible behind, snap points, drag handle, drag to dismiss (Sheets) |
| Navigation or a side task while the page stays usable | Drawer or side panel |
| A few contextual options | Popover or menu anchored to its trigger |
| A short label explaining a control | Tooltip |

Never stack modals. Never put primary navigation in a blocking overlay. Reach for a modal only when a popover, sheet, or inline expansion can't do the job.

## Modal

- Beyond the baseline focus rules: scrim behind, body scroll locked, titled via `aria-labelledby`.
- Native `<dialog>` opened with `showModal()` makes the rest of the page inert on its own. A custom modal (a `div` with `role="dialog"` and `aria-modal="true"`, a modal drawer or sheet) sets `inert` on the page content outside it while open and removes it on close: a focus trap alone stops Tab, but a screen reader's virtual cursor and a pointer can still reach the page behind. Render the overlay outside the element that gets `inert`, or it disables itself.
- Initial focus goes to the first field, or to the least destructive button in a confirmation.
- A modal that interrupts to confirm or warn (a destructive confirmation, a session about to expire) is `role="alertdialog"` with `aria-describedby` on its message, so the message is read on open, not just the title.
- A scrim click, swipe down, or Escape closes at once only without unsaved input; with input it asks first.
- A modal never grows past the viewport: `max-height: calc(100dvh - 2rem)`, with the title and the action row outside the scrolling region and only the body scrolling (`overflow-y: auto`, `overscroll-behavior: contain`), so Save never ends up below the fold. On a phone, a modal that can't fit becomes a full-height sheet.

## Sheets

- Header of a task sheet: dismiss on the left ("Cancel" when it discards input, "Close" when nothing is lost), the commit on the right named by its verb ("Save", "Add", or "Done" when edits already applied), title between. A commit always has a way out next to it: never a lone Done, never Back, Cancel, and Done together.
- Multi-step sheet: Cancel on the left on step 1, Back in its place after that; the commit stays visible but unavailable until the last step, so the flow's length is no surprise. A long or many-step task (editing a document, more than about three steps) gets a full page or route, not a sheet.
- Half-height rest only when the first rows do the job alone and the page behind still matters (share targets, a map pin's details, filters with live results, formatting controls); dragging up or scrolling expands it to full. Writing or editing with the keyboard (a composer, a form) opens at full height with no half rest, because the keyboard leaves a sliver of a half sheet.
- A resizable sheet shows a grabber that is also a `<button>` ("Expand sheet" / "Collapse sheet"): tap or Enter moves between rest heights, since keyboard and screen-reader users can't drag.
- Drag down or a flick dismisses (`gestures.md`, Flick to dismiss), except with unsaved input: the sheet springs back to its rest height and asks "Discard changes?" with "Discard" and "Keep editing". Escape and a scrim click ask the same; on `<dialog>`, handle the `cancel` event.

## Dismissal

- **Outside press, on `pointerdown`.** Listen in the capture phase on `document` for `pointerdown`, not `click`: a click fires on release, so a drag that starts inside (selecting text, moving a slider) and ends outside closes the popover. Count as inside the trigger (or its own toggle reopens what the press just closed) and every child layer rendered in a portal (submenu, a select inside a popover): test `event.composedPath()` against the registered layers, not DOM `contains`. An overlay with unsaved input asks first (Modal).
- **Escape closes the topmost layer only.** Keep a stack of open layers (the library's, or one shared module); the Escape handler acts only when its layer is on top. `stopPropagation()` in a `document` listener doesn't stop other `document` listeners, so without the stack a Select inside a Dialog closes both. Escape during IME composition (`event.isComposing`) cancels the composition, not the layer.

## Menus and dropdowns

- The trigger looks interactive: a caret, a hover state, a hit area of at least 24px, and 44px under `pointer: coarse` when it is a primary control, padded without changing its size (`baseline.md`, Pointer and touch).
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
- **Keyboard.** Shift+F10 and the Menu key open it at the focused element; focus goes to the first item and returns to the element on close. It also closes on a press outside (Dismissal), scroll, resize, and window blur.
- **Two triggers, one list.** A visible "…" button opens the same menu. On touch, a long press (about 500ms) opens the same actions in a bottom sheet headed by the target ("roadmap-v2.png · 8.1 MB"). Cancel the press if the finger moves more than about 10px (it's a scroll), suppress the native callout (`-webkit-touch-callout: none`) and the click on release, and open once even where the browser also fires `contextmenu` for the press. Define the actions once and render them in both.

## Tooltips

- Appears after about 300–500ms of hover and immediately on keyboard focus; hides on pointer leave, blur, and Escape.
- An arrow points at the trigger; it flips near viewport edges; width is capped around 280–320px, one sentence.
- Never put essential information or interactive content in a tooltip.

## Checks

- [ ] Every overlay closes with Escape (asking first when it holds unsaved input) and returns focus; a custom modal makes the background `inert` while open.
- [ ] A modal taller than the viewport scrolls its body only; the title and actions stay visible.
- [ ] A sheet has its dismiss on the left and commit on the right, a grabber that works without dragging, a half-height rest only for content that works at half, and asks before a swipe, scrim click, or Escape discards input.
- [ ] Outside dismissal fires on `pointerdown` and ignores the trigger and portaled child layers; Escape closes only the topmost layer.
- [ ] Menus, popovers, and tooltips never clip at viewport edges.
- [ ] A context menu opens at the pointer and mirrors at the edges, takes over only its own objects, opens from the keyboard, and has a visible "…" and a long press with the same actions.
