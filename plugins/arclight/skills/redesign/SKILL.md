---
name: redesign
description: "Give an existing product, site, or screen a new visual language while keeping its content, information architecture, URLs, and behavior. Use when the user wants to redesign, revamp, overhaul, modernize, or refresh the look of something that already exists, change its style or direction (\"làm lại giao diện\", \"đổi phong cách\", \"make it feel premium/editorial/brutalist\"), or apply a new brand look to current pages. Not for a screen that doesn't exist yet (use design), and not for removing the generated look while keeping the layout (use restyle)."
argument-hint: "[editorial-minimal | soft-premium | brutalist | none] [file, folder, or page]"
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

## Workflow

0. If the skill was invoked with arguments and the first word is a style name (`editorial-minimal`, `soft-premium`, `brutalist`) or `none`, that is the style (`none` means no style); the rest is the target. Otherwise the style comes from the brief in step 3.
1. **Snapshot the original** before any edit. Copy the source folder the rebuild may touch, including shared components and layouts (e.g. `src`, not the repo root), to a fresh temp dir and note the printed path; step 7 compares against it:
   ```bash
   d=$(mktemp -d) && cp -R <src> "$d" && echo "$d"
   ```
   Don't use `git stash` or checkout: they change the working tree, which may hold uncommitted work by the user or another agent.
2. **Audit what exists** (short, in the user's language):
   - Brand to carry over: logo, brand colors, typefaces, photography. A brand that is already violet stays violet unless the user says otherwise.
   - Structure: routes, nav labels and order, section order, the main conversion or task paths.
   - Content: which blocks carry information and which are filler.
   - Keep: elements users recognize, accessibility that already works, and classes that tests or analytics select on (search e2e selectors, `querySelector`, tracking config).
   - Retire: run `python3 ${CLAUDE_SKILL_DIR}/../restyle/scripts/scan_tells.py <src>` for generated-look tells, then add broken layouts and dead ends you see in the code.
3. **Set the direction** with the design skill (`${CLAUDE_SKILL_DIR}/../design/SKILL.md`, workflow steps 1–5): `DESIGN.md`, profile per surface, the style from step 0 or one the brief clearly implies, tokens before markup. Use the brand values from the audit as fixed inputs to the tokens. An existing `DESIGN.md` is expected to change: update it with the new direction and list the change in the report. State the design read and a short "changes / stays" list before editing.
4. **Rebuild in order of value per risk**: tokens (type, color, spacing, radius) → shared components → section composition → a new block only where the old one can't carry its content. Start with the highest-traffic surface (home or hero, or the main app shell) and continue through the requested scope; pause only for an item from step 5.
5. **Never change silently** (ask first): URLs, route slugs, and anchor ids; nav labels and order; form field `name`s and order; ids, classes, and `data-*` attributes analytics or tests may use; logo and wordmark; legal, consent, and pricing copy; page titles and meta descriptions. Copy stays unless a rewrite was asked for: fix only what is broken (typos, filler the audit flagged) and list each change.
6. **Behavior stays:** event handlers, data fetching, props, validation. When a recomposed section needs new states (a new tab control, a new form layout), follow the ui-interaction skill (`${CLAUDE_SKILL_DIR}/../ui-interaction/SKILL.md`).
7. **Verify:**
   - `python3 ${CLAUDE_SKILL_DIR}/scripts/preserve_check.py <snapshot-dir>/<src-name> <src>` (`<snapshot-dir>` is the path printed in step 1) lists hrefs, ids, form names, `data-*` attributes, titles, and meta descriptions that disappeared. Every missing item is either restored or reported as an intentional change.
   - The check doesn't cover classes. Confirm each class the audit listed under Keep still exists in the markup.
   - Re-run the scanner: remaining hits are intentional.
   - Check contrast for every pair you introduced: `node ${CLAUDE_SKILL_DIR}/../design/scripts/contrast.mjs "fg|bg|kind" ...` (usage in the design skill, step 6).
8. **Report:** audit summary, direction (profile, style, design read), what changed per surface, the preserve-check result, and anything flagged instead of changed.

## Don't

- Don't migrate frameworks, styling systems, or component libraries as part of a redesign unless asked.
- Don't invent proof (customer counts, ratings, logos, testimonials) to fill a recomposed section; leave a labeled placeholder and list it.
- Don't redesign surfaces outside the requested scope without saying so.
