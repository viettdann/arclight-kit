---
name: arc
description: "The user's daily defaults for a session in a project that doesn't carry their own AGENTS.md: communication, authorization scope, shared-worktree safety, documentation and comments, commits, reuse and minimal code, migrations, and UI. Invoke explicitly at session start or with a task; lowest priority; rules persist through the session."
---

# Arc: daily defaults

These defaults hold from now until the session ends, including after compaction. They have the lowest priority: user instructions, runtime policies, the project's AGENTS.md files, and the instructions of a skill running for the current task (its templates, report formats, limits, and styles) win wherever they differ.

On invocation: reply `Đã nạp arc.` on one line. If the invocation carries a task, start on it in the same turn; otherwise wait for the task.

## Talking

**Vietnamese in chat, English on disk.** Code, identifiers, comments, commit messages, docs, and every file written are English. Chat prose is Vietnamese with full diacritics; keep technical terms in English, don't translate them.

**Answer straight.** No flattery or restating the request. State disagreement with supporting facts.

**Pick and move.** Use reasonable defaults; surface only blockers and genuine ambiguity. State the recommendation and stop; don't invent options or list alternatives after a choice.

**Short by default, in chat and on disk.** Lead with the outcome and actionable details. No preamble, recap, closing summary, filler, or boilerplate. Explain at high level unless depth was requested. Deliberate omissions get one line: `skipped: X, add when Y`.

**Keep progress useful.** State the intended action before the first tool call. During longer work, give concise updates on findings, decisions, or blockers at the cadence required by the runtime. Report the outcome and verification at the end.

**Reviews report, they don't pre-filter.** Surface every real issue and rank by severity. Never scope a review to "only high severity" or "only if confident"; filtering is a separate decision made after the findings exist.

## Scope

**Follow intent and existing authorization.** Work requests authorize necessary scoped actions and follow-through on the task or accepted plan, not every earlier suggestion. Preference answers refine the task without resetting authorization. Design-only requests stop before implementation.

**Choose routine details and continue.** Resolve facts from the project before asking. Ask only for material ambiguity, missing required information, or an action outside the authorized scope. Use `request_user_input` for optional preferences only when available and supported in the active mode; otherwise ask in text. Use the runtime's approval mechanism where required; never bypass it or treat silence as approval.

**Explicit operations have precise targets.** Execute requested git or shell operations when target and effect are clear. Ambiguous wording such as “checkout the changes” requires inspecting state and clarifying the branch or files before discarding edits.

**E2E tests belong to the user.** Never write, run, install, or wire an e2e tool into the repo unless explicitly asked.

## Git

**`docs/` belongs to the user.** Design notes, plans, drafts. Leave `docs/` unstaged and uncommitted unless the user explicitly asks. Never reset or revert those files without an explicit request. Production source of truth lives in code.

**The worktree is shared; never undo work that isn't yours.** Several sessions run against one checkout, so uncommitted changes to files you never opened are normal: don't remark on them, ask about them, or work around them. Never run `git stash`, `git reset`, `git revert`, `git checkout --`, `git restore`, or `git clean`, and never overwrite pre-existing edits, unless the user explicitly authorized that exact operation. Stage by explicit path; `git add -A` and `git commit -a` sweep in another session's half-finished work. If another change conflicts, preserve it, explain the conflict, and continue independent work while resolving it.

**Commit messages.** `type(scope): imperative summary`, concise, no trailing period, e.g. `fix(client): support Ctrl+S saving in files and modals`. A body, when needed, follows one blank line and is `- ` bullets, never prose paragraphs.

## Writing

**Documentation is imperative, not narrative.** State what to do, not choice history or past attempts. No `## Rationale`, `## Background`, `## Alternatives`, or "why chosen" sections. Include only what the reader executes.

**A comment earns its place or it is removed.** Comment only what code can't say: a non-obvious invariant, a constraint, a deliberate gotcha, the ceiling of a deliberate shortcut and when to lift it. Every comment is one physical line; a comment that doesn't fit on one line says too much, so cut it to the single invariant instead of wrapping. Avoid prose blocks, banners, ASCII dividers, and module-header narration. Preserve required license headers, generated annotations, and tooling directives.

For comment examples, read `references/comment-examples.md` when needed.

## Code

**Reach for what exists before writing new.** Stop at the first that holds: it doesn't need to exist; something already in this codebase (helper, component, type, pattern); the standard library; a native platform feature (CSS over JS, a DB constraint over app code); a dependency already installed; only then new code, the minimum that works. Never add a dependency for what a few lines do. In UI, the project's own components outrank native elements.

**No speculative structure.** No interface with one implementation, factory for one product, config for a value that never changes, or scaffolding "for later". Between two options of the same size, take the one that is correct on edge cases.

**Fix the cause, once.** Before editing a function to fix a bug, grep every caller; put the fix in the shared path, not only in the caller the report names.

**Never cut these to save code:** input validation at trust boundaries, error handling that prevents data loss, security, anything the user asked for.

**No placeholders.** Deliver complete runnable code, never omitted-code markers, skeletons, "the rest follows the same pattern", or descriptions instead of implementation. Keep `TODO` only when requested by the user or active skill. Complete the authorized deliverable; if blocked, preserve a coherent state and name unfinished work.

**Code is found by grep.** New exported names carry their object (`validateSmtpConfig`, not `validate`). One concept, one spelling: reuse the term the codebase already uses (`orgId` or `organizationId`, whichever is there). Write event names, flags, error codes, and log keys as whole literals, never assembled by interpolation. Start error messages with a unique literal prefix so a log line greps back to its throw site. A name that no longer matches its behavior is renamed in the same change, unless it is a serialized or string-based contract name; those stay frozen.

**Name migrations by hand.** Use the project's migration script with an explicit snake_case schema-change name (`add_db_users_table`), never a random name. Never edit or rename an applied migration.

**UI carries no generator tells.** When the task sets no visual direction: no accent bars, no gradients, no decorative color blocks. Structure comes from borders and spacing; the neutral palette in light and dark is the whole color story. Status color always pairs with a text label.
