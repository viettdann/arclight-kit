# Forms and Inputs

## Structure

- Every field has a real `<label for>` that stays visible when the field is empty, focused, and filled.
- Default: the label sits above the field, with helper text below.
- A floating label is allowed. The label sits inside the empty field and moves to the field's top edge on focus or when the field has a value. Conditions:
  - It is a `<label>`, never the `placeholder` attribute.
  - Floated, it is at least 12px and passes 4.5:1 against the field fill.
  - The field is tall enough that the floated label and the value never overlap.
  - The float is driven by field state, not by focus alone: `:focus`, `:not(:placeholder-shown)` with `placeholder=" "`, and `:autofill`. That way it also floats when the browser autofills or code sets the value.
  - Because the placeholder holds the blank `" "`, a floating-label field shows any example value in its helper text, not in a placeholder.
- On a field with a label above, a placeholder is only an example value. It disappears on input, so a format or requirement the user needs while typing goes in helper text, never only in the placeholder.
- Every field has the right `type`, `inputmode`, `autocomplete`, and `name` (`email`, `tel`, `current-password`, `new-password`, `one-time-code`, `given-name`, `postal-code`, `cc-number`, ...). Emails, usernames, and codes also get `autocapitalize="none"`, `autocorrect="off"`, and `spellcheck="false"`, or the phone keyboard capitalizes the first letter and "corrects" the value into a different one. Codes use `inputmode`, not `type="number"` (see Codes and identifiers).
- `enterkeyhint` names what the keyboard's Enter key does (`search`, `send`, `go`, `next` on a field followed by another, `done` on the last), so the label on the phone keyboard matches the action it triggers.
- Inputs, selects, and textareas render at 16px or larger on touch: iOS Safari zooms the page into any focused field under 16px and leaves it zoomed. Keep the dense size for fine pointers only: 16px under `@media (pointer: coarse)`, or `text-base sm:text-sm`, which approximates touch by width and misses a large tablet. Never fix it with `maximum-scale=1` in the viewport meta, which also blocks the pinch zoom low-vision users need.
- Group fields by meaning (Personal, Shipping, Payment). The gap inside a group is at most half the gap between groups, so no divider lines are needed.
- Long forms that split naturally become steps grouped by meaning, not by field count. Show progress, validate within each step, and persist entered data so Back and refresh lose nothing.
- Never ask for the same information twice in one flow (WCAG 3.3.7): prefill it from an earlier step or offer a choice ("Billing address same as shipping"), unless re-entry is the point (confirming a new password) or the old value is no longer valid.

## Validation timing

- First validation runs on blur after the user edited the field, or on submit for a field never touched. Never validate on keystrokes before that.
- Once a field shows an error, it re-validates on every input until it is valid, so the error clears the moment it is fixed.
- Once valid again, the field returns to on-blur validation.
- Rules that guide input (password requirements) are visible up front and tick live as the user types. That is guidance, not an error.
- A success mark is for checks the user can't see themselves (username availability, async verification), not for every field.
- An error is color plus icon plus text saying what is wrong and how to fix it, anchored under the field, wired with `aria-invalid` and `aria-describedby`.

## Errors

- **Message slot:** every field has one message slot under it, reserved at the height of one line of helper text even when empty. The error replaces the helper text in that slot, so an error appearing moves neither the fields below nor the submit button. Write messages to fit that one line. When a message still wraps (a narrow screen, a longer translation), only that slot grows, downward: nothing above the field moves, while the fields below and the submit button may move down.
- **Submit button:** it stays where it is and stays enabled (`## Submit`).
- **Error summary:** on a submit with errors, every form, short ones too, shows an error summary at the top of the form with:
  - a heading with the count, e.g. "Fix 3 fields";
  - one entry per broken field, in form order, with the same text as that field's inline error;
  - each entry a link (`href="#<field-id>"`) that moves focus to the input.
- **Summary focus:** the summary container has `tabindex="-1"`. In the same frame it renders, focus moves to it and it is scrolled into view. Client-side validation renders it synchronously on submit; a server-side validation response does the same when it arrives. This summary is the exception to the layout-stability rule against inserting above the viewport (`baseline.md`, Layout stability), because the view moves to it.
- Inline errors show under each field at the same time as the summary.
- The summary's content changes only on the next submit, and the summary is removed when a submit passes validation.

## Submit

- Submit and Next stay enabled for invalid input and go busy, not disabled, while in flight (`baseline.md`, Unavailable actions); the busy label names the progress.
- On failure every typed value stays. The message distinguishes network failure, validation rejection, and server error, and offers a retry.
- The server recomputes prices and totals from its own data, never from the submitted values.
- The label names the outcome ("Create account", "Send invoice"), not "Submit".

## Specific inputs

- **Password:** show/hide toggle, paste allowed, requirements shown live, length favored over symbol rules. `autocomplete="new-password"` lets password managers generate one.
- **OTP:** one string in state, the boxes are just a view of it. Paste into any box strips non-digits and fills all boxes. Focus advances on entry, and Backspace on an empty box moves back. Set `inputmode="numeric"` and `autocomplete="one-time-code"`. Resend is throttled behind a visible countdown. A wrong code clears the boxes, refocuses, and says so.
- **Codes and identifiers:** `type="number"` is only for quantities a user would step up or down. OTP, PIN, CVC, postal/ZIP, card, account, phone, and ID numbers use `type="text"` (`tel` for phone) with `inputmode="numeric"`, plus `autocomplete` where one applies. `type="number"` breaks codes: the mouse wheel over a focused field and the arrow keys change the value; leading zeros are dropped; `e`, `+`, `-`, and `.` are accepted; `maxlength` is ignored; spinners are drawn; `.value` is `""` for input the browser can't parse.
- **Autofill:** browsers paint autofilled fields with their own fill and text color and ignore the theme, which leaves a bright block in dark mode. Style the state on `input:autofill` plus `input:-webkit-autofill` (Safari), including the `:hover` and `:focus` combinations. Fill: an inset shadow covering the box in the field's own surface color, e.g. `box-shadow: 0 0 0 1000px var(--field-bg) inset`. Text: `-webkit-text-fill-color: var(--text)` and `caret-color: var(--text)`. If the focus ring is a box-shadow, list it in the same `box-shadow` after the inset fill so autofill doesn't erase it; an `outline` ring needs nothing. The autofilled field matches the normal field surface in every theme, and its text passes 4.5:1 against that surface. A floating label is floated in this state.
- **Masked input (card, phone, IBAN):** display formatted, store raw. The caret stays after the character just typed when a separator is inserted. Pasted separators are cleaned, not rejected. Card brand shows from the leading digits. Validate on blur.
- **Date:** date ranges lead with presets (Today, Last 7 days, Last 30 days, This quarter) and keep a custom range for the rest. Show two months side by side for ranges. The date can be typed. The grid is keyboard navigable (arrows, Page Up/Down for month, Enter, Escape). On mobile use a full-screen sheet or the native input.
- **Slider:** filled track, live value readout, snaps to steps, hit area spans the row height, arrows/Home/End/Page keys work, two thumbs for ranges. Pair with a number input when exact values matter.
- **Toggle:** `role="switch"` with `aria-checked`, Space toggles. It applies immediately; a toggle inside a form that waits for Save should be a checkbox instead. Async toggles flip optimistically, show pending inside the knob, and roll back with a message on failure.
- **Switch look:** a `full`-radius track about twice as wide as it is tall (36×20px at every pointer, with the hit area extended to the target size per `baseline.md` rather than a larger track on touch) and a round knob inset 2px. On: accent track, white knob at the end. Off: neutral track filled at 3:1 against its surface, because the track is the only boundary the control has; a pale grey track with a white knob reads as missing. The knob takes a contact shadow (`0 1px 2px rgb(0 0 0 / 0.2)`); the track has no border. The label sits beside the switch and names the on state (`feedback.md`); no ON/OFF text inside the track, where it doubles the state and gets clipped in translation. An icon in the knob is fine when it names the value itself (sun and moon for theme). A square or rectangular switch reads as a button or a segmented control, so keep the pill.
- **Switch motion:** the knob moves with `transform: translateX()` and the track color crossfades with `background-color`, both as CSS transitions (never keyframes, `motion.md`) over 150–200ms on `--ease-enter`. Pressing stretches the knob a few pixels toward its travel and releasing slides it, so a held press already shows which way it goes. The first render shows the current state without animating, under `prefers-reduced-motion: reduce` the knob jumps and only the color changes, and in RTL the travel mirrors (`translateX` with a negative value, or logical `inset-inline-start`).
- **Segmented control** (one choice of 2–5 short options, applied at once): a track one surface step below its container, `md` radius, 2px padding, no border; the selected option is a raised surface (`surface` with a contact shadow) in the `text` color at 600, the others transparent in `text-muted`, hover one step darker on the track. No border on the track or on the selected option: the 3:1 boundary rule is for inputs (`materials.md`), and here fill, weight, and `aria-pressed` (or `role="radiogroup"` with `aria-checked`) carry the state. This spec is for a new control; a project whose segmented control or switch already draws a border keeps it. Reserve the 600 weight's width on every option (a hidden bold copy of the label, or a fixed width) so selecting doesn't nudge its neighbors. The selected surface is one element that slides to the new option (`transform: translateX()` plus `scaleX()` for options of different widths, 150–200ms), except in a tool filter switched many times a session, where the frequency gate makes it instant (`motion.md`).
- **Inline edit:** see the section below.
- **File upload:** the dropzone reacts on drag-over (border, background, copy). Type and size are checked before uploading, with a specific message. Each file gets its own progress (percent, plus time remaining for large files) and its own retry that doesn't require re-selecting. Show a preview or thumbnail with type and size as proof of the right file.

## Inline edit

- **Match the mode to the cost of a typo.** Click-to-edit is for fields where a slip is cheap and undone in a keystroke: a title, a name, a label. Fields whose change means something or triggers something (status, amount, dates that bill or notify, permissions) open an explicit edit (an Edit button, then Save and Cancel). In a grid, a single click selects the cell and editing starts with Enter, F2, typing, or a double-click, so a stray click never writes.
- **Say it's editable.** On hover and focus the text gets a soft background tint and a pencil. The pencil is a real `<button>` ("Rename"), so keyboard users reach it; on touch (`@media (hover: none)`), where hover never fires, it stays visible. Clicking the text is a shortcut to the same edit.
- **Same box, different chrome.** The input takes the text's font, size, weight, line-height, tracking, and padding. The border exists in both states, transparent at rest and visible while editing, so the box doesn't grow by its width. A value that can wrap becomes a `<textarea>` that grows with its content (`field-sizing: content`, or a measured height), never a one-line input that collapses two lines into one.
- **Keys.** Enter commits and Escape restores the original; both return focus to the text or its pencil. In a multi-line field Enter adds a line and Cmd/Ctrl+Enter commits. Enter pressed while an IME is composing (`event.isComposing`) finishes the word, not the edit.
- **Blur commits, everywhere.** Clicking away saves, as in docs and spreadsheets, so work is never lost to a stray click. Pick this once for the whole app and never vary it. An unchanged value sends no request; an empty required value reverts to the saved one.
- **Save optimistically** (`feedback.md`): the new value shows at once. If the server rejects it, the text rolls back to the saved value, the draft is kept, and the message says why and offers a retry ("Couldn't save, your draft is kept · Retry"); reopening the edit restores the draft.

## Consent

- Refusing is as easy and as visible as accepting: "Reject all" sits beside "Accept all" on the first layer, same size, style, and number of clicks. A refusal shown as a muted link or behind "Manage settings" is what European regulators treat as invalid consent.
- Required processing is stated, not asked, so it has no checkbox. Each optional purpose (analytics, marketing, personalization) is its own control, off by default, never pre-ticked and never bundled into accepting the terms.
- Labels name the choice and its effect ("Allow analytics cookies", "Email me product updates"), with no shaming decline ("No thanks, I like paying more") and no false urgency.
- Withdrawing is as easy as giving: a persistent link (footer or settings) reopens the same choices, and a change applies without a reload.
- Browser permission prompts (notifications, location, camera) fire from the user action that needs them, after one line saying why, never on page load: once denied, the page can't ask again, so a wasted prompt costs the feature.
- Legal and consent wording comes from its owner: write a placeholder marked for review instead of inventing terms, and never change the meaning of existing text.

## Checks

- [ ] Every input has a label that stays visible when filled, the correct `type`, and `autocomplete`.
- [ ] On touch every field is at least 16px with zoom left enabled; email, username, and code fields don't autocapitalize or autocorrect.
- [ ] The network-failure and server-error branches keep all values and show distinct messages with a retry.
- [ ] Errors appear on blur, re-check on every input while shown, and go back to on-blur once fixed.
- [ ] Every field reserves its message slot, so showing a one-line error moves neither the fields below nor the submit button.
- [ ] A submit with errors shows a top summary that links every broken field and takes focus in the frame it renders.
- [ ] Autofilled fields keep the theme's surface and readable text in every theme.
- [ ] No code or identifier uses `type="number"`.
- [ ] Submit is never disabled for validity, and a double submit is impossible.
- [ ] Paste works in password, OTP, and masked fields.
- [ ] Switches are pills with a round knob, an off track at 3:1, and a sliding knob that skips the first render and reduced motion; segmented controls have no border on the track or the selected option.
- [ ] No step asks again for information an earlier step already collected.
- [ ] Inline edit is used only where a typo is cheap; entering edit moves nothing; Enter, Escape, and blur behave the same everywhere; a rejected save rolls back and keeps the draft.
- [ ] Consent offers reject beside accept at equal weight, optional purposes start off and are separate from required processing, and the choices can be reopened later; permission prompts fire only from a user action.
