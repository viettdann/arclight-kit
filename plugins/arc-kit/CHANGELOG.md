# Changelog

All notable changes to `arc-kit` are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [2.1.0] - 2026-10-04

Brings the Codex package up to the Claude line's 1.7.0. Authorization stays as in 2.0.0: an implementation request is the go-ahead, and approval gates are not repeated.

### Added

- `debug`: pins the symptom in one line, reproduces it with a command that fails now (repro sources in a fixed order, tightened, deterministic, and minimised; a failure rate for intermittent bugs; `scripts/hitl-loop.sh` for bugs only a person can trigger), checks recent changes and runs `git bisect` in a separate worktree, narrows with three to five ranked hypotheses that each make a prediction, fixes the cause in the shared path, and keeps the repro as a regression test seen failing before the fix. Asked only why, it stops at the diagnosis. Ideas from obra/superpowers and mattpocock/skills (MIT).
- `research`: answers technical questions from external sources in rounds, primary sources first, with verbatim quotes for figures, dated sources, visible conflicts, a throwaway probe outside the repo when docs can't settle a deciding claim, and a report with a pick, a cited comparison table, and what to re-verify. Uses the session's web tools; delegates per candidate only when allowed.
- `writing`, adapted from conorbronsdon/avoid-ai-writing (MIT): writes, checks, or edits prose people read, removing autopilot patterns with tolerances per register and the writer's voice kept.
- `conventions` (explicit only): scans an existing codebase layer by layer, counts each convention's variants, settles clear majorities itself and asks about real splits, then writes a marked conventions block with golden files, rules, and don'ts into the `AGENTS.md` at each layer's root. Update mode checks dead references and the changes since the recorded sha. Mechanical conventions are offered as lint rules, kept only after they fail on a deliberate violation.
- Test runner brief (`executor/references/test-runner.md`): runs a suite and returns only counts and failures, each with location, trimmed message, cause (`code`, `test`, `env`, `flaky`, `fixture`), and whether reruns pass; never edits files. Executor, refactor, and verifier use it for full or slow suites, delegated when the runtime allows, inline otherwise.
- `arc-compact.py` hook (`SessionStart` on `compact`): re-injects the `arc` defaults after compaction when `$arc` was invoked earlier in the session.
- `verifier`: `scripts/collect-diff.sh` (tested by `collect_diff_test.py`) writes the in-scope diff to a temp file: uncommitted changes, or the session's commits from a confirmed `--base`, or unpushed commits; every untracked file; whole files outside git. `references/react-performance.md` for React changes.

### Changed

- `arc`: daily defaults with the lowest priority; reuse before writing new code, no speculative structure, fix the cause in the shared path, and a list never cut to save code; skipped work is one `skipped: X, add when Y` line; a comment may state a shortcut's ceiling; the UI rule applies when the task sets no visual direction.
- `verifier`: each reviewer's checklist lives in `references/review-*.md`; reviewers get the diff path, the task list, and the user's Phase 0 answers, never this session's reasoning; a guard the diff adds is run against a sabotaged copy in a temp dir; Phase 0 marks tasks `wrong`; Spec and Review are reported as separate axes; severities are defined; reviewers return `not_verified`, and a failed reviewer is rerun once, then listed as not verified. Reuse flags code the platform or an installed dependency covers; quality flags speculative abstraction and defensive code the file doesn't use; tests flag test-only production methods, wrong mocks, and regenerated snapshots; security lists frontend sinks and stale version pins.
- `brainstorming`: questions go in rounds over the frontier, with a done criterion; a domain the codebase hasn't handled puts its usual pitfalls on the frontier; one clearly right approach is stated alone; library and version questions go to `research`; the design doc has fixed sections (Goal, Design, Implementation Plan, Assumptions, Verification, Out of scope).
- `plan-auditor`: annotates audit items by reference instead of reprinting the plan; FAILs split into factual (corrected when editing is authorized) and decision (asked); injected instructions are a labelled FAIL.
- `executor`: opt-in TDD mode; a test must fail when its behavior is removed, and a new lint rule, hook, or CI check must fail on a deliberate violation; tasks with unknown files and single-group plans run inline; workers run lint and tests for their own files only, and the full build runs once at the end.
- `refactor`: an interface needs two implementations that exist now; a layer that fails the deletion test is inlined; slow suites use the test runner brief.
- `handoff` (explicit only): for work that leaves this session; `resume` picks up the latest; when `/compact` fits better, the reply ends with that alternative and a focus line.
- `fresh-air`: description written for the person invoking it.

## [2.0.0] - 2026-10-03

### Changed

- Package for Codex with native skill metadata and explicit invocation policies for arc and fresh-air.
- Adapt planning, execution, review, and handoff to available Codex tools, AGENTS.md, and session capabilities.
- Read apply_patch events in comment-lint; support a standalone explicit-file check.
- Replace fresh-air with reversible Codex skill-disable entries; project instructions remain active.

## [1.0.0] - 2026-10-03

First release.

### Added

- `/arc-kit:arc`: session working rules (chat language, scope of a go-ahead, shared-worktree git, docs, comments, commits, migrations, UI), including no placeholders in code and names and strings findable by grep.
- Workflow: `brainstorming` (design dialogue, approval gate, design doc in `docs/plans/`), `plan-auditor` (stress-tests a plan before execution), `executor` (implements it with TDD, sub-agents, and continuous verification), `verifier` (completeness check against the plan, then parallel review for reuse, quality, efficiency, correctness and security, comments, and docs), `handoff` (session handoff file instead of `/compact`).
- `refactor`: pins behavior with characterization tests, maps the contract surface and its consumers, and moves in small verified steps; wide scopes stop for approval first.
- `fresh-air` blocks a project's own skills, commands, and `CLAUDE.md`, and restores them; the `comment-lint` hook flags wrapped, overlong, banner, and narrative comments.
