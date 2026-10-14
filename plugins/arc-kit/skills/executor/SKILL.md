---
name: executor
description: "Execute an existing implementation plan or task list with scoped exploration, safe ordering, optional TDD, risk-based validation, and completeness review. Use when the user requests execute the plan, implement this plan, thực thi, triển khai, or bắt đầu làm. Not for a one-off edit without a plan."
---

# Executor

Implement plans with discipline. Scan for blockers, explore per-task, verify everything.

Before starting, read `references/codex-workflow.md` for the complete workflow, checks, and report format. Load its other references only when the relevant step calls for them.

Resolve bundled paths from the parent skill directory containing SKILL.md, including paths in references; resolve target project paths from the project working directory. Before a shell command, resolve bundled script paths to absolute paths and quote them. Follow project AGENTS.md and the active runtime's instructions, tools, permissions, and concurrency limits. Existing user authorization persists across discovery, implementation, and review; ask only about unresolved scope or actions outside it. Use available question tools for preferences, or ask in chat when unavailable. Delegate only when allowed and supported; otherwise run the same checks inline and report when an independent review was unavailable. Inherit the session model unless the user explicitly requests model routing and the runtime supports it. Do not assume named plugin agents, fixed model names, or a fixed worker count.
