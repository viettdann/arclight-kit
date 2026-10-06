# Executor detailed instructions

Resolve all relative paths in this reference from the parent skill directory containing `SKILL.md`, not from `references/`.

## 2. Order and assign work

Map tasks to their files and dependencies. When the plan doesn't name the files, a quick search usually does; a task whose files still can't be named without exploring goes to an inline lane that runs after the parallel groups. Execute overlapping file edits and dependent interface changes in sequence. If every task lands in one group, implement it inline, sequentially, with no workers. Batch independent searches and reads when the available tools support it.

Delegate only when authorized by the user or applicable instructions and when the runtime exposes delegation tools. Otherwise execute the same work inline. Do not assume agent tool names, model identifiers, context inheritance, or a fixed concurrency limit. Inherit the session model and obey the runtime's concurrency budget. Small edits and one-command checks usually belong inline.

Before parallel edits, confirm each assignment has disjoint files, no dependency on unfinished types or exports, and no conflicting database, queue, cache, or external state. Give each worker its exact scope, relevant plan and decisions, verification commands, and these rules:

- Read existing files before changing them; preserve unrelated edits in the shared worktree.
- Edit only assigned files; report required scope expansions to the coordinator.
- Do not stage, commit, stash, reset, revert, restore, clean, or discard changes.
- Never perform irreversible actions (data deletion, external publishing, schema drops, force operations); report the required action to the coordinator.
- Run lint and the tests that cover your own files after meaningful changes; never the project-wide build or type-check, which other workers' half-written files make fail.
- Follow the TDD mode stated in this assignment.
- Return completed tasks, changed paths, actual checks and results (lint and tests for your own files, and with TDD on, each test and the failure seen before implementing), and unresolved issues.
- Include "Decided for you" in the report: each judgment call resolved without asking and the alternative not taken, or "none".

A worker cannot see this skill: its assignment carries these rules, the section 3 implement-and-validate steps, the TDD mode text with whether it is on, and the report fields verbatim.

The coordinator owns cross-task integration and final verification. Serialize shared fixes and resolve routine conflicts from the intended behavior; ask the user only when the conflict requires a product or scope decision.
