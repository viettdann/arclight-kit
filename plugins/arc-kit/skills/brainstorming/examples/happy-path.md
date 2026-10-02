# Example: Happy Path

> Fictional project: paths, symbols, and findings below are illustrative, not facts about this repository.

Shows the full workflow when the user engages cooperatively, answers clarifying questions, and approves the plan without pivoting.

## User prompt

> I want to add a rate limiter to our Hono API server. Each IP should be capped at some reasonable amount per minute across all endpoints.

## Step 1: Grasp + targeted codebase discovery

Assistant response:

> Before I suggest a design, let me check how the server is structured.

Runs (in parallel):
- `Grep` for `hono` imports in `server/src`
- `Read` `server/src/main.ts`, `server/src/middleware/` (if exists)
- `Grep` for existing `rateLimit|throttle` patterns

Summary back to user:
- Hono app entrypoint at `server/src/main.ts`, middleware chain already uses CORS + auth
- No existing rate-limit middleware found
- Routes split across `server/src/routes/` (17 files)
- Bun runtime, no Redis in deps

## Step 2: Self-verify + Clarify

The assistant resolves factual constraints from codebase discovery instead of asking:

> **Resolved from codebase:**
>
> Verified:
> - Single-node deployment, no Redis in `package.json` dependencies → in-memory storage is the right fit. No reason to add a new dependency
> - Pino imported in `createLogger()` at `server/src/lib/logger.ts`, called by `authMiddleware` in `server/src/middleware/auth.ts`. Available for the rate-limit middleware as well
>
> Assumed (listed in the plan's assumptions to validate):
> - Client IP reachable via `c.req.header('x-forwarded-for')` in this deployment
>
> **Preference question (requires user input):**
>
> Two algorithm shapes fit:
> 1. **Sliding window per IP** (recommended): rolling 60s window, drops old timestamps on each request. Accurate, small memory footprint
> 2. **Fixed window counter:** simpler, but allows 2x burst at window boundaries
>
> I recommend sliding window. Which do you prefer, and what cap per IP per minute? (60/min is a common starting point if you have no number in mind.)

Note: the assistant did NOT ask "how should state be stored?" because codebase discovery already answered that (single-node, no Redis). It stated the conclusion as a fact and only asked the genuine preference question.

User: "Sliding window, 30 a minute."

## Step 3: Present full design in one message

The assistant presents the entire design as a single coherent message, NOT section-by-section:

> **Architecture:**
> Middleware `rateLimitMiddleware(limit, windowMs)` registered in `server/src/main.ts` before routes. Stores a `Map<ip, number[]>` keyed by client IP. Sliding window algorithm.
>
> **Components:**
> - `server/src/middleware/rateLimit.ts`: middleware factory
> - In-memory store scoped to module (cleared on restart)
> - Returns `429` with `Retry-After` header when limit exceeded
>
> **Error handling:**
> - Log at `warn` level via Pino with `{ ip, path, count }` when limit hit
>
> **Testing:**
> - Unit test: inject fake clock, verify window behavior
> - Integration test: hit endpoint 31 times in 60s, expect 30 success + 1 rejection
>
> Does this design look right?

Note: ONE confirmation ask at the end of the full design, not after each section.

User: "Yes."

## Step 4: Implementation plan

```
Files touched:
- server/src/middleware/rateLimit.ts (new): sliding-window factory, exports rateLimitMiddleware
- server/src/main.ts (edit): register middleware before routes
- server/src/middleware/rateLimit.test.ts (new): unit tests with fake clock
- server/tests/rateLimit.integration.test.ts (new): integration test

Assumptions to validate:
- Client IP is available via Hono's c.req.header('x-forwarded-for') or c.env.remoteAddr

Verification criteria:
- Unit test: 30 requests in window succeed, 31st returns 429
- Integration test: real HTTP, same result
- No TypeScript errors, biome check passes
```