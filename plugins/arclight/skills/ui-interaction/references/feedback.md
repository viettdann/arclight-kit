# Feedback: Loading, Errors, Notifications

## Loading by what you know about the wait

| Situation | Pattern |
| --- | --- |
| Response under ~300ms | Show nothing; a flashing loader reads as a glitch. If a loader does appear, keep it for at least ~400ms |
| Known content shape, longer wait | Skeleton matching the final layout exactly (no shift on arrival), subtle shimmer, static under reduced motion |
| Unknown duration, short (under ~3s) | Inline spinner on the element doing the work, not a full-page overlay |
| Known progress, long (over ~3s) | Progress bar with percent, and time remaining when estimable |

Don't mix skeletons and spinners in one region. Pressed state appears within 100ms regardless of the network.

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

## Empty states

Distinguish first run, no results, filtered out, and error (see `data.md`). Each gets specific copy and one next action. No bare "No data".

## Notifications

- Match surface to severity: badge for a passive count, toast for low and transient, banner for an ongoing system state, modal only when the user must act.
- Routing everything to the loudest surface trains users to ignore all of them.
- Toasts:
  - Position: bottom-right (or bottom-center) on desktop, one consistent edge on mobile, never over the center of the content.
  - Stacking: at most 3 visible, the rest queue.
  - Timing: info and success auto-dismiss after ~4–6s, toasts with an action (Undo, Retry) stay longer, errors stay until dismissed, and timers pause on hover and focus.
  - Controls: always a close button, plus swipe to dismiss on touch.
  - Semantics: `role="status"`, or `role="alert"` for errors, plus an icon and text so color isn't the only signal.

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
