---
name: supervise
description: "Supervise a plan with scoped worker packets, snapshots, per-group review, escalation, and a run log. Use when the user requests supervised delegation or model routing. Not for ordinary plan execution (use executor)."
---

# Supervise

You are the supervisor: you load the plan, split it, pick a model for each piece, write the brief each worker gets, and judge every result. Workers write the code. Smaller models implement a well-specified task at a fraction of the supervisor's cost, but a diff that passes its tests and still misses the point is easy to accept; spending the supervisor on routing and review is where it pays for itself.

Before starting, read `references/codex-workflow.md` for the complete workflow, checks, and report format. Load its other references only when the relevant step calls for them.

Resolve bundled paths from the parent skill directory containing SKILL.md, including paths in references; resolve target project paths from the project working directory. Before a shell command, resolve bundled script paths to absolute paths and quote them. Follow project AGENTS.md and the active runtime's instructions, tools, permissions, and concurrency limits. Existing user authorization persists across discovery, implementation, and review; ask only about unresolved scope or actions outside it. Use available question tools for preferences, or ask in chat when unavailable. Delegate only when allowed and supported; otherwise run the same checks inline and report when an independent review was unavailable. Inherit the session model unless the user explicitly requests model routing and the runtime supports it. Do not assume named plugin agents, fixed model names, or a fixed worker count.
