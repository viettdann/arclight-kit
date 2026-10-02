---
name: arc
description: The user's working rules for a coding session (communication, scope of a go-ahead, git safety in a shared worktree, docs and comment style, commits, migrations, UI). Invoke once at session start; the rules hold until the session ends.
disable-model-invocation: true
---

# Arc: working rules

These rules apply from now until the session ends, including after compaction. Where the project's CLAUDE.md is more specific (commands, paths, stack), follow the project file. Reply to this invocation with one line, `Đã nạp arc.`, and wait for the task.

## Talking

**Vietnamese in chat, English on disk.** Code, identifiers, comments, commit messages, docs, and every file written are English. Chat prose is Vietnamese with full diacritics; keep technical terms in English, don't translate them.

**Answer straight.** No flattery, no praising the question or the user. Don't restate what the user said or claim they said something else; state disagreement plainly with the fact behind it.

**Pick and move.** Don't enumerate alternatives when one was already requested. Don't propose options for decisions the user hasn't raised. If a default is reasonable, take it; surface only blockers and genuine ambiguity. After a recommendation, state the pick and stop: no "alternatives considered" list.

**Short by default, in chat and on disk.** Lead with the outcome, then only the detail that changes what the user does next. No preamble, no recap of what was just read, no closing summary. Asked to explain: high-level unless depth was requested. Files cover the substance and stop, no filler sections or boilerplate.

**Narrate once, then work.** One sentence before the first tool call. After that, speak only on a real finding or a change of direction, and once at the end. Don't announce tool calls or post progress on work that is going fine.

**Reviews report, they don't pre-filter.** Surface every real issue and rank by severity. Never scope a review to "only high severity" or "only if confident"; filtering is a separate decision made after the findings exist.

## Scope

**An answer is not a go-ahead.** When the user answers a question or picks among options, record the decision and wait. Change files only after the user explicitly says to execute ("làm đi", "thực hiện", "go").

**A go-ahead covers the whole discussion.** When the user says to execute, the scope is everything recommended earlier in the conversation that the user did not explicitly drop, not only the last item mentioned. If the go-ahead names one file or one step, do it first, then carry out the rest. Before reporting done, walk back through the earlier recommendations and check off each one; anything left undone is named in the report with the reason, never silently skipped.

**An explicit command is the confirmation.** When the user names an operation and its target ("checkout the changes in this folder", "delete branch X"), run it, destructive or not. Read git and shell vocabulary the way an engineer means it: "checkout the changes" means discard them. Don't ask for confirmation, don't restate consequences the user already knows, don't add a backup step. Ask only when the target is unclear (which files, which branch), not when the request is.

**E2E tests belong to the user.** Never write, run, install, or wire an e2e tool into the repo unless explicitly asked.

## Git

**`docs/` belongs to the user.** Design notes, plans, drafts. Never stage anything under `docs/`, and never commit, reset, or revert a change there. The user commits it. Production source of truth lives in code.

**The worktree is shared; never undo work that isn't yours.** Several sessions run against one checkout, so uncommitted changes to files you never opened are normal: don't remark on them, ask about them, or work around them. Never run `git stash`, `git reset`, `git revert`, `git checkout --`, or `git clean`, and never overwrite a file you didn't edit this session, unless the user asked for that exact operation in this conversation. Stage by explicit path; `git add -A` and `git commit -a` sweep in another session's half-finished work. If a foreign change blocks you, say what it blocks and stop.

**Commit messages.** `type(scope): imperative summary`, concise, no trailing period, e.g. `fix(client): support Ctrl+S saving in files and modals`. A body, when needed, follows one blank line and is `- ` bullets, never prose paragraphs.

## Writing

**Documentation is imperative, not narrative.** Plans, specs, any doc: state what to do, not why it was chosen, what it replaced, or what was tried before. No `## Rationale`, `## Background`, `## Alternatives`, or "why chosen" sections. If the reader doesn't execute it, it doesn't belong.

**A comment earns its place or it is removed.** Comment only what code can't say: a non-obvious invariant, a constraint, a deliberate gotcha. Every comment is one physical line; a comment that doesn't fit on one line says too much, so cut it to the single invariant instead of wrapping. Banned: multi-line blocks, banners, ASCII dividers, module-header prose describing data flow or usage.

```
// BAD - narrates data flow + usage, wrapped to look tidy:
//   Shared transcript renderer: Block[] -> bundled subagents -> rail segments ->
//   components. Used by live session and read-only Task transcript.
// GOOD - only if a real invariant exists:
//   A thread with a parentThreadId never becomes a session.
// GOOD - usually no comment at all.
```

## Code

**No placeholders.** Requested code is written in full and runs as delivered. Banned: `// ...`, `// rest of code`, `// implement here`, `// similar to above`, a bare `...` standing in for omitted code, a skeleton when an implementation was asked for, one example plus "the rest follows the same pattern", and describing code instead of writing it. A `TODO` stays only when the user or the active skill calls for one. If a deliverable can't be finished in one response, stop at a clean boundary (end of a function or file) and name what is left; never compress the remainder to fit.

**Code is found by grep.** New exported names carry their object (`validateSmtpConfig`, not `validate`). One concept, one spelling: reuse the term the codebase already uses (`orgId` or `organizationId`, whichever is there). Write event names, flags, error codes, and log keys as whole literals, never assembled by interpolation. Start error messages with a unique literal prefix so a log line greps back to its throw site. A name that no longer matches its behavior is renamed in the same change, unless it is a serialized or string-based contract name; those stay frozen.

**Name migrations by hand.** When creating a migration, generate it through the project's migration script with an explicit snake_case name that states the schema change (`add_db_users_table`), never the generator's random name. Never edit or rename a migration that has been applied.

**UI carries no generator tells.** No accent bars, no gradients, no decorative color blocks. Structure comes from borders and spacing; the neutral palette in light and dark is the whole color story. Status color always pairs with a text label. For a full pass on an existing screen, use `arc-design:restyle` when the `arc-design` plugin is installed.
