# Changelog

All notable changes to `arc-kit` are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

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

### Changed

- `verifier`: each reviewer's checklist lives in its own `references/review-*.md`, which each reviewer reads itself; `SKILL.md` holds only the flow, the reviewer prompt, and the summary. `scripts/collect-diff.sh` (tested by `collect_diff_test.py`) writes the in-scope diff to a temp file: uncommitted changes, or the session's commits from a confirmed `--base`, or unpushed commits; every untracked file, directories included; whole files outside git. Reviewers get its path; it is rewritten when Phase 0 edits code and deleted after the summary. Contract breaks move to the reuse reviewer, since both search the whole repository; security and test checks read as sub-lists. Severity levels are defined. Reviewers get the user's Phase 0 answers and whether skill or agent files are in review scope, and return a `not_verified` list, which covers a guard that still cannot run outside the repository after its config is copied and a skill the reviewer cannot call. The correctness reviewer alone checks the React rules marked (correctness). Full or slow suites run through `test-runner` when it is available.

### Removed

- `verifier`: the Phase 0 sub-agents, the fresh agent that attacks high-severity fixes, and the design-smell checks.

## [1.6.0] - 2026-10-04

### Changed

- `verifier`: review agents get the diff and the Phase 0 task list, never this session's account of why the code works, and never run as forks. A small diff touching authentication, authorization, payments, secrets, or a data-deleting migration still sends Agent 5 to a fresh agent. Agent 5 flags regenerated snapshot or approved files (`*.snap`, `*.verified.*`) without a planned behavior change, and version ceilings or pins that exclude the registry's current release with no stated reason. A guard the diff adds is run against a sabotaged copy in `$TMPDIR` and must fire; the repository stays untouched. An agent that errors or returns nothing is rerun once, then listed under Not verified. A fix for a high correctness or security finding gets one fresh agent that tries to break it.
- `brainstorming`: in a domain the codebase hasn't handled, the decisions that domain usually gets wrong go on the frontier, since the frontier only holds decisions someone knew to make.
- `conventions`: path globs write bracketed folder names (`[locale]`) as `*`, and each glob is checked with `git ls-files ':(glob)…'` against the layer's file count.
- `handoff`: when `/compact` fits better, the reply ends with a ready-to-paste `/compact <focus>` line.
- Ideas from sangrokjung/claude-forge (MIT): `adversarial-reviewer`, `task-grade-routing`, `blind-spot-pass`, `harness-diet`, `relay`.

## [1.5.0] - 2026-10-04

### Added

- `debug/scripts/hitl-loop.sh`: a repro for bugs only a person can trigger; it prompts the user step by step and prints their observations as `KEY=VALUE` lines.

### Changed

- `debug`: repro sources in a fixed order (test, `curl`, CLI fixture diff, replayed capture, throwaway harness, old-versus-new diff, then the HITL script); the repro is tightened to assert the reported symptom, deterministic and fast, and no theory is built before it has run; it is minimised until every remaining piece is needed. Three to five hypotheses, each with a prediction, shown to the user before testing; performance regressions start from a baseline measurement; a bug with no seam that exercises it as the call site does is reported instead of covered by a shallow test; secrets are redacted in everything shown.
- `brainstorming`: questions go in rounds over the frontier (decisions whose prerequisites are settled), and Understanding has a done criterion; shorter description.
- `verifier`: Phase 0 marks tasks done but `wrong`; Spec (Phase 0) and Review (Phase 1-2) are reported as separate axes, never merged or ranked together; the quality agent flags Feature Envy, Data Clumps, Primitive Obsession, Shotgun Surgery, and Message Chains as judgment calls.
- `refactor`: an interface needs two implementations that exist now; a layer that fails the deletion test is inlined.
- `executor` and `conventions`: a new lint rule, hook, CI step, or check is kept only after it fails on a deliberate violation. `conventions` steps 2 and 3 have done criteria and offer lint rules for mechanical conventions.
- `handoff`, `conventions`, and `fresh-air` are user-invoked only, with descriptions written for the person typing them; `handoff` takes `resume`, and no longer replaces `/compact`: it is for work that leaves this session.
- `writing`: shorter description. Cross-skill calls say "call the Skill tool with" the skill.
- Ideas from mattpocock/skills (MIT): `diagnosing-bugs`, `grilling`, `code-review`, `codebase-design`, `writing-for-agents`, `setup-ts-deep-modules`.

## [1.4.0] - 2026-10-03

### Added

- `writing`, adapted from conorbronsdon/avoid-ai-writing (MIT): writes or checks prose people read (READMEs, docs, design docs, release notes, messages) in write, check, or edit mode; removes chatbot artifacts, inflated vocabulary, narrated candor, negation reveals, hooks, hedge stacks, bold and header overuse, em-dash splices, and diff-narrating docs, with tolerances per register and the writer's voice kept.

### Changed

- `debug`: a test that passes alone and fails in the suite is narrowed to the test that leaves state behind; the bisect worktree gets dependencies and untracked config, and commits that don't build exit 125; similar working code is diffed against the failing path; multi-layer failures are logged at every boundary in one run; three failed fixes stop for a design discussion. Ideas from obra/superpowers `systematic-debugging` (MIT).
- `verifier`: quality flags defensive code the surrounding file doesn't use; tests flag test-only production methods, mocks of the side effect under test, and mocks missing fields of the real API; security lists frontend sinks (`dangerouslySetInnerHTML`, unchecked `href` schemes, tokens in `localStorage`, `message` handlers without an origin check, open redirects); the summary ends with what couldn't be verified. `react-performance.md` adds props copied into state, effect chains, a parent's `onChange` called from an effect, and in-place `.sort()` on props or state.
- `conventions` Update checks that every path, command, and symbol named in the rules, `CLAUDE.md`, `AGENTS.md`, and the README still exists before re-counting patterns. Adapted from Context Architecture by Sergio Azócar (context-architecture.dev, CC BY 4.0), reworded and narrowed to the Update step.

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
