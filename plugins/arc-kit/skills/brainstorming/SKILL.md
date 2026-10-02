---
name: brainstorming
description: "Use this skill before implementing non-trivial features, designing components, or making architectural decisions. Explores user intent, requirements, and design through collaborative dialogue before any implementation begins. Trigger on phrases like 'I want to build', 'how should I design', 'let's design', 'brainstorm', 'plan this out', 'tôi muốn làm', 'thiết kế', 'lên kế hoạch', 'nên làm thế nào', or when the user describes a multi-step feature or system they want to create. Do not trigger for small, self-contained tasks like adding a single helper function."
---

# Brainstorming Ideas Into Designs

## Overview

Help turn ideas into fully formed designs and specs through natural collaborative dialogue.

Start from a high-level description of what the user wants to build and the current project context, then ask questions to refine the idea. Once you understand what you're building, present the design.

## The Process

### Understanding the Idea

- **Grasp the idea first.** Ask the user for a high-level description of what they want to build (1-2 sentences is enough to proceed)
- **Targeted codebase discovery:** informed by the user's stated intent:
  - If the project is empty or the user explicitly states it's a greenfield/new project, skip codebase discovery entirely and note this assumption
  - Otherwise, search and read the local codebase
  - Summarize findings before proceeding: enough for the user to check your reading of the codebase, and no more
- **Self-verify before asking.** Before formulating any question for the user, apply this gate:
  - **Answerable from the codebase?** (installed deps, patterns in use, available APIs) → Resolve it yourself and state it as a resolved constraint, not a question
  - **Answerable from an external dependency?** (see Research) → Resolve it yourself the same way
  - **A preference, trade-off, scope, or judgment call only the user can decide?** ("Approach A or B?", "Async or sync?", "Is this in scope?") → Ask the user
- **Use AskUserQuestion tool** for preference/judgment questions only:
  - Group related choices into one question (e.g., all storage choices together); independent decisions go in separate questions of the same call (up to 4 per call)
  - Each question states your recommended option and why
  - Prefer multiple-choice options when possible; open-ended when the answer space is genuinely open
- Focus on: purpose, constraints, success criteria
- For performance work, record the current measurement and a target number before designing; "faster" is not a success criterion

### Verification Discipline

Codebase claims must be anchored to something the reader can locate. Name the file plus a stable handle inside it: a function, exported symbol, or short quoted identifier. Line numbers shift on every commit, so pick a handle that survives edits.

- **Anchor every load-bearing claim.** Anything the design relies on, anything driving a yes/no decision, anything reused as a constraint later in the document. Illustrative anchor: `createLogger() in server/src/lib/logger.ts`, or `` `import { logger } from './lib/logger'` at top of server/src/main.ts ``. Passing context that does not bear weight can stay unanchored
- **Split discovery output into Verified and Assumed.** Verified items carry an anchor. Assumed items carry the reason they were not checked (deferred for cost, outside current tooling, anything else). A design step may rely on an Assumed item only when the user confirms it or it is listed in the plan's assumptions to validate
- **Treat earlier claims as drafts, not facts.** A claim made earlier in the same conversation is not ground truth. When a later step depends on it, re-verify before relying on it
- **Retract before defending.** When the user asks to verify a claim, re-run discovery from scratch instead of restating the prior claim. If the original was wrong, name the error, state the corrected anchor, and list every design decision that inherited the error so they can be revisited together

See `examples/verify-callout.md` for the recovery flow when a claim turns out to be wrong.

### Handling Disagreement or Stalled Dialogue

- **User contradicts an earlier answer.** Name the contradiction explicitly, list which prior decisions it invalidates, ask which version is correct. Do not silently absorb the new answer. See `examples/user-pivots.md`
- **User stays unclear across 3+ turns on the same decision, or keeps giving non-answers ("whatever", "you decide").** Pick the safest reasonable default, state it as a decision (not a question), and move on. If no safe default exists, narrow scope to what's already clear or defer the decision and proceed with the rest
- **User wants to skip the design phase.** State your default assumptions in one message, let the user veto any item, then proceed to the plan. The approval gate still applies. See `examples/skip-design.md`

### Exploring Approaches

- Propose 2-3 different approaches with trade-offs
- Lead with your recommended option and explain why
- **Always present the proper solution.** If a workaround or shortcut exists, present it alongside the proper solution with clear trade-offs (effort, tech debt created, future cost). Never present only the workaround
- **When to ask vs. when to just do it:** If the proper fix is small or obvious, just pick it and move on. Only use AskUserQuestion when the effort difference between proper fix and workaround is significant (e.g., hours vs. minutes, or requires touching many unrelated files) or the trade-off is genuinely ambiguous

### Research (when needed)

Research covers external dependencies only: whether a library exists, its API surface, its runtime behavior. Check the installed package source and types first, then the official docs.

### Presenting the Design

- Present the entire design in one message, organized with headings, and ask for confirmation once at the end, never per section
- Cover: architecture, components, data flow, error handling, testing considerations
- Go back and clarify if something doesn't land correctly

### Implementation Plan

- After the user confirms the design, present a concrete implementation plan:
  - List every file the plan touches. Do not summarize multiple files into one line
  - Each line: file path + what changes + the check that proves it (test name, command, or observable state). Add why only when it is not obvious from the change, in a few words
  - Highlight assumptions that need validation
- **Stop here. Do not proceed until the user explicitly approves the plan.**
  Approval is an unambiguous instruction to start building, in whatever language the user writes it (`proceed`, `go ahead`, `implement it`, `tiến hành`, `làm đi`). Judge it by intent, not by matching those words.
  Praise for the design is not approval, and neither is a reply that stays ambiguous or ends in a question (`looks good`, `sounds good`, `ok`). When it is unclear, ask once whether to start implementing.
- **Scope Creep Rule:** If the user adds a new constraint or feature at this approval stage, revise the design and plan in chat, show the delta, and ask for approval again. The design doc is written only after approval

### Design Doc Wording

The saved design doc describes the target state only. When a draft element is dropped, omit it; the doc never records history or removals ("Removed X", "There is no X"). Deltas and removal notes belong in chat (Scope Creep Rule, YAGNI flags), not in the doc.
- *Incorrect:* "There is no header subtitle. Removed the subtitle text."
- *Correct:* "The header contains a primary title."

## After the Design

- Once the user approves the plan, write the design to `${CLAUDE_PROJECT_DIR}/docs/plans/YYYY-MM-DD-<topic>-design.md` (`docs/plans/` below means this directory; take the date from `date +%F`)
  - **Topic slug must match `^[a-z0-9-]{1,60}$`**
  - Derive the slug by lowercasing, replacing spaces/underscores with hyphens, and stripping invalid characters. Example: `Input: My Feature/Design v2 → Output: my-feature-design-v2`
  - Truncate the slug to 60 characters after normalization. Fall back to `untitled` if empty
  - Never interpolate the raw topic into a shell command; only pass the validated slug to the `Write` tool as part of the fixed `docs/plans/` path
  - **If `docs/plans/` does not exist**, create it (`mkdir -p docs/plans`) and note its creation in your reply. If the current working directory is not a writable project root (e.g., outside a repo, or user is in a path like `/tmp`), ask the user where to save the design instead of silently creating directories
- The doc must stand alone after `/clear`: include the approved Implementation Plan (every file + what changes + its check, and the assumptions to validate) as its own section, since the next session only has the doc
- Include a **Verification Criteria** section in the design doc:
  - What tests to write/run to validate the implementation
  - What constitutes "done"
  - Known edge cases to verify
- Include an **Out of scope** section: what the user explicitly excluded, one line each, written as a boundary ("Leaves the billing module untouched"), never as removal history
- Suggest to the user: "Run `/arc-kit:plan-auditor docs/plans/<filename>` to stress-test before execution."

## Key Principles

- **YAGNI ruthlessly.** Before finalizing any design section, flag a feature for removal if ALL of the following are true:
  1. The user has not mentioned it in the original prompt or any clarifying answer
  2. It does not appear in the stated goals, constraints, or success criteria
  3. It is not a direct consequence of an explicitly required feature (e.g., auth → session storage is a direct consequence)

  When flagging, state the feature + the reason, and let the user reinstate it. Example: "Removed: admin dashboard. Not in stated goals. Reinstate?"

## Additional Resources

The examples run on a fictional Hono/Bun rate-limiter scenario. Their paths, symbols, and findings do not describe this repository - discover the real codebase fresh. What they pin down is the shape of the exchange: what gets resolved without asking, what gets asked, and when the design lands.

- `examples/happy-path.md`: full workflow when user engages cooperatively
- `examples/user-pivots.md`: handling contradictions and rollback mid-design
- `examples/skip-design.md`: handling "just do it" requests without losing alignment
- `examples/verify-callout.md`: recovering when a codebase claim turns out to be wrong
