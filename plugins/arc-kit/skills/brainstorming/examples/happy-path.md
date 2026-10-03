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

Save a durable design if the work needs one, then implement and verify. If the original request was only to discuss a design, finish with the design and plan instead.
