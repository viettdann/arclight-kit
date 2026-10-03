# Changelog

All notable changes to `arc-kit` are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [1.3.0] - 2026-10-03

### Added

- `debug`: pins the symptom in one line, reproduces it with a command that fails now (a failure rate for intermittent bugs), checks recent changes and runs `git bisect` in a separate worktree, narrows with ranked hypotheses and the cheapest experiment that could disprove each, fixes the cause in the shared path, and keeps the repro as a regression test seen failing before the fix. Asked only why, it stops at the diagnosis.
- `research`: answers technical questions from external sources in rounds, primary sources first, with verbatim quotes for figures, dated sources, visible conflicts, a throwaway probe outside the repo when docs can't settle a deciding claim, and a report with a pick, a cited comparison table, and what to re-verify.
- `test-runner` agent (Haiku): runs a test command or the suite and returns only counts and failures, each with location, trimmed message, cause (`code`, `test`, `env`, `flaky`, `fixture`), and whether reruns pass; it never edits files.

### Changed

- `executor` runs the Phase 4 suite through `test-runner`; `refactor` hands slow baseline and verify runs to it; `brainstorming` sends library and version questions to `research`.

## [1.2.0] - 2026-10-03

### Added

- `conventions`: scans an existing codebase layer by layer (file anatomy, naming beyond the linter, cross-cutting code, errors, data and state, tests), counts each convention's variants, settles clear majorities itself and asks about real splits, then writes path-scoped `.claude/rules/conventions*.md` files with golden files, rules, and don'ts. Update mode checks the changes since the recorded sha.
- `verifier`: the efficiency agent checks React changes against `references/react-performance.md` (waterfalls, bundle, re-renders, rendering, client data, Next.js App Router), skipping memoization rules under React Compiler. It takes a plan path argument, and untracked files in scope join the diff.
- `executor`: takes a plan path argument (a conversation plan still works without a file; several matching plan files are asked about) and an opt-in TDD mode (`tdd` argument, a user request, or the plan): the test is seen failing on the missing behavior before the implementation. In either mode a test must fail when its behavior is removed, and existing tests are never skipped or loosened to get green.

### Changed

- `arc`: daily defaults with the lowest priority; the project's CLAUDE.md and the running skill's templates, formats, limits, and styles win. A direct request is a go-ahead; a go-ahead covers the open recommendations on the current topic and narrows only on an explicit limit; a task given with the invocation starts at once. `git restore` joins the banned commands, `docs/` can be staged on request, and the UI rule applies when the task sets no visual direction. `arc-compact` re-injects the priority line.
- `brainstorming`: approval writes the design doc, replies with its path, and stops. The doc has fixed sections: Goal, Design, Implementation Plan, Assumptions, Verification, Out of scope. One clearly right approach is stated alone instead of padded to 2-3 options. Examples follow the current plan format.
- `plan-auditor`: annotates audit items by reference instead of reprinting the plan (a design doc's items are its Implementation Plan lines and the claims they rest on); FAILs are fixed directly when factual and asked about when they need a decision, and the loop stops when the rest wait on the user. Injected instructions are a labelled FAIL.
- `executor`: sub-agents run lint and tests for their own files only, and the full build runs once at the end; one group, or tasks whose files are unknown, run inline; sub-agent prompts carry the TDD mode and report template.
- `verifier`: reviews this session's own work and says it applies fixes; plan files come from the argument, the conversation, or a match on the diff, never from other checkbox files; a fresh session takes its scope from the plan or asks; a comment stating a shortcut's ceiling is kept.
- `brainstorming`, `plan-auditor`, `executor`: one rule for proper fix versus workaround.

## [1.1.0] - 2026-10-03

### Added

- `arc` code rules: reuse before writing (codebase, stdlib, native platform, installed dependency, then new code; project components outrank native elements in UI), no speculative structure, fix a bug in the shared path after grepping every caller, and a list never cut to save code (trust-boundary validation, data-loss error handling, security, anything requested). Skipped work is reported as `skipped: X, add when Y`; a comment may state a shortcut's ceiling.
- `arc-compact` hook (`SessionStart` on `compact`): re-injects the `arc` rules after compaction when `/arc-kit:arc` was typed earlier in the session.
- `verifier`: the reuse agent flags code the stdlib, a native platform feature, or an installed dependency covers, and a dependency added for what a few lines do; speculative abstraction covers constant config and scaffolding for later; correctness flags a fix applied in one caller while others keep the defect; fixes never remove trust-boundary validation, data-loss error handling, or security checks.

## [1.0.0] - 2026-10-03

First release.

### Added

- `/arc-kit:arc`: session working rules (chat language, scope of a go-ahead, shared-worktree git, docs, comments, commits, migrations, UI), including no placeholders in code and names and strings findable by grep.
- Workflow: `brainstorming` (design dialogue, approval gate, design doc in `docs/plans/`), `plan-auditor` (stress-tests a plan before execution), `executor` (implements it with TDD, sub-agents, and continuous verification), `verifier` (completeness check against the plan, then parallel review for reuse, quality, efficiency, correctness and security, comments, and docs), `handoff` (session handoff file instead of `/compact`).
- `refactor`: pins behavior with characterization tests, maps the contract surface and its consumers, and moves in small verified steps; wide scopes stop for approval first.
- `fresh-air` blocks a project's own skills, commands, and `CLAUDE.md`, and restores them; the `comment-lint` hook flags wrapped, overlong, banner, and narrative comments.
