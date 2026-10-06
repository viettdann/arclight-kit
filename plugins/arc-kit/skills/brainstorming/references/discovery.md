# Brainstorming detailed instructions

Resolve all relative paths in this reference from the parent skill directory containing `SKILL.md`, not from `references/`.

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

## Additional Resources

The examples run on fictional Hono/Bun projects (a rate limiter, and a webhook signature check). Their paths, symbols, and findings do not describe this repository - discover the real codebase fresh. What they pin down is the shape of the exchange: what gets resolved without asking, what gets asked, and when the design lands.

- `examples/happy-path.md`: full workflow when user engages cooperatively
- `examples/user-pivots.md`: handling contradictions and rollback mid-design
- `examples/skip-design.md`: handling "just do it" requests without losing alignment
- `examples/verify-callout.md`: recovering when a codebase claim turns out to be wrong
