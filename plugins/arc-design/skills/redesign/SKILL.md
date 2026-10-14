---
name: redesign
description: "Give an existing product, site, or screen a new visual language while keeping its content, information architecture, URLs, and behavior. Use when the user wants to redesign, revamp, overhaul, modernize, or refresh the look of something that already exists, change its style or direction (\"làm lại giao diện\", \"đổi phong cách\", \"make it feel premium/minimal/brutalist/cinematic/playful\"), or apply a new brand look to current pages. Not for a screen that doesn't exist yet (use design), and not for removing the generated look while keeping the layout (use restyle)."
---

# Redesign

A redesign changes how an existing product looks and how its sections are composed. It does not change what the product says, where things live, or how they behave. Most redesign damage comes from that second part: renamed nav labels, broken URLs, dropped analytics hooks, copy rewritten without being asked.

Before starting, read `references/codex-workflow.md` for the complete workflow, checks, and report format. Load its other references only when the relevant step calls for them.

Resolve bundled paths from the parent skill directory containing SKILL.md, including paths in references; resolve target project paths from the project working directory. Before a shell command, resolve bundled script paths to absolute paths and quote them. Follow project AGENTS.md and the active runtime's instructions, tools, permissions, and concurrency limits. Existing user authorization persists across discovery, implementation, and review; ask only about unresolved scope or actions outside it. Use available question tools for preferences, or ask in chat when unavailable. Delegate only when allowed and supported; otherwise run the same checks inline and report when an independent review was unavailable. Inherit the session model unless the user explicitly requests model routing and the runtime supports it. Do not assume named plugin agents, fixed model names, or a fixed worker count.
