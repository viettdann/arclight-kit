# Settings Pages

## Apply model

Choose per section, by what a change costs:

- **Preferences apply instantly** (theme, density, language, notification switches): the control is the save. Flip, done, with a quiet "Saved" per the autosave states (`feedback.md`). If the write fails, the control flips back and says why.
- **Identity waits for Save** (name, email, username, password, domain, billing details, security): edits are a draft. A save bar appears only while the draft differs from the saved values, pinned to the bottom of the viewport: "2 unsaved changes · Cancel · Save changes". Cancel restores the saved values; leaving with a draft asks first (`beforeunload` plus the router's blocker), and only then.
- One model per section. A Save button beside toggles that already saved leaves the user unsure what the button still does, so no page-wide Save at the bottom of a settings form.
- A change that needs proof applies only after the proof: a new email stays "Pending, verify new@example.com" until the link is clicked, and a password change asks for the current one.

## Structure

- Group by the job the user came to do, not by the table the values live in: Payments, Billing, Team, Notifications, not `users`, `org_settings`, `preferences`.
- Large products give each job its own page in a settings nav, with its own URL (`/settings/billing`), so it can be linked and reloaded.
- When personal and workspace settings both exist, split them and say whose settings a page changes ("acme · Workspace", "Your account").
- Each row is a label, one line on what it changes, and the control. Common settings come first; advanced ones sit behind one "Advanced" disclosure at the end of their group, not on a separate page.

## Search

- Past about 20 settings, one search box above the settings nav filters every level: pages, groups, single settings, including those under Advanced. Match labels, descriptions, and keywords ("dark" finds Theme, "2FA" finds Two-factor authentication).
- Each result shows its path ("Workspace › Security › Session timeout") and highlights the matched part.
- Enter jumps to the first result, arrows move between results: open the page, expand the collapsed group, scroll to the row, focus its control, and highlight the row briefly. Every setting has an anchor (`/settings/security#session-timeout`), so help docs and support can link to it.
- No match follows the search rules in `data.md`.

## Modified state

- A changed row is marked, not only colored: a dot beside the label, with "Modified" for screen readers, and the group header counts them ("1 modified").
- What "changed" means follows the apply model. In an instant section it means different from the default, and the row offers "Reset to default" naming the value ("Reset to 14px"), which applies at once. In a draft section it means different from the saved value, and Cancel on the save bar reverts it.
- The reset control sits beside the control it resets, visible only on changed rows, and keeps its space so the control doesn't move.

## Danger zone

- Destructive and hard-to-undo actions live in one danger zone at the bottom of the page they belong to, set apart by a danger-colored border and heading. Nothing destructive sits among ordinary settings.
- One row per action: what it does, what it affects, and an outlined danger button naming it ("Transfer ownership", "Archive workspace", "Delete workspace"). Order by severity, delete last.
- Friction follows `destructive.md`: the largest actions open a dialog that states the consequence and asks for the resource name. The confirm button stays unavailable until the typed text matches exactly (trimmed), and the prompt above the field shows the name to type, so the reason is in view.
- Account and workspace deletion re-asks for the password or second factor when the session is old.

## Checks

- [ ] Preferences apply on change and revert on failure; identity fields use a save bar that appears only with a draft; no section mixes the two.
- [ ] Groups follow user jobs, each job page has a URL, and advanced options are one click away.
- [ ] Search reaches every setting, shows its path, and Enter lands on the focused control.
- [ ] Changed rows are marked with text, not color alone, and each can be reset to its reference.
- [ ] Destructive actions sit only in the danger zone, with friction matched to severity.
