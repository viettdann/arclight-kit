# Gestures: Drag, Resize, Swipe, Pull

## Drag and drop

- Pickup shows a lift (shadow, slight scale); the drop target is indicated before release (insertion line between items, highlight for a container); items snap to valid slots.
- A non-drag alternative exists (move up/down, "Move to…" menu, keyboard reordering).

## Interrupted gestures

Every pointer gesture (drag, resize, swipe, pull) ends cleanly when the platform takes it away.

- Handle `pointercancel` and `lostpointercapture` like a release that commits nothing: restore the start state and drop the overlay and cursor lock. A window `blur` mid-drag does the same.
- A second pointer during a one-finger gesture cancels it or is ignored, never starts a second drag.
- Drag surfaces set `touch-action` (`none`, or `pan-y` for a horizontal swipe), or the browser scrolls and cancels the gesture.
- Desktop device emulation proves the layout, not the gesture: say whether a touch gesture was tried on a real touch device.
- Every drop can be undone for a few seconds.

## Resize handles

A split-pane handle is a control, not a border.

- **Clamp:** width stays between a min where the pane is still usable and a max that leaves the main content its own minimum. Clamp on every move, on load, and on window resize (a saved width can be too wide for a smaller window).
- **Snap:** released below a collapse threshold, the pane snaps shut; between the threshold and the min it snaps to the min. Never a sliver. A collapsed pane keeps a visible way back (its edge handle or a toggle button, plus a shortcut).
- **Follow the pointer 1:1:** no CSS `transition` on the width while dragging, only on the snap. Write the width to a CSS variable or style through a ref and commit to state on release (`baseline.md`).
- **Keep the drag:** pointer events with `setPointerCapture` on the handle, not `mousemove` on `document`. While dragging, cover the page with a transparent overlay (or set `pointer-events: none` on iframes and embeds), because an iframe swallows the pointer and ends the drag halfway.
- **Lock the cursor:** during the drag set `cursor: col-resize` (or `row-resize`) and `user-select: none` on the body or the overlay, so the cursor doesn't flicker when the pointer drifts off the thin handle and text doesn't get selected.
- **Hit area:** the visible line is 1px; the target is about 8px wide with a fine pointer and 24px under `pointer: coarse`, with a hover highlight after a short delay. The keyboard and the collapse toggle cover anyone who can't hit it.
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

- [ ] Every pointer gesture handles `pointercancel`, lost capture, and blur by restoring its start state, and sets `touch-action`.
- [ ] Resize handles clamp, snap shut instead of leaving a sliver, survive iframes and reloads, and work from the keyboard.
- [ ] Pull to refresh resists, fires only when released past the threshold, hands the indicator off to the spinner, and has a non-gesture alternative.
