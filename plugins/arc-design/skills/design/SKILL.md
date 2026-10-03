---
name: design
description: "Design UI that doesn't exist yet: visual direction, profile (dense tool vs marketing/consumer) and optional style (minimal, premium, brutalist, cinematic, playful), design tokens, color, typography, spacing, radius, elevation and glass, motion, dark mode, and the project's DESIGN.md. Use when building a new page, screen, or project from scratch (landing, pricing, dashboard, app shell), setting up or reworking Tailwind or CSS-variable tokens and themes, adding dark mode (also to an existing project), or when the user asks for a visual direction or a named style (\"thiết kế giao diện\", \"làm trang landing\", \"dựng màn hình mới\", \"thêm dark mode\"). For a screen that already exists, use restyle (keep the layout, remove the generated look) or redesign (new visual language on existing content). Not for component behavior and states (see ui-interaction)."
argument-hint: "[minimal|premium|brutalist|cinematic|playful|none] [brief]"
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

0. If the skill was invoked with arguments and the first word is a style name (`minimal`, `premium`, `brutalist`, `cinematic`, `playful`) or `none`, that is the user's style choice for step 4; the rest is the brief. The old names `editorial-minimal` and `soft-premium` (in arguments or an existing `DESIGN.md`) mean `minimal` and `premium`.
1. If `DESIGN.md` exists at the repo root, follow it where the brief is silent. Where the brief asks for something else (another style, profile, or direction), follow the brief and propose the matching `DESIGN.md` change in the summary instead of silently diverging.
2. If it doesn't exist and this is a project (not a one-off file), derive token decisions from the sources allowed above: Tailwind config or `@theme`, CSS variables, theme files, component library, and one or two existing screens for their values only. Write `DESIGN.md` from `references/design-md-template.md`. Don't stop to ask: choose where the code is silent and list those choices as assumptions at the end of the summary, so the user can correct them. Ask first only when a wrong guess would be costly to undo.
3. Pick the **profile** per surface (one product can use both). The profile sets density, type size, and how depth is made:
   - **Tool** (admin, dashboard, editor, internal or B2B app): `references/profile-tool.md`.
   - **Marketing/consumer** (landing, pricing, onboarding, storefront, consumer app): `references/profile-marketing.md`.
4. Pick a **style** only when the user names one (as the step 0 argument or in the brief) or the brief describes the look with that style's words below; otherwise the profile alone is the direction. A page or product type (launch, portfolio, docs, developer tool) is not a signal. If step 0 gave `none`, use no style.
   A style is layered on the profile: where the style file states a value or rule, it wins; everything it doesn't mention stays as the profile sets it. The rules for every profile and style (below) hold unless the style file says it overrides one. If the user names a style that doesn't list the surface's profile (premium for a dashboard), apply its palette, type, and radius on top of the profile, keep the profile's space and motion, and say so in the summary:

   | Style | Signals in the brief | Profiles |
   | --- | --- | --- |
   | `references/styles/minimal.md` | minimal, calm, quiet, document-like, Notion/Linear | tool, marketing |
   | `references/styles/premium.md` | premium, luxury, wellness, Apple-like, expensive, soft | marketing |
   | `references/styles/brutalist.md` | brutalist, Swiss, raw, terminal look, blueprint | tool, marketing |
   | `references/styles/cinematic.md` | immersive, cinematic, Awwwards, storytelling, dark tech | marketing |
   | `references/styles/playful.md` | playful, fun, colorful, bubbly, neo-brutalism, Duolingo/Gumroad | marketing, consumer app |

   Read only the chosen style file. Its signature moves are examples of the style's spirit, not a menu: take the surface's distinctive move from this product (its data, workflow, or brand), and use a listed move only when it fits that product better than anything derived from it. If you wrote `DESIGN.md` in step 2, record profile and style there; if it already existed and doesn't match, propose the change (step 1).
5. Tokens before markup, following `references/tokens.md`, `references/typography.md`, `references/radius.md`, and `references/materials.md` (surfaces, hairlines, shadow, glass, scrim, gradient, texture); components reference semantic tokens only. If the surface has cards, panels, or grouped sections, follow `references/cards.md`. If it shows people (avatars, member lists, comments), follow `references/avatars.md`. If there is a dark theme, follow `references/dark-mode.md`.
   If the surface has interactive components or async data (forms, tables, lists, search, filters, overlays, anything that loads), follow the ui-interaction skill (`${CLAUDE_PLUGIN_ROOT}/skills/ui-interaction/SKILL.md`) for their states and behavior. A new screen that renders only the happy path (no loading, empty, or error state) isn't finished.
6. Check contrast in each theme for the pairs you added or changed, in one command. Include muted, placeholder, link, and status text (where failures hide), plus UI boundaries and focus rings: `node ${CLAUDE_SKILL_DIR}/scripts/contrast.mjs "#6b6b66|#ffffff|text" "#0f766e|#ffffff|ui"`. Pairs are `fg|bg|kind`; colors are hex (8-digit for alpha), `rgb()`, `hsl()`, or `oklch()`, passed as written in the CSS; resolve a `var()` to its value first, and pass a `color-mix()` as its result (`materials.md`, Glass). Kind is `text` (4.5:1, default), `large` or `ui` (3:1: large text, UI boundaries, icons, focus rings). It exits 1 if any pair fails, and 2 if a color can't be parsed: that is an input error, not a contrast failure; fix the input and re-run. Fix and re-run once; if pairs still fail, list them with their ratios in the summary. If `node` isn't available, compute the WCAG ratio another way or say in the summary that contrast wasn't machine-checked.
   For a marketing surface, also run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/restyle/scripts/scan_tells.py <page files>`: fix each `6-marketing` hit or explain it in the summary. If `python3` or the script isn't available, skip it and say so.
   Then check the result against the `Checks` list of each reference you loaded and fix what fails.
7. Don't take screenshots or launch browsers unless asked; the user judges the look. One exception: a marketing page that opens now (a static file or a dev server that is already running) gets one run at 1280 and 390 to verify the profile's render checks (hero fits with its CTA, nav on one line, no display type colliding); if it can't be opened, say those checks weren't rendered. When asked to check or test the result, run the ui-check skill on it (`${CLAUDE_PLUGIN_ROOT}/skills/ui-check/SKILL.md`). For a marketing surface, the summary's first line is the design read (see the profile), naming the style if one applies. End with what to look at (narrow viewport, hover and focus, and both themes if there are two).
   Screenshots, for every arc-design skill: `node ${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/screenshot.mjs <url-or-file> out.png --width 1280,390` writes `out-<width>.png` per width (`out-<width>-<scheme>.png` with two schemes) and prints each path. Options: `--full` the whole page; `--root <site-root>` serves a local file from there so root-relative assets (`/style.css`) load; `--scheme light,dark` both themes through `prefers-color-scheme` (a theme set by a class or `data-theme` needs `--eval "document.documentElement.dataset.theme='dark'"` or the matching class instead); `--eval "js"` runs before the shot, to open a step or reveal scroll-in content; `--wait-for <css>` waits for async content; `--hover <css>`/`--focus <css>` show one element's real hover or keyboard-focus state; `--selector <css>` captures one component; `--media reduced-motion,contrast-more,reduced-transparency,forced-colors` emulates preferences. Exit 1: shots written, but a width scrolls sideways (the `overflow` line says by how much). Exit 2: no shot was taken. It needs Node 22+ and Chrome, Chromium, or Edge (`CHROME=/path` picks one); without them, or without a running dev server for a page that needs one, skip it and say so.

## Rules for every profile and style

- One accent per view, spent on the primary action and the current selection. Status colors only for status.
- Don't ship a framework's default palette as the brand unless the project already committed to it. Swapping it for another habitual choice (the same "tasteful" font, accent, or card style on every project) is the same problem; each choice gets a reason tied to this product in `DESIGN.md`. Styles define how values relate, not fixed values: colors and fonts still come from the brand.
- Every value comes from a scale (spacing on a 4px base, type, radius, elevation, duration). Off-scale values need a reason.
- Radius is a role on one scale; nested corners are concentric (inner = outer − padding). See `references/radius.md`.
- Hierarchy comes from size, weight, contrast, and space together. Two weights, 400 and 600, unless the style lists another (`references/typography.md`).
- Responsive layout is a structural decision, not the desktop layout shrunk. For each surface, decide what stacks, what collapses (navigation into a menu, secondary panels into a drawer or disclosure), what scrolls on its own axis (wide tables, tab rows, filter chips), and what stays fixed or reachable (the primary action, the current location). Narrow tables follow `${CLAUDE_PLUGIN_ROOT}/skills/ui-interaction/references/data.md`.
- Under `prefers-reduced-motion: reduce`, override every animation and every transition that moves or scales (including hover `translateY`); color and opacity transitions may stay.
- Light theme by default. Add a dark theme, or follow `prefers-color-scheme`, only when the user asks for it or the project already has one; otherwise the page renders differently from what was reviewed.
- Dark mode is its own token set, not an inversion: near-black layers stepped in lightness, alpha inks and hairlines, a calmer accent. See `references/dark-mode.md`.
