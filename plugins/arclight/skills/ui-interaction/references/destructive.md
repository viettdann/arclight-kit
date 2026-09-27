# Destructive Actions, Undo, Settings

## Friction follows reversibility

A confirmation dialog on everything punishes every user for the rare mistake and gets clicked through on autopilot. Classify each destructive action first:

| Case | Pattern |
| --- | --- |
| Reversible (archive, move, remove item, delete to trash) | Execute immediately, then an undo toast with a visible countdown (5–10s); soft delete underneath |
| Irreversible, small blast radius | Confirmation dialog naming the action and its consequence ("Delete 3 invoices? This can't be undone."), buttons "Delete invoices" / "Cancel", initial focus on Cancel |
| Irreversible, large blast radius (project, workspace, account, data wipe) | Type the resource name to confirm, placed in a danger zone; prefer scheduled deletion with a cancelable grace period (e.g. 14–30 days) |
| Send or publish | Delayed send with an undo window where feasible |

Hold-to-confirm is an acceptable alternative on touch if it shows progress and has a keyboard equivalent.

## Visual language

- The danger color is spent only on destructive actions and errors, never on logout, decoration, or emphasis, so it keeps meaning something.
- On regular screens a destructive action never sits in the primary-action slot; it goes to an overflow menu or the danger zone.
- Labels name the action: "Delete project", "Remove member". Never Yes/No or OK.

## After the action

- Removing an item moves focus to the next item (or the previous one, or the list heading when the list is empty), otherwise keyboard and screen reader users are dropped at the top of the page.
- If the server rejects the action, the item stays or comes back, with a message and a retry. Only remove it optimistically when undo exists.

## Undo

- The undo toast states what happened ("12 invoices archived") and shows the remaining time as a draining bar or ring.
- Editors keep an undo stack bound to Cmd/Ctrl+Z.
- Soft delete means a flag, a trash view with restore, and a purge job, not an immediate row delete.

## Settings pages

- Group by user task, not by the data model. Past about 20 settings, add search. Collapse advanced options.
- Apply model by stakes: low-risk toggles apply instantly with a quiet "Saved"; identity, security, and billing fields use explicit Save/Cancel with a dirty indicator and a leave guard.
- Values changed from the default show that they are modified and have a per-setting reset where defaults matter.
- A labeled, bordered danger zone sits at the bottom.

## Server side

The UI's safeguards are not security. The server re-checks authorization and validation, destructive endpoints are idempotent, and multi-row writes run in one transaction.

## Checks

- [ ] Every destructive action is classified and uses the matching pattern.
- [ ] No generic "Are you sure?" with Yes/No.
- [ ] The undo path actually restores the data.
