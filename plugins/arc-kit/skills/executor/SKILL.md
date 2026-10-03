---
name: executor
description: "Execute an existing implementation plan or task list with scoped exploration, safe ordering, risk-based validation, and completeness review. Use for execute the plan, implement this plan, thực thi, triển khai, or bắt đầu làm. Not for a one-off edit without a plan."
---

# Executor

Carry the authorized plan through implementation and verification. Use Vietnamese in chat and English in files unless the user requests otherwise. Follow applicable AGENTS.md files and the active runtime's tools and permission policies.

## 1. Establish the task

Read the user-named plan first. Otherwise use the active conversation plan or locate the relevant checklist under the project root; do not adopt unrelated TODO files. Treat recent user corrections as amendments. Extract a compact checklist with file scope, dependencies, and an observable completion check for each item.

If no plan is identifiable, say what is missing and ask for its source. An explicit implementation request already authorizes the work: do not introduce another plan approval gate. A go-ahead covers the accepted scope, not all suggestions made earlier.

Verify referenced files, installed interfaces, dependencies, and required configuration. Resolve routine gaps yourself using project evidence. Ask only when an unresolved decision materially changes the requested behavior or scope. Continue independent tasks while a dependent task is blocked.

## 2. Order and assign work

Map tasks to their files and dependencies. Execute overlapping file edits and dependent interface changes in sequence. Batch independent searches and reads when the available tools support it.

Delegate only when authorized by the user or applicable instructions and when the runtime exposes delegation tools. Otherwise execute the same work inline. Do not assume agent tool names, model identifiers, context inheritance, or a fixed concurrency limit. Inherit the session model and obey the runtime's concurrency budget. Small edits and one-command checks usually belong inline.

Before parallel edits, confirm each assignment has disjoint files, no dependency on unfinished types or exports, and no conflicting database, queue, cache, or external state. Give each worker its exact scope, relevant plan and decisions, verification commands, and these rules:

- Read existing files before changing them; preserve unrelated edits in the shared worktree.
- Edit only assigned files; report required scope expansions to the coordinator.
- Do not stage, commit, stash, reset, revert, restore, clean, or discard changes.
- Return completed tasks, changed paths, actual checks and results, and unresolved issues.

The coordinator owns cross-task integration and final verification. Serialize shared fixes and resolve routine conflicts from the intended behavior; ask the user only when the conflict requires a product or scope decision.

## 3. Implement and validate

For each task, inspect its actual implementation and consumers, make the complete change, and run the relevant checks. Reuse existing patterns and dependencies. Fix root causes; do not suppress errors to obtain a green check.

Scale testing to risk:

- For a behavior change, use existing unit or integration tests to cover meaningful outcomes and edge cases.
- For a bug fix, add a regression test when the existing harness can reproduce the defect.
- For refactoring, pin affected observable behavior before restructuring; apply `arc-kit:refactor` when available.
- For documentation, metadata, or a mechanical low-impact edit, validate syntax, references, and the diff; do not add tests that merely mirror text or implementation.
- Run required project checks. Do not invent a test harness or install e2e tooling unless requested. Record unavailable checks and existing failures accurately.

When the user steers ongoing work, update affected tasks and stop or redirect workers whose assignments became stale. A correction inside the authorized task does not require renewed permission. Update an existing plan when needed so it describes the current intended work; preserve explicitly deferred work in its checklist. If the new request is materially outside scope, clarify that boundary while continuing independent work.

## 4. Finish the plan

Review the integrated diff and check each plan item against actual files and observable results. Account for missing, partial, and explicitly deferred work. Use the installed `arc-kit:verifier` skill when available (explicit invocation: `$verifier`); otherwise perform completeness, correctness, contract, and documentation review inline.

Run required build, type, lint, and test checks appropriate to the affected packages. Broaden testing when cross-package effects or a failure justify it. Re-run checks after relevant fixes; do not repeat an unchanged passing suite without a reason. Worker reports do not replace integration checks.

Continue until all authorized work is done or name the specific unresolved blocker and affected items. Report the outcome, relevant checks with pass/fail/not-run status, and remaining limitations concisely.

## 5. Git delivery

Commit only when the user has authorized a commit; earlier authorization persists. Otherwise leave the reviewed changes ready for inspection. Follow AGENTS.md and existing commit style, defaulting to `type(scope): imperative summary`.

Inspect git status and stage explicit paths containing only this task's changes. Preserve unrelated staged content; never include it accidentally. Do not stage `docs/` unless the user explicitly asks, consistent with the user's working rules. Review the staged diff for scope and secrets before committing. Do not force-push or bypass hooks without explicit authorization.

## Decisions and blockers

Resolve codebase facts before escalating. Pick the existing project pattern when several routine implementations fit. Reuse an installed dependency before adding one; raise a new dependency only if it introduces a material scope, licensing, operational, or maintenance choice. Flag unnecessary plan steps with evidence rather than silently dropping them.

Use `request_user_input` for optional preferences only when available and supported by the active mode; otherwise ask in text. Required approval follows the runtime's approval mechanism. Never invent unavailable tools or claim a check was run when it was only proposed.
