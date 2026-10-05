---
name: brainstorming
description: "Design before code: turn an idea into a design and implementation plan from verified project context, asking in rounds only the judgment calls the codebase can't answer, and save docs/plans/<date>-<topic>-design.md for substantial work. Use before a non-trivial feature, component, or architectural change (I want to build, how should I design, brainstorm, tôi muốn làm, thiết kế, lên kế hoạch). Continues into implementation when already authorized. Not for a small self-contained change."
---

# Brainstorming Ideas Into Designs

## Overview

Help turn ideas into fully formed designs and specs through natural collaborative dialogue.

Start from the user's stated intent and project context. Resolve facts independently, ask only about consequential unknowns until Understanding is done, and present the design with its execution steps.

## The Process

### Understanding the Idea

- **Use the intent already provided.** Infer the goal from the request and current conversation. Ask for a high-level description only if the goal is missing.
- **Targeted codebase discovery:** informed by the user's stated intent:
  - If the project is empty or the user explicitly states it's a greenfield/new project, skip codebase discovery entirely and note this assumption
  - Otherwise, search and read the local codebase
  - When the change touches one member of a family (one endpoint, one worker, one handler), list its siblings and which of them share the gap
  - Grep `docs/plans/` for designs that overlap the topic; when one does, name it and ask whether to build on it or start fresh
  - Summarize findings before proceeding: enough for the user to check your reading of the codebase, and no more
- **Self-verify before asking.** Before formulating any question for the user, apply this gate:
  - **Answerable from the codebase?** (installed deps, patterns in use, available APIs) → Resolve it yourself and state it as a resolved constraint, not a question
  - **Answerable from an external dependency?** (see Research) → Resolve it yourself the same way
  - **A preference, trade-off, scope, or judgment call only the user can decide?** ("Approach A or B?", "Async or sync?", "Is this in scope?") → Ask the user
- **Surface what nobody asked.** The frontier holds only decisions someone knew to make. When the feature enters a domain the codebase hasn't handled yet (money, time zones, i18n, file uploads, permissions, offline sync), list the domain's decisions that usually bite later, each glossed in a few words, and put the ones that apply on the frontier
- **Check the premise.** Before choosing an approach, ask yourself: is this the right problem, what does doing nothing cost, and does the request fix the pain or a proxy for it. Raise a doubtful premise in the first round; when the premise is sound, don't invent doubt
- **Ask in rounds, frontier first.** The frontier is every open decision whose prerequisites are already settled. Ask the frontier with `request_user_input` when available and supported in the current mode; otherwise ask in text:
  - A decision that depends on another question still open goes in a later round, not this one; each round's answers unblock the next frontier
  - One question holds one choice: alternative mechanisms for the same thing go together (e.g., storage options); a choice the user could accept while rejecting another is independent and goes in its own question of the same call (respect the actual tool schema and question limit; a larger frontier asks first the decisions most others depend on)
  - Each question states your recommended option and why, and the default an engineer would ship if nobody decides
  - Prefer multiple-choice options when possible; open-ended when the answer space is genuinely open
  - A fact still being looked up (codebase search, research) blocks only the decisions that depend on it; ask the rest of the frontier meanwhile
- Focus on: purpose, constraints, success criteria
- For performance work, record the current measurement and a target number before designing; "faster" is not a success criterion
- **Done when** the frontier is empty: the purpose and success criterion are stated, every judgment call is answered or defaulted (see Handling Disagreement), and every fact the design relies on is Verified or listed as Assumed. Then present the design.

### Verification Discipline

Codebase claims must be anchored to something the reader can locate. Name the file plus a stable handle inside it: a function, exported symbol, or short quoted identifier. Line numbers shift on every commit, so pick a handle that survives edits.

- **Anchor every load-bearing claim.** Anything the design relies on, anything driving a yes/no decision, anything reused as a constraint later in the document. Illustrative anchor: `createLogger() in server/src/lib/logger.ts`, or `` `import { logger } from './lib/logger'` at top of server/src/main.ts ``. Passing context that does not bear weight can stay unanchored
- **Split discovery output into Verified and Assumed.** Verified items carry an anchor. Assumed items carry the reason they were not checked (deferred for cost, outside current tooling, anything else). A design step may rely on an Assumed item only when the user confirms it or it is listed in the plan's assumptions to validate
- **Treat earlier claims as drafts, not facts.** A claim made earlier in the same conversation is not ground truth. When a later step depends on it, re-verify before relying on it
- **Retract before defending.** When the user asks to verify a claim, re-run discovery from scratch instead of restating the prior claim. If the original was wrong, name the error, state the corrected anchor, and list every design decision that inherited the error so they can be revisited together

See `examples/verify-callout.md` for the recovery flow when a claim turns out to be wrong.

### Handling Disagreement or Stalled Dialogue

- **User changes an earlier answer.** State the affected decisions and apply the latest clear correction. Ask which interpretation is intended only if the new instruction is ambiguous. See `examples/user-pivots.md`
- **User delegates a choice ("you decide").** Pick a reasonable default, state it briefly, and move on. If a required answer remains unclear and no safe default exists, ask for that missing detail while continuing independent work.
- **User wants to skip the design phase.** State your default assumptions in one message, let the user veto any item, then proceed to the plan. If implementation was already requested, proceed within that authorization. See `examples/skip-design.md`

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

The examples run on fictional Hono/Bun projects (a rate limiter, and a webhook signature check). Their paths, symbols, and findings do not describe this repository - discover the real codebase fresh. What they pin down is the shape of the exchange: what gets resolved without asking, what gets asked, and when the design lands.

- `examples/happy-path.md`: full workflow when user engages cooperatively
- `examples/user-pivots.md`: handling contradictions and rollback mid-design
- `examples/skip-design.md`: handling "just do it" requests without losing alignment
- `examples/verify-callout.md`: recovering when a codebase claim turns out to be wrong
