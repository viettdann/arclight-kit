---
name: ui-interaction
description: "Behavior and state rules for interactive UI: forms and validation, submit, loading, errors, empty states, tables, selection, pagination, search, filters, overlays, menus, tabs, toasts, destructive actions, undo, autosave, settings, keyboard and focus. Use when building an interactive component or screen, or adding or changing its behavior (React, Vue, Svelte, plain HTML/CSS). Not for visual styling, color, or tokens (see design, restyle, redesign)."
---

# UI Interaction Rules

Generated UI tends to render only the happy path: every column in the table, a disabled submit button, a blank screen when search finds nothing, a generic "Are you sure?". These rules cover the rest.

## Workflow

1. Load `references/baseline.md`, plus only the references for surfaces you are creating or changing, not everything on the screen. Adding a delete button to an existing table needs `destructive.md`, not the form or overlay rules.

| Surface you create or change | Load |
| --- | --- |
| Forms, inputs, validation, password, OTP, masked fields, date, slider, toggle, inline edit, file upload | `references/forms.md` |
| Tables, lists, selection, bulk actions, pagination, search, filters, command palette | `references/data.md` |
| Modals, sheets, drawers, popovers, menus, dropdowns, tooltips, tabs, accordions, navigation, drag and drop, swipe | `references/overlays.md` |
| Loading, errors, empty states, toasts, notifications, optimistic updates, autosave, microcopy | `references/feedback.md` |
| Delete, irreversible actions, undo, settings pages | `references/destructive.md` |

2. For each new component, note in one or two lines which states apply and which you skip and why. Put it in the summary or PR description, not in code comments. Skip this for small changes.
3. Build what was asked. Don't add surfaces nobody requested (offline banner, bulk selection, settings panel); suggest them instead.
4. Check the code against the `Checks` of the loaded references and fix what fails. If the project already has a fast typecheck or lint command, run it on the changed files; run tests only when a test covers the changed code. Don't install tooling or launch browsers unless asked. If nothing was run, say so.
5. End with a short list of what needs manual verification (screen reader, touch, real network).

## When rules conflict

Data safety, then accessibility, then preserving the user's input and place, then speed, then polish.

## Project overrides

If `DESIGN.md` or existing components already define a behavior (toast position, blur-to-save, confirmation policy), follow the project. Flag it only when it breaks data safety or accessibility.
