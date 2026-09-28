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
- Submenus tolerate diagonal movement toward them with a safe triangle: its tip is the pointer, its base the near edge of the open submenu, recomputed on each pointer move. While the pointer stays inside, hovering a sibling item doesn't switch submenus; leaving it (or resting on a sibling for about 100ms) does. A submenu flips to the left when there's no room on the right, and the triangle follows.
- Past about 10 options, make it a searchable combobox.
- Opens in about 120–150ms, closes faster.

### Context menus

- **Measure, then open.** The menu anchors to the pointer, not the element: a zero-size virtual anchor at `clientX`/`clientY` (Floating UI's virtual element; CSS anchor positioning needs a real element). Render it hidden, measure it, place it, then show it, so it never flashes at the wrong spot.
- **Collide by mirroring.** No room below: it opens upward, bottom edge at the cursor. No room on the right: it opens to the left, right edge at the cursor. Still too tall: shift inside the viewport with an 8px margin and scroll within the menu.
- **Scope.** Take over `contextmenu` only on the objects the menu is for. Text fields, selected text, and ordinary links keep the browser's menu.
- **Target.** Right-clicking an item outside the selection selects it first; right-clicking inside a selection acts on all of it, and the labels say so ("Delete 3 files").
- **Contents.** Grouped by intent: open first, then edit, then share, destructive last in its own group. The order is the same for every object of a type; an action that doesn't apply right now stays in place and explains itself (`baseline.md`), one that never applies to this type is left out. Shortcuts show on the right.
- **Keyboard.** Shift+F10 and the Menu key open it at the focused element; focus goes to the first item and returns to the element on close. It also closes on click outside, scroll, resize, and window blur.
- **Two triggers, one list.** A visible "…" button opens the same menu. On touch, a long press (about 500ms) opens the same actions in a bottom sheet headed by the target ("roadmap-v2.png · 8.1 MB"). Cancel the press if the finger moves more than about 10px (it's a scroll), suppress the native callout (`-webkit-touch-callout: none`) and the click on release, and open once even where the browser also fires `contextmenu` for the press. Define the actions once and render them in both.

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

## Scroll position in client-side routing

The browser restores scroll on Back for real page loads; a client-side router has to do it itself.

- A new navigation (link, push) starts at the top and moves focus to the new page's heading. Back and Forward restore the exact position the entry was left at.
- Prefer the router's built-in restoration (React Router `<ScrollRestoration>`, Vue Router `scrollBehavior`, the Next.js and SvelteKit defaults). Hand-rolled: `history.scrollRestoration = "manual"`, save the position on leave (the router's before-navigate hook, plus `pagehide`), and restore on return. Never on a scroll listener (`baseline.md`).
- Key saved positions by history entry (`history.state` key or `location.key`), not by path: the same URL can sit in history twice at different positions.
- Restore after the content has height: keep the list's data cached so it renders immediately on Back, or restore once it has rendered. Restoring before the data arrives lands at zero.
- An app shell that scrolls an inner pane instead of the window saves and restores that pane; the browser never does it for you.
- A route effect that calls `scrollTo(0, 0)` on every path change breaks Back; scroll to top only for new navigations.

## Sticky headers and anchors

- Offset every scroll target by the sticky header's height with CSS, not a number in code: `scroll-padding-top: var(--header-height)` on the scroller covers jump links, `scrollIntoView`, and keyboard focus (a focused control never hides under the header), and `scroll-margin-top` handles single targets.
- A hash link in a client-side route scrolls to the target after it renders and moves focus to it (`tabindex="-1"` on non-focusable targets). Smooth scroll only without `prefers-reduced-motion`.
- A feed with infinite scroll has no footer to reach; its footer links live elsewhere (`data.md`).

## Drag and drop

- Pickup shows a lift (shadow, slight scale); the drop target is indicated before release (insertion line between items, highlight for a container); items snap to valid slots.
- A non-drag alternative exists (move up/down, "Move to…" menu, keyboard reordering).
- Every drop can be undone for a few seconds.

## Resize handles

A split-pane handle is a control, not a border.

- **Clamp:** width stays between a min where the pane is still usable and a max that leaves the main content its own minimum. Clamp on every move, on load, and on window resize (a saved width can be too wide for a smaller window).
- **Snap:** released below a collapse threshold, the pane snaps shut; between the threshold and the min it snaps to the min. Never a sliver. A collapsed pane keeps a visible way back (its edge handle or a toggle button, plus a shortcut).
- **Follow the pointer 1:1:** no CSS `transition` on the width while dragging, only on the snap. Write the width to a CSS variable or style through a ref and commit to state on release (`baseline.md`).
- **Keep the drag:** pointer events with `setPointerCapture` on the handle, not `mousemove` on `document`. While dragging, cover the page with a transparent overlay (or set `pointer-events: none` on iframes and embeds), because an iframe swallows the pointer and ends the drag halfway.
- **Lock the cursor:** during the drag set `cursor: col-resize` (or `row-resize`) and `user-select: none` on the body or the overlay, so the cursor doesn't flicker when the pointer drifts off the thin handle and text doesn't get selected.
- **Hit area:** the visible line is 1px, the target about 8px wide, with a hover highlight after a short delay.
- **Remember it:** save the width and the collapsed state per layout (`localStorage`, or a cookie when server-rendered) on release, not on every move, and apply it before first paint so the layout doesn't jump.
- **Keyboard:** `role="separator"` with `aria-orientation`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax`, and `tabindex="0"`. Arrows resize by a step, Enter toggles collapse, and a double-click resets to the default width.

## Swipe

- Swipe is never the only path: the same actions exist in a menu or detail view.
- Show an affordance for discovery. At most two actions per side, with consistent direction semantics across the app.
- A destructive swipe reveals a button to tap, or commits on full swipe with an undo toast.

## Pull to refresh

A pull is a promise: past the line it refreshes, before the line it doesn't, and the user can feel which.

- Only on touch, only when the list is scrolled to the top, and never the only way to refresh: a refresh button or automatic updates cover keyboard, pointer, and screen readers.
- Set `overscroll-behavior-y: contain` on the scroller, or the browser's own pull-to-refresh (a full page reload) and bounce run on top of yours.
- **Resistance:** the content moves less than the finger, with damping that grows with distance, so the pull carries weight. 1:1 movement feels cheap and overshoots the threshold by accident.
- **Threshold:** one fixed distance of the resisted pull. Released below it, the content springs back and nothing loads; released past it, the refresh fires. Never before release.
- **Armed feedback:** crossing the threshold changes the indicator (the ring completes) and gives one haptic tick where the platform has one (`navigator.vibrate(10)` where supported, feature-detected; native haptics in apps). Dragging back above the line disarms it without a second tick.
- **Handoff:** the indicator fills with pull progress and, on release, becomes the spinner in the same place; one element, not a swap. The content holds at the indicator's height while loading, then settles back.
- **Settle:** release carries the finger's velocity into a spring with a small overshoot, the one place a bounce is physics rather than decoration. Under `prefers-reduced-motion`, settle without overshoot.
- **Result:** new items appear at the top, and a polite live region says what happened ("3 new messages", "Up to date"). A fast response still holds the spinner briefly (about 400ms) so it doesn't flash. A failed refresh keeps the current content and shows an error with retry (`feedback.md`).

## Checks

- [ ] Every overlay closes with Escape and returns focus.
- [ ] Menus, popovers, and tooltips never clip at viewport edges.
- [ ] A context menu opens at the pointer and mirrors at the edges, takes over only its own objects, opens from the keyboard, and has a visible "…" and a long press with the same actions.
- [ ] Back restores the exact scroll position (window or inner pane); new routes start at the top.
- [ ] Jump links and focused controls land below the sticky header.
- [ ] Pull to refresh resists, fires only when released past the threshold, hands the indicator off to the spinner, and has a non-gesture alternative.
- [ ] Resize handles clamp, snap shut instead of leaving a sliver, survive iframes and reloads, and work from the keyboard.
