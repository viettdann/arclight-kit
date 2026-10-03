---
name: conventions
description: "Write an existing codebase's unwritten conventions into path-scoped .claude/rules/ files with golden files, or refresh them after the code moved on."
argument-hint: "[path or layer]"
disable-model-invocation: true
---

# Conventions

Write down what a competent developer new to this repo would get wrong: the conventions the code follows that no linter checks. The output is a few short rules files Claude Code loads when it reads or edits matching files, so it costs no context elsewhere.

## 1. Mode

If `.claude/rules/conventions*.md` exists, run Update (step 6). Otherwise run a first scan. Say which in one line and continue.

## 2. Inventory

- Read what is already written down: `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING.md`, `.editorconfig`, linter and formatter configs (`eslint`, `biome`, `prettier`, `.globalconfig`, `Directory.Build.props`, analyzers). Anything they state or enforce stays out of the rules.
- Split the repo into layers by `git ls-files` (for example ASP.NET projects, a Next or Vite frontend, shared packages). Each layer gets its own scan and its own rules file.
- Size each layer by source file count and pick the depth: up to 50 files, read them all; 50 to 500, read shared and infrastructure code fully and sample two or three files per dimension; above 500, sample from `git log --since=6.months --name-only` first, then the largest and most imported files. Recently changed files show where the team is heading; old files show what exists.
- Done when every layer has a path glob, a file count, and a chosen depth, and the list of what existing docs and configs already enforce is written down.

## 3. Scan each layer

| Dimension | Look for |
| --- | --- |
| File anatomy | Folder by feature or by layer, one type per file, member order, file and folder naming, where tests sit |
| Naming beyond the linter | Suffixes (`Service`, `Handler`, `Dto`, `Request`/`Response`, `Async`), boolean and loading-flag names (`isLoading` or `loading`), handler props (`onX`) and handlers (`handleX`), hook and store names |
| Cross-cutting code | The HTTP client wrapper, DI registration, mapping (manual or a mapper), validation library, logging, options and config, dates, i18n, auth checks |
| Errors | Exceptions or result types, global middleware or interceptors versus local try/catch, error response shape, how the UI surfaces errors (toast, inline, boundary) |
| Data and state | ORM usage (repositories or `DbContext` directly, tracking, projections), query or fetch library, where server state and client state live |
| Tests | Framework, naming, arrange style, builders and fixtures, what gets mocked |

Count, don't guess: for each candidate convention, grep both variants and record the counts with two example paths each (`MapGet` 41 vs `: ControllerBase` 3). A convention with no countable form gets the files it was seen in.

Done when each of the six dimensions, in each layer, has its candidate conventions with counts and example paths, or a one-line note that the layer has nothing there (a backend with no UI errors, a package without tests).

## 4. Settle conflicts

- **Weak minority** (under 5% and under 10 occurrences): the majority is the rule; the minority goes under Don't with one example path. Don't ask.
- **Real split** (both sides common, or old files use A while files changed in the last months use B): ask. Below 50 files a 3 to 2 count is a split, not a majority.

Ask with AskUserQuestion, one conflict per question and up to four questions per call. Each question shows the counts and one path per side; options: follow A, follow B, B is the direction (new code uses B, old A code stays as it is), or the user's own rule.

## 5. Write the rules

One file per layer, plus `conventions.md` without `paths` only for rules that hold across all layers:

```markdown
---
paths:
  - "src/Api/**/*.cs"
---
<!-- conventions 3f2a9c1 2026-10-03 -->
# Conventions: API

## Golden files
- `src/Api/Orders/CreateOrder.cs`: endpoint + validator + handler in one feature folder

## Rules
- Endpoints are Minimal API groups under `Features/<Feature>/`, one file per endpoint
- Expected failures return `Results.Problem` through `ErrorMapper.ToProblem`; never throw for validation

## Don't
- `: ControllerBase` controllers (old code in `src/Api/Legacy/`)
```

- **Golden files:** three to six real files that are recent, typical, and mid-sized, each with what it demonstrates. Pick files without known bugs; a bug in a golden file gets copied.
- **Rules:** one checkable line each, naming the concrete type, helper, folder, or pattern. Keep a line only if a capable developer new to the repo would likely get it wrong without it; generic good practice the model already follows is cut.
- **Don't:** minority patterns that must not spread, each with where they live.
- A rule the project's linter or analyzer could enforce (a banned import, a naming pattern, a forbidden base class): offer it as a lint rule instead of a prose line. If the user takes it, prove it before keeping it: the linter passes on the code, fails on a deliberate violation, and passes again once that violation is reverted.
- Keep each file under about 60 lines; it loads every time a matching file is read.
- The comment line holds the short HEAD sha and date for Update.

Show the files and their line counts. Committed, they apply to every Claude Code session in the repo; to keep them personal, add them to `.git/info/exclude`.

## 6. Update

1. Read the rules files and their sha; list what changed with `git diff --stat <sha>..HEAD`, sampling the largest changes when the list is long.
2. Check every file path, command, and symbol named in the rules files, `CLAUDE.md`, `AGENTS.md`, and the README: paths with `git ls-files`, symbols with grep, commands against the scripts or tasks that define them. A dead reference (a deleted golden file, a renamed helper, a removed script) is the first fix: correct it in the rules files, and report the ones in files this skill doesn't own.
3. Check the changed files against the rules. A broken rule in one or two files is drift: report it. The same new pattern across several recent files is a possible new direction: ask, as in step 4.
4. Edit the rules in place, swap golden files that were deleted or rewritten, and update the sha and date. The files hold current rules only, no change log.
