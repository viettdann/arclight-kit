# Changelog

All notable changes to `arc-kit` are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [2.5.0] - 2026-10-15

- Sync main through `debfef9` (upstream 1.16.0); retain inherited Codex models and authorized delegation with inline fallback.
- Add small-task guidance, self-contained design plans, fresh-reader checks, and worker validation rules.
- Include accepted workers in review scope and React performance references in relevant reviews; cap test reruns at ten failures.
- Continue authorized work through completion while respecting runtime approval and progress requirements.

## [1.16.0] - 2026-10-15

Tuned for Claude Opus 5.5 as the session model and Sonnet 5.5 and Haiku 5.5 as workers.

### Changed

- `executor`, `supervise`, `arc`: a turn ends only on a question only the user can answer, before an irreversible action, or with the final report; mid-run notes ride with the next tool call.
- `arc`: corrections only when they change the user's code, conclusions, or decisions; a mistaken-looking request is flagged in one sentence and done as asked; subagents only for big independent work, never to double-check your own.
- `executor`: sub-agents deliver only their tasks; an unnecessary-looking plan step is done and noted, scope creep is deferred; a direction change deletes dropped tasks from the plan file instead of marking them; the summary omits empty sections.
- `supervise`: every Haiku call (worker and Lookup) at effort `high` (no longer `max`); a packet's verify commands include the tests of the owned files' direct callers; the verifier gets the accepted groups' files in scope and the stopped groups' tasks as not done; a worker blocked on a verify command that couldn't start goes to the user.
- `worker`: never runs the project-wide build, type-check, or full test suite; keeps working until every task is done, then stops without unrequested features, files, docs, or refactors (Suggestions instead); a verify command that didn't start or only checked syntax isn't a pass, packages aren't installed to run it, and the narrowest real check runs when the packet's don't exercise the change.
- `test-runner`: effort `high`; the output log is the one file it writes; reruns capped at 10 failing tests.
- `verifier`: files edited by sub-agents and workers are in scope; `react-performance.md` goes to Agents 3 and 5 on React diffs.
- `brainstorming`: the design doc is self-contained and holds only what gets done (Goal, Decisions, Plan, Assumptions, Verification; no Design or Out of scope section, no rationale, exclusions, or pointers back at the conversation); the fresh-context review becomes a fresh-reader check on Sonnet that explains each Plan line back and lists its questions, missing references, and narrating lines; `examples/happy-path.md` shows a full doc; examples follow the one-choice-per-question rule.
- `plan-auditor`: reads the new doc sections; flags lines that depend on the conversation or narrate what isn't done; rewrites add no rationale or exclusions; sub-agents get every claim in their area.
- `refactor`, `debug`, `research`: concrete approval threshold and no progress stops in refactor; debug records its test baseline; research subagents get the full rules and every criterion.
- `writing`: edit mode drops the re-read; the rebuild rule applies to write mode only.
- `conventions`: layer files are named `conventions-<layer>.md` so Update finds them.
- `handoff`: effort `medium`; the example carries the evidence markers the template requires.
- `fresh-air`: `--model haiku --effort high` instead of a pinned id; no settings re-read step.

## [1.15.0] - 2026-10-15

### Added

- `arc`: a Small tasks section for work that doesn't need the full skill: spec an idea (at most three questions that change the build, user steps, inputs, success criterion, UI states, an acceptance checklist, in chat), build a scoped feature (existing structure and tools, UI states, changed files, dependencies, steps to verify by hand), and diagnose an error (shown apart from inferred, ask for the exact missing log, smallest fix and why it works, repro and verify steps).

### Changed

- `brainstorming`: a question whose every answer leads to the same build isn't asked; a UI feature settles the user's steps, inputs, and each screen's loading, empty, failure, and success states; Verification opens with an acceptance checklist.
- `executor`: the summary lists the files changed, any dependency added and why, and the steps to verify by hand.
- `debug`: the fix is the smallest change that removes the cause; the report adds what is still unconfirmed, why the fix works, and the repro.

## [2.4.0] - 2026-10-14

- Sync main through `5fe23ac`; preserve Codex packaging, runtime adaptation, and patch hooks.
- Add Codex supervise with worker/reviewer briefs, snapshots, run logs, fix rounds, and runtime-aware model routing.
- Port test-guard to completed apply_patch calls; retain comment lint, arc reload, and opt-in destructive guard.
- Integrate plan-gap checks, fix-round review, and tests by necessity without resetting existing authorization.

## [1.14.0] - 2026-10-14

### Added

- `supervise`: `snapshot log` keeps a run log of every dispatch, verdict, escalation, and stop, read back after a compaction so an accepted group is never dispatched again. `snapshot mark` and `snapshot diff --since-review` make the review after a `fix` a fix round: the `reviewer` rules on each earlier finding and checks only the fix diff, and a problem outside the fix no longer counts as a failed attempt.

### Changed

- Tests run by necessity: a change that can't alter behavior (docs, comments, Markdown, formatting only) runs no build or tests (`arc`, `executor`, `supervise`, `verifier`); otherwise the tests covering the touched files, and the full suite only when the change reaches shared code, a public contract, config, dependencies, or build files, or those tests can't be named. A failing test whose file and the code it runs the diff doesn't touch is reported as not from this change instead of fixed, and doesn't fail a `supervise` worker's gate.
- `executor` and `supervise`: sub-agent prompts and packets carry the plan's project-wide constraints and Out of scope lines verbatim. `supervise` may group tasks making the same small change in different files.
- `plan-auditor`: FAIL for a name the plan introduces that differs between items; FLAG for an input or failure mode a user would hit that no item's check covers, and for an item that decides nothing. `brainstorming`'s Verification section ties each such input to the plan line whose check covers it.
- Tests: an expected value computed by the code under test is a weak test (`executor`, `worker`, `reviewer`, verifier's `review-correctness.md`); a fixed sleep standing in for finished async work is nondeterministic, and `debug` suspects it first in a flaky test. `executor` without TDD sees a bug fix's regression test fail with the fix undone.

Ideas drawn from obra/superpowers (writing-plans, subagent-driven-development, test-driven-development, systematic-debugging), rewritten.

## [1.13.0] - 2026-10-14

### Changed

- `test-runner`: the report stays under 80 lines and 8 KiB; past that, failures with one cause and message are grouped with a count, the rest are listed by name and location, and the report ends with the full log's path.
- Descriptions: `debug` excludes a deployed Azure resource failing live (`mgi-kit:azure-diagnose`); `plan-auditor` excludes code already written (`verifier`); `supervise` states its exclusion as "Not for"; `brainstorming` no longer has a tag-like `<date>-<topic>` path, which marketplace sync rejects; `executor`, `research`, `debug`, `plan-auditor`, and `verifier` are shorter to keep the skill menu in budget.

## [1.12.0] - 2026-10-10

### Changed

- `plan-auditor`: a goal or success criterion that is an activity (`improve`, `investigate`, `clean up`, `make faster`) or names no check that could fail is FLAG, reported above the first item with a rewrite naming the outcome, the proving command or observation, and the threshold.
- `worker`: requested code is written in full, with no placeholder comments, stub bodies, skeletons, or unrequested `TODO`; a task it can't finish is reported `blocked` or `failed`, never `done`. `reviewer` counts a criterion a stub stands in for as not met.

### Removed

- `verifier`: the RTL direction bullet in `review-ui.md`.

Ideas drawn from openai/skills (define-goal) and Leonxlnx/taste-skill (full-output-enforcement, the source of the worker rule), rewritten.

## [1.11.0] - 2026-10-08

### Added

- `test-guard` hook (`PostToolUse` on `Edit|Write`, on by default, `test_guard_enabled` turns it off): when an edit adds test cases to a code file named as a test, it lists each new case and exits 2, asking Claude to delete the junk ones and name the regression each kept test catches. Recognizes Python, JS/TS, Go, C#, Java/Kotlin, Rust, Swift, PHP, and RSpec cases, and reads attribute-style names from the following lines. A case is new only when its name occurs more often than before the edit, so editing, renaming, or moving a case doesn't trigger it; each case is asked about once per session. Tested by `test_guard_test.py`.

### Changed

- Test rules in `arc`, `executor`, `worker`, `reviewer`, and `verifier`: test by necessity, not by imitation. A test needs a nameable plausible regression; the project's existing tests are never the reason; tests of copied constants or strings, markup or style, or only that a call happened are junk; no test is a valid outcome. `executor` with TDD off no longer adds a test for every new behavior, and `verifier` reports junk tests.
- `refactor`: each characterization test pins a call path the refactor touches and names it.
- `supervise`: the Haiku tier takes a test for a named regression instead of a test that follows an existing pattern.
- `comment-lint` reads added lines and skipped paths from the shared `scripts/added_lines.py`.
- `executor` and `worker`: a characterization test pinned before a refactor is an exception to the rule against asserting what the code currently returns.

## [1.10.0] - 2026-10-08

### Added

- `supervise`: Opus loads a plan (file or chat), consolidates it into tasks with derived acceptance criteria, groups them by file overlap with shared helpers and types built first, and routes each group to a Haiku (max), Sonnet (high), or Opus (medium) worker by difficulty. Every diff is measured against a backup of the group's files taken before dispatch and reviewed: up to about 150 lines inline against `reviewer`'s checks, larger ones by `reviewer`. A failed report, a failing gate, or a `fix` or `rewrite` verdict is a failed attempt; two at a tier move the group up one tier, and `rewrite` goes to Opus at high, the ceiling. `haiku`, `sonnet`, or `opus` sets the starting tier, "only" a tier pins it, and a ceiling or floor said in words is honored. A snapshot of HEAD, the stash list, and hashes of uncommitted files outside the run is compared after every report: a moved HEAD, a changed stash list, or a touched foreign file pauses the run for the user, and a stray edit stops its group. Snapshot, backups, the check, and per-group diffs run through `scripts/snapshot.py` (`take`, `backup`, `check`, `diff`), so they behave the same under bash, zsh, and macOS, with paths through symlinks, spaces, non-ASCII names, staged renames, binary files, and files without a final newline; tested by `snapshot_test.py`. Ends with build, full suite, plan cross-check, and `verifier`, and reports each group's tier path.
- `worker` agent (Read, Edit, Write, Grep, Glob, Bash): implements one task packet within its owned files, fixes errors in code its change touched, reports other failures with whether its change caused them, undoes work by hand or from the backup, never with git, and returns a fixed report or stops as blocked.
- `reviewer` agent (Opus, medium, no Edit or Write): returns `accept`, `fix` with `file:line` findings, or `rewrite` for one group's diff against its backup.
- `agent-git-guard` hook (`PreToolUse` on `Bash` and the edit tools, always on): inside `worker` and `reviewer`, allows only read-only git and denies the rest, `stash` included, plus config overrides through flags, `GIT_*` variables, or `HOME`/`XDG_CONFIG_HOME` in front of git, writing or program-launching options, aliases and `git-*` helpers, git started by launchers such as `find -exec`, `xargs`, `watch`, and `env -S`, and any access to `.git/` or git config files; the denial tells the agent to report to the supervisor. Fails closed for those agents and never starts Python for others. Reuses `destructive-guard`'s command walker. Tested by `agent_git_guard_test.py`.

### Changed

- `destructive-guard`: `check_command` and `check_argv` take the per-command check, the whole-command check, and the unparseable-command hint as arguments, so `agent-git-guard` reuses the walk through shells, `eval`, substitutions, wrappers, and obfuscation instead of copying it. An unparseable command's reason now names the keyword it mentions.

### Fixed

- `destructive-guard`: `env -S 'cmd'` and `env --split-string='cmd'` are checked as command lines; before, `strip_wrappers` dropped the value as an option argument, so `env -S 'rm -rf /'` passed.

## [2.3.0] - 2026-10-06

### Changed

- Adopt main through `ac70815` (upstream arc-kit 1.9.0): UI review checklist, combined dirty-tree and unpushed diff collection, and warnings for in-progress Git operations.
- Carry decision and irreversible-action rules in executor worker assignments; retain Codex authorization and inline fallback behavior.

## [2.2.0] - 2026-10-05

### Changed

- Sync the Codex package with main through `f2bb39d` using a recorded Git merge; adapt new instructions and checks to Codex.

## [2.1.0] - 2026-10-04

## [1.9.0] - 2026-10-06

Ideas drawn from jakubkrehel/skills (MIT), rewritten.

### Added

- `verifier`: `references/review-ui.md` for diffs that touch UI files: removed accessibility signals, changes incomplete against their intent, finding status (introduced, regression, pre-existing), and the blast radius of a shared component.

### Fixed

- `collect-diff.sh`: with a dirty tree and no `--base`, commits ahead of upstream are now included; an in-progress rebase, merge, cherry-pick, or revert prints a warning.

## [1.8.1] - 2026-10-06

### Fixed

- `executor`: the sub-agent brief now carries the Decision Framework's "Judgment call resolved without asking" and "Irreversible action" rules, so workers know what goes under "Decided for you" and that asking means stopping and reporting.

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
