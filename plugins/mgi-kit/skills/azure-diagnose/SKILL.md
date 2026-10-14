---
name: azure-diagnose
description: "Read-only az CLI diagnosis of live App Service, Functions, Container Apps, PostgreSQL flexible, Service Bus: why one resource errors, slows or won't start, or an audit of a whole tenant, cost included. Use when a deployed app or Azure resource misbehaves (\"app lỗi 500\", \"Azure có gì đáng lo\", \"audit tenant\", \"chi phí Azure tăng\"). Not for a failed pipeline run (see mgi-kit:ado-pipelines-advisor) or a bug that reproduces locally (see arc-kit:debug)."
---

# Azure diagnose

Two modes. **Diagnose**: find out why one running workload misbehaves, from evidence with timestamps (sections 1 to 4). **Audit**: survey a tenant for what is failing, at risk, or unobservable, then rank it ([Audit](#audit)). Both are read-only: no restart, scale, setting change, redeploy, or diagnostic setting added, even when it is the obvious fix. Give the fix and the command, and let the user run it.

Before starting, read `references/codex-workflow.md` for the complete workflow, checks, and report format. Load its other references only when the relevant step calls for them.

Resolve bundled paths from the parent skill directory containing SKILL.md, including paths in references; resolve target project paths from the project working directory. Before a shell command, resolve bundled script paths to absolute paths and quote them. Follow project AGENTS.md and the active runtime's instructions, tools, permissions, and concurrency limits. Existing user authorization persists across discovery, implementation, and review; ask only about unresolved scope or actions outside it. Use available question tools for preferences, or ask in chat when unavailable. Delegate only when allowed and supported; otherwise run the same checks inline and report when an independent review was unavailable. Inherit the session model unless the user explicitly requests model routing and the runtime supports it. Do not assume named plugin agents, fixed model names, or a fixed worker count.
