---
name: design
description: "Design UI that doesn't exist yet: visual direction, profile (dense tool vs marketing/consumer) and optional style (editorial-minimal, soft-premium, brutalist), design tokens, color, typography, spacing, radius, elevation, motion, dark mode, and the project's DESIGN.md. Use when building a new page, screen, or project from scratch (landing, pricing, dashboard, app shell), setting up or reworking Tailwind or CSS-variable tokens and themes, adding dark mode (also to an existing project), or when the user asks for a visual direction or a named style. For a screen that already exists, use restyle (keep the layout, remove the generated look) or redesign (new visual language on existing content). Not for component behavior and states (see ui-interaction)."
argument-hint: "[editorial-minimal | soft-premium | brutalist | none] [what to build]"
---

# Design

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
- **This skill's rules replace any other design skill run earlier in the session.** Rules from redesign or restyle (keep the content, rebuild from what exists) don't carry into a design run.

## Workflow

0. If the skill was invoked with arguments and the first word is a style name (`editorial-minimal`, `soft-premium`, `brutalist`) or `none`, that is the user's style choice for step 4; the rest is the brief.
1. If `DESIGN.md` exists at the repo root, follow it where the brief is silent. Where the brief asks for something else (another style, profile, or direction), follow the brief and propose the matching `DESIGN.md` change in the summary instead of silently diverging.
2. If it doesn't exist and this is a project (not a one-off file), derive token decisions from the sources allowed above: Tailwind config or `@theme`, CSS variables, theme files, component library, and one or two existing screens for their values only. Write `DESIGN.md` from `references/design-md-template.md`. Don't stop to ask: choose where the code is silent and list those choices as assumptions at the end of the summary, so the user can correct them. Ask first only when a wrong guess would be costly to undo.
3. Pick the **profile** per surface (one product can use both). The profile sets density, type size, and how depth is made:
   - **Tool** (admin, dashboard, editor, internal or B2B app): `references/profile-tool.md`.
   - **Marketing/consumer** (landing, pricing, onboarding, storefront, consumer app): `references/profile-marketing.md`.
4. Pick a **style** only when the user names one (as the step 0 argument or in the brief) or the brief clearly points to it; otherwise the profile alone is the direction. If step 0 gave `none`, use no style. A style is a visual language layered on the profile, never a replacement for its rules:

   | Style | Signals in the brief | Profiles |
   | --- | --- | --- |
   | `references/styles/editorial-minimal.md` | minimal, calm, editorial, document-like, Notion/Linear | tool, marketing |
   | `references/styles/soft-premium.md` | premium, luxury, wellness, Apple-like, expensive, soft | marketing |
   | `references/styles/brutalist.md` | brutalist, Swiss, raw, terminal, technical, blueprint | tool, marketing |

   Read only the chosen style file. Its signature moves are examples of the style's spirit, not a menu: take the surface's distinctive move from this product (its data, workflow, or brand), and use a listed move only when it fits that product better than anything derived from it. If you wrote `DESIGN.md` in step 2, record profile and style there; if it already existed and doesn't match, propose the change (step 1).
5. Tokens before markup, following `references/tokens.md`, `references/typography.md`, and `references/radius.md`; components reference semantic tokens only. If the surface has cards, panels, or grouped sections, follow `references/cards.md`. If it shows people (avatars, member lists, comments), follow `references/avatars.md`. If there is a dark theme, follow `references/dark-mode.md`.
6. Check contrast in each theme for the pairs you added or changed, in one command. Include muted, placeholder, link, and status text (where failures hide), plus UI boundaries and focus rings: `node ${CLAUDE_SKILL_DIR}/scripts/contrast.mjs "#6b6b66|#ffffff|text" "#0f766e|#ffffff|ui"`. Pairs are `fg|bg|kind`; colors are hex (8-digit for alpha), `rgb()`, or `oklch()`, passed as written in the CSS without converting them first; kind is `text` (4.5:1, default), `large` or `ui` (3:1: large text, UI boundaries, icons, focus rings). It exits 1 if any pair fails. Fix and re-run once; if pairs still fail, list them with their ratios in the summary. If `node` isn't available, compute the WCAG ratio another way or say in the summary that contrast wasn't machine-checked.
   For a marketing surface, also run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/restyle/scripts/scan_tells.py <page files>`: fix each `6-marketing` hit or explain it in the summary. If `python3` or the script isn't available, skip it and say so.
   Then check the result against the `Checks` list of each reference you loaded and fix what fails.
7. Don't take screenshots or launch browsers unless asked; the user judges the look. When asked, use `node ${CLAUDE_SKILL_DIR}/scripts/screenshot.mjs <url-or-file> out.png --width 1280,390` (writes `out-<width>.png` per width, `--full` for the whole page, `--root <site-root>` for root-relative assets; exits 1 with an `overflow` line when a width scrolls sideways, 2 when no shot was taken; needs Node 22+ and Chrome, Chromium, or Edge). For a marketing surface, the summary's first line is the design read (see the profile), naming the style if one applies. End with what to look at (narrow viewport, hover and focus, and both themes if there are two).

## Rules for every profile and style

- One accent per view, spent on the primary action and the current selection. Status colors only for status.
- Don't ship a framework's default palette as the brand unless the project already committed to it. Swapping it for another habitual choice (the same "tasteful" font, accent, or card style on every project) is the same problem; each choice gets a reason tied to this product in `DESIGN.md`. Styles define how values relate, not fixed values: colors and fonts still come from the brand.
- Every value comes from a scale (spacing on a 4px base, type, radius, elevation, duration). Off-scale values need a reason.
- Radius is a role on one scale; nested corners are concentric (inner = outer − padding). See `references/radius.md`.
- Hierarchy comes from size, weight, contrast, and space together. Two weights, 400 and 600, unless the style lists another (`references/typography.md`).
- Under `prefers-reduced-motion: reduce`, override every animation and every transition that moves or scales (including hover `translateY`); color and opacity transitions may stay.
- Light theme by default. Add a dark theme, or follow `prefers-color-scheme`, only when the user asks for it or the project already has one; otherwise the page renders differently from what was reviewed.
- Dark mode is its own token set, not an inversion: near-black layers stepped in lightness, alpha inks and hairlines, a calmer accent. See `references/dark-mode.md`.
