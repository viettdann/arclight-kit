# Custom Components

For a control that neither the platform nor the project's component library provides (rating, tag input, color picker, tree, custom select). A native element or an existing headless library comes first (`baseline.md`, Semantics); keyboard models for composites are in `navigation.md`, dismissal and layering in `overlays.md`.

## State API

- **One component, both modes.** Stateful props come as a trio: `value` (controlled), `defaultValue` (start value when uncontrolled), `on{Name}Change` (fires on every user change in both modes); likewise `open`/`defaultOpen`/`onOpenChange`, `checked`/`defaultChecked`/`onCheckedChange`, `page`/`defaultPage`/`onPageChange`. One shared helper (the library's or a `useControllableState`) picks the mode, so components don't each re-implement it and drift apart.
- **Controlled means `value !== undefined`, fixed at mount.** Use `null` for "controlled and empty" so `undefined` stays the only uncontrolled signal; warn in development when a component switches mode mid-life, because ownership of the state silently moves.
- **Controlled never writes its own state.** It calls `on{Name}Change` and renders whatever `value` comes back, so a parent that rejects a change (a max, a validation) keeps the old value on screen instead of a value nobody owns.
- **The callback reports user intent.** `on{Name}Change` fires on user actions, never when the `value` prop changes from outside, or a parent that sets state in the callback loops.

## Form participation

- **It submits with its form.** Given a `name`, the control renders `<input type="hidden" name value>` that tracks its value (one per value with the same name for multi-value controls such as tags), so a plain submit, `FormData`, and server actions read it with no glue code. On the form's `reset` event it returns to `defaultValue`, as a native input does. A web component uses form-associated custom elements (`ElementInternals.setFormValue`, `setValidity`) instead.
- **`required` blocks an empty submit.** A hidden input is excluded from constraint validation, so `required` on it does nothing. If the control has a real inner input (a tag input's text field), set `setCustomValidity("Add at least one tag")` on it while empty. Otherwise render a validation proxy while required and empty: a visually hidden (`sr-only`, never `display: none`, which the browser can't focus and so blocks submit silently) text input with `required`, `tabindex="-1"`, `aria-hidden="true"`, whose `invalid` handler calls `preventDefault()`, moves focus to the visible control, and shows the field error (`forms.md`, Validation timing).
- **The proxy is the one exception to baseline's no-`aria-hidden`-on-focusable rule** (`baseline.md`, Semantics), and only in this exact form: `tabindex="-1"` keeps it out of the Tab order and the `invalid` handler moves focus off it at once, so the keyboard never rests on a silent element. Anything looser, or a proxy where a real inner input could carry `setCustomValidity`, falls back under the baseline rule.

## Styling hooks

- **State as `data-*`, booleans by presence.** Expose the state consumers style against (`data-open`, `data-disabled`, `data-highlighted`, `data-state="checked|unchecked|indeterminate"`, `data-orientation`). A boolean attribute is present or absent, never `"false"`: `[data-open]` also matches `data-open="false"`, so the closed element styles as open. React renders `data-open={false}` as the string `"false"`; write `data-open={open || undefined}`. ARIA keeps its own `"true"`/`"false"` strings and is set alongside: data attributes are for CSS, ARIA for assistive tech.
- **Continuous values as CSS variables.** A value that varies continuously (percent filled, item count, trigger width, available height) goes in a custom property on the element that uses it (`--progress: 42%`), so consumers write `width: var(--progress)` instead of re-deriving it; an attribute can't feed `calc()`. Values that change every frame (drag, scroll) follow `motion.md`, Performance.

## Picking the role

Native first (`<input type="range">`, `<meter>`, `<progress>`); a role only when you build the element yourself. State attributes per role are in `baseline.md`, Semantics; a confirming modal's `alertdialog` is in `overlays.md`.

| What it is | Role | Must also have |
| --- | --- | --- |
| A number the user sets within a range | `slider` | `aria-valuenow`/`min`/`max`; `aria-valuetext` when the bare number misleads ("3 of 5 stars", "$40 to $80", "Medium") |
| A read-only measure in a known range (storage used, quota, password strength) | `meter` | value, min, max; never `progressbar`, which says a task is advancing |
| Progress of a task | `progressbar` | `aria-valuenow` when known, omitted when indeterminate; a name saying what is loading |
| Buttons acting on one target (editor formatting, row actions) | `toolbar` | `aria-label`, one Tab stop (`navigation.md`), `aria-orientation="vertical"` when vertical; a row of links stays `<nav>` |
| Nested expandable items in an app (file tree, folder picker) | `tree` / `treeitem` / `group` | `aria-expanded` on parents, `aria-selected` when selectable; site navigation with nested lists stays `<nav>` plus disclosure buttons, since tree arrow keys surprise users expecting Tab |

## Checks

- [ ] Stateful props follow `value`/`defaultValue`/`on{Name}Change` through one shared helper; a controlled component renders only the value it is given.
- [ ] A named custom control submits through a hidden input, resets with its form, and a required empty one blocks submit and focuses the visible control.
- [ ] No boolean `data-*` attribute renders as `"false"`; continuous values are CSS variables on the element that uses them.
- [ ] Each custom range, measure, progress, toolbar, or tree carries the role and attributes from the table.
