---
name: api-contract
description: "Audit ASP.NET controllers, Minimal API endpoints, and DTOs against their TypeScript/JavaScript consumers (hand-written fetch/axios/HttpClient services or NSwag/OpenAPI clients) for contract drift in both directions: renamed or removed JSON keys, enum values, new required fields, status codes, type changes. Reads source, reports only. Use when checking for breaking API changes, FE/BE contract sync, or a DTO or controller change before merging, including after a refactor (\"check breaking change\", \"API có vỡ không\", \"FE BE còn khớp không\"). Not for .NET version upgrades or EF Core query performance review."
license: MIT (adapted from github/awesome-copilot, see LICENSE.txt)
---

# API Contract

Cross-reference the C# API's actual contract (routes, DTOs, status codes) against its TypeScript/JavaScript consumers and report contract drift in both directions before it reaches production. This skill does not modify code.

Before starting, read `references/codex-workflow.md` for the complete workflow, checks, and report format. Load its other references only when the relevant step calls for them.

Resolve bundled paths from the parent skill directory containing SKILL.md, including paths in references; resolve target project paths from the project working directory. Before a shell command, resolve bundled script paths to absolute paths and quote them. Follow project AGENTS.md and the active runtime's instructions, tools, permissions, and concurrency limits. Existing user authorization persists across discovery, implementation, and review; ask only about unresolved scope or actions outside it. Use available question tools for preferences, or ask in chat when unavailable. Delegate only when allowed and supported; otherwise run the same checks inline and report when an independent review was unavailable. Inherit the session model unless the user explicitly requests model routing and the runtime supports it. Do not assume named plugin agents, fixed model names, or a fixed worker count.
