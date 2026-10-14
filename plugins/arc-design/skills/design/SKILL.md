---
name: design
description: "Design UI that doesn't exist yet: visual direction, profile (dense tool vs marketing/consumer) and optional style (minimal, premium, brutalist, cinematic, playful), design tokens, color, typography, spacing, radius, elevation and glass, motion, dark mode, and the project's DESIGN.md. Use when building a new page, screen, or project from scratch (landing, pricing, dashboard, app shell), setting up or reworking Tailwind or CSS-variable tokens and themes, adding dark mode (also to an existing project), or when the user asks for a visual direction or a named style (\"thiết kế giao diện\", \"làm trang landing\", \"dựng màn hình mới\", \"thêm dark mode\"). For a screen that already exists, use restyle (keep the layout, remove the generated look) or redesign (new visual language on existing content). Not for component behavior and states (see ui-interaction)."
---

# Design

Without an explicit direction, generated UI falls back to framework defaults (Tailwind indigo and zinc, Inter, the default shadcn theme, a gradient blob behind the hero), so every project looks the same. This skill makes the visual decisions explicit and keeps later work consistent with them.

Before starting, read `references/codex-workflow.md` for the complete workflow, checks, and report format. Load its other references only when the relevant step calls for them.

Resolve bundled paths from the parent skill directory containing SKILL.md, including paths in references; resolve target project paths from the project working directory. Before a shell command, resolve bundled script paths to absolute paths and quote them. Follow project AGENTS.md and the active runtime's instructions, tools, permissions, and concurrency limits. Existing user authorization persists across discovery, implementation, and review; ask only about unresolved scope or actions outside it. Use available question tools for preferences, or ask in chat when unavailable. Delegate only when allowed and supported; otherwise run the same checks inline and report when an independent review was unavailable. Inherit the session model unless the user explicitly requests model routing and the runtime supports it. Do not assume named plugin agents, fixed model names, or a fixed worker count.
