# UI review

Review UI changes (`.tsx`, `.jsx`, `.vue`, `.svelte`, `.html`, `.css`, `.scss`, Tailwind classes in any file) for what they broke or left half done. Category `correctness` throughout; start each `issue` with its status from item 4.

1. **Removed signals**: read the `-` side of every hunk, since a regression is invisible in the code that remains. Search deleted lines only, so an addition elsewhere can't mask a removal: `grep -E '^-' <diff> | grep -vE '^--- (a/|/dev/null)' | grep -E 'aria-|role=|alt=|<label|htmlFor|focus|outline|tabindex|prefers-|lang=|dir=|text-wrap|tabular-nums|-inline|-block|inert'`, then read each hit's hunk for the element it sat on. A removed signal is a finding unless the `+` side carries an equivalent:
   - focus: the removed `outline` or `outline-none` sits next to a visible `focus-visible:` ring or box-shadow on the same element
   - semantics: the element became its native counterpart (`<button>`, `<nav>`, `<a href>`), so its `role` and `tabindex="0"` are now redundant
   - naming: the `aria-label` gave way to visible text that names the control, through `aria-labelledby` or a bound `<label>`
   - preferences: the `prefers-*` query moved to a shared stylesheet or became a `motion-safe:`/`motion-reduce:` variant
   - direction: `left` or `margin-right` became `inset-inline-start` or `margin-inline-end`, an improvement for RTL

   What an unmatched removal costs: an accessible name, description, or live region gone; `alt` or a label association gone; a focus indicator or tab stop gone; motion that now ignores `prefers-reduced-motion`; `lang` or `dir` dropped; `text-wrap` or `tabular-nums` dropped where text wraps or numbers align in columns; logical properties swapped for physical ones; `inert` removed from content behind a modal. A deleted or shortened user-facing string has no pattern: read those hunks for a label, error, or empty state that lost its information.
2. **Incomplete change against the stated intent**: compare the diff with the Phase 0 task list and look for the states that are absent, which a review of the existing code never surfaces:
   - a new variant, size, or theme styled for some of hover, focus-visible, active, disabled, loading, and selected but not all
   - a new user-facing string missing from the translation catalogue, when the project has one (`locales/`, `messages/`, `i18n/`, `*.po`, `*.resx`); quote the hardcoded string and the catalogue path
   - a new list, table, or fetching component with no empty, loading, or error state
   - a new interactive element a keyboard can't reach or operate: a click handler on a `div` or `span` without a native element, `tabindex`, and key handler, or a custom popover with no Escape and no focus return
   - a control added to one surface but not to the sibling surfaces that already carry its peers
3. **Blast radius of a shared component**: when the diff changes a component, hook, token, or style other files import, review up to 5 consumers, route and layout entry points first (`app/**/page.*`, `app/**/layout.*`, `pages/**`, `routes/**`, `src/views/**`), then by how many files import each. For a token or CSS variable, search its name, not the file. Check each consumer still gets the props, slots, variants, and states it relied on: a renamed or removed prop, a changed default, a class the consumer overrides that no longer exists. State how many consumers were not expanded in `not_verified`.
4. **Status per finding**:
   - `Introduced`: new code in this diff has the defect
   - `Regression`: it worked before and this diff broke it; confirm with `git show <base>:<path>` (`HEAD` for uncommitted work) or `git blame` on the line before calling it a regression, and quote the old line in `evidence` alongside the new one
   - `Pre-existing`: present before the diff and not made worse by it, so out of scope; report only a `high` one, at most three, and Phase 2 leaves them unfixed

   Status by cause, not location: an untouched consumer broken by a changed shared component or token is `Regression`, not `Pre-existing`.
5. **Rendering and handler checks**: when the diff changes layout, styles, or focus behavior and the app can be served, also call the Skill tool with `arc-design:ui-check` to measure the rendered page; when it changes an event handler or a shared store action, also call `arc-design:state-check`. Use each only when it appears in your skill list; otherwise list the check under `not_verified`.
