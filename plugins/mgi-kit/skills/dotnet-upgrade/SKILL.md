---
name: dotnet-upgrade
description: "Upgrade a .NET solution to a newer target framework (for example net8.0 to net10.0) with its runtime-tied packages, SDK pin, Docker images, CI, and tools. Inventories every project and where its TFM is set, reads Microsoft's breaking-change pages for each version crossed, records a build and test baseline, upgrades in an order that keeps the solution building, and reports new warnings and what lives outside the repo. Use when moving to a new .NET version or off one that is losing support (\"upgrade .NET\", \"nâng .NET\", \"lên .NET 10\", \"net8 hết support\", \"migrate to net10\"). Not for porting .NET Framework apps (it inventories them and stops), or for bumping a single package."
---

# .NET upgrade

Move the solution to the target framework with the build and tests green at every step, changing only what the upgrade requires. Facts about versions, support dates, and breaking changes are fetched, not recalled.

Before starting, read `references/codex-workflow.md` for the complete workflow, checks, and report format. Load its other references only when the relevant step calls for them.

Resolve bundled paths from the parent skill directory containing SKILL.md, including paths in references; resolve target project paths from the project working directory. Before a shell command, resolve bundled script paths to absolute paths and quote them. Follow project AGENTS.md and the active runtime's instructions, tools, permissions, and concurrency limits. Existing user authorization persists across discovery, implementation, and review; ask only about unresolved scope or actions outside it. Use available question tools for preferences, or ask in chat when unavailable. Delegate only when allowed and supported; otherwise run the same checks inline and report when an independent review was unavailable. Inherit the session model unless the user explicitly requests model routing and the runtime supports it. Do not assume named plugin agents, fixed model names, or a fixed worker count.
