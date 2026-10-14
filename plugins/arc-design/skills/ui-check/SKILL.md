---
name: ui-check
description: "Measure rendering defects on a running page or static file at phone to wide widths: horizontal overflow and its cause, clipped or overlapping text, contrast per theme, focus without a visible state, unnamed controls, clickable elements a keyboard can't reach, targets under 24px, broken images, missing page language, blocked zoom, a lazy LCP image, JS errors and failed requests; optionally layout shifts, load timings and bytes against a baseline, and broken same-origin links. Use when the user asks to check, QA, or verify how a page renders (\"check the UI\", \"is anything broken\", \"kiểm tra giao diện\"), or before shipping a UI change; restyle and redesign run it last. Reports by impact, fixes only when asked. Not for taste (restyle), a new direction (redesign), component behavior (ui-interaction), or a control that does the wrong thing (state-check)."
---

# UI check

A page can pass every rule in its code and still break when it renders: a table pushes the page sideways at 375px, a label lands on a heading at 768px, a muted grey fails contrast only in the dark theme, a custom button loses its focus ring. These are measurable, so measure them instead of eyeballing a screenshot. This skill reports defects, not taste; taste is restyle's job.

Before starting, read `references/codex-workflow.md` for the complete workflow, checks, and report format. Load its other references only when the relevant step calls for them.

Resolve bundled paths from the parent skill directory containing SKILL.md, including paths in references; resolve target project paths from the project working directory. Before a shell command, resolve bundled script paths to absolute paths and quote them. Follow project AGENTS.md and the active runtime's instructions, tools, permissions, and concurrency limits. Existing user authorization persists across discovery, implementation, and review; ask only about unresolved scope or actions outside it. Use available question tools for preferences, or ask in chat when unavailable. Delegate only when allowed and supported; otherwise run the same checks inline and report when an independent review was unavailable. Inherit the session model unless the user explicitly requests model routing and the runtime supports it. Do not assume named plugin agents, fixed model names, or a fixed worker count.
