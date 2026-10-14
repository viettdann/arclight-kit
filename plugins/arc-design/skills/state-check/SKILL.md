---
name: state-check
description: "Trace what each button, toggle, form submit, or shortcut does to state, call by call, to find handlers whose calls each work but leave the wrong final state: a later call or store action resetting what an earlier one set, an effect reverting the change, async responses landing out of order, stale closures, a read of state set earlier in the same handler, a label promising a save the handler never makes. Use when a control \"does nothing\" or does the wrong thing (\"bấm nút không ăn\", \"state bị reset\", \"click không chạy\"), after changing a shared store action (Zustand, Redux, context, query cache) to audit its callers, after a refactor touching shared state, or before shipping a critical flow. Reports first, fixes only when asked. Not for rendering defects (ui-check), backend/frontend API contract drift, or visual design."
---

# State check

Reading each function finds functions that are wrong. This skill finds handlers whose functions are all right and whose result is still wrong: `setComposeMode(true)` then `selectThread(null)`, where `selectThread` also clears `composeMode`. The button has a handler, nothing throws, the types check, and it does nothing. Read only the current working tree.

Before starting, read `references/codex-workflow.md` for the complete workflow, checks, and report format. Load its other references only when the relevant step calls for them.

Resolve bundled paths from the parent skill directory containing SKILL.md, including paths in references; resolve target project paths from the project working directory. Before a shell command, resolve bundled script paths to absolute paths and quote them. Follow project AGENTS.md and the active runtime's instructions, tools, permissions, and concurrency limits. Existing user authorization persists across discovery, implementation, and review; ask only about unresolved scope or actions outside it. Use available question tools for preferences, or ask in chat when unavailable. Delegate only when allowed and supported; otherwise run the same checks inline and report when an independent review was unavailable. Inherit the session model unless the user explicitly requests model routing and the runtime supports it. Do not assume named plugin agents, fixed model names, or a fixed worker count.
