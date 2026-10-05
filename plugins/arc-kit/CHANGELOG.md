# Changelog

All notable changes to `arc-kit` are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [2.2.0] - 2026-10-05

### Changed

- Sync the Codex package with main through `f2bb39d` using a recorded Git merge; adapt new instructions and checks to Codex.

## [2.1.0] - 2026-10-04

## [1.8.0] - 2026-10-05

### Added

- `destructive-guard` hook (`PreToolUse` on `Bash`, off by default, `destructive_guard_enabled`; when off it exits before starting Python): splits compound commands, including `$( )`, backticks, `bash -c`/`-lc`, and wrappers, and treats heredoc bodies as data; denies recursive `rm` or `find -delete` of `/`, `~`, `$HOME`, or `..`, `${IFS}`, and decoded payloads piped into a shell; asks before other recursive deletes, `rsync --delete`, git discards, destructive SQL sent to a SQL client, and docker, compose, kubectl, or terraform teardown; lets build artifacts by relative path and temp paths through. Tested by `destructive_guard_test.py`.
- `scripts/plugin_options.py`: the one reader of `CLAUDE_PLUGIN_OPTION_<KEY>` for `comment-lint` and `destructive-guard`.

### Changed

- `verifier`: each finding quotes `file:line` and the line (the generating code for a framework-generated symbol); an unquoted finding is listed as unconfirmed, never applied. Security or race fixes that change behavior, design decisions, fixes over about 20 lines, removed functionality, user-visible changes, and cross-file helper extractions are asked before applying. Reviewers share a do-not-flag list. Phase 0 runs the plan's behavioral assertions and adds `changed` and `unverifiable`. Correctness covers new enum values and their consumers, conditional side effects, data migrations, flaky and denied-case tests, webhooks, constant-time comparison, CSPRNG tokens, untrusted deserialization, CI injection, and LLM output as input. Checks record the command's own exit code; 127 and uncaptured output are failures.
- `test-runner`: reports the command's exit code, taken before any pipe.
- `plan-auditor`: a FAIL quotes its code line or drops to FLAG; a failure-mode table (handled, tested, visible, logged) replaces the timeout check; medium depth checks revert history on touched paths; 8+ files or 2+ new modules must answer whether fewer moving parts would do.
- `brainstorming`: checks the premise; lists siblings of a touched family member and overlapping designs in `docs/plans/`; one question holds one choice and names the default; a fresh-context subagent reviews the written doc, up to 2 rounds.
- `executor`: a "Decided for you" list in the summary and agent reports; irreversible actions are always escalated, and sub-agents never take them.
- `debug`: external error searches strip hosts, IPs, paths, SQL, tokens, and customer data; a fix over 5 files is asked first.
- `handoff`: claims behind the next step carry `(run, exit 0)`, `(read)`, or `(assumed)`; resume re-checks the unrun ones.
- Repo: `scripts/skill_lint_test.py` checks frontmatter, description and body budgets, referenced paths, qualified skill names, README and `plugin.json` listings, and that each `plugin.json` version matches its changelog.

## [1.7.0] - 2026-10-04

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
