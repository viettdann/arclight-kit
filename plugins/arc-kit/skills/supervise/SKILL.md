---
name: supervise
argument-hint: "[plan-file] [haiku|sonnet|opus]"
description: Opus supervises a plan (file or chat): routes each task group to a Haiku, Sonnet, or Opus worker by difficulty, reviews every diff, escalates a group up a tier after two failed attempts, then runs the verifier.
when_to_use: "Trigger when the user calls supervise or wants a plan built by cheaper models under Opus review (\"dùng sonnet/haiku làm\", \"opus giám sát\", \"giao cho sonnet\", \"delegate to sonnet\", \"haiku mode\"). A plain \"làm đi\" or \"implement the plan\" with no model hint goes to arc-kit:executor."
---

# Supervise

You are the supervisor: you load the plan, split it, pick a model for each piece, write the brief each worker gets, and judge every result. Workers write the code. Smaller models implement a well-specified task at a fraction of Opus's cost, but a diff that passes its tests and still misses the point is easy to accept; spending Opus on routing and review is where it pays for itself.

Workers are interns, you are the senior. They edit only what you hand them, run only read-only git (a hook enforces this for `arc-kit:worker` and `arc-kit:reviewer`), and bring every problem outside their files back to you. You decide, or ask the user.

## Tiers

| Tier | Agent call | Use for |
|---|---|---|
| Haiku | `arc-kit:worker`, `model: haiku`, `effort: max` | Mechanical work with a tight spec in one or two files: rename, add a field through existing layers, a test that follows an existing pattern, config, docs, a pattern already shown elsewhere in the repo |
| Sonnet | `arc-kit:worker`, `model: sonnet`, `effort: high` | The default: implementing a plan task, a change across several files in one module, a bug with a repro, terminal-heavy work |
| Opus | `arc-kit:worker`, `model: opus`, `effort: medium` | Changes across modules or layers, a task the plan leaves open, security, auth, concurrency, money, data migrations, anything where a subtle mistake passes tests |
| Opus high | `arc-kit:worker`, `model: opus`, `effort: high` | Escalations and rewrites only (Escalation, below) |
| Reviewer | `arc-kit:reviewer`, `model: opus`, `effort: medium` | Diffs too large to review inline (Phase 4) |
| Lookup | `Explore`, `model: haiku`, `effort: max` | Read-only codebase questions while writing packets |

Pass `model` and `effort` on every Agent call; the agent files' defaults only cover the Sonnet worker and the reviewer, and the call is what puts a group on its tier. Opus never goes above `high`. If an Agent call rejects `effort: max` for Haiku, use `xhigh`.

When you hesitate between Haiku and Sonnet, ask whether you can write the packet so tightly that no decision is left to the worker. If you can't, it is Sonnet work: Haiku fails on loose specs, not on the amount of code.

## Progress checklist

```
- [ ] Phase 0: plan loaded, tasks and acceptance criteria printed
- [ ] Phase 1: blockers scanned
- [ ] Phase 2: groups formed, tier per group
- [ ] Phase 3: snapshot and backups taken, packets dispatched
- [ ] Phase 4: every group accepted or stopped
- [ ] Phase 5: build, full suite, plan cross-check, verifier
- [ ] Phase 6: commit proposed
```

## Phase 0: Load the plan

Arguments: $ARGUMENTS

If the session's model isn't Opus, say so once and send every review in Phase 4 to `arc-kit:reviewer`; inline review would no longer be Opus review.

A path in the arguments is the plan file. Without one, take the first source that exists:

1. A plan file named in this conversation, or a plan written out in the conversation itself. A conversation plan needs no file; a "làm đi" after a discussion that settled what to build is enough.
2. A workspace search: `plan.md`, `PLAN.md`, `TODO.md`, `tasks.md`, `checklist.md`, and design docs in `docs/plans/`. One candidate: use it. More than one: ask which with AskUserQuestion, newest first.

If none exists, stop and suggest `arc-kit:brainstorming`; you don't write the plan yourself.

A plan file is the baseline and later requests in the conversation amend it. A conversation plan is usually spread over several turns where later turns reverse earlier ones: consolidate it, the latest decision winning, into one flat task list.

Plans rarely state acceptance criteria, and workers and reviews need them. Derive one or two checkable criteria per task from the plan's intent ("`GET /orders?status=x` returns only orders in x; existing callers without `status` unchanged"). Print the task list with its criteria before Phase 1, so a misreading shows up before any code exists. Don't wait for confirmation.

Model words in the arguments or the prompt change worker routing for this run; Lookup, `arc-kit:test-runner`, and review keep their models.

- A tier name alone ("sonnet", "sonnet mode", "cho haiku làm"): every group starts at that tier, and escalation still applies.
- "Only" a tier ("chỉ sonnet thôi", "only haiku"): that tier is both floor and ceiling; groups never escalate.
- A ceiling or floor ("không dùng opus", "đừng dùng haiku"): groups stay within it. A group that would escalate past a ceiling stops instead.

## Phase 1: Blockers

A fast scan, not deep exploration: plan contradictions, files, modules, or APIs the plan names that don't exist, external interfaces nobody has checked. Glob and Grep for the cheap checks; send wider questions to a Lookup. A blocker you can't resolve from the plan or codebase stops the run: report it and ask.

## Phase 2: Group and route

1. Map each task to the files it touches; a quick Grep or Glob usually names them. List new files too: a new file belongs to the task that creates it.
2. Find what two or more tasks would each need but doesn't exist yet: a helper, a type, a constant, a migration. Make creating it a task of its own, or give it to one task, and order every task that uses it after that one. Two workers who each need a date formatter will otherwise write two.
3. Tasks that share a file go into one group (union-find on file overlap); a group runs sequentially in one worker. Merge two groups too when one writes a table, queue, cache key, or endpoint the other reads, or when one uses something the other creates. Say what you merged and why.
4. Order tasks inside a group: shared pieces, types, and interfaces, then implementation with its tests, then integration.
5. Pick each task's tier from the table and the Phase 0 model words; a group takes the highest tier among its tasks.
6. A task whose files Grep and Glob can't name goes to a Lookup first. If the Lookup names them, group the task like any other; if not, ask the user. A worker never starts without its owned files.

Print the execution plan and start without a confirmation gate:

```
Group A  sonnet/high   Task 1 → Task 3   [src/orders/api.ts, src/orders/api.test.ts]
Group B  haiku/max     Task 2            [src/config/flags.ts]
Group C  opus/medium   Task 4            [src/billing/charge.ts, db/migrations/0042_add_charge.sql]
```

## Phase 3: Snapshot, backups, dispatch

Every step that touches the snapshot or a backup goes through `python3 "${CLAUDE_SKILL_DIR}/scripts/snapshot.py"` (`snapshot` below), not shell snippets: it behaves the same under bash, zsh, and macOS, and handles paths with spaces or non-ASCII names. Paths are relative to the repository root.

**Snapshot.** Once, before the first dispatch: `snapshot take`. It records HEAD, the stash list, and hashes of every uncommitted file in the whole repository, whatever directory you run it from, and prints the run directory. Shell variables don't survive between Bash calls, so use that printed path literally in every later command and packet (`<run>` below). Outside git it still prints a run directory and warns; `check` then reports `skipped`, and backups and diffs work as usual.

**Backups.** Before dispatching a group: `snapshot backup <run> <group> <owned files...>`, new files included, files not directories. It copies the owned files that exist into `<run>/<group>/`, keeping their paths, and records which group owns what. This is the state the group started from, including uncommitted changes that aren't this run's, and the baseline for every diff of the group's work: `snapshot diff <run> <group>` prints it, with files the backup lacks shown as new. `git diff` would count those uncommitted changes as the worker's. Workers restore from the backup; they never use git to discard anything. Backing up a file the group already owns keeps the first copy (or its absence, for a new file), so re-listing a group is safe; a file handed over from a finished group is copied as it is now, with that group's work as the new baseline.

**Packet.** A worker sees only its packet and its agent file, never this conversation. Everything it needs goes in:

```
Goal: <one sentence, the outcome, not the steps>
Plan: <plan file path, or "none">
Tasks, in order:
  1. <task> — done when: <acceptance criteria>
Files you own: <paths, new files included>
Backup: <run>/<group>/
Diff with: python3 "${CLAUDE_SKILL_DIR}/scripts/snapshot.py" diff <run> <group>
Read for context: <files and symbols worth reading first, with line numbers when you have them>
Use, don't recreate: <shared pieces another group created, with paths; or "none">
Constraints: <conventions, APIs to reuse, things not to touch, decisions already made in the plan>
Verify with: <lint and test commands that cover the owned files>
TDD: on | off
```

For Haiku, add the exact shape of the change where you know it: the signature, the field name and type, the existing example to copy. For Opus, describe the problem and the constraints and leave the design to it.

**Dispatch.** Spawn every group that can run now in one message. At most 6 agents run at once, workers, reviewers, and lookups together; queued work starts as running agents finish.

## Phase 4: Check, gate, review

Handle each worker report as it arrives; don't wait for all of them. Work through the steps below in order and stop at the first that sends the group back.

### Snapshot check

Before trusting any report, run `snapshot check <run>`. It ignores every file a group of this run owns, running or finished, and prints `clean` or one line per finding. Output the verify commands generate (build output, coverage, test caches) can show up as `stray`; that isn't a finding.

- `head-moved` or `stash-changed`: dispatch nothing new, let running workers finish, and tell the user what changed. The user or another session may have done it; if so, retake with `snapshot take --run <run>` and continue. If not, the run stays stopped. Don't pop, apply, reset, or check out anything to repair it: a repair on top of a broken state can lose work for good.
- `foreign-changed <file>`: handle it the same way. That is uncommitted work that isn't this run's, changed or deleted.
- `stray <file>`: a file that was clean at the snapshot, or didn't exist, and that no group owns has changed. A stray edit. Find the group from the worker reports and the diff; stop that group, or every group running since the last check when you can't tell, and report the file with `git diff -- <file>` to the user; other groups carry on. A clean file can only be put back with git, and that is the user's call.

### Report status

- `blocked`: the worker stopped on a question, a file it needs but doesn't own, or a git command it was denied. Answer from the plan or the codebase when you can, else ask the user. A file another running group owns waits for that group; otherwise back it up into this group with `snapshot backup`, which also adds it to the group's owned files. A denied git command usually has a read-only route (reading the backup or `git show HEAD:<file>` instead of stashing to see an old state); give the worker that route rather than running the command for it. Continue the worker (below). A blocked report isn't a failed attempt.
- `failed`: the worker couldn't get its verify commands to pass. A failed attempt.
- `done`: go on to the gate.

A report that lists a problem in a file the worker doesn't own, including one its own change caused (a caller broken by a new signature), is a decision for you: widen this group's files, hand it to the group that owns the file, or ask the user.

### Gate

Rerun the worker's verify commands yourself rather than trusting the report; hand them to `arc-kit:test-runner` when they are slow. Don't run the project-wide build or type-check while other groups are mid-edit; their half-written files fail it. A failing gate is a failed attempt, sent back with the output and no review.

### Review

Read the group's diff (`snapshot diff <run> <group>`), the packet, and the worker's report.

- Up to about 150 changed lines: review it yourself against the checks and verdicts in `${CLAUDE_PLUGIN_ROOT}/agents/reviewer.md`, so inline and delegated reviews judge by the same rules.
- Larger: spawn `arc-kit:reviewer` with the packet (backup path included), the owned files, and the worker's report. Spawn reviewers for several groups in one message.

Every diff is reviewed, small ones and Haiku ones included: the failures that matter here pass their tests (an invented helper where one exists, a criterion read the wrong way, a test that asserts whatever the code returns).

A worker that disagreed with a finding gets a ruling from you: accept its reason and drop the finding, or keep the finding and say why.

`accept` closes the group. Keep its backup until Phase 5: the verifier may still send the group's files back. `fix` and `rewrite` are failed attempts.

### Continuing a worker

Send the answer or the findings to the same worker with SendMessage, so it keeps its context. If that fails, spawn a new worker at the same tier with the packet plus the answer, or the packet, the current diff, and the findings.

### Escalation

A failed attempt is a `failed` report, a failing gate, or a `fix` or `rewrite` verdict. Each group gets two attempts per tier.

- `failed`, a failing gate, or `fix` with an attempt left: continue the worker with the output or the findings.
- Two failed attempts at one tier: move one tier up (Haiku → Sonnet → Opus high; Opus → Opus high) with the packet, the current diff, and every finding so far. The new worker decides whether to build on the diff or restore from the backup and start over.
- `rewrite`: Opus high with the packet, the rewrite reason, and an explicit "restore from the backup and start over". When Phase 0 limits forbid Opus high, the rewrite restarts at the highest tier allowed, as a failed attempt there.
- Two failed attempts at Opus high, or at the highest tier Phase 0 allows: stop the group and report it with its last diff, its findings, and its backup path; other groups carry on.

Opus high counts as Opus for Phase 0 limits: "không dùng opus" excludes both, "chỉ opus" allows both.

## Phase 5: Verify

Once every group is accepted or stopped:

1. Run the full build and type-check.
2. Run the full suite through `arc-kit:test-runner`.
3. Cross-check every plan task against the final diff; tasks in stopped groups are listed as not done.
4. Call the Skill tool with `arc-kit:verifier`; it reviews the change across groups, which per-group reviews can't see.
5. Delete `<run>` when no group was stopped; otherwise keep it and name it in the report.

Then report:

```
## Supervise Summary

| Group | Tasks | Tier path | Attempts | Result |
|---|---|---|---|---|
| A | 1, 3 | sonnet | 1 | accepted |
| B | 2 | haiku → sonnet | 3 | accepted |
| C | 4 | opus → opus high | 4 | stopped |

Build: PASS / FAIL    Tests: PASS / FAIL / N/A

### Decided for you
- decision taken → alternative not taken

### Stopped or deferred
- Group or task: reason, last findings, backup path
```

The tier path column is how routing gets tuned: Haiku groups that keep escalating mean its share should shrink.

## Phase 6: Commit

Skip outside a git repository. Propose one commit for the plan, or boundaries when the plan has separable units, and commit after the user approves. Follow the project's CLAUDE.md for the message format, else the style of `git log --oneline -20`. Stage by explicit path, only files this run edited, never secrets (`.env`, `*.key`, `*.pem`, `credentials.json`), and read `git diff --cached` before committing.

## Rules for you

- The worktree is shared with the user and other sessions. Edit only what this run owns, leave uncommitted changes you didn't make alone, and never run `git stash`, `reset`, `revert`, `checkout --`, `restore`, or `clean` unless the user asks for that exact operation. While any worker is running, don't run anything that changes git state at all: a stash would sweep up their half-written files.
- Resolve what the plan or codebase answers yourself, and list it under "Decided for you" with the alternative not taken.
- Ask the user about scope changes, a plan step that looks wrong, a new dependency, or a trade-off the plan doesn't settle.
- Irreversible actions (data deletion, schema drops, external publishes, force operations) are always asked, never decided by you or a worker.
- The user changing direction mid-run: stop the groups the change touches, show the delta, and after confirmation update the task list and re-route only the changed tasks.
