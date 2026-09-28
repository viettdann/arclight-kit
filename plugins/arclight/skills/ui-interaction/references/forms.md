# Forms and Inputs

## Structure

- A visible label sits above every field, helper text below it. A placeholder is an example value, never the label.
- Every field has the right `type`, `inputmode`, `autocomplete`, and `name` (`email`, `tel`, `current-password`, `new-password`, `one-time-code`, `given-name`, `postal-code`, `cc-number`, ...). Turn `spellcheck` off for codes, emails, and usernames.
- Group fields by meaning (Personal, Shipping, Payment). The gap inside a group is clearly smaller than the gap between groups, so no divider lines are needed.
- Long forms that split naturally become steps grouped by meaning, not by field count. Show progress, validate within each step, and persist entered data so Back and refresh lose nothing.

## Validation timing

- First validation runs on blur (or on submit for fields never touched), never on every keystroke.
- Once a field has shown an error, re-validate it live so the error disappears the moment it is fixed.
- Rules that guide input (password requirements) are visible up front and tick live as the user types. That is guidance, not an error.
- A success mark is for checks the user can't see themselves (username availability, async verification), not for every field.
- An error is color plus icon plus text saying what is wrong and how to fix it, anchored under the field, wired with `aria-invalid` and `aria-describedby`.
- On a submit with errors, move focus to the first invalid field. Long forms also get a summary at the top linking to each field.

## Submit

- Don't disable submit (or a wizard's Next) to signal invalid input: disabled buttons leave the tab order, can't show a tooltip, and don't say why. Keep them enabled, validate on click, mark the fields, focus the first one.
- While a request is in flight the button is busy, not disabled: spinner plus label, `aria-busy="true"`, repeat clicks ignored, focus kept.
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
- **Inline edit:** editability is signaled on hover and focus (pencil or background tint). The input matches the text's font, size, and padding exactly so nothing shifts. Enter commits and Escape cancels; blur behavior is one rule across the whole app. Save optimistically, and on failure roll back while keeping the draft.
- **File upload:** the dropzone reacts on drag-over (border, background, copy). Type and size are checked before uploading, with a specific message. Each file gets its own progress (percent, plus time remaining for large files) and its own retry that doesn't require re-selecting. Show a preview or thumbnail with type and size as proof of the right file.

## Checks

- [ ] Every input has a visible label, the correct `type`, and `autocomplete`.
- [ ] The network-failure and server-error branches keep all values and show distinct messages with a retry.
- [ ] Errors appear on blur, not while typing, and clear live once fixed.
- [ ] Submit is never disabled for validity, and a double submit is impossible.
- [ ] Paste works in password, OTP, and masked fields.
