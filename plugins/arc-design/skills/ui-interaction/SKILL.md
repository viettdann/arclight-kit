---
name: ui-interaction
description: "Behavior and state rules for interactive UI: forms and validation, inline edit, submit, loading, errors, success and confirmation screens, empty states, tables (including narrow widths), selection and bulk actions, pagination, search, filters, modals, menus and context menus, tabs, navigation and scroll restoration, toasts, badges, copy to clipboard, destructive actions, undo, autosave, settings pages, drag and drop, resizable panes, pull to refresh, installed apps, custom components, microcopy, consent, sound, keyboard and focus, animations and transitions (whether to animate, durations, enter and exit). Use when building an interactive component or screen, or adding or changing its behavior (React, Vue, Svelte, plain HTML/CSS). Not for visual styling, color, or tokens (see design, restyle, redesign), or for debugging an existing control that does nothing or the wrong thing (see state-check)."
---

# UI Interaction Rules

Generated UI tends to render only the happy path: every column in the table, a disabled submit button, a blank screen when search finds nothing, a generic "Are you sure?". These rules cover the rest.

## Workflow

1. Load `references/baseline.md`, plus only the references for surfaces you are creating or changing, not everything on the screen. Adding a delete button to an existing table needs `destructive.md`, not the form or overlay rules. A surface that matches several rows of the table below needs each of their references: a modal holding a form needs `overlays.md` and `forms.md`. When a reference points to the design skill (`typography.md`, `avatars.md`, `profile-tool.md`), those files are in `${CLAUDE_PLUGIN_ROOT}/skills/design/references/`; read one only when you build what it covers.

| Surface you create or change | Load |
| --- | --- |
| Forms, inputs, validation, password, OTP, masked fields, date, slider, toggle, inline edit, file upload, consent and cookie choices, browser permission prompts | `references/forms.md` |
| Custom components the platform and library don't provide: controlled and uncontrolled props, form submission and `required`, `data-*` and CSS-variable styling hooks, role choice (slider, meter, progressbar, toolbar, tree) | `references/components.md` |
| Tables (including tables on phones and in narrow panels), lists, clickable cards, selection, bulk actions, pagination, search, filters, command palette | `references/data.md` |
| Modals, sheets, drawers, popovers, menus, dropdowns, right-click and context menus, submenus, tooltips | `references/overlays.md` |
| Tabs, accordions, navigation, scroll restoration, sticky headers and jump links | `references/navigation.md` |
| Drag and drop, resizable panes and split handles, swipe, pull to refresh | `references/gestures.md` |
| Loading, errors, success and done screens, empty states, toasts, notifications, badges and unread counts, copy to clipboard, optimistic updates, autosave, microcopy (tone, case, status wording), onboarding steps, UI sound, AI-generated output (streaming, drafts, prompt box) | `references/feedback.md` |
| Animations and transitions: whether to animate, durations, popover origins, enter and exit, tooltip groups, motion performance | `references/motion.md` |
| Delete, remove, archive, disconnect, irreversible actions, undo | `references/destructive.md` |
| Settings pages: apply model and save bar, grouping, settings search, modified and reset, danger zone | `references/settings.md` |
| Installed web app or PWA: manifest, home-screen icons, startup images, navigation in standalone mode, install prompt or hint | `references/installed-app.md` |

2. For each new component, or existing component that gains a new async state, decide its states before building: loading, empty, error, success, and partial (some items failed, some data missing, a stream cut off). For a new screen, write a state table: one row per feature, one column per state, and every cell holds a decided design (what shows and what the user can do next) or `n/a` with the reason. For a single component, one or two lines do, e.g. "UserTable: loading skeleton, empty (no users / no match), error with retry, partial (failed rows marked, retry per row); skipped bulk selection (not requested)." Put it in the summary or PR description, not in code comments. Skip it when the change adds no new component and no new async state.
3. Build what was asked. Don't add surfaces nobody requested (offline banner, bulk selection, settings panel); suggest them instead.
4. Verify:
   - Check the code against the `Checks` of the loaded references and fix what fails.
   - Run the project's existing typecheck or lint command on the changed files, if there is one.
   - Run tests only if a test covers the changed code.
   - Say in the summary what was run, or that nothing was.
5. End with a short list of what needs manual verification, each naming the component and the behavior, e.g. "InvoiceTable: screen reader announces the new sort", "Upload: retry after dropping the network mid-file".

Don't install tooling or launch browsers unless asked.

## When rules conflict

Data safety, then accessibility, then preserving the user's input and place, then speed, then polish.

## Project overrides

If `DESIGN.md` or existing components already define a behavior (toast position, blur-to-save, confirmation policy), follow the project. Flag it only when it breaks data safety or accessibility.
