# Example: Design and implement a rate limiter

> Fictional project: paths, symbols, and findings are illustrative.

User: “I want to add a rate limiter to our Hono API server. Cap each IP per minute across all endpoints.”

## Discover the constraints

Read the middleware registration, deployment configuration, dependencies, and tests. Use `rg` and the available file-reading tools; batch independent reads.

Illustrative findings:

- Verified: `createApp()` in `server/src/main.ts` registers CORS and authentication middleware.
- Verified: `getTrustedClientIp()` in `server/src/middleware/clientIp.ts` supplies the validated client identity.
- Verified: the deployment configuration in `deploy/api.yaml` runs one API process.
- Assumed: 60 requests per minute is an appropriate product default; the user did not specify a number.

Do not infer deployment topology from missing dependencies. Identify stable symbols and paths for facts the design relies on.

## Choose the behavior

If the cap is consequential, use an optional preference question through `request_user_input` when available and supported, or ask in text. Resolve API signatures and storage capabilities yourself. Two algorithms genuinely fit (sliding and fixed window), so offer both with a recommendation; with one clear fit, state it in one line instead of inventing alternatives.

User: “Sliding window, 30 a minute.”

This refines the active implementation request. It does not require another execution approval.

## State the design and plan

Goal: cap each client IP at 30 requests per rolling minute across all endpoints; success is request 31 within 60 seconds getting `429`.

Use a sliding window keyed by the existing trusted client identity, with bounded storage and expiry cleanup. Return `429` and `Retry-After` when over the limit. State restart behavior and the single-process scope.

| File | Change | Check |
| --- | --- | --- |
| `server/src/middleware/rateLimit.ts` | Implement the middleware using project patterns | Deterministic clock tests at the limit and window boundary |
| `server/src/main.ts` | Register middleware in the intended route scope | HTTP integration test for limited and exempt routes |
| `server/src/middleware/rateLimit.test.ts` | Cover limits, expiry, cleanup, and client isolation | Run the relevant test file |
| `server/tests/rateLimit.integration.test.ts` | Exercise the registered middleware | Existing integration test command passes |

Save a durable design if the work needs one, using Goal, Decisions, Plan, optional Assumptions, and Verification. Each Plan line names the file, symbols or signatures to change, and a command or observable check. Verification uses `- [ ]` items. Run the fresh-reader check when delegation is authorized and available; otherwise check inline and report the missing independent review. Then implement and verify. If the original request was only to discuss a design, finish with the design and plan instead.


Illustrative saved doc (verify the fictional symbols and commands against the real repo before use):

```markdown
# IP rate limiter
## Goal
Request 31 from one client IP within 60 seconds returns 429; the middleware and integration tests pass.
## Decisions
- Sliding window, 30 requests per IP per 60 seconds, bounded in-memory storage with expiry cleanup.
- `server/src/middleware/clientIp.ts` exports the existing trusted identity helper `getTrustedClientIp()`.
- Register on every API endpoint in `server/src/main.ts`; send `Retry-After` with 429 responses.
- The verified single-process deployment resets the window on restart.
## Plan
1. `server/src/middleware/rateLimit.ts`: export `rateLimitMiddleware({ limit, windowMs, now })` using the trusted identity helper; bound storage and expire old entries. Check: `bun test server/src/middleware/rateLimit.test.ts`.
2. `server/src/middleware/rateLimit.test.ts`: use a fake clock to cover requests 1–30, request 31, the 60-second boundary, expiry cleanup, and client isolation. Check: `bun test server/src/middleware/rateLimit.test.ts`.
3. `server/src/main.ts`: register `rateLimitMiddleware({ limit: 30, windowMs: 60_000 })` before API routes. Check: `bun test server/tests/rateLimit.integration.test.ts`.
4. `server/tests/rateLimit.integration.test.ts`: exercise registered middleware, 429 and Retry-After, and independent client limits. Check: `bun test server/tests/rateLimit.integration.test.ts`.
## Verification
- [ ] `bun test server/src/middleware/rateLimit.test.ts` passes.
- [ ] `bun test server/tests/rateLimit.integration.test.ts` passes.
- [ ] Requests 1–30 pass, request 31 returns 429 with Retry-After, and a request after expiry passes.
```
