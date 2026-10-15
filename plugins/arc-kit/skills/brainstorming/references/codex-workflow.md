# Brainstorming Ideas Into Designs

Resolve bundled paths from the parent skill directory containing SKILL.md, including paths in references; resolve target project paths from the project working directory. Before a shell command, resolve bundled script paths to absolute paths and quote them. Follow project AGENTS.md and the active runtime's instructions, tools, permissions, and concurrency limits. Existing user authorization persists across discovery, implementation, and review; ask only about unresolved scope or actions outside it. Use available question tools for preferences, or ask in chat when unavailable. Delegate only when allowed and supported; otherwise run the same checks inline and report when an independent review was unavailable. Inherit the session model unless the user explicitly requests model routing and the runtime supports it. Do not assume named plugin agents, fixed model names, or a fixed worker count.

## Overview

Help turn ideas into fully formed designs and specs through natural collaborative dialogue.

Start from a high-level description of what the user wants to build and the current project context, then ask questions to refine the idea until Understanding is done, then present the design.

## The Process

### Understanding the Idea

- **Grasp the idea first.** Use the goal already stated in the request; ask for a high-level description only when it is missing (1-2 sentences is enough to proceed)
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
  - **Would every answer lead to the same build?** → Don't ask; take the default and state it in the design
- **Surface what nobody asked.** The frontier holds only decisions someone knew to make. When the feature enters a domain the codebase hasn't handled yet (money, time zones, i18n, file uploads, permissions, offline sync), list the domain's decisions that usually bite later, each glossed in a few words, and put the ones that apply on the frontier
- **Check the premise.** Before choosing an approach, ask yourself: is this the right problem, what does doing nothing cost, and does the request fix the pain or a proxy for it. Raise a doubtful premise in the first round; when the premise is sound, don't invent doubt
- **Ask in rounds, frontier first.** The frontier is every open decision whose prerequisites are already settled. Ask the frontier with the available user-question tool, for preference/judgment questions only:
  - A decision that depends on another question still open goes in a later round, not this one; each round's answers unblock the next frontier
  - One question holds one choice: alternative mechanisms for the same thing go together (e.g., storage options); a choice the user could accept while rejecting another is independent and goes in its own question of the same call (up to the question tool’s supported limit per call; a larger frontier asks first the decisions most others depend on)
  - Each question states your recommended option and why, and the default an engineer would ship if nobody decides
  - Prefer multiple-choice options when possible; open-ended when the answer space is genuinely open
  - A fact still being looked up (codebase search, research) blocks only the decisions that depend on it; ask the rest of the frontier meanwhile
- Focus on: purpose, constraints, success criteria
- For a feature with UI, settle the user's steps, the inputs and their validation, and each screen's loading, empty, failure, and success states; `arc-design:ui-interaction`, when installed, holds the rules for each state
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

- **User contradicts an earlier answer.** Name the contradiction explicitly, list which prior decisions it invalidates, ask which version is correct. Do not silently absorb the new answer. See `examples/user-pivots.md`
- **User stays unclear across 3+ turns on the same decision, or keeps giving non-answers ("whatever", "you decide").** Pick the safest reasonable default, state it as a decision (not a question), and move on. If no safe default exists, narrow scope to what's already clear or defer the decision and proceed with the rest
- **User wants to skip the design phase.** State your default assumptions in one message, let the user veto any item, then proceed to the plan. Previously authorized implementation continues without a new approval gate. See `examples/skip-design.md`

### Exploring Approaches

- When more than one approach fits, propose 2-3 with their trade-offs, leading with your recommendation and why. When one approach is clearly right, state it and the reason in one line; don't invent weaker options to compare against
- **Proper fix first.** Never present only a workaround. Take the proper fix without asking when it is small or obvious. Ask only when it costs far more than the workaround (a large refactor, or changes outside the plan's files) or the trade-off is genuinely ambiguous, and then show both: `Proper fix: X (effort). Workaround: Y (debt it creates).`

### Research (when needed)

Research covers external dependencies only: whether a library exists, its API surface, its runtime behavior. Check the installed package source and types first, then the official docs. Choosing between libraries or services, or checking current versions, support dates, or prices, goes through `arc-kit:research` when it is installed: read and follow the installed skill it.

### Presenting the Design

- Present the entire design in one message, organized with headings, and ask for confirmation once at the end, never per section
- Cover: the goal and its success criterion, architecture, components, data flow, error handling, testing considerations
- Go back and clarify if something doesn't land correctly

### Implementation Plan

- After the user confirms the design, present a concrete implementation plan:
  - List every file the plan touches. Do not summarize multiple files into one line
  - Each line: file path + the exact change (names, signatures, fields, types) + the check that proves it (test name, command, or observable state). Add a why only when an implementer would otherwise get the change wrong, in a few words inside the line
  - Highlight assumptions that need validation
- For discussion-only requests, present the plan and wait for an implementation request. For an existing implementation request, proceed once consequential unresolved decisions are settled.
- **Authorization carries forward.** If implementation is already requested, save the design and continue into execution in the same turn. Discussion-only requests stop at the design; approval of a design alone does not invent implementation scope.
- **Scope Creep Rule:** If the user adds a new constraint or feature at this approval stage, revise the design and plan in chat, show the delta, and ask for approval again. Save settled decisions; ask only about unresolved scope

### Design Doc Wording

The saved design doc holds only what gets done, stated as the target state. Everything the implementer won't do stays out: no exclusions, deferrals, removals, or history ("Removed X", "There is no X", "Not in this change: Y"), no rationale, alternatives considered, or background, and nothing the code already shows. Deltas, YAGNI flags, and trade-offs belong in chat, not in the doc.
- *Incorrect:* "There is no header subtitle. Removed the subtitle text."
- *Correct:* "The header contains a primary title."

The doc is self-contained: a reader with only the doc and the repo can carry out every line without asking. Every file and symbol carries its path, every command is written out, and every decision settled in the conversation is restated as fact. Never point back at the conversation ("as discussed", "see above", "option B", "the approach we chose").

## After the Design

- Once the design is settled within the authorized scope, write the design to `docs/plans/YYYY-MM-DD-<topic>-design.md` (`docs/plans/` below means this directory; take the date from `date +%F`)
  - **Topic slug must match `^[a-z0-9-]{1,60}$`**
  - Derive the slug by lowercasing, replacing spaces/underscores with hyphens, and stripping invalid characters. Example: `Input: My Feature/Design v2 → Output: my-feature-design-v2`
  - Truncate the slug to 60 characters after normalization. Fall back to `untitled` if empty
  - Never interpolate the raw topic into a shell command; only pass the validated slug to the available file-edit tool as part of the fixed `docs/plans/` path
  - **If `docs/plans/` does not exist**, create it (`mkdir -p docs/plans`) and note its creation in your reply. If the current working directory is not a writable project root (e.g., outside a repo, or user is in a path like `/tmp`), ask the user where to save the design instead of silently creating directories
- The doc must stand alone after a new session, since the next session only has the doc (Design Doc Wording). Use these sections, in this order:

  ```markdown
  # <Topic>
  ## Goal          one or two lines: the outcome and the check that proves it (a target number for performance work)
  ## Decisions     every decision settled in the conversation, one line each, stated as fact; contracts between files and data flow go here
  ## Plan          ordered, one line per file: path + exact change (names, signatures, fields, types) + the check that proves it; a UI file's line names its loading, empty, failure, and success states
  ## Assumptions   only unverified facts the plan relies on, each with the command or read that verifies it
  ## Verification  `- [ ]` items, each a command or an observable result of something the Plan does, including each input or failure mode the Plan handles
  ```

  Omit `Assumptions` when empty; the other four are always present. A line where a line does; no restating the request. See the doc at the end of `examples/happy-path.md`.
- **Fresh-reader check.** After writing the doc and before replying with its path, when delegation is authorized and available, use one fresh reviewer with no conversation context and the inherited session model: give it only the doc path and repo root. Ask it to read the doc and the code it names, then return, for each Plan line, what it would change and how it would check it in its own words; every question it would ask before starting; every file, symbol, or command it could not find; and every line that narrates, justifies, or describes something not being done. Rewrite lines it read differently, answer questions the doc should settle, and bring user-only decisions to the user. Flagged wording follows Design Doc Wording. Run at most two rounds; stop when a round raises nothing new. Otherwise perform the same check inline and report that independent review was unavailable.
- In the reply with the doc path, suggest an optional audit: "Run `$plan-auditor docs/plans/<filename>` to stress-test before execution."

## Key Principles

- **YAGNI ruthlessly.** Before finalizing any design section, flag a feature for removal if ALL of the following are true:
  1. The user has not mentioned it in the original prompt or any clarifying answer
  2. It does not appear in the stated goals, constraints, or success criteria
  3. It is not a direct consequence of an explicitly required feature (e.g., auth → session storage is a direct consequence)

  When flagging, state the feature + the reason, and let the user reinstate it. Example: "Removed: admin dashboard. Not in stated goals. Reinstate?"

## Additional Resources

The examples run on fictional Hono/Bun projects (a rate limiter, and a webhook signature check). Their paths, symbols, and findings do not describe this repository - discover the real codebase fresh. What they pin down is the shape of the exchange: what gets resolved without asking, what gets asked, and when the design lands.

- `examples/happy-path.md`: full workflow when user engages cooperatively
- `examples/user-pivots.md`: handling contradictions and rollback mid-design
- `examples/skip-design.md`: handling "just do it" requests without losing alignment
- `examples/verify-callout.md`: recovering when a codebase claim turns out to be wrong