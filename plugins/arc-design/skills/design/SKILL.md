---
name: design
description: "Design UI that doesn't exist yet: visual direction, profile (dense tool vs marketing/consumer) and optional style (minimal, premium, brutalist, cinematic, playful), design tokens, color, typography, spacing, radius, elevation and glass, motion, dark mode, and the project's DESIGN.md. Use when building a new page, screen, or project from scratch (landing, pricing, dashboard, app shell), setting up or reworking Tailwind or CSS-variable tokens and themes, adding dark mode (also to an existing project), or when the user asks for a visual direction or a named style (\"thiết kế giao diện\", \"làm trang landing\", \"dựng màn hình mới\", \"thêm dark mode\"). For a screen that already exists, use restyle (keep the layout, remove the generated look) or redesign (new visual language on existing content). Not for component behavior and states (see ui-interaction)."
---

# Design

Before choosing a direction or editing UI, read `references/workflow.md` for the numbered workflow, reference selection, helper commands, and report contract.

Resolve reference and script paths relative to this `SKILL.md`. Before running a helper from the project directory, replace its relative path with the absolute installed path; keep the project working directory so target paths resolve correctly. Read applicable `AGENTS.md` instructions first. Use the session’s available shell, file-editing, and image-viewing tools; load only the references needed for the task.

Without an explicit direction, generated UI falls back to framework defaults (Tailwind indigo and zinc, Inter, the default shadcn theme, a gradient blob behind the hero), so every project looks the same. This skill makes the visual decisions explicit and keeps later work consistent with them.

## Match the effort to the task

- **Small change** (tweak a component, add a button or column, adjust spacing): use the tokens and the shared components already in the code. Skip `DESIGN.md`, profile and style references, and questions. Check contrast only for color pairs you introduced.
- **New surface or token work** (new page or screen, new project, setting up or reworking tokens or themes, or the user asks for a direction): follow the workflow below.

A change inside an existing surface (a new section, a modal) is a small change if it uses only existing tokens; if it needs a color, font, or scale value the tokens don't have, it's token work.

## Sources

The brief decides what to build; the code decides only which values to reuse. Carry over only what the user names.

- **Read:** the brief and the skill's arguments, `DESIGN.md`, token and theme files (Tailwind config or `@theme`, CSS variables), the component library and shared primitives, all in the current working tree.
- **Don't read** unless the user names the exact source in this conversation: git history (`git log`, `git show`, `git diff` against old commits), other branches, stashes, other repos, worktrees, or sibling project folders, redesign snapshots in a temp dir, and earlier attempts at the same surface. A previous version of the surface is not a reference; it is the thing being replaced.
- **Existing screens give values, not content.** Read them for tokens, conventions, and which shared components exist. Write the new surface's markup, section structure, and copy from the brief; don't copy them from another page, file, or commit.
- **Precedence:** the arguments and brief of this turn, then `DESIGN.md`, then the code. Where the brief departs from `DESIGN.md`, follow the brief and list the departure in the summary.
- **Use this workflow for the current design task.** Keep applicable project instructions and the user’s current constraints. Rules from redesign or restyle (keep the content, rebuild from what exists) don't carry into a design run.

## Workflow

Read and follow steps 0–7 in `references/workflow.md` before designing: parse the brief, follow or create `DESIGN.md`, choose the profile and any requested style, set tokens, build complete interaction states, check contrast, and verify rendering. Load only the profile, style, and domain references the surface needs.

## Variants (only when asked)

When the user asks for options, variants, or directions, explore before building the real surface:

1. Name the axis the variants differ on (density, hierarchy, layout, type, palette), one per run unless the user asks for a broad exploration; with a `DESIGN.md`, the axis is layout or composition. A variant set that differs on everything can't tell the user which choice they preferred.
2. Write N named one-line concepts (three unless the user gives a number), each at a different position on that axis.
3. Reject any pair whose one-line headlines could be swapped without anyone noticing: they are one concept. Replace it.
4. Confirm the concepts with the user before building.
5. Build each as a static HTML file in a fresh temp dir (`mktemp -d`), from the brief's real content and the tokens of workflow step 5, and shoot each at 1280 and 390 with the screenshot script (step 7). Present the shots by concept name with their paths, plus a table with one row per concept: what it is right for, and what it costs. Don't mark a favourite; the user picks.
6. Build the chosen concept through the workflow; it becomes the direction recorded in `DESIGN.md`. Delete the temp dir afterwards; the variants are never a source for later work.

## Rules for every profile and style

- One accent per view, spent on the primary action and the current selection. Status colors only for status.
- Don't ship a framework's default palette as the brand unless the project already committed to it. Swapping it for another habitual choice (the same "tasteful" font, accent, or card style on every project) is the same problem; each choice gets a reason tied to this product in `DESIGN.md`. Styles define how values relate, not fixed values: colors and fonts still come from the brand. Three looks are the habitual choice of generated pages; unless the brief asks for one, avoid (a) a cream background with a serif display and a terracotta accent, (b) near-black with one neon accent and glowing edges, (c) newspaper hairlines with an italic serif and tiny tracked mono labels. A warm, bookish, or child-facing subject doesn't license (a). Test any direction: if someone could guess the look from the product category alone, it's habit, not a decision.
- Every value comes from a scale (spacing on a 4px base, type, radius, elevation, duration). Off-scale values need a reason.
- Radius is a role on one scale; nested corners are concentric (inner = outer − padding). See `references/radius.md`.
- Hierarchy comes from size, weight, contrast, and space together. Two weights, 400 and 600, unless the style lists another (`references/typography.md`).
- Monospace only for code, ids, data, and measurements, never as a costume that makes labels or headings look technical.
- Responsive layout is a structural decision, not the desktop layout shrunk. For each surface, decide what stacks, what collapses (navigation into a menu, secondary panels into a drawer or disclosure), what scrolls on its own axis (wide tables, tab rows, filter chips), and what stays fixed or reachable (the primary action, the current location). Narrow tables follow `../ui-interaction/references/data.md`.
- Under `prefers-reduced-motion: reduce`, override every animation and every transition that moves or scales (including hover `translateY`); color and opacity transitions may stay.
- Light theme by default. Add a dark theme, or follow `prefers-color-scheme`, only when the user asks for it or the project already has one; otherwise the page renders differently from what was reviewed.
- Dark mode is its own token set, not an inversion: near-black layers stepped in lightness, alpha inks and hairlines, a calmer accent. See `references/dark-mode.md`.
