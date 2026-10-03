# Forms and Inputs

## Structure

- A visible label sits above every field, helper text below it. A placeholder is an example value, never the label.
- Every field has the right `type`, `inputmode`, `autocomplete`, and `name` (`email`, `tel`, `current-password`, `new-password`, `one-time-code`, `given-name`, `postal-code`, `cc-number`, ...). Turn `spellcheck` off for codes, emails, and usernames.
- Group fields by meaning (Personal, Shipping, Payment). The gap inside a group is clearly smaller than the gap between groups, so no divider lines are needed.
- Long forms that split naturally become steps grouped by meaning, not by field count. Show progress, validate within each step, and persist entered data so Back and refresh lose nothing.
- Never ask for the same information twice in one flow (WCAG 3.3.7): prefill it from an earlier step or offer a choice ("Billing address same as shipping"), unless re-entry is the point (confirming a new password) or the old value is no longer valid.

## Validation timing

- First validation runs on blur (or on submit for fields never touched), never on every keystroke.
- Once a field has shown an error, re-validate it live so the error disappears the moment it is fixed.
- Rules that guide input (password requirements) are visible up front and tick live as the user types. That is guidance, not an error.
- A success mark is for checks the user can't see themselves (username availability, async verification), not for every field.
- An error is color plus icon plus text saying what is wrong and how to fix it, anchored under the field, wired with `aria-invalid` and `aria-describedby`.
- On a submit with errors, move focus to the first invalid field. Long forms also get a summary at the top linking to each field.

## Submit

- Submit and Next stay enabled for invalid input and go busy, not disabled, while in flight (`baseline.md`, Unavailable actions); the busy label names the progress.
- On failure every typed value stays. The message distinguishes network failure, validation rejection, and server error, and offers a retry.
- The server recomputes prices and totals from its own data, never from the submitted values.
- The label names the outcome ("Create account", "Send invoice"), not "Submit".

## Specific inputs

- **Password:** show/hide toggle, paste allowed, requirements shown live, length favored over symbol rules. `autocomplete="new-password"` lets password managers generate one.
- **OTP:** one string in state, the boxes are just a view of it. Paste into any box strips non-digits and fills all boxes. Focus advances on entry, and Backspace on an empty box moves back. Set `inputmode="numeric"` and `autocomplete="one-time-code"`. Resend is throttled behind a visible countdown. A wrong code clears the boxes, refocuses, and says so.
- **Masked input (card, phone, IBAN):** display formatted, store raw. The caret stays after the character just typed when a separator is inserted. Pasted separators are cleaned, not rejected. Card brand shows from the leading digits. Validate on blur.
- **Date:** date ranges lead with presets (Today, Last 7 days, Last 30 days, This quarter) and keep a custom range for the rest. Show two months side by side for ranges. The date can be typed. The grid is keyboard navigable (arrows, Page Up/Down for month, Enter, Escape). On mobile use a full-screen sheet or the native input.
- **Slider:** filled track, live value readout, snaps to steps, hit area spans the row height, arrows/Home/End/Page keys work, two thumbs for ranges. Pair with a number input when exact values matter.
- **Toggle:** `role="switch"` with `aria-checked`, Space toggles. It applies immediately; a toggle inside a form that waits for Save should be a checkbox instead. Async toggles flip optimistically, show pending inside the knob, and roll back with a message on failure.
- **Inline edit:** see the section below.
- **File upload:** the dropzone reacts on drag-over (border, background, copy). Type and size are checked before uploading, with a specific message. Each file gets its own progress (percent, plus time remaining for large files) and its own retry that doesn't require re-selecting. Show a preview or thumbnail with type and size as proof of the right file.

## Inline edit

- **Match the mode to the cost of a typo.** Click-to-edit is for fields where a slip is cheap and undone in a keystroke: a title, a name, a label. Fields whose change means something or triggers something (status, amount, dates that bill or notify, permissions) open an explicit edit (an Edit button, then Save and Cancel). In a grid, a single click selects the cell and editing starts with Enter, F2, typing, or a double-click, so a stray click never writes.
- **Say it's editable.** On hover and focus the text gets a soft background tint and a pencil. The pencil is a real `<button>` ("Rename"), so keyboard users reach it; on touch (`@media (hover: none)`), where hover never fires, it stays visible. Clicking the text is a shortcut to the same edit.
- **Same box, different chrome.** The input takes the text's font, size, weight, line-height, tracking, and padding. The border exists in both states, transparent at rest and visible while editing, so the box doesn't grow by its width. A value that can wrap becomes a `<textarea>` that grows with its content (`field-sizing: content`, or a measured height), never a one-line input that collapses two lines into one.
- **Keys.** Enter commits and Escape restores the original; both return focus to the text or its pencil. In a multi-line field Enter adds a line and Cmd/Ctrl+Enter commits. Enter pressed while an IME is composing (`event.isComposing`) finishes the word, not the edit.
- **Blur commits, everywhere.** Clicking away saves, as in docs and spreadsheets, so work is never lost to a stray click. Pick this once for the whole app and never vary it. An unchanged value sends no request; an empty required value reverts to the saved one.
- **Save optimistically** (`feedback.md`): the new value shows at once. If the server rejects it, the text rolls back to the saved value, the draft is kept, and the message says why and offers a retry ("Couldn't save, your draft is kept · Retry"); reopening the edit restores the draft.

## Checks

- [ ] Every input has a visible label, the correct `type`, and `autocomplete`.
- [ ] The network-failure and server-error branches keep all values and show distinct messages with a retry.
- [ ] Errors appear on blur, not while typing, and clear live once fixed.
- [ ] Submit is never disabled for validity, and a double submit is impossible.
- [ ] Paste works in password, OTP, and masked fields.
- [ ] No step asks again for information an earlier step already collected.
- [ ] Inline edit is used only where a typo is cheap; entering edit moves nothing; Enter, Escape, and blur behave the same everywhere; a rejected save rolls back and keeps the draft.
