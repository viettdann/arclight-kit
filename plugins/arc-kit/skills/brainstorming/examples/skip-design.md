# Example: User Wants to Skip the Design Phase

> Fictional project: paths, symbols, and findings below are illustrative, not facts about this repository.

Shows how to handle "just do it" / "skip the questions" requests without either railroading the user into a full design or losing alignment entirely.

## User prompt

> Add a rate limiter to the Hono API. Don't ask me a bunch of questions, just do it.

## Response: confirm the trade-off, then request the minimum viable anchor

Do NOT dive into implementation blind. Do NOT force a full design either. Middle path:

> Understood. Skipping design means I'll make these choices on your behalf:
>
> - Storage: in-memory (single-node assumption)
> - Algorithm: sliding window, 60 requests / minute / IP
> - Error response: 429 with `Retry-After` header
> - Scope: all `/api/*` routes
>
> If any of those are wrong, tell me now. Otherwise I'll proceed with a plan and stop only for explicit approval before writing code.

This is one message, not a questionnaire. The user can either correct one item or say "go."

## User responses and how to handle them

### Case A: "Go"

Proceed directly to the implementation plan (same format as `happy-path.md`). Still require explicit approval on the plan before writing code. Skipping design does not mean skipping the approval gate.

### Case B: "Change storage to Postgres, otherwise fine"

Acknowledge, update the assumption list, present the plan:

> Got it, Postgres. Everything else as stated. Plan:
> [plan...]
> Approve?

### Case C: "Just write the code already"

This is NOT approval to skip the plan gate. Respond:

> The plan step costs one message and protects us from rewriting the feature. Here it is:
> [plan...]
> Reply `proceed` to start.

### Case D: User contradicts own "skip" and starts asking detailed questions

Drop back into the normal design flow. Do not insist on the skip path once the user has re-engaged with design decisions.

## Key principles

1. **Skip design, not alignment:** state your default assumptions in one shot, let user veto
2. **Skip design, not the approval gate:** the plan gate still applies
3. **Use project defaults aggressively.** CLAUDE.md conventions, existing patterns in the codebase, safest-reasonable choice for anything not specified
4. **Flag irreversible or high-blast-radius choices:** even in skip mode, if a default choice would be hard to undo (schema change, breaking API), surface it before applying
