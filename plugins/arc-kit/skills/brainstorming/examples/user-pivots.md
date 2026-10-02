# Example: User Pivots Mid-Design

> Fictional project: paths, symbols, and findings below are illustrative, not facts about this repository.

Shows how to handle a user who contradicts an earlier decision or introduces new constraints after the design has been presented.

## Setup

Same rate-limiter scenario as `happy-path.md`. User has already:
- Picked **in-memory** storage
- Received the full design in one message: Section A (architecture), Section B (components), Section C (error handling + tests)

## Pivot event

Before confirming the design, the user says:

> Actually, we might deploy multiple nodes later. Should rate-limit state survive across nodes?

## Response: surface the contradiction explicitly

Do NOT silently revise the earlier design. Name what changed:

> This changes the Section A assumption (single-node, in-memory store). A multi-node deploy makes in-memory incorrect because each node tracks its own counters and an attacker gets `N * limit` throughput.
>
> Two options:
>
> 1. **Keep in-memory, accept degraded guarantee under multi-node:** documented caveat, zero infra change. Suitable if multi-node is hypothetical
> 2. **Move state to Postgres:** already in stack, durable, adds ~1 query per request on every endpoint
>
> Which reflects reality: single-node for the foreseeable future, or multi-node is on the near-term roadmap?

User: "Multi-node in Q3. Let's use Postgres."

## Roll back the affected sections

Explicitly identify what needs to change, not just the current section:

> Rolling back Section A and Section B since storage changed:
>
> - Section A: middleware now queries `rate_limit_events` table
> - Section B: new file `server/src/db/schema/rateLimitEvents.ts` (Drizzle schema), `rateLimit.ts` becomes async
> - Section C (new): error handling for DB failures: fail open or fail closed?
>
> Fail open (allow request if DB is unreachable) is safer for availability; fail closed is safer for abuse. Which do you want?

User: "Fail open, log at error level."

## Re-present revised design

Present the revised Section A + B + C as a single block so the user sees the coherent new picture, not fragments:

> **Revised design:**
>
> - Middleware: async, queries `rate_limit_events` in a transaction, inserts new event row, prunes rows older than `windowMs`
> - New table: `rate_limit_events(ip, endpoint, created_at)`, index on `(ip, created_at)`
> - Failure mode: on DB error, log at `error`, allow request through
>
> Does this revised design look right? (Yes / needs more changes)

## Revised implementation plan

Only now present a new plan that replaces the old one:

```
Files touched:
- server/src/db/schema/rateLimitEvents.ts (new): Drizzle schema
- server/src/db/schema/index.ts (edit): export rateLimitEvents
- server/src/middleware/rateLimit.ts (new): async middleware, Postgres-backed
- server/src/main.ts (edit): register middleware
- server/src/middleware/rateLimit.test.ts (new): mock db, verify behavior
- server/tests/rateLimit.integration.test.ts (new): real db, end-to-end

Assumptions to validate:
- Drizzle migrations will be generated via `bun run db:generate` after schema change
- Connection pool handles extra query volume (check pool size in db config)
- "Fail open" on DB error is acceptable per user decision
```

## Key moves illustrated

1. **Never silently absorb contradictions:** call out which prior decision is invalidated
2. **Identify blast radius:** list every section/file that needs to change, not just the one in front of you
3. **Re-present coherent revised design:** don't leave the user reconstructing it from patches
4. **New plan replaces old plan:** do not hand the user two versions to reconcile
