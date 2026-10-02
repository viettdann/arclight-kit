# Example: User Calls Out an Unverified Claim

> Fictional project: paths, symbols, and findings below are illustrative, not facts about this repository.

Shows how to recover when codebase discovery includes a claim that turns out to be wrong, and the user asks for verification.

## Scenario

The user wants to add HMAC signature verification to the Azure DevOps webhook endpoint at `/api/automation/webhooks/ado`. During codebase discovery the assistant grepped quickly, missed details, and reported back:

> **Codebase findings:**
> - Webhook route registered in `automationRoutes` at `server/src/routes/automation.ts`
> - `crypto` is already used elsewhere in the server for HMAC, so there is a shared helper to reuse

The design that followed assumed `crypto.timingSafeEqual` and an existing HMAC helper were available, and proposed reusing them.

## User pushback

> wait, where do we use HMAC already? I don't think we do.

## Right move: re-run discovery from scratch, retract explicitly

Do not restate the original claim, do not search for partial matches that prop it up, do not hedge with "it might be in...". Re-verify and name the error.

> The earlier claim was wrong. Re-checked across `server/src`: no module calls `crypto.createHmac` or `crypto.timingSafeEqual`. The only HMAC reference is a stub `verifyAdoSignature()` in `server/src/routes/automation.ts` whose body currently returns `true` unconditionally, so it is not a real verifier.
>
> Corrected codebase findings:
>
> Verified:
> - Webhook route registered in `automationRoutes` at `server/src/routes/automation.ts`
> - Stub `verifyAdoSignature()` in the same file, body returns `true`
> - `ADO_WEBHOOK_SECRET` declared in the env schema at `server/src/config/env.ts`
>
> Assumed (needs check before the design depends on it):
> - Azure DevOps signs payloads with HMAC-SHA256 over the raw request body. Confirm against the ADO service-hooks docs before settling on the algorithm

## Trace contamination

Naming what the bad claim contaminated is part of the retraction. Otherwise the user has to do the bookkeeping.

> The design section that proposed "reuse existing HMAC helper" is invalidated. Replacement: implement `verifyAdoSignature()` from scratch in `server/src/routes/automation.ts`, using `crypto.createHmac` and `crypto.timingSafeEqual` directly. The Implementation Plan drops the "extract shared HMAC util" item and adds a unit test for the new function plus an integration test that posts a signed and an unsigned payload.

## Re-present the affected sections

Present the revised design and plan as a single block so the user sees the corrected picture coherently, not a chain of patches.

## Key moves

1. Retract before defending. "The earlier claim was wrong" leads, no hedging
2. Re-run discovery from scratch. Do not mine for partial matches that rescue the original claim
3. Anchor the corrected findings. File plus function or symbol, never line numbers
4. Split Verified from Assumed. Items not re-checked move into Assumed with a reason
5. Trace contamination. Name every design decision and plan item that inherited the bad claim, then update them in one revised block
