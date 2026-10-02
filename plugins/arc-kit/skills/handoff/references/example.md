# Example handoff

A filled-in handoff at the density and specificity to target. Note the Failed
attempts entry: it names the exact dead end and the reason, so the next session
doesn't waste a turn re-discovering it.

---

# Handoff: auth-token-refresh - 2026-06-06

> To resume: read this file top to bottom, then run `git status` and `git diff`
> to confirm the repo matches what's described below before continuing.
> Source session: `3f2a9c1e-7b4d-4e8a-9c6f-1d2e3b4a5c6d` (full transcript: `claude --resume 3f2a9c1e-7b4d-4e8a-9c6f-1d2e3b4a5c6d`)

## Goal

Refresh expired access tokens transparently so API calls don't 401 mid-session.
Target: a request that hits an expired token retries once with a fresh token.

## Current state

Refresh logic works in isolation - `refreshToken()` returns a new token pair and
`src/auth/token.test.ts` passes for the happy path. Not yet wired into the
request layer: live API calls still fail on expiry because nothing calls
`refreshToken()` on a 401. Expiry-during-refresh (token expires while the
refresh request is in flight) is unhandled.

## Files in flight

- `src/auth/token.ts` - `refreshToken()` implemented and tested; the 401 retry
  hook is stubbed (`onUnauthorized` exists but only logs, doesn't refresh).
- `src/auth/token.test.ts` - happy-path test passes; no test for concurrent
  refresh or refresh-failure yet.

## Changed this session

- `src/auth/token.ts` - added `refreshToken()`, added `onUnauthorized` stub.
- `src/auth/token.test.ts` - new file, one passing test.

## Failed attempts

- Tried implementing the retry as an axios interceptor - failed because the test
  harness mocks `fetch`, not axios, so every test silently passed without
  exercising the retry. Reverted. The retry must hook into the existing `fetch`
  wrapper in `src/api/client.ts`, not a new axios layer.

## Next step

Wire `onUnauthorized` in `src/auth/token.ts` to call `refreshToken()` and replay
the original request once, hooking into the `fetch` wrapper in
`src/api/client.ts:request()`. Alternative if that wrapper is hard to intercept:
catch the 401 in `request()` directly.

## Open questions / unverified

- Assuming the refresh endpoint returns a new refresh token too (rotation), not
  just an access token - did not confirm against the API docs. If it doesn't
  rotate, the stored refresh token stays valid and the replace logic simplifies.
