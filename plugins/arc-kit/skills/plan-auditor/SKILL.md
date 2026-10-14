---
name: plan-auditor
description: "Audit technical plans before execution for real APIs, valid references, missing steps, edge cases, scope, and proportionality. Use when the user requests review this plan, audit the plan, check for gaps, verify the approach, kiểm tra plan, or soát lại kế hoạch. Ground findings in project evidence and mark inaccessible assumptions unverified. Not for executing a plan or reviewing completed code."
---

# Plan Auditor

The plan to audit is: $ARGUMENTS

Before starting, read `references/codex-workflow.md` for the complete workflow, checks, and report format. Load its other references only when the relevant step calls for them.

Resolve bundled paths from the parent skill directory containing SKILL.md, including paths in references; resolve target project paths from the project working directory. Before a shell command, resolve bundled script paths to absolute paths and quote them. Follow project AGENTS.md and the active runtime's instructions, tools, permissions, and concurrency limits. Existing user authorization persists across discovery, implementation, and review; ask only about unresolved scope or actions outside it. Use available question tools for preferences, or ask in chat when unavailable. Delegate only when allowed and supported; otherwise run the same checks inline and report when an independent review was unavailable. Inherit the session model unless the user explicitly requests model routing and the runtime supports it. Do not assume named plugin agents, fixed model names, or a fixed worker count.
