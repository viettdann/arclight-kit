# Destructive Actions, Undo

## Friction follows reversibility

A confirmation dialog on everything punishes every user for the rare mistake and gets clicked through on autopilot. Classify each destructive action first:

| Case | Pattern |
| --- | --- |
| Reversible (archive, move, remove item, delete to trash) | Execute immediately, then an undo toast with a visible countdown (8–10s); soft delete underneath |
| Irreversible, small blast radius | Confirmation dialog naming the action and its consequence ("Delete 3 invoices? This can't be undone."), buttons "Delete invoices" / "Cancel", initial focus on Cancel |
| Irreversible, large blast radius (project, workspace, account, data wipe) | Type the resource name to confirm, placed in a danger zone (`settings.md`); prefer scheduled deletion with a cancelable grace period (e.g. 14–30 days) |
| Send or publish | Delayed send with an undo window where feasible |

## Visual language

- The danger color is spent only on destructive actions and errors, never on logout, decoration, or emphasis, so it keeps meaning something.
- On regular screens a destructive action never sits in the primary-action slot; it goes to an overflow menu or the danger zone.
- Labels name the action: "Delete project", "Remove member". Never Yes/No or OK.
- Each verb means one thing across the product: remove takes an item out of this list, group, or project while it lives on elsewhere; delete destroys it for everyone (to trash when restorable, saying "permanently" when not); archive hides it from active views with data and links intact and restorable; disconnect ends a link to an external account or integration, stops syncing, and leaves the data on both sides; discard drops unsaved changes; revoke withdraws access or a token; leave takes yourself out. A "Remove" that deletes, or a "Delete" that only archives, makes every other button untrustworthy.
- The confirmation body names the object, the scope, and who is affected: "This permanently removes Q3 Campaign and its 84 assets for everyone on the team.", not "This action cannot be undone."
- When a dialog's primary action is safe and it also offers a destructive one (Save / Discard / Cancel), the destructive button moves to the opposite side, outlined rather than filled, so the habitual click on the primary slot never destroys. A dialog whose sole purpose is confirming a deletion keeps the destructive button as its primary.

## After the action

- Removing an item moves focus to the next item (or the previous one, or the list heading when the list is empty), otherwise keyboard and screen reader users are dropped at the top of the page.
- If the server rejects the action, the item stays or comes back, with a message and a retry. Only remove it optimistically when undo exists.

## Undo

- The undo toast states what happened ("12 invoices archived") and shows the remaining time as a draining bar or ring.
- Editors keep an undo stack bound to Cmd/Ctrl+Z.
- Soft delete means a flag, a trash view with restore, and a purge job, not an immediate row delete.

## Server side

Destructive endpoints are idempotent, and multi-row writes run in one transaction.

## Checks

- [ ] Every destructive action is classified and uses the matching pattern.
- [ ] No generic "Are you sure?" with Yes/No.
- [ ] The undo path actually restores the data.
- [ ] Remove, delete, archive, and disconnect each do what their word says, and the confirmation repeats the same verb.
