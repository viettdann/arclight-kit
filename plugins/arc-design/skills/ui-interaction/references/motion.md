# Motion

The baseline motion rules (reduced motion, `transform` and `opacity` only, interruptions from the live value, no `transition: all`) are in `baseline.md`. Durations, curves, and exit timing come from the token scale in `${CLAUDE_PLUGIN_ROOT}/skills/design/references/tokens.md`. This file decides whether something moves and how. Gesture physics (springs, momentum, rubber-banding) is in `gestures.md`.

## Should it move at all

- **Frequency gate:** no animation on a keyboard shortcut or an action used 100+ times a day (command palette toggle, list navigation, tab switches in a tool). A control activated with Enter or Space animates as it does on click. At that frequency a 200ms open is a 200ms wait every time, and by the tenth use it reads as lag. Rare and first-time moments (onboarding, a finished import, the first item in an empty list) may carry expressive motion.
- **Named purpose:** every animation serves one of feedback (the press registered), spatial continuity (where this came from, where it went), state change (on/off, expanded/collapsed), avoiding a jarring jump (content inserted or removed), or explanation (how a feature works). If none fits, cut it.
- **Show the rejects:** when proposing motion for a screen, list the candidates you rejected and why (keyboard-driven, too frequent, no purpose, competes with the main animation), so the reviewer sees a choice, not an oversight.

## Origin and scale

- Popovers, menus, dropdowns, and tooltips grow from their trigger: set `transform-origin` from the positioning library's variable (Radix `--radix-popover-content-transform-origin`, `--radix-dropdown-menu-content-transform-origin`, `--radix-tooltip-content-transform-origin`; Base UI `--transform-origin`). A centered origin makes a menu below a button seem to grow out of empty space and flips wrong when collision handling moves it above.
- Modals and dialogs are not tied to the trigger: they scale and fade from the center of the viewport.
- Never enter from `scale(0)`: the first frames are invisible, then the element pops. Start at about `scale(0.95)` with `opacity: 0`.
- Press feedback: `:active { transform: scale(0.97) }` over 100–160ms. Deeper than about 0.95 looks like the control collapsed.

## Duration by element

Pick the nearest step of the token scale. UI motion stays under 300ms; only a drawer or sheet that travels most of the viewport goes past it.

| Element | Entrance |
| --- | --- |
| Press feedback | 100–160ms |
| Tooltip | 125–200ms |
| Dropdown, menu, popover | 120–250ms (dense tools at the low end, `overlays.md`) |
| Modal, dialog | 200–300ms |
| Drawer, sheet | 250–500ms by travel distance (past 300ms only for most of the viewport) |

- **Tooltip warm-up:** the first tooltip waits for the hover delay (`overlays.md`). Once one is open, moving to a neighbor opens it at once with no delay and no animation, until the pointer has left the group for about 300ms (Radix `skipDelayDuration`). Otherwise scanning a toolbar means waiting through a delay and an animation per button.

## Interruptible by construction

- Anything toggled rapidly (toasts stacking and dismissing, toggles, accordions, hover states) uses CSS transitions, not `@keyframes`. A re-triggered keyframe animation restarts from its first frame, so a quick double toggle snaps back before playing; a transition retargets from the current computed value, which is how the baseline's "continue from where it is" holds in CSS.
- Drag-driven motion uses springs, not either of the above (`gestures.md`).

## Enter and exit mechanics

- **From `display: none` without JS:** `@starting-style` supplies the first frame, and `transition-behavior: allow-discrete` with `display` and `overlay` in the transition list keeps the element rendered, and in the top layer, until its exit finishes. Without them a popover or `<dialog>` appears and vanishes instantly. Browsers without support skip the animation, an acceptable fallback; this replaces the `useEffect` "mounted" flag.

```css
[popover] {
  opacity: 0;
  transform: scale(0.95);
  transition-property: opacity, transform, display, overlay;
  transition-duration: 100ms;
  transition-timing-function: var(--ease-exit);
  transition-behavior: allow-discrete;
}
[popover]:popover-open {
  opacity: 1;
  transform: none;
  transition-duration: 150ms;
  transition-timing-function: var(--ease-enter);
}
@starting-style {
  [popover]:popover-open { opacity: 0; transform: scale(0.95); }
}
```

- **Unmount after the exit, not at it.** When script removes the node (a framework conditional, no `@starting-style` or presence component available), keep it mounted in a closing state until the exit ends, then unmount. Wait on `Promise.allSettled(el.getAnimations().map(a => a.finished))`, or on `transitionend` filtered to `event.target === el` and one property, since a child's transition bubbles up and ends the wait early. Add a timeout at the token duration: a transition that never starts (reduced motion set it to none, the value didn't change, the tab is hidden) fires no `transitionend`, and the node stays mounted for good. Reopening mid-exit cancels the pending unmount and reverses from the live value.
- **First render:** wrap a state swap (icon toggle, counter, tab content) in Framer Motion's `<AnimatePresence initial={false}>`, so the page loads showing the current state instead of animating it in. Leave `initial` alone where the mount animation is the point (a reveal, a toast region that mounts with its first toast).
- **Crossfade:** when the outgoing and incoming states visibly overlap (label, icon, or image swap), add `filter: blur(2px)` to both during the transition so the eye reads one thing changing, not two layered. Keep it to a few px: blur is paid per frame, worst in Safari.
- **Hold to confirm:** the fill (`clip-path: inset()` or `scaleX`) runs linear over the whole hold (about 1.5–2s) while pressed, so progress tracks time honestly; on early release it snaps back in about 200ms with `--ease-exit`. Slow where the user decides, fast where the system responds. Space and Enter hold it the same way as the pointer.

## Performance

- Set the transform on the moving element itself. Driving children through a CSS variable on a parent (`--swipe-offset` on a list) invalidates style for every descendant on every frame; in a list of 100 rows that is the jank.
- Add `will-change: transform` when the animation starts and remove it when it ends, never in the base stylesheet. Each promoted layer holds GPU memory, and `will-change` on `transform` or `filter` creates a stacking context and makes the element the containing block for `position: fixed` descendants, so a fixed tooltip or modal inside it stops following the viewport.
- Scripted motion without a library: the Web Animations API (`element.animate(keyframes, { duration, easing, fill })`) runs `transform` and `opacity` off the main thread like CSS, can be reversed or cancelled mid-flight, and exposes `.finished` for sequencing. Prefer it to a `requestAnimationFrame` loop writing styles.

## Checks

- [ ] No animation on keyboard-triggered or high-frequency actions; each remaining animation has a named purpose, and rejected candidates are listed.
- [ ] Anchored overlays scale from the trigger's `transform-origin`; modals from the center; nothing enters from `scale(0)`.
- [ ] Durations come from the token scale within the element's range; UI motion stays under 300ms except long-travel drawers and sheets.
- [ ] Neighboring tooltips open instantly once one is open.
- [ ] Rapidly toggled elements use transitions, not keyframes; `display: none` overlays animate via `@starting-style` and `allow-discrete`; a script-driven unmount waits for the exit with a timeout fallback.
- [ ] `will-change` exists only during an animation; no per-frame CSS variable on a parent of many children.
