---
name: executor
argument-hint: "[plan-file] [tdd]"
description: >
  Implements plans step-by-step with per-task codebase exploration, optional TDD, parallel sub-agents, and verification.
  Reads a plan file, TODO list, checklist, or conversation plan, does a quick scan for
  blocking unknowns, then each sub-agent explores on-the-fly before implementing its task.
  Validates builds and tests continuously, cross-checks every plan item before reporting done,
  and proposes commits once everything is verified. Use when a plan exists and implementation should begin.
  Triggers when the user asks to begin implementing an existing plan, in English or Vietnamese
  ("execute the plan", "implement this", "start building", "thực thi", "triển khai",
  "bắt đầu làm"), or confirms a plan for execution. Not for one-off edits with no plan.
---

# Executor

Implement plans with discipline. Scan for blockers, explore per-task, verify everything.

## Core Principles

1. **Plan-driven**: always work from an explicit task list
2. **Scoped exploration**: quick scan for blockers upfront, deep explore per-task on-the-fly
3. **Root cause over quick fix**: never patch symptoms
4. **Parallel where safe**: run task groups concurrently when the Phase 2 Step 4 safety check passes, sequentially otherwise
5. **Verify before done**: build must pass, all plan items implemented
6. **User decides scope, not mechanics**: escalate scope changes and trade-offs via AskUserQuestion. How to execute (parallel vs sequential, sub-agent count, grouping) is yours to decide

## Shared Worktree

Other sessions and your own sub-agents write to the same checkout. These rules bind you and go verbatim into every sub-agent prompt:

- Edit only the files in your assigned list. If the task needs another file, stop and report the file and the reason; the orchestrator regroups.
- Uncommitted changes in files you never edited belong to someone else. Leave them, don't remark on them, don't work around them.
- Never run `git stash`, `git reset`, `git revert`, `git checkout --`, `git restore`, or `git clean`, and never overwrite a file you didn't edit this session, unless the user asked for that exact operation.
- Sub-agents never stage or commit; commits happen only in Phase 5.
- If a foreign change blocks the task, say what it blocks and stop.

## Progress Checklist

Copy and track as you execute:

```
- [ ] Phase 0: Plan loaded, task list extracted
- [ ] Phase 1: Blockers scanned
- [ ] Phase 2: File edit sequence planned, parallel batches identified
- [ ] Phase 3: All tasks implemented + validated
- [ ] Phase 4: Build pass, tests pass, all plan items cross-checked
- [ ] Phase 5: Commit proposed, created after user approval
```

## Workflow

### Phase 0: Load the Plan

Arguments: $ARGUMENTS

A path in the arguments is the plan file; the word `tdd` turns TDD mode on. Without a path, take the first source that exists:

1. A plan file named in this conversation, or a plan written out in the conversation itself. A conversation plan needs no file.
2. A workspace search: `plan.md`, `PLAN.md`, `TODO.md`, `tasks.md`, `checklist.md`, `*.todo`, and design docs in `docs/plans/`. One candidate: use it. More than one: ask which with AskUserQuestion, newest first.

A plan file is the baseline; requests in the conversation after it are amendments.

Extract a flat checklist of discrete tasks. Each task gets a status: `pending`.

If no plan exists in the arguments, the conversation, or the workspace, stop. Ask the user to provide or create one first.

### Phase 1: Quick Scan for Blockers

Fast, lightweight scan for issues that would block execution, not deep exploration:

- Plan contradictions or impossible steps
- References to non-existent files/modules/APIs
- Missing critical dependencies or unclear integration points
- External APIs or libraries with unknown interfaces

**Actions:**

- Glob/Grep to verify referenced files exist
- Spot-check key interfaces mentioned in the plan (function signatures, types); list each as verified or missing
- Use AskUserQuestion for ambiguities (see Decision Framework)

**Output:** blocker list. If any blocker is found, report it and stop. Do not start Phase 2 until the user resolves it. Each task explores its own implementation context in Phase 3.

### Phase 2: Dependency Analysis & Task Grouping

#### Step 1: Build file-task matrix

Map each task to the files it touches. When the plan doesn't name them, a quick Grep/Glob usually does; a task whose files still can't be named without exploring goes to the inline lane.

```
Task 1 → [src/foo.ts, src/foo.test.ts]
Task 2 → [src/bar.ts]
Task 3 → [src/foo.ts, src/baz.ts]
Task 4 → [src/qux.ts]
Task 5 → [unknown] → inline lane
```

#### Step 2: Detect file overlaps → form task groups

Tasks sharing any file belong to the same group (union-find on file overlap):

```
Group A: Task 1, 3 (share src/foo.ts) → run sequentially within group
Group B: Task 2 (independent)
Group C: Task 4 (independent)
→ Groups A, B, C run in parallel (one sub-agent per group)
```

If every task lands in one group, implement it inline in this session, sequentially; spawn no sub-agents. The inline lane also runs inline, after the parallel groups finish.

#### Step 3: Order tasks within each group

Sort by dependency: types/interfaces first → implementations with their tests (with TDD mode on, each test comes first) → integrations.

#### Step 4: Safety check for parallel execution

Before spawning parallel sub-agents, verify each of these conditions per group pair:

- [ ] No shared files between groups (already guaranteed by grouping)
- [ ] No shared DB tables where one group writes and another reads
- [ ] No shared external state (same API endpoint mutations, same queue, same cache key)
- [ ] No ordering dependency (Group B's code doesn't import types Group A is creating)

If all conditions pass → spawn sub-agents immediately.
If any condition fails → merge the conflicting groups into one sequential group, re-check remaining groups. Do not ask the user to confirm the merge; state what was merged and why in the execution log, then proceed.

#### Step 5: Produce execution plan

```
Parallel Groups:
  Group A (agent-1): Task 1 → Task 3 [src/foo.ts, src/foo.test.ts, src/baz.ts]
  Group B (agent-2): Task 2 [src/bar.ts]
  Group C (agent-3): Task 4 [src/qux.ts]

Inline: Task 5 (files unknown until explored)
Sequential follow-up: (none / list cross-group integration tasks)
TDD mode: on / off
```

Log the execution plan for transparency, then spawn immediately. No confirmation gate.

### Phase 3: Execute

Whoever runs a task (you inline, or the sub-agent for its group) follows:

1. **Explore**: read target files, understand current state, inspect related code, check the types/interfaces the task needs.
2. **Implement**: write the code, following TDD mode when it is on. Follow project conventions from CLAUDE.md if it exists. If not, infer conventions from existing code style in the files being modified.
3. **Validate**: after meaningful changes, run lint and the tests that cover the files you changed, and fix failures immediately. A sub-agent never runs the project-wide build or type-check: other groups' half-written files make them fail. Inline work may run them. Phase 4 runs both, and the full suite, once every group has finished.

**Parallel execution rules:**

Spawn every group that passed the Phase 2 Step 4 check in one message with multiple tool calls; that is what makes them run concurrently. Issuing them one per message serialises the work.

- **Max 6 concurrent sub-agents.** If task groups exceed 6, queue the remainder and start each queued group as a running group completes.
- One sub-agent per task group (from Phase 2), not per individual task
- Tasks within a group run sequentially (shared files)
- Groups run in parallel (no file overlap between groups)
- A sub-agent cannot see this skill. Its prompt carries the plan file path (if any), its group's tasks and file list, relevant blocker findings, and, verbatim: the Shared Worktree rules, Phase 3 steps 1-3, the TDD mode section with whether it is on, and the Agent Report template

**User changes direction mid-execution:**

- Stop queued and running groups the change touches; let unaffected groups finish.
- Show the delta before touching code: tasks added, dropped, or changed, and already-written code the change makes wrong.
- After the user confirms, edit the plan file in place so a fresh session can execute from it alone: mark dropped tasks as dropped (keep them visible), add new tasks, rewrite changed ones. Each new or changed task names its files and functions and a checkable done criterion. Keep the file's existing format and change only the affected lines; update a status field only if the plan already has one. Never stage it; `docs/` belongs to the user.
- Re-run the Phase 1 blocker scan on the changed tasks only, then continue.

**TDD mode:**

Off by default. On when the arguments contain `tdd`, the user asks for TDD, or the plan says to use it.

- **On:** for each task that adds or changes behavior, write the test first, run it, and see it fail on the missing behavior, not on a typo, a bad import, or broken setup. Then implement until it passes. Refactor, config, and docs tasks skip the failing run.
- **Off:** implement first, then add or update tests for new behavior and a regression test for each bug fix, when test infrastructure exists. If none exists, note it; don't create it unless the user asks.

In either mode a test must fail when the behavior it covers is removed. Never write a test that asserts whatever the code currently returns, and never delete, skip, or loosen an existing test to get green. Change an existing test only when the plan changes the behavior it covers, and say so in the report.

**Per-agent result reporting:**

Each sub-agent must return a structured report upon completion:

```
## Agent Report: Group X

### Tasks completed
- [x] Task N: description

### Files modified
- path/to/file.ts: what changed

### Validation
- Lint (own files): PASS/FAIL
- Tests (covering own files): PASS/FAIL/N/A
- TDD failing runs (TDD on): test name → failure seen

### Issues encountered
- (none / description + resolution)
```

Collect all agent reports before proceeding to Phase 4. If any agent reports FAIL, resolve before continuing.

**Error handling during execution:**

- Build failure → fix root cause, not suppress
- Test failure → investigate, fix, re-run
- Discovery that invalidates plan or scope creep → see Decision Framework
- Ambiguous requirement → see Decision Framework
- Conflicting changes from parallel agents → stop both agents, present the conflict and both proposed changes to the user, wait for resolution before continuing
- Cascading failures / Blocked agent → if a sub-agent is blocked or fails unrecoverably, let running agents finish but do not spawn new parallel agents. Stop and report to the user.

### Opportunistic Sub-Agents

Beyond task-group parallelism, sub-agents are worth spawning for:

- **Read-only work**: reading unrelated modules, running typecheck/lint/tests, researching an unfamiliar API. Safe by construction; no user approval needed.
- **Writes to disjoint files**: test writing across independent modules, doc/schema generation alongside unrelated code. Apply the Phase 2 Step 4 check first; watch for shared test fixtures and shared imports.

### Phase 4: Verify

Final gate after all tasks executed:

1. Run the full build; it must succeed
2. Run the full test suite; it must pass
3. Cross-check every plan item against actual changes
4. Run the `arc-kit:verifier` skill for review

**Report format:**

```
## Execution Summary

### Completed
- [x] Task 1: description
- [x] Task 2: description

### Build: PASS / FAIL
### Tests: PASS / FAIL / N/A

### Issues Found & Fixed
- Issue description → fix applied

### Remaining / Deferred
- Task N: reason deferred
```

### Phase 5: Git Commits & Rules

**Guard:** Verify workspace is a git repository (`.git` exists) before this phase. If not a git repo, skip.

Commit only here, after Phase 4 passes and the user approves or asks for it; never during execution, never on a broken build.
Default to a single cohesive commit per plan. If the plan spans logically separable units (e.g., migration + feature code), propose commit boundaries to user for approval.

**Format:** `type(scope): short summary`, then a `-` bullet body grouping related changes. Summary length cap and allowed types come from the project's CLAUDE.md (`${CLAUDE_PROJECT_DIR}/CLAUDE.md` or `${CLAUDE_PROJECT_DIR}/.claude/CLAUDE.md`); without one, match the style of `git log --oneline -20`.

**Rules:**

- The message summarizes the entire plan's execution
- Never commit secrets or credentials: before staging, verify the file is not `.env`, `*.key`, `*.pem`, `credentials.json`, etc.
- Stage by explicit path, only files this session edited; `git add .`, `git add -A` and `git commit -a` sweep in other sessions' work
- Run `git diff --cached` to review staged content before committing


## Decision Framework

When encountering choices during execution, **self-verify before escalating to user:**

- **Can you resolve it from codebase or plan context?** (grep, read files, check existing deps, re-read plan) → Resolve it yourself, state your reasoning, move on.
- **Is it a judgment call, trade-off, or scope decision?** → Ask the user.

Decision types:

- **Multiple valid approaches**: Pick the one most consistent with existing codebase patterns. Only AskUserQuestion if trade-offs are genuinely ambiguous.
- **Quick fix vs proper fix**: Never apply a workaround silently. Take the proper fix without asking when it is small or obvious. Ask with AskUserQuestion only when it costs far more than the workaround (a large refactor, or changes outside the plan's files) or the trade-off is genuinely ambiguous, and then show both: `Proper fix: X (effort). Workaround: Y (debt it creates).`
- **Missing requirement detail**: Check if the plan, design doc, or codebase answers it first. AskUserQuestion only if genuinely unresolvable.
- **Plan step seems unnecessary**: Flag to user, don't skip silently
- **New dependency needed**: Check if an existing dep already covers the need. If so, use it. If truly new, check with user before adding.
- **Scope creep detected**: Flag, let user decide to include or defer

## Anti-Patterns

- Silently deviating from the plan
- Using `--no-verify` or `--force` without explicit user approval
- Skipping Phase 4 verification because all agent reports returned PASS
- Spawning a sub-agent for a single-file edit or a one-command check: the spawn overhead exceeds the work