---
name: conventions
description: "Write an existing codebase's unwritten conventions into directory-scoped AGENTS.md blocks with golden files, or refresh them after the code moved on."
---

# Conventions

Write down what a competent developer new to this repo would get wrong: the conventions the code follows that no linter checks. The output is one short block per layer in the `AGENTS.md` at that layer's root directory. Codex loads `AGENTS.md` files from the project root down to the working directory and applies a nested one to the files in its directory tree, so a layer's block costs no context outside that layer.

Follow applicable AGENTS.md instructions. Use Vietnamese in chat and English in files unless the user requests otherwise. A path or layer named in the request limits the scan to it.

## 1. Mode

If a tracked `AGENTS.md` holds a `<!-- conventions <sha> <date> -->` block (`git grep -l '<!-- conventions ' -- '*AGENTS.md'`), run Update (step 6). Otherwise run a first scan. Say which in one line and continue.

## 2. Inventory

- Read what is already written down: every `AGENTS.md` and `AGENTS.override.md`, `CONTRIBUTING.md`, `.editorconfig`, linter and formatter configs (`eslint`, `biome`, `prettier`, `.globalconfig`, `Directory.Build.props`, analyzers). Anything they state or enforce stays out of the rules.
- Split the repo into layers by `git ls-files` (for example ASP.NET projects, a Next or Vite frontend, shared packages). Each layer gets its own scan and its own block, in the `AGENTS.md` of the directory that holds the layer.
- Size each layer by source file count and pick the depth: up to 50 files, read them all; 50 to 500, read shared and infrastructure code fully and sample two or three files per dimension; above 500, sample from `git log --since=6.months --name-only` first, then the largest and most imported files. Recently changed files show where the team is heading; old files show what exists.
- Done when every layer has a root directory, a path glob, a file count, and a chosen depth, and the list of what existing docs and configs already enforce is written down.

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

Ask one conflict per question, with `request_user_input` when available in the active mode (up to four questions per call), otherwise in text. Each question shows the counts and one path per side; options: follow A, follow B, B is the direction (new code uses B, old A code stays as it is), or the user's own rule.

## 5. Write the rules

One block per layer in `<layer root>/AGENTS.md`, plus one block in the root `AGENTS.md` only for rules that hold across all layers. Create the file when it doesn't exist; in an existing one, add or replace only the block between the conventions markers and leave the rest of the file as it is.

```markdown
<!-- conventions 3f2a9c1 2026-10-03 -->
## Conventions: API

Applies to: `src/Api/**/*.cs`

### Golden files
- `src/Api/Orders/CreateOrder.cs`: endpoint + validator + handler in one feature folder

### Rules
- Endpoints are Minimal API groups under `Features/<Feature>/`, one file per endpoint
- Expected failures return `Results.Problem` through `ErrorMapper.ToProblem`; never throw for validation

### Don't
- `: ControllerBase` controllers (old code in `src/Api/Legacy/`)
<!-- /conventions -->
```

- **Golden files:** three to six real files that are recent, typical, and mid-sized, each with what it demonstrates. Pick files without known bugs; a bug in a golden file gets copied.
- **Rules:** one checkable line each, naming the concrete type, helper, folder, or pattern. Keep a line only if a capable developer new to the repo would likely get it wrong without it; generic good practice the model already follows is cut.
- **Don't:** minority patterns that must not spread, each with where they live.
- A rule the project's linter or analyzer could enforce (a banned import, a naming pattern, a forbidden base class): offer it as a lint rule instead of a prose line. If the user takes it, prove it before keeping it: the linter passes on the code, fails on a deliberate violation, and passes again once that violation is reverted.
- `Applies to` globs: brackets are a character class, so a folder named `[locale]` or `[id]` written literally matches nothing; write that segment as `*`. Check each glob with `git ls-files ':(glob)<pattern>' | wc -l` against the layer's file count. A layer whose files don't share one directory (test files spread across features) goes in the nearest common directory's `AGENTS.md`, its glob naming the files.
- Keep each block under about 60 lines; Codex caps the combined `AGENTS.md` text it loads (`project_doc_max_bytes`, 32 KiB by default), and every block on the path counts.
- The opening marker holds the short HEAD sha and date for Update.

Show the blocks and their line counts. Committed, they apply to every Codex session in the repo, and to other agents that read `AGENTS.md`; to keep a new `AGENTS.md` personal, add it to `.git/info/exclude` (a file that is already tracked can't be kept personal this way).

## 6. Update

1. Read the conventions blocks and their sha; list what changed with `git diff --stat <sha>..HEAD`, sampling the largest changes when the list is long.
2. Check every file path, command, and symbol named in the conventions blocks, the rest of each `AGENTS.md`, and the README: paths with `git ls-files`, symbols with grep, commands against the scripts or tasks that define them. A dead reference (a deleted golden file, a renamed helper, a removed script) is the first fix: correct it in the conventions blocks, and report the ones outside them, which this skill doesn't own.
3. Check the changed files against the rules. A broken rule in one or two files is drift: report it. The same new pattern across several recent files is a possible new direction: ask, as in step 4.
4. Edit the blocks in place, swap golden files that were deleted or rewritten, and update the sha and date. The blocks hold current rules only, no change log.
