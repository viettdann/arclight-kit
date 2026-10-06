---
name: executor
description: "Execute an existing implementation plan or task list with scoped exploration, safe ordering, optional TDD, risk-based validation, and completeness review. Use for execute the plan, implement this plan, thực thi, triển khai, or bắt đầu làm. Not for a one-off edit without a plan."
---

# Executor

Before assigning or implementing tasks, read `references/work-order.md` for dependency ordering, shared-worktree rules, delegation limits, and worker reporting.

Carry the authorized plan through implementation and verification. Use Vietnamese in chat and English in files unless the user requests otherwise. Follow applicable AGENTS.md files and the active runtime's tools and permission policies.

## 1. Establish the task

Read the user-named plan first; the word `tdd` in the request turns TDD mode on (section 3). Otherwise use the active conversation plan, which needs no file, or locate the relevant checklist under the project root (`plan.md`, `PLAN.md`, `TODO.md`, `tasks.md`, `checklist.md`, `*.todo`, design docs in `docs/plans/`); do not adopt unrelated TODO files. One candidate: use it. More than one: ask which, newest first. A plan file is the baseline; treat requests and corrections after it as amendments. Extract a compact checklist with file scope, dependencies, and an observable completion check for each item.

If no plan is identifiable, say what is missing and ask for its source. An explicit implementation request already authorizes the work: do not introduce another plan approval gate. A go-ahead covers the accepted scope, not all suggestions made earlier.

Verify referenced files, installed interfaces, dependencies, and required configuration. Resolve routine gaps yourself using project evidence. Ask only when an unresolved decision materially changes the requested behavior or scope. Continue independent tasks while a dependent task is blocked.

## 2. Order and assign work

Order tasks and assign work using `references/work-order.md`. Execute overlapping edits and dependencies sequentially; delegate only when authorized and supported, with disjoint file ownership and explicit worker instructions.

## 3. Implement and validate

For each task, inspect its actual implementation and consumers, make the complete change, and run the relevant checks. Reuse existing patterns and dependencies. Fix root causes; do not suppress errors to obtain a green check. Inline work may run the project-wide build and type-check; section 4 runs both, and the full suite, once every worker has finished.

TDD mode is off by default. It is on when the request contains `tdd`, the user asks for TDD, or the plan says to use it. On: for each task that adds or changes behavior, write the test first, run it, and see it fail on the missing behavior, not on a typo, a bad import, or broken setup; then implement until it passes. Refactor, config, and docs tasks skip the failing run. Off: scale testing to risk as below.

Scale testing to risk:

- For a behavior change, use existing unit or integration tests to cover meaningful outcomes and edge cases.
- For a bug fix, add a regression test when the existing harness can reproduce the defect.
- For refactoring, pin affected observable behavior before restructuring; apply `arc-kit:refactor` when available.
- For documentation, metadata, or a mechanical low-impact edit, validate syntax, references, and the diff; do not add tests that merely mirror text or implementation.
- Run required project checks. Do not invent a test harness or install e2e tooling unless requested. Record unavailable checks and existing failures accurately.

In either mode a test must fail when the behavior it covers is removed. Never write a test that asserts whatever the code currently returns, and never delete, skip, or loosen an existing test to get green. Change an existing test only when the plan changes the behavior it covers, and say so in the report. A lint rule, hook, CI step, or architecture check the plan adds is proven the same way: it passes on the code, fails on a deliberate violation, and passes again once the violation is reverted.

When the user steers ongoing work, update affected tasks and stop or redirect workers whose assignments became stale. A correction inside the authorized task does not require renewed permission. Update an existing plan when needed so it describes the current intended work; preserve explicitly deferred work in its checklist. If the new request is materially outside scope, clarify that boundary while continuing independent work.

## 4. Finish the plan

Review the integrated diff and check each plan item against actual files and observable results. Account for missing, partial, and explicitly deferred work. Use the installed `arc-kit:verifier` skill when available (explicit invocation: `$verifier`); otherwise perform completeness, correctness, contract, and documentation review inline.

Run required build, type, lint, and test checks appropriate to the affected packages; run a full or slow suite under the test runner brief (`references/test-runner.md`). Broaden testing when cross-package effects or a failure justify it. Re-run checks after relevant fixes; do not repeat an unchanged passing suite without a reason. Worker reports do not replace integration checks.

Continue until all authorized work is done or name the specific unresolved blocker and affected items. Report the outcome, relevant checks with pass/fail/not-run status, and remaining limitations concisely.

## 5. Git delivery

Commit only when the user has authorized a commit; earlier authorization persists. Otherwise leave the reviewed changes ready for inspection. Follow AGENTS.md and existing commit style, defaulting to `type(scope): imperative summary`.

Inspect git status and stage explicit paths containing only this task's changes. Preserve unrelated staged content; never include it accidentally. Do not stage `docs/` unless the user explicitly asks, consistent with the user's working rules. Review the staged diff for scope and secrets before committing. Do not force-push or bypass hooks without explicit authorization.

## Decisions and blockers

Resolve codebase facts before escalating. Pick the existing project pattern when several routine implementations fit. Never apply a workaround silently: take the proper fix without asking when it is small or obvious; ask only when it costs far more than the workaround (a large refactor, or changes outside the plan's files) or the trade-off is genuinely ambiguous, and then show both: `Proper fix: X (effort). Workaround: Y (debt it creates).` Reuse an installed dependency before adding one; raise a new dependency only if it introduces a material scope, licensing, operational, or maintenance choice. Flag unnecessary plan steps with evidence rather than silently dropping them.

Use `request_user_input` for optional preferences only when available and supported by the active mode; otherwise ask in text. Required approval follows the runtime's approval mechanism. Never invent unavailable tools or claim a check was run when it was only proposed.

## Decisions and delegated limits

Record judgment calls resolved without asking under "Decided for you", including the alternative, in worker reports and the execution summary. Workers never perform irreversible actions (data deletion, external publishing, schema drops, force operations); report them to the orchestrator. The orchestrator checks existing authorization and asks only for actions outside it.
