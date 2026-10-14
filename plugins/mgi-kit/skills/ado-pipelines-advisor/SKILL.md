---
name: ado-pipelines-advisor
description: "Write, optimize, review, and preview Azure DevOps (Azure Pipelines) YAML from verified rules: templates, extends, parameters, ${{ }} / $[ ] / $( ) expressions, output variables, conditions, triggers, deployment jobs and environments, service connections, secrets, caching, task versions, failed runs. Use when editing azure-pipelines.yml or pipeline templates, when a pipeline doesn't trigger, skips a stage, has an empty variable, or fails at template expansion, or a run failed, even if the user never says \"Azure Pipelines\". Not for a deployed app failing at runtime (see mgi-kit:azure-diagnose)."
---

# Azure Pipelines advisor

Five modes: **Write** a pipeline or template, **Optimize** an existing one, **Review** one for defects, **Preview** its server-side expansion, **Diagnose** a failed run. Diagnose needs only [Mode routing](references/codex-workflow.md#mode-routing) and [Scripts](references/codex-workflow.md#scripts); the YAML rules below matter only when the cause is in the YAML.

Before starting, read `references/codex-workflow.md` for the complete workflow, checks, and report format. Load its other references only when the relevant step calls for them.

Resolve bundled paths from the parent skill directory containing SKILL.md, including paths in references; resolve target project paths from the project working directory. Before a shell command, resolve bundled script paths to absolute paths and quote them. Follow project AGENTS.md and the active runtime's instructions, tools, permissions, and concurrency limits. Existing user authorization persists across discovery, implementation, and review; ask only about unresolved scope or actions outside it. Use available question tools for preferences, or ask in chat when unavailable. Delegate only when allowed and supported; otherwise run the same checks inline and report when an independent review was unavailable. Inherit the session model unless the user explicitly requests model routing and the runtime supports it. Do not assume named plugin agents, fixed model names, or a fixed worker count.
