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

0. If the skill was invoked with arguments and the first word is a style name (`minimal`, `premium`, `brutalist`, `cinematic`, `playful`; the old `editorial-minimal` and `soft-premium` mean `minimal` and `premium`) or `none`, that is the style (`none` means no style); the rest is the target (file, folder, or page). Otherwise the style comes from the brief in step 3.
1. **Snapshot the original** before any edit. Copy the source folder the rebuild may touch, including shared components and layouts (e.g. `src`, not the repo root), to a fresh temp dir; step 7 compares against the printed path:
   ```bash
   s=<src>; d=$(mktemp -d) && cp -R "${s%/}" "$d/" && echo "$d/$(basename "${s%/}")"
   ```
   Don't use `git stash` or checkout: they change the working tree, which may hold uncommitted work by the user or another agent. If the page renders now (static file or a running dev server), also take before shots with the screenshot command step 7 uses and `before` in the file name, so the user can compare at the same widths.
2. **Audit what exists**, as working notes for the steps below, not a section of the report:
   - Brand to carry over: logo, brand colors, typefaces, photography. A brand that is already violet stays violet unless the user says otherwise.
   - Structure: routes, nav labels and order, section order, the main conversion or task paths.
   - Content: which blocks carry information and which are filler.
   - Keep: elements users recognize, accessibility that already works, and classes that tests or analytics select on (search e2e selectors, `querySelector`, tracking config).
   - Retire: run `python3 ${CLAUDE_PLUGIN_ROOT}/skills/restyle/scripts/scan_tells.py <src>` for generated-look tells, then add broken layouts and dead ends you see in the code.
3. **Set the direction** with the design skill (`${CLAUDE_PLUGIN_ROOT}/skills/design/SKILL.md`, workflow steps 1–5; its relative paths are under `${CLAUDE_PLUGIN_ROOT}/skills/design/`): `DESIGN.md`, profile per surface, the style from step 0 or one the brief clearly implies, tokens before markup. Use the brand values from the audit as fixed inputs to the tokens. An existing `DESIGN.md` is expected to change: update it with the new direction (instead of proposing, as design step 1 says) and list the change in the report. A later design run follows this `DESIGN.md` only where its own brief is silent. Settle the design read (marketing surfaces) before editing.
4. **Rebuild in order of value per risk**: tokens (type, color, spacing, radius) → shared components → section composition → a new block only where the old one can't carry its content. Start with the highest-traffic surface (home or hero, or the main app shell) and continue through the requested scope; pause only for an item from step 5.
5. **Never change silently** (ask first): URLs, route slugs, and anchor ids; nav labels and order; form field `name`s and order; ids, classes, and `data-*` attributes analytics or tests may use; logo and wordmark; legal, consent, and pricing copy; page titles and meta descriptions. Copy stays unless a rewrite was asked for: fix only what is broken (typos, filler the audit flagged) and list each change.
6. **Behavior stays:** event handlers, data fetching, props, validation. When a recomposed section needs new states (a new tab control, a new form layout), follow the ui-interaction skill (`${CLAUDE_PLUGIN_ROOT}/skills/ui-interaction/SKILL.md`).
7. **Verify:**
   - `python3 ${CLAUDE_SKILL_DIR}/scripts/preserve_check.py <snapshot> <src>` (`<snapshot>` is the path printed in step 1) lists hrefs, ids, form names and actions, `data-*` attributes, and titles and meta descriptions written as HTML tags that disappeared (framework metadata APIs such as Next.js `metadata` aren't parsed; compare those by hand). Every missing item is either restored or reported as an intentional change.
   - The check doesn't cover classes. Confirm each class the audit listed under Keep still exists in the markup.
   - Re-run the scanner: remaining hits are intentional, or `7-code` behavior items (disabled, clipboard, keyboard, scroll, drag handlers) listed in the report; fix those only if asked.
   - Check contrast for every pair you introduced: `node ${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/contrast.mjs "fg|bg|kind" ...` (usage in the design skill, step 6). Colors go in as written in the CSS: hex, 8-digit hex, `rgb()`, or `oklch()`, so don't convert them first.
   - Look at the rendered page at desktop and phone width: `node ${CLAUDE_PLUGIN_ROOT}/skills/design/scripts/screenshot.mjs <url-or-file> out.png --width 1280,390` writes `out-1280.png` and `out-390.png` and prints each path; exit 1 means the shots are written but a width scrolls sideways (the `overflow` line says by how much), exit 2 means no shot was taken. Add `--root <site-root>` for a local page below the site root that uses root-relative assets, `--full` for the whole page, `--eval "js"` to show a hidden step such as a later checkout state, `--scheme light,dark` when there are two themes, `--hover`/`--focus <css>` for a recomposed control's states, `--wait-for <css>` for async content (all options: restyle skill, step 4); for an app, use the dev server that is already running. Check for large empty areas, sections detached from what they describe, and a primary action that isn't visible without scrolling on the phone. Then run `node ${CLAUDE_PLUGIN_ROOT}/skills/ui-check/scripts/ui_check.mjs <url-or-file>` (`--scheme light,dark` with two themes; usage in the ui-check skill): every P1 and P2 finding on the rebuilt surfaces is fixed, and the rest are listed in the report. Without Node 22+ and Chrome, Chromium, or Edge, or without a running dev server for a page that needs one, skip this and say so.
8. **Remove the snapshot** once every check above has run: `rm -rf "$(dirname <snapshot>)"` with the path printed in step 1. Its path is never a source for later work in the session.
9. **Report** in a few lines, only what the page doesn't show: the direction in one line (profile, style, design read), each intentional change to something step 5 protects and to `DESIGN.md`, items from the preserve check, behavior hits and proof flagged instead of changed, placeholders left, and checks that couldn't run. No audit summary or per-surface change list; the page shows those.

## Don't

- Don't migrate frameworks, styling systems, or component libraries as part of a redesign unless asked.
- Don't invent proof (customer counts, ratings, logos, testimonials) to fill a recomposed section; leave a labeled placeholder and list it.
- Don't redesign surfaces outside the requested scope without saying so.
