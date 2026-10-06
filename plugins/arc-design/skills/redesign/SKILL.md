---
name: redesign
description: "Give an existing product, site, or screen a new visual language while keeping its content, information architecture, URLs, and behavior. Use when the user wants to redesign, revamp, overhaul, modernize, or refresh the look of something that already exists, change its style or direction (\"làm lại giao diện\", \"đổi phong cách\", \"make it feel premium/minimal/brutalist/cinematic/playful\"), or apply a new brand look to current pages. Not for a screen that doesn't exist yet (use design), and not for removing the generated look while keeping the layout (use restyle)."
---

# Redesign

Before editing, read `references/workflow.md`, including its protected-content rules, snapshot procedure, and preservation checks. Preserve content, URLs, and behavior within the authorized scope.

Resolve reference and script paths relative to this `SKILL.md`. Before running a helper from the project directory, replace its relative path with the absolute installed path; keep the project working directory so target paths resolve correctly. Read applicable `AGENTS.md` instructions first. Use the session’s available shell, file-editing, and image-viewing tools; load only the references needed for the task.

A redesign changes how an existing product looks and how its sections are composed. It does not change what the product says, where things live, or how they behave. Most redesign damage comes from that second part: renamed nav labels, broken URLs, dropped analytics hooks, copy rewritten without being asked.

## Is it a redesign?

| The user wants | Use |
| --- | --- |
| Same layout, without the generic generated look | restyle |
| A new visual language; sections may be recomposed; content and structure stay | this skill |
| A new product or page, or brand, content, and structure all change | design (carry over only what the user names) |

If the request could be either restyle or redesign, ask once: "Keep the current layout and clean it up, or a new look with the content kept?"

## Sources

Read the target the user named and the sources the design skill allows (`../design/SKILL.md`, Sources). The target's current state in the working tree is the only original: don't read git history, other branches, stashes, other repos or worktrees, or earlier redesign attempts and snapshots, unless the user names the exact source in this conversation. The new composition comes from the brief and the chosen direction, not from another version of the page. Use this workflow for the current task, alongside applicable project instructions and the user’s constraints.

## Workflow

Follow steps 0–9 in `references/workflow.md`: parse the style and target, snapshot the current sources, audit the brand and structure, set the direction, rebuild, preserve behavior and protected content, verify, remove the snapshot, and report.

## Don't

- Don't migrate frameworks, styling systems, or component libraries as part of a redesign unless asked.
- Don't invent proof (customer counts, ratings, logos, testimonials) to fill a recomposed section; leave a labeled placeholder and list it.
- Don't redesign surfaces outside the requested scope without saying so.
