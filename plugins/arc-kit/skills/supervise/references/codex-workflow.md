# Supervise

Resolve bundled paths from the parent skill directory containing SKILL.md, including paths in references; resolve target project paths from the project working directory. Before a shell command, resolve bundled script paths to absolute paths and quote them. Follow project AGENTS.md and the active runtime's instructions, tools, permissions, and concurrency limits. Existing user authorization persists across discovery, implementation, and review; ask only about unresolved scope or actions outside it. Use available question tools for preferences, or ask in chat when unavailable. Delegate only when allowed and supported; otherwise run the same checks inline and report when an independent review was unavailable. Inherit the session model unless the user explicitly requests model routing and the runtime supports it. Do not assume named plugin agents, fixed model names, or a fixed worker count.

Load the plan, split it into scoped packets, and judge every result against acceptance criteria. Delegate implementation when allowed; model routing is optional and requires user-requested, supported model selection.

Workers are interns, you are the senior. They edit only what you hand them, run only read-only git (the worker brief requires this; Codex hook enforcement is unavailable), and bring every problem outside their files back to you. You decide, or ask the user.

## Worker routing

Use the active runtime's supported delegation tools and model options. Inherit the session model by default. Only route to other models when the user requests it and those models are exposed by the runtime; never translate provider model names by guesswork. Classify work as mechanical, ordinary implementation, or complex/risky to choose scope and review depth. Escalate by tightening the packet, increasing review depth, or using a supported model within the user's constraints. If model selection is unavailable, use inherited-model workers and state that cost-tier routing was not exercised. If delegation is unavailable or prohibited, execute groups inline and state that independent review was unavailable.

Worker brief: `../executor/references/worker.md`. Reviewer brief: `../executor/references/reviewer.md`. These are instructions to include in a worker assignment, not installed custom agents. Workers run only read-only git and never modify .git or git configuration; this is an instruction contract, not an enforced Codex agent hook.

## Progress checklist

```
- [ ] Phase 0: plan loaded, tasks and acceptance criteria printed
- [ ] Phase 1: blockers scanned
- [ ] Phase 2: groups formed, tier per group
- [ ] Phase 3: snapshot and backups taken, packets dispatched
- [ ] Phase 4: every group accepted or stopped
- [ ] Phase 5: build and tests, plan cross-check, verifier
- [ ] Phase 6: commit proposed
```

## Phase 0: Load the plan

Arguments: $ARGUMENTS

If independent review is available, use a fresh reviewer with only the packet and diff; otherwise review inline and report that limitation.

A path in the arguments is the plan file. Without one, take the first source that exists:

1. A plan file named in this conversation, or a plan written out in the conversation itself. A conversation plan needs no file; a "làm đi" after a discussion that settled what to build is enough.
2. A workspace search: `plan.md`, `PLAN.md`, `TODO.md`, `tasks.md`, `checklist.md`, and design docs in `docs/plans/`. One candidate: use it. More than one: ask which with the available user-question tool, newest first.

If none exists, stop and suggest `arc-kit:brainstorming`; you don't write the plan yourself.

A plan file is the baseline and later requests in the conversation amend it. A conversation plan is usually spread over several turns where later turns reverse earlier ones: consolidate it, the latest decision winning, into one flat task list.

Plans rarely state acceptance criteria, and workers and reviews need them. Derive one or two checkable criteria per task from the plan's intent ("`GET /orders?status=x` returns only orders in x; existing callers without `status` unchanged"). Print the task list with its criteria before Phase 1, so a misreading shows up before any code exists. Don't wait for confirmation.

Routing preferences apply only to runtime-supported models. Respect an explicit floor, ceiling, or single-model constraint. If the requested model is unavailable, report it and continue only work independent of that model choice; do not silently substitute a different provider model.

## Phase 1: Blockers

A fast scan, not deep exploration: plan contradictions, files, modules, or APIs the plan names that don't exist, external interfaces nobody has checked. Glob and Grep for the cheap checks; send wider questions to a Lookup. A blocker you can't resolve from the plan or codebase stops the run: report it and ask.

## Phase 2: Group and route

1. Map each task to the files it touches; a quick Grep or Glob usually names them. List new files too: a new file belongs to the task that creates it.
2. Find what two or more tasks would each need but doesn't exist yet: a helper, a type, a constant, a migration. Make creating it a task of its own, or give it to one task, and order every task that uses it after that one. Two workers who each need a date formatter will otherwise write two.
3. Tasks that share a file go into one group (union-find on file overlap); a group runs sequentially in one worker. Merge two groups too when one writes a table, queue, cache key, or endpoint the other reads, or when one uses something the other creates. Tasks making the same small change in different files (one rename, one added field, one import swap) may share a group without sharing a file: one worker and one review instead of one each. Say what you merged and why.
4. Order tasks inside a group: shared pieces, types, and interfaces, then implementation with its tests, then integration.
5. Pick each task's tier from the table and the Phase 0 routing preferences; a group takes the highest tier among its tasks.
6. A task whose files Grep and Glob can't name goes to a Lookup first. If the Lookup names them, group the task like any other; if not, ask the user. A worker never starts without its owned files.

Print the execution plan and start without a confirmation gate:

```
Group A  inherited model   Task 1 → Task 3   [src/orders/api.ts, src/orders/api.test.ts]
Group B  inherited model     Task 2            [src/config/flags.ts]
Group C  inherited model   Task 4            [src/billing/charge.ts, db/migrations/0042_add_charge.sql]
```

## Phase 3: Snapshot, backups, dispatch

Every step that touches the snapshot or a backup goes through `python3 "./scripts/snapshot.py"` (`snapshot` below), not shell snippets: it behaves the same under bash, zsh, and macOS, and handles paths with spaces or non-ASCII names. Paths are relative to the repository root.

**Snapshot.** Once, before the first dispatch: `snapshot take`. It records HEAD, the stash list, and hashes of every uncommitted file in the whole repository, whatever directory you run it from, and prints the run directory. Do not assume shell variables survive between tool calls, so use that printed path literally in every later command and packet (`<run>` below). Outside git it still prints a run directory and warns; `check` then reports `skipped`, and backups and diffs work as usual.

**Backups.** Before dispatching a group: `snapshot backup <run> <group> <owned files...>`, new files included, files not directories. It copies the owned files that exist into `<run>/<group>/`, keeping their paths, and records which group owns what. This is the state the group started from, including uncommitted changes that aren't this run's, and the baseline for every diff of the group's work: `snapshot diff <run> <group>` prints it, with files the backup lacks shown as new. `git diff` would count those uncommitted changes as the worker's. Workers restore from the backup; they never use git to discard anything. Backing up a file the group already owns keeps the first copy (or its absence, for a new file), so re-listing a group is safe; a file handed over from a finished group is copied as it is now, with that group's work as the new baseline.

**Packet.** A worker sees only its packet and its worker brief, never this conversation. Everything it needs goes in:

```
Goal: <one sentence, the outcome, not the steps>
Plan: <plan file path, or "none">
Tasks, in order:
  1. <task> — done when: <acceptance criteria>
Files you own: <paths, new files included>
Backup: <run>/<group>/
Diff with: python3 "./scripts/snapshot.py" diff <run> <group>
Read for context: <files and symbols worth reading first, with line numbers when you have them>
Use, don't recreate: <shared pieces another group created, with paths; or "none">
Constraints: <conventions, APIs to reuse, things not to touch, decisions already made in the plan, the plan's project-wide constraints verbatim>
Out of scope: <the plan's Out of scope lines, verbatim; or "none">
Verify with: <lint and test commands that cover the owned files>
TDD: on | off
```

For mechanical, add the exact shape of the change where you know it: the signature, the field name and type, the existing example to copy. For the supervisor, describe the problem and the constraints and leave the design to it.

**Dispatch.** Spawn every group that can run now in one message. Respect the runtime concurrency limit across workers, reviewers, and lookups together; queued work starts as running agents finish.

**Run log.** Record every dispatch, verdict, escalation, and stop: `snapshot log <run> <group> <tier> <attempt> <event>`. After a compaction, or whenever you are unsure where the run stands, `snapshot log <run>` prints it (a lost `<run>` is the newest `supervise-*` directory in the temp directory); a group the log shows accepted is never dispatched again. The Phase 5 table is built from it.

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

Rerun the worker's verify commands yourself rather than trusting the report; hand them to the test runner brief (`../executor/references/test-runner.md`) when they are slow. Don't run the project-wide build or type-check while other groups are mid-edit; their half-written files fail it. A failing gate is a failed attempt, sent back with the output and no review; a failing test whose file and the code it runs the group's diff doesn't touch doesn't fail the gate, it goes to the Phase 5 report.

### Review

Read the group's diff (`snapshot diff <run> <group>`), the packet, and the worker's report.

- Up to about 150 changed lines: review it yourself against the checks and verdicts in `../executor/references/reviewer.md`, so inline and delegated reviews judge by the same rules.
- Larger: spawn a reviewer following `../executor/references/reviewer.md` with the packet (backup path included), the owned files, and the worker's report. Spawn reviewers for several groups in one message.

Every diff is reviewed, small ones and mechanical ones included: the failures that matter here pass their tests (an invented helper where one exists, a criterion read the wrong way, a test that asserts whatever the code returns).

A worker that disagreed with a finding gets a ruling from you: accept its reason and drop the finding, or keep the finding and say why.

Before sending a `fix` back, run `snapshot mark <run> <group>`. The next review of the group is then a fix round: the reviewer gets the earlier findings and `snapshot diff <run> <group> --since-review`, rules on each finding, and looks for new problems only in that fix diff (the fix round in `reviewer.md`). Problems it lists outside the fix go back to the same worker with the next message, or to the verifier, and never count as a failed attempt. The review after an escalation or a `rewrite` is a full review again.

`accept` closes the group. Keep its backup until Phase 5: the verifier may still send the group's files back. `fix` and `rewrite` are failed attempts.

### Continuing a worker

Send the answer or the findings to the same worker with the runtime’s worker messaging tool, so it keeps its context. If that fails, spawn a new worker at the same tier with the packet plus the answer, or the packet, the current diff, and the findings.

### Escalation

A failed attempt is a `failed` report, a failing gate, or a `fix` or `rewrite` verdict. Each group gets two attempts per tier.

- `failed`, a failing gate, or `fix` with an attempt left: continue the worker with the output or the findings.
- After two failed attempts, tighten the packet and review depth, or escalate to a user-authorized supported model within the routing limits. Carry forward the current diff and every finding.
- `rewrite`: explain why local fixes are insufficient. Restore only the group's owned files from its backup when no foreign edits landed, then restart within the authorized routing limits.
- After two further failed attempts, or if no allowed escalation exists, stop the group and report its diff, findings, and backup path. Independent groups may continue.


## Phase 5: Verify

Once every group is accepted or stopped:

1. Build and test what the change can break: nothing for a change that can't alter behavior (docs, comments, Markdown, formatting only); otherwise the full build and type-check, plus the tests covering the touched files, or the full suite through the test runner brief (`../executor/references/test-runner.md`) when the change reaches shared code, a public contract, config, dependencies, or build files, or those tests can't be named.
2. A failing test whose file and the code it runs the final diff doesn't touch is reported as not from this run, with that evidence, and fixed only when the plan covers it.
3. Cross-check every plan task against the final diff; tasks in stopped groups are listed as not done.
4. Read and follow the installed skill `arc-kit:verifier`; it reviews the change across groups, which per-group reviews can't see.
5. Delete `<run>` when no group was stopped; otherwise keep it and name it in the report.

Then report:

```
## Supervise Summary

| Group | Tasks | Tier path | Attempts | Result |
|---|---|---|---|---|
| A | 1, 3 | inherited | 1 | accepted |
| B | 2 | inherited; packet refined | 3 | accepted |
| C | 4 | inherited; deeper review | 4 | stopped |

Build: PASS / FAIL    Tests: PASS / FAIL / N/A

### Decided for you
- decision taken → alternative not taken

### Stopped or deferred
- Group or task: reason, last findings, backup path
```

The tier path column is how routing gets tuned: mechanical groups that keep escalating mean its share should shrink.

## Phase 6: Commit

Skip outside a git repository. Propose one commit for the plan, or boundaries when the plan has separable units, and commit after the user approves. Follow the project's AGENTS.md for the message format, else the style of `git log --oneline -20`. Stage by explicit path, only files this run edited, never secrets (`.env`, `*.key`, `*.pem`, `credentials.json`), and read `git diff --cached` before committing.

## Rules for you

- The worktree is shared with the user and other sessions. Edit only what this run owns, leave uncommitted changes you didn't make alone, and never run `git stash`, `reset`, `revert`, `checkout --`, `restore`, or `clean` unless the user asks for that exact operation. While any worker is running, don't run anything that changes git state at all: a stash would sweep up their half-written files.
- Resolve what the plan or codebase answers yourself, and list it under "Decided for you" with the alternative not taken.
- Ask the user about scope changes, a plan step that looks wrong, a new dependency, or a trade-off the plan doesn't settle.
- Irreversible actions (data deletion, schema drops, external publishes, force operations) are always asked, never decided by you or a worker.
- The user changing direction mid-run: stop the groups the change touches, show the delta, and after confirmation update the task list and re-route only the changed tasks.