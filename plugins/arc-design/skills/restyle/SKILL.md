---
name: restyle
description: De-AI a generic, template-looking UI. Audits the code for "AI tells" (gradients, decorative icon tiles, identical card grids, big radius + drop shadow everywhere, pure-black dark themes, greetings/emoji, fake identical deltas, unaligned numbers) and rewrites it into a restrained, information-first design with one meaningful accent, clear hierarchy, borders instead of shadows, and honest copy. Use whenever the user wants to restyle, clean up or polish the look, "make it look less AI", "look more professional/like Linear/Stripe", de-template, or critique the visual design of an existing dashboard, admin panel, settings page, landing section, or any app UI, even without the word "restyle". Layout and structure stay; for a new visual language use redesign, for a screen that doesn't exist yet use design, for measured rendering defects (overflow, contrast, focus) use ui-check.
---

# Restyle: remove the AI tells

Use `references/principles.md` when evaluating or changing presentation.

Before editing, read `references/workflow.md` and `references/principles.md` for the workflow, five principles, data integrity rules, and limits on overcorrection.

Resolve reference and script paths relative to this `SKILL.md`. Before running a helper from the project directory, replace its relative path with the absolute installed path; keep the project working directory so target paths resolve correctly. Read applicable `AGENTS.md` instructions first. Use the session’s available shell, file-editing, and image-viewing tools; load only the references needed for the task.

Generated UIs look generic for a consistent reason: every visual choice is decoration instead of information. Gradients, rainbow icon tiles, equal-weight cards, soft shadows on everything, and friendly filler copy all say nothing. The fix is one rule applied five ways:

> **Every visual decision must carry information. If it says nothing, remove it. If it stays, it must mean something.**

The result should still be polished: this is restraint, not brutalism. Keep the layout's purpose, data bindings, behavior, and accessibility intact. If the user wants a new style or direction rather than the generated look removed, that is the redesign skill; if unclear, ask once: "Keep the current layout and clean it up, or a new look with the content kept?"

## Workflow

Follow the restyling workflow in `references/workflow.md`: inspect the current sources, identify the primary content, remove generated-look tells, apply the five principles, check contrast and rendering, and report. Keep the layout and behavior.

## The five principles

Apply the five principles in `references/principles.md`: meaningful color, useful decoration, content hierarchy, borders and radius, and informative copy and numbers. Follow its data integrity and overcorrection rules.

## References
- `references/tailwind.md`: class-level before/after mappings, a token setup snippet, the primary+secondary metric layout, and an inline SVG sparkline. Read it when applying fixes in Tailwind code.
- `../design/references/`: `profile-marketing.md` (marketing surfaces), `materials.md` (surfaces, shadow, glass), `dark-mode.md` (dark themes), `typography.md`, `radius.md`, `cards.md` (when the principles above say so).
