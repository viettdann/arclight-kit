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

1. **Audit what exists** (short, in the user's language):
   - Brand to carry over: logo, brand colors, typefaces, photography. A brand that is already violet stays violet unless the user says otherwise.
   - Structure: routes, nav labels and order, section order, the main conversion or task paths.
   - Content: which blocks carry information and which are filler.
   - Keep: elements users recognize, accessibility that already works.
   - Retire: run `python3 <skill-dir>/../restyle/scripts/scan_tells.py <src>` for generated-look tells, then add broken layouts and dead ends you see in the code.
2. **Set the direction** with the design skill (`<skill-dir>/../design/SKILL.md`, workflow steps 1–5): `DESIGN.md`, profile per surface, a style if the user named one or the brief clearly implies it, tokens before markup. Existing brand values are inputs to the tokens, not something to discard. If the skill was invoked with arguments and the first word is a style name or `none`, use it; the rest is the target. State the design read and a short "changes / stays" list before editing.
3. **Rebuild in order of value per risk**, stopping once the brief is met: tokens (type, color, spacing, radius) → shared components → section composition → a new block only where the old one can't carry its content. Start with the highest-traffic surface (home or hero, or the main app shell).
4. **Never change silently** (ask first): URLs, route slugs, and anchor ids; nav labels and order; form field `name`s and order; ids, classes, and `data-*` attributes analytics or tests may use; logo and wordmark; legal, consent, and pricing copy; page titles and meta descriptions. Copy stays unless a rewrite was asked for: fix only what is broken (typos, filler the audit flagged) and list each change.
5. **Behavior stays:** event handlers, data fetching, props, validation. When a recomposed section needs new states (a new tab control, a new form layout), follow ui-interaction.
6. **Verify:**
   - `python3 <skill-dir>/scripts/preserve_check.py <old> <new>` lists hrefs, ids, form names, `data-*` attributes, titles, and meta descriptions that disappeared. Every missing item is either restored or reported as an intentional change. Keep a copy of the original (or use `git stash`/`git show HEAD:<file>`) to compare against.
   - Re-run the scanner: remaining hits are intentional.
   - Check contrast with the design skill's script for every pair you introduced.
7. **Report:** audit summary, direction (profile, style, design read), what changed per surface, the preserve-check result, and anything flagged instead of changed.

## Don't

- Don't migrate frameworks, styling systems, or component libraries as part of a redesign unless asked.
- Don't invent proof (customer counts, ratings, logos, testimonials) to fill a recomposed section; leave a labeled placeholder and list it.
- Don't redesign surfaces outside the requested scope without saying so.
