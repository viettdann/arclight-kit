# Feedback: Loading, Errors, Success, Notifications

## Loading by what you know about the wait

| Situation | Pattern |
| --- | --- |
| Response under ~300ms | Show nothing; a flashing loader reads as a glitch. If a loader does appear, keep it for at least ~400ms |
| Known content shape, longer wait | Skeleton matching the final layout exactly (no shift on arrival), subtle shimmer, static under reduced motion |
| Unknown duration, short (under ~3s) | Inline spinner on the element doing the work, not a full-page overlay |
| Known progress, long (over ~3s) | Progress bar with percent, and time remaining when estimable |

Don't mix skeletons and spinners in one region.

## Optimistic updates

- For reversible, almost-always-successful actions (like, favorite, toggle, rename, reorder): update instantly, sync in the background, and on failure roll back with a message while keeping any draft.
- Never for payments, transfers, sending, bookings, permission changes, or anything irreversible: those wait for the server.
- After the response, render server truth (real ids, totals, timestamps). Ignore stale responses and serialize rapid repeated toggles.

## Errors

| Scope | Surface |
| --- | --- |
| One field | Inline under the field |
| One section failed to load | Inline in that section, with retry; the rest of the page keeps working |
| Connection lost | Persistent banner until restored |
| An action failed transiently | Toast with retry |
| Blocking (no permission, fatal) | Full panel or page state with a way out |

- Copy says what happened, why if known, and what to do next. Raw codes go behind a "Details" disclosure for support, not in the headline.
- Every error has a way forward: retry, edit, go back, or contact.
- User input survives every error.

## Success

- Say what happened with server data: the object, where it went, and the key values ("INV-2051 sent to Northwind Labs · €2,400 · due Oct 12"). Never a bare "Success!".
- Surface follows stakes: routine, reversible changes get an inline state change or a toast (with Undo when possible); payments, sends, bookings, and account changes get a confirmation page with a reference number that survives refresh and never resubmits.
- A done screen offers one primary next action and one way back. No dead end, no OK-only dialog.
- When the outcome continues asynchronously (delivery, payment, review), show the current stage and how the user will learn about the next one.
- Routine success stays quiet: the state change is the feedback. Celebration is reserved for a user's first real milestone (first payment received), shown once, never blocking, and static under reduced motion.

## Empty states

Distinguish first run, no results, filtered out, and error (see `data.md`). Each gets specific copy and one next action. No bare "No data".

## Notifications

- Match surface to severity: badge for a passive count, toast for low and transient, banner for an ongoing system state, modal only when the user must act.
- Routing everything to the loudest surface trains users to ignore all of them.
- Toasts:
  - Position: bottom-right (or bottom-center) on desktop, one consistent edge on mobile, never over the center of the content.
  - Stacking: at most 3 visible, the rest queue.
  - Timing: info and success auto-dismiss after ~4–6s, toasts with an action (Undo, Retry) stay 8–10s, errors stay until dismissed, and timers pause on hover and focus.
  - Controls: always a close button, plus swipe to dismiss on touch.
  - Semantics: `role="status"`, or `role="alert"` for errors, plus an icon and text so color isn't the only signal.

### Badges

- Badge the decisions, not everything: only what needs the user's action gets a count. "New" labels on every nav item and feature leave nothing to notice.
- A count and a status are different signals with different rules. A count is a number of things to act on, and clears when they are handled. A status is a dot with no number (changed, live), and opening doesn't clear it; presence on an avatar is its ring (see the design skill's `avatars.md`). Counts use one color across the app, never a status color; a status dot has a text alternative (`aria-label`, tooltip).
- One signal per row: a dot or a number, never both.
- The count is capped (99+, or 9+ on a small badge) so its width is bounded. Use `tabular-nums`, a min-width equal to its height so one digit is a circle, and hide it at zero. The full number goes on the control for screen readers ("Notifications, 348 unread") with the badge itself `aria-hidden`.
- The badge pins to the corner: `absolute` on a `relative` wrapper, anchored by its right edge so it grows leftward, with a 2px ring in the surface color to separate it from the icon. The icon and the button never move or grow.
- Opening clears it. Opening the panel clears the count of unseen items; each item keeps its own unread state until read, with "Mark all read". Clear optimistically and sync across tabs. A badge that never clears trains people to ignore it.
- The count changes in place and never blinks: outside the user's own actions it doesn't drop to zero and come back. Keep the last known value while refetching; with no value yet, show no badge rather than "0". No pulse.

## Copy to clipboard

- The check reports the write, not the click: `await navigator.clipboard.writeText(value)`, then flip the icon. The promise resolves within a frame, so no spinner and no delay; on rejection there is no check.
- Flip in place: the icon swaps at the same size, and a label ("Copy" → "Copied") reserves the width of the longer word so nothing shifts. Announce "Copied" through a polite live region; the button's name says what it copies ("Copy API key").
- Reset after about 2s so the next copy signals again; a repeat click restarts the timer.
- Copy the raw value from its source (state or a `data-` attribute), never the rendered text: line breaks from wrapping, grouping spaces in card numbers or IBANs, zero-width characters, a masked "••••", a `$` prompt, or line numbers break whatever it is pasted into.
- Fall back, don't lie. The Clipboard API needs a secure context (HTTPS or localhost), a user gesture, and `allow="clipboard-write"` inside iframes. When it rejects, try `document.execCommand("copy")` on a temporary textarea and check its return value; if that fails too, select the value and say so ("Couldn't copy. Press ⌘C"), never a check.

## Autosave

- Save after a pause in input (debounce ~500–1000ms), and also on blur and when the page becomes hidden.
- The status indicator is a state machine: unsaved, saving, saved (with time), offline (N pending), error (retry). It never says "Saved" before the server acknowledges.
- While offline, queue changes locally and replay them in order on reconnect.
- Detect concurrent edits (version or ETag) and merge or warn; never overwrite silently.
- Register a `beforeunload` guard only while unsaved changes exist.

## Microcopy

- Buttons are verb plus object or outcome: "Save changes", "Create project", "Delete 3 files". Not "Submit", "OK", or "Yes".
- Errors are human and specific with a next step: "That email already has an account. Log in instead?", not "Invalid input".

## Checks

- [ ] Loaders are delayed for fast responses, and the skeleton matches the final layout.
- [ ] Every mutation's failure branch keeps the input, shows a specific message, and offers a retry.
- [ ] Every list and search has distinct loading, empty, and error states.
- [ ] Every success message names what happened, and every done screen has a next action and a way back.
- [ ] Copy buttons show the check only after the write resolves, copy the raw value, reset after ~2s, and have a fallback that admits failure.
- [ ] Badges are capped, pinned to the corner, cleared on open, and never flash to zero on refetch; counts and status dots don't share a color or a row.
