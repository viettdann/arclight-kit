---
name: design
description: "Design UI that doesn't exist yet: visual direction, profile (dense tool vs marketing/consumer) and optional style (editorial-minimal, soft-premium, brutalist), design tokens, color, typography, spacing, radius, elevation, motion, dark mode, and the project's DESIGN.md. Use when building a new page, screen, or project from scratch (landing, pricing, dashboard, app shell), setting up or reworking Tailwind or CSS-variable tokens and themes, adding dark mode, or when the user asks for a visual direction or a named style. For a screen that already exists, use restyle (keep the layout, remove the generated look) or redesign (new visual language on existing content). Not for component behavior and states (see ui-interaction)."
argument-hint: "[editorial-minimal | soft-premium | brutalist | none] [what to build]"
---

# Design

Without an explicit direction, generated UI falls back to framework defaults (Tailwind indigo and zinc, Inter, the default shadcn theme, a gradient blob behind the hero), so every project looks the same. This skill makes the visual decisions explicit and keeps later work consistent with them.

## Match the effort to the task

- **Small change** (tweak a component, add a button or column, adjust spacing): use the tokens and patterns already in the code. Skip `DESIGN.md`, profile and style references, and questions. Check contrast only for color pairs you introduced.
- **New surface or token work** (new page or screen, new project, setting up or reworking tokens or themes, or the user asks for a direction): follow the workflow below.

A change inside an existing surface (a new section, a modal) is a small change if it uses only existing tokens; if it needs a color, font, or scale value the tokens don't have, it's token work.

## Workflow

0. If the skill was invoked with arguments and the first word is a style name (`editorial-minimal`, `soft-premium`, `brutalist`) or `none`, that is the user's style choice for step 4; the rest is the brief.
1. If `DESIGN.md` exists at the repo root, follow it. To change it, propose the change instead of silently diverging.
2. If it doesn't exist and this is a project (not a one-off file), derive decisions from the code first: Tailwind config or `@theme`, CSS variables, theme files, component library, one or two existing screens. Write `DESIGN.md` from `references/design-md-template.md`. Don't stop to ask: choose where the code is silent and list those choices as assumptions at the end, so the user can correct them. Ask first only when a wrong guess would be costly to undo.
3. Pick the **profile** per surface (one product can use both). The profile sets density, type size, and how depth is made:
   - **Tool** (admin, dashboard, editor, internal or B2B app): `references/profile-tool.md`.
   - **Marketing/consumer** (landing, pricing, onboarding, storefront, consumer app): `references/profile-marketing.md`.
4. Pick a **style** only when the user names one (as the step 0 argument or in the brief) or the brief clearly points to it; otherwise the profile alone is the direction. If step 0 gave `none`, use no style. A style is a visual language layered on the profile, never a replacement for its rules:

   | Style | Signals in the brief | Profiles |
   | --- | --- | --- |
   | `references/styles/editorial-minimal.md` | minimal, calm, editorial, document-like, Notion/Linear | tool, marketing |
   | `references/styles/soft-premium.md` | premium, luxury, wellness, Apple-like, expensive, soft | marketing |
   | `references/styles/brutalist.md` | brutalist, Swiss, raw, terminal, technical, blueprint | tool, marketing |

   Read only the chosen style file. If you wrote `DESIGN.md` in step 2, record profile and style there; if it already existed and doesn't match, propose the change (step 1). For a marketing surface, start the summary with its design read (see the profile), naming the style if one applies.
5. Tokens before markup, following `references/tokens.md`; components reference semantic tokens only.
6. Check contrast in each theme for the pairs you added or changed, in one command. Include muted, placeholder, link, and status text (where failures hide), plus UI boundaries and focus rings: `node ${CLAUDE_SKILL_DIR}/scripts/contrast.mjs "#8a8a85|#ffffff|text" "#0f766e|#ffffff|ui"`. Pairs are `fg|bg|kind`; colors are hex, `oklch()`, or translucent; kind is `text` (4.5:1, default), `large` or `ui` (3:1). It exits 1 if any pair fails. Fix and re-run once; if pairs still fail, list them with their ratios in the summary. If `node` isn't available, compute the WCAG ratio another way or say in the summary that contrast wasn't machine-checked.
   For a marketing surface, also run `python3 ${CLAUDE_SKILL_DIR}/../restyle/scripts/scan_tells.py <page files>`: fix each `6-marketing` hit or explain it in the summary. If `python3` or the script isn't available, skip it and say so.
7. Don't take screenshots or launch browsers unless asked; the user judges the look. End with what to look at (narrow viewport, hover and focus, and both themes if there are two).

## Rules for every profile and style

- One accent per view, spent on the primary action and the current selection. Status colors only for status.
- Don't ship a framework's default palette as the brand unless the project already committed to it. Swapping it for another habitual choice (the same "tasteful" font, accent, or card style on every project) is the same problem; each choice gets a reason tied to this product in `DESIGN.md`. Styles define how values relate, not fixed values: colors and fonts still come from the brand.
- Every value comes from a scale (spacing on a 4px base, type, radius, elevation, duration). Off-scale values need a reason.
- Nested corners are concentric: inner radius = outer radius − padding.
- Hierarchy comes from size, weight, contrast, and space together. No weight below 400 under 16px.
- Under `prefers-reduced-motion: reduce`, override every animation and every transition that moves or scales (including hover `translateY`); color and opacity transitions may stay.
- Light theme by default. Add a dark theme, or follow `prefers-color-scheme`, only when the user asks for it or the project already has one; otherwise the page renders differently from what was reviewed.
- Dark mode is its own token set, not an inversion: near-black base (not `#000`), off-white text (not `#FFF`), elevation by lighter surfaces, accents adjusted to keep contrast without glowing.
- Contrast: 4.5:1 for text; 3:1 for large text, UI boundaries, icons, and focus rings.
