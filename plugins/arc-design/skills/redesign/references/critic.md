# Blind critic

An optional second opinion on the rendered result, from an agent that didn't build it. Use it only when the user asks for a score or a quality bar ("get it to 8/10", "is this good enough"), or asks to pick between variants. The builder grading its own work reads its intent into the page; a critic that sees only pixels judges what a visitor sees.

## Setup

- Evidence is screenshots only, at the widths and themes the skill's verify step rendered. No code, no diff, no `DESIGN.md`, no brief beyond one line on what the surface is for and who uses it. The builder's rationale ("the accent is muted on purpose") never goes to the critic.
- Name shots by surface and width (`pricing-1280.png`), never by round or version (`round-3`, `v2-final`): an ordinal tells the critic which one you expect to be better.
- Spawn a fresh sub-agent for every round, with the identical rubric and prompt, so no critic knows which version came first. Fresh critics drift by a point or two on the same page, so a change smaller than two points between rounds isn't a signal; for a decision that hinges on the score, run two critics and take the lower.

## Rubric

Five criteria per surface, each scored 0, 1, or 2, for a total out of 10:

| Criterion | 2 | 1 | 0 |
| --- | --- | --- | --- |
| Hierarchy | the first thing the eye lands on is the surface's main task | the main task is in the first three | the eye lands on decoration or competes between equals |
| Grouping and rhythm | every area's purpose is nameable at a glance, spacing separates groups | one area unclear or spacing inconsistent | areas blur together |
| Type | one scale, two weights, comfortable measure, no orphaned last words in headings | one slip | sizes or weights look picked per element |
| Color and material | one accent spent on action and selection, depth only where the profile and style put it (`${CLAUDE_PLUGIN_ROOT}/skills/design/references/materials.md`) | one competing color or stray shadow | color or depth says nothing |
| Narrow width | the phone shot is composed, not the desktop shrunk, main action reachable | usable with a visible compromise | broken, cramped, or main action lost |

Swap a row for a criterion the brief cares about more (data density for a dashboard, imagery for a storefront), keeping five.

Anchors for the total: 10 is something you'd study, 8 is polished with nits, 7 has one noticeable flaw, 6 shows rough edges, 5 or below distracts or is broken.

## Prompt

```text
You are judging screenshots of <surface>, a <profile> surface for <who, one line>. You did not build it. Judge only what the images show.
Open every file before scoring: <paths>.
Score each criterion 0, 1, or 2 using this rubric: <rubric table>.
Return per surface: the score per criterion and the total; the single fault costing the most points, the element it's on, and the fix; anything the images can't show you.
Never round up. Don't credit what the images don't show. Five lines per surface at most.
```

## Using the scores

- A target ("get it to 8") applies to every surface, not the average.
- Before acting on a fault, find it in the full-resolution shot yourself; a critic misreads small details at a glance, and a fault you can't see isn't one.
- For two critics on the same evidence, the lower score stands.
- A fault whose fix can't be stated as one change is reported, not chased.
- Never change the rubric or the target mid-loop to reach the goal. After two rounds without progress on a surface, change the approach rather than nudging values.
- Report the final scores per surface and any fault you chose not to fix, with the reason.
