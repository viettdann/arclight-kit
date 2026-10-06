---
name: verifier
description: "Verify this session's finished work against the requested scope, then review reuse, contracts, quality, efficiency, correctness, security, tests, and documentation. Use for review my work, check before commit, did I miss anything, review lại, kiểm tra lại code vừa làm, trước khi commit, or sót gì không. Report findings for review-only requests; fix within existing implementation or cleanup authorization. Not for someone else's PR."
---

# Verifier: Completeness Check and Code Review

Before reviewing changes, read `references/review-and-fixes.md` for review and fix rules and the report template. Review-only requests remain read-only; authorized implementation or cleanup includes scoped fixes.

Phase 0 confirms every planned or requested task was done; Phases 1-2 review the changed code and fix it within the authorized scope. Completeness runs first even when the user asks only for a code review: tasks get dropped silently through context truncation, interruptions, or oversight, and reviewing the code that exists never surfaces the code that does not.

Use Vietnamese in chat and English in files unless requested otherwise. Follow applicable AGENTS.md files. Resolve `references/` and `scripts/` paths relative to this `SKILL.md`; run scripts by their absolute installed path from the project root.

## Phase 0: Completeness Verification

Establish what was supposed to happen, then check it against what actually changed. Run this phase yourself: the conversation is already in your context, and a plan file is short.

### Step 1: Identify the source of truth

1. **Plan file**: most reliable, not subject to truncation. Use the plan file named with the request or earlier in this conversation. Without one, search for `plan.md`, `PLAN.md`, `TODO.md`, `tasks.md`, `checklist.md`, `*.todo`, and design docs under `docs/plans/`, and use one only when it describes this session's work (it names files this session edited or that `git status --short` lists); with more than one match, ask which. Never take tasks from other files that happen to hold checkboxes: handoff notes, READMEs, changelogs.
2. **Conversation history**: ad-hoc requests, mid-stream changes, and corrections that never reached a plan file. With both (the common case), the plan file is the baseline and the conversation carries additions and modifications; a recent user instruction overrides stale plan text. Earlier suggestions are not requirements unless accepted.

### Step 2: Extract the full task list

Read the plan file, if any, and list every discrete task or requirement, noting anything marked deferred, skipped, or out of scope. Then scan the conversation for requests, corrections, and mid-stream additions the plan file lacks. Requests that interrupted or redirected ongoing work are the highest-risk source of dropped tasks, so call those out explicitly.

Tag each task with its origin (`plan` or `conversation`).

### Step 3: Establish the diff and verify each task

The worktree is shared: uncommitted changes in files this session never edited belong to the user or another session. Leave them out of the diff and never edit them.

The in-scope paths are the files the user named or this session edited. In a fresh session (a new thread, or resuming from a handoff) that list is empty: use the files the plan names, and when it names none, show `git status --short` and ask which files are in scope. Outside git, past 10 files, ask which ones to review.

When this session committed any of its work, find its base: read `git log -10 --format='%h %ar %s'`, identify the oldest commit belonging to this session, and confirm that boundary from the task context, asking the user when it stays ambiguous; never guess how many commits are yours, since commits from an earlier session look identical from here.

Then run `sh scripts/collect-diff.sh [--base <oldest>~1] <paths>`. It writes the uncommitted changes (or, with no `--base` and nothing uncommitted, the commits not yet pushed), every untracked file, and outside git the whole files, to one temp file, and prints its path (`<diff>` below). Phase 1 reviews from it; when Phase 0 edits code, rerun the script and use the new path. Delete each `<diff>` after the summary. Exit 2 means nothing in scope changed: stop and ask the user for a review scope rather than reviewing nothing.

Merge the Step 2 lists, deduplicate, then mark each task against the diff:

- `done`: the diff satisfies the requirement
- `partial`: changes exist but fall short, for example a file created without its key logic, or an API route whose handler is still a stub
- `wrong`: changes address the task but behave differently from what it asks (filters on the wrong field, returns 200 where the plan says 404); quote the requirement
- `changed`: a different approach from the one the plan describes that still meets its goal; name the difference
- `missing`: no corresponding changes
- `unclear`: cannot be decided from the diff, or the diff takes one reading of an ambiguous requirement (sort order, default value, inclusive or exclusive bound); state the reading taken
- `unverifiable`: the task is state outside the repository (DNS records, env vars in a hosting dashboard, an OAuth allowlist, a file in another repo that isn't on disk); name the manual check the user must make

Code that handles a deliverable is not the deliverable: a parser for a config file is not the config file, a migration runner is not the migration. When torn between `done` and `unverifiable`, pick `unverifiable`.

Then mark changes in the diff that no task covers as `extra`: unrequested features, options, abstractions, or files. Changes a task needs in order to work (a helper it calls, a migration, its tests) are not extra.

Verify non-code tasks (config changes, file moves, deletions) directly against the filesystem rather than the diff. Run each behavioral assertion in the plan ("returns 404", "command X prints Y") and compare the output; never mark one `done` from reading the diff. When it can't run here (no server, no credentials), mark it `unverifiable` with the command to run.

### Step 4: Report and decide

If every task is `done`, `changed`, or `unverifiable` and nothing is `extra`, say so, naming each `changed` difference and each `unverifiable` manual check, and continue to Phase 1.

Otherwise report the gaps with evidence:

> - [missing] Task X: no corresponding changes found
> - [partial] Task Y: file created, logic incomplete
> - [wrong] Task W: "only active users" but the query filters on `deletedAt`
> - [unclear] Task Z: "sort by date" implemented newest first; intended order?
> - [extra] path/to/file: caching layer no task asks for

During authorized implementation or cleanup, complete clear in-scope `missing` and `partial` tasks and correct each `wrong` one without asking again. For a review-only request, report them without editing. Ask about each `unclear` reading and each `extra` (keep or remove), one question per item, with `request_user_input` when available in the active mode, otherwise in text; continue reviewing independent areas meanwhile. Never remove an extra or someone else's addition without the user's answer, and never skip missing work silently.

## Phase 1: Review the changes

After completeness verification, follow `references/review-and-fixes.md` for all five review areas, evidence and severity rules, deduplication, authorized fixes, validation, and the verification summary. Keep completeness results separate from code-review findings.
