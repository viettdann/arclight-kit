---
name: brainstorming
description: "Design before code: turn an idea into a design and implementation plan from verified project context, asking in rounds only the judgment calls the codebase can't answer, and save docs/plans/<date>-<topic>-design.md for substantial work. Use before a non-trivial feature, component, or architectural change (I want to build, how should I design, brainstorm, tôi muốn làm, thiết kế, lên kế hoạch). Continues into implementation when already authorized. Not for a small self-contained change."
---

# Brainstorming Ideas Into Designs

Before discovery or questions, read `references/discovery.md` for the discovery, verification, and dialogue rules. Existing implementation authorization persists through design.

## Overview

Help turn ideas into fully formed designs and specs through natural collaborative dialogue.

Start from the user's stated intent and project context. Resolve facts independently, ask only about consequential unknowns until Understanding is done, and present the design with its execution steps.

## The Process

### Understanding the Idea

Follow `references/discovery.md` to discover project facts, ask only consequential unresolved decisions in dependency order, verify claims, and handle changed answers or delegated choices. Finish when the goal, success criterion, decisions, and assumptions are clear.

### Exploring Approaches

- When more than one approach fits and the trade-off needs the user's judgment, propose 2-3 with their trade-offs, leading with your recommendation and why. When one approach is clearly right, state it and the reason in one line; don't invent weaker options to compare against
- **Proper fix first.** Never present only a workaround. Take the proper fix without asking when it is small or obvious. Ask only when it costs far more than the workaround (a large refactor, or changes outside the plan's files) or the trade-off is genuinely ambiguous, and then show both: `Proper fix: X (effort). Workaround: Y (debt it creates).`

### Research (when needed)

Research covers external dependencies only: whether a library exists, its API surface, its runtime behavior. Check the installed package source and types first, then the official docs. Choosing between libraries or services, or checking current versions, support dates, or prices, goes through the installed `arc-kit:research` skill when available (explicit invocation: `$research`).

### Presenting the Design

- Present the design together with a concrete implementation plan. Ask for a decision only if one is still needed; do not create repeated confirmation gates for work the user already requested.
- Cover: the goal and its success criterion, architecture, components, data flow, error handling, testing considerations
- Go back and clarify if something doesn't land correctly

### Implementation Plan

- List each affected file or clearly bounded file group, its change, and a check that proves it (test, command, or observable state). Expand exact paths as discovery resolves them.
- Highlight unverified assumptions that could change the design and validate them before dependent edits.
- For a design-only request, finish with the design and plan; implementation needs a request to execute.
- When the user has already asked to implement, migrate, or fix the feature, continue after stating the approach. A preference answer or correction refines that authorization; it does not require another go-ahead.
- A go-ahead covers the requested task or accepted plan, not unrelated suggestions from earlier discussion.
- If the user introduces new constraints, revise affected parts and proceed within the revised authorized scope. Ask only about unresolved scope or consequential choices.

### Design Doc Wording

The saved design doc describes the target state only. When a draft element is dropped, omit it; the doc never records history or removals ("Removed X", "There is no X"). Deltas and removal notes belong in chat, not in the doc.
- *Incorrect:* "There is no header subtitle. Removed the subtitle text."
- *Correct:* "The header contains a primary title."

## After the Design

For substantial work needing a durable plan, write `docs/plans/YYYY-MM-DD-<topic>-design.md` beneath the verified project root. Find the root from the workspace context and git when available; do not assume a platform environment variable. Use the local date. Resolve examples relative to this loaded skill directory.

Normalize the topic to lowercase kebab case matching `^[a-z0-9-]{1,60}$`, falling back to `untitled`. Use safe file APIs or properly quoted arguments, never raw user text in a shell command. Create `docs/plans/` when the project root is known and writable; otherwise ask for the destination. Never overwrite an unrelated existing plan.

Keep the saved document self-contained for a fresh session, since the next session only has the doc. Use these sections, in this order:

```markdown
# <Topic>
## Goal                 what it achieves and how success is measured (a target number for performance work)
## Design               architecture, components, data flow, error handling
## Implementation Plan  one line per file: path + what changes + the check that proves it
## Assumptions          what the plan relies on that is not verified yet, and how to verify each
## Verification         tests to write or run, what counts as done, edge cases to check
## Out of scope         what the user excluded, one line each, as a boundary ("Leaves the billing module untouched")
```

Omit `Assumptions` or `Out of scope` when empty; the other four are always present. Use English on disk and Vietnamese in chat unless the user requests otherwise. Follow applicable AGENTS.md instructions.

For a substantial or uncertain design, use the installed `arc-kit:plan-auditor` skill if available (explicit invocation: `$plan-auditor docs/plans/<filename>`). If it is unavailable, verify the plan's references and assumptions directly. An audit recommendation is not an extra permission gate before authorized implementation.

## Key Principles

- **YAGNI ruthlessly.** Before finalizing any design section, flag a feature for removal if ALL of the following are true:
  1. The user has not mentioned it in the original prompt or any clarifying answer
  2. It does not appear in the stated goals, constraints, or success criteria
  3. It is not a direct consequence of an explicitly required feature (e.g., auth → session storage is a direct consequence)

  Leave unsolicited features outside the plan. Mention a consequential scope boundary briefly; ask only when it is ambiguous whether the user requested the feature.

## Additional Resources

Use the example index in `references/discovery.md` only when the matching situation arises.

## Fresh-context review

After saving the design, when delegation is allowed, use one subagent with no conversation context: give only the doc path and repo root. Ask about contradictions, missing scope, implementability, and simpler approaches. Fix factual issues and surface unresolved judgment calls. Run at most two rounds, stopping on repeated findings. Otherwise check these inline and report the lack of fresh-context review. This adds no approval gate before authorized implementation.
