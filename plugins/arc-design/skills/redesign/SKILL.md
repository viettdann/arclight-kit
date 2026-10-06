---
name: redesign
description: "Give an existing product, site, or screen a new visual language while keeping its content, information architecture, URLs, and behavior. Use when the user wants to redesign, revamp, overhaul, modernize, or refresh the look of something that already exists, change its style or direction (\"làm lại giao diện\", \"đổi phong cách\", \"make it feel premium/minimal/brutalist/cinematic/playful\"), or apply a new brand look to current pages. Not for a screen that doesn't exist yet (use design), and not for removing the generated look while keeping the layout (use restyle)."
argument-hint: "[minimal|premium|brutalist|cinematic|playful|none] [target]"
---

# Redesign

A redesign changes how an existing product looks and how its sections are composed. It does not change what the product says, where things live, or how they behave. Most redesign damage comes from that second part: renamed nav labels, broken URLs, dropped analytics hooks, copy rewritten without being asked.

## Is it a redesign?

| The user wants | Use |
| --- | --- |
| Same layout, without the generic generated look | restyle |
| A new visual language; sections may be recomposed; content and structure stay | this skill |
| A new product or page, or brand, content, and structure all change | design (carry over only what the user names) |

If the request could be either restyle or redesign, ask once: "Keep the current layout and clean it up, or a new look with the content kept?"

## Sources

Read the target the user named and the sources the design skill allows (`${CLAUDE_PLUGIN_ROOT}/skills/design/SKILL.md`, Sources). The target's current state in the working tree is the only original: don't read git history, other branches, stashes, other repos or worktrees, or earlier redesign attempts and snapshots, unless the user names the exact source in this conversation. The new composition comes from the brief and the chosen direction, not from another version of the page. This skill's rules replace any other design skill run earlier in the session.

## Workflow

0. If the skill was invoked with arguments and the first word is a style name (`minimal`, `premium`, `brutalist`, `cinematic`, `playful`; the old `editorial-minimal` and `soft-premium` mean `minimal` and `premium`) or `none`, that is the style (`none` means no style); the rest is the target (file, folder, or page). Otherwise a path-like word (a file, folder, or route) is the target and the remaining words are the brief, from which step 3 takes the style.
1. **Snapshot the original** before any edit. Copy the source folder the rebuild may touch, including shared components and layouts (e.g. `src`, not the repo root), to a fresh temp dir; step 7 compares against the printed path:
   ```bash
   s=<src>; d=$(mktemp -d) && cp -R "${s%/}" "$d/" && echo "$d/$(basename "${s%/}")"
   ```
   When the touched code spans several top-level folders (Next.js `app/` and `components/`), copy each into the same temp dir (one `cp -R` per folder) and run step 7's preserve check once per folder pair. Don't use `git stash` or checkout: they change the working tree, which may hold uncommitted work by the user or another agent. If the page renders now (static file or a running dev server), also take before shots with step 7's render command, naming the shot `before.png`, so the user can compare at the same widths.
2. **Audit what exists**, as working notes for the steps below, not a section of the report:
   - Brand to carry over: logo, brand colors, typefaces, photography. A brand that is already violet stays violet unless the user says otherwise.
   - Structure: routes, nav labels and order, section order, the main conversion or task paths.
   - Content: which blocks carry information and which are filler.
   - Keep: elements users recognize, accessibility that already works, and classes that tests or analytics select on (search e2e selectors, `querySelector`, tracking config).
   - Retire: run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/restyle/scripts/scan_tells.py <src>` for generated-look tells, then add broken layouts and dead ends you see in the code.
3. **Set the direction** with the design skill (`${CLAUDE_PLUGIN_ROOT}/skills/design/SKILL.md`, workflow steps 1–5; its relative paths are under `${CLAUDE_PLUGIN_ROOT}/skills/design/`): `DESIGN.md`, profile per surface, the style from step 0 or one the brief clearly implies, tokens before markup. Use the brand values from the audit as fixed inputs to the tokens. An existing `DESIGN.md` is expected to change: update it with the new direction (instead of proposing, as design step 1 says) and list the change in the report. A later design run follows this `DESIGN.md` only where its own brief is silent. Settle the design read (marketing surfaces) before editing. When the user asks for options or directions, run the design skill's Variants section first, keeping the audited content and structure.
4. **Rebuild in order of value per risk**: tokens (type, color, spacing, radius) → shared components → section composition → a new block only where the old one can't carry its content. Start with the highest-traffic surface (home or hero, or the main app shell) and continue through the requested scope; pause only for an item from step 5.
5. **Never change silently** (ask first): URLs, route slugs, and anchor ids; nav labels and order; form field `name`s and order; ids, classes, and `data-*` attributes analytics or tests may use; logo and wordmark; legal, consent, and pricing copy; page titles and meta descriptions. Copy stays unless a rewrite was asked for: fix only what is broken (typos, filler the audit flagged) and list each change.
6. **Behavior stays:** event handlers, data fetching, props, validation. When a recomposed section needs new states (a new tab control, a new form layout), follow the ui-interaction skill (`${CLAUDE_PLUGIN_ROOT}/skills/ui-interaction/SKILL.md`).
7. **Verify:**
   - `python3 ${CLAUDE_SKILL_DIR}/scripts/preserve_check.py <snapshot> <src>` (`<snapshot>` is the path printed in step 1) lists hrefs, ids, form names and actions, `data-*` attributes, titles, and meta descriptions that disappeared. Titles and descriptions are read from `<title>`/`<meta>` tags and from string literals in `metadata`, `generateMetadata`, `useHead`, `useSeoMeta`, and `definePageMeta`; a computed value (template string, function call) needs a hand check. SVG internals, icon names, and stylesheet, font, and icon `<link>`s are skipped as presentation. Every missing item is either restored or reported as an intentional change.
   - The check doesn't cover classes. Confirm each class the audit listed under Keep still exists in the markup.
   - Re-run the scanner: remaining hits are intentional. Its `7-code` hits are tagged: fix `presentation` hits; list `behavior` hits in the report and fix them only if asked (then follow the ui-interaction skill).
   - Check contrast for every pair you introduced: `node ${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/contrast.mjs "fg|bg|kind" ...` (color formats and exit codes in the design skill, step 6).
   - Render and measure the page in one run, at desktop and phone width:
     ```bash
     d=$(mktemp -d) && node ${CLAUDE_PLUGIN_ROOT}/skills/ui-check/scripts/ui_check.mjs <url-or-file> --width 1280,390 --shot "$d/after.png"
     ```
     It writes `after-1280.png` and `after-390.png` and lists rendering findings (options in the ui-check skill, step 2: `--scheme light,dark` with two themes, `--eval` for a later step such as a checkout state, `--wait-for`, `--root`, `--full`); for an app, use the dev server that is already running. In the shots, check for large empty areas, sections detached from what they describe, and a primary action that isn't visible without scrolling on the phone. Then the first-impression check: in the widest shot, name the first three things the eye lands on; the first is the screen's main conversion or task from the audit, or hierarchy needs another pass. Each area's purpose must be nameable at a glance; an area you can't name in a few words needs a heading, a label, or regrouping. Fix every P1 and P2 finding on the rebuilt surfaces, confirming each `[review]` finding in its shot first and dropping it when the layout intends it (ui-check step 3); list the rest in the report. Exit 2 means it couldn't run (no Node 22+, no Chrome, Chromium, or Edge, or no running dev server for a page that needs one): say so. For a recomposed control's hover or focus state, use the screenshot script (options: design skill, step 7).
   - When the user asks for a score or a quality bar ("get it to 8/10"), or to choose between variants, have the shots judged by a blind critic: `references/critic.md`.
8. **Remove the snapshot** once every check above has run: `rm -rf "$(dirname <snapshot>)"` with the path printed in step 1. Its path is never a source for later work in the session.
9. **Report** in a few lines, only what the page doesn't show: the direction in one line (profile, style, design read), each intentional change to something step 5 protects and to `DESIGN.md`, items from the preserve check, behavior hits and proof flagged instead of changed, placeholders left, and checks that couldn't run. No audit summary or per-surface change list; the page shows those.

## Don't

- Don't migrate frameworks, styling systems, or component libraries as part of a redesign unless asked.
- Don't invent proof (customer counts, ratings, logos, testimonials) to fill a recomposed section; leave a labeled placeholder and list it.
- Don't redesign surfaces outside the requested scope without saying so.
