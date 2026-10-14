---
name: restyle
description: "De-AI a generic, template-looking UI. Audits the code for \"AI tells\" (gradients, decorative icon tiles, identical card grids, big radius + drop shadow everywhere, pure-black dark themes, greetings/emoji, fake identical deltas, unaligned numbers) and rewrites it into a restrained, information-first design with one meaningful accent, clear hierarchy, borders instead of shadows, and honest copy. Use whenever the user wants to restyle, clean up or polish the look, \"make it look less AI\", \"look more professional/like Linear/Stripe\", de-template, or critique the visual design (code, render, or a screenshot) of an existing dashboard, admin panel, settings page, landing section, or any app UI, even without the word \"restyle\". Not for new layouts or visual directions (design/redesign), or measured rendering defects (ui-check)."
---

# Restyle: remove the AI tells

Generated UIs look generic because every visual choice is decoration instead of information: gradients, rainbow icon tiles, equal-weight cards, shadows on everything, filler copy. The fix is one rule applied five ways:

Before starting, read `references/codex-workflow.md` for the complete workflow, checks, and report format. Load its other references only when the relevant step calls for them.

Resolve bundled paths from the parent skill directory containing SKILL.md, including paths in references; resolve target project paths from the project working directory. Before a shell command, resolve bundled script paths to absolute paths and quote them. Follow project AGENTS.md and the active runtime's instructions, tools, permissions, and concurrency limits. Existing user authorization persists across discovery, implementation, and review; ask only about unresolved scope or actions outside it. Use available question tools for preferences, or ask in chat when unavailable. Delegate only when allowed and supported; otherwise run the same checks inline and report when an independent review was unavailable. Inherit the session model unless the user explicitly requests model routing and the runtime supports it. Do not assume named plugin agents, fixed model names, or a fixed worker count.
