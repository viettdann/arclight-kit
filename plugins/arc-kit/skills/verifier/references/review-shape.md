# Shape review

Ask of every touched unit: is this the least code that does what is needed? Category `shape` for code, with `rank` set on items 1-16; `correctness` for Placeholders; `comments` and `docs` for the last section.

## Scope

A unit is a function, method, component, type, or module-level block. Every unit the diff adds or changes is in scope and is read whole, its unchanged lines included. Units the diff doesn't touch are out of scope.

## Method

1. **Contract.** For each unit, list what it must do: the inputs its real callers pass, the outputs and side effects callers or the task use, the error cases a caller handles or the task names, the edge cases a test pins. Each entry names its source (caller `file:line`, test name, task item). What no caller, test, or task needs is not in the contract.
2. **Necessity.** Point each function, parameter, branch, type, piece of state, wrapper layer, and option at one contract entry. One that points at none is rank `delete`.
3. **Rewrite.** From the contract alone, without editing the existing code, write the smallest version that meets it, using what the codebase, standard library, platform, or installed dependencies already provide. Count concepts: functions, types, state, branches, parameters, layers of indirection; line count only breaks ties. When the rewrite has fewer concepts and meets every entry, report rank `simplify` with the full rewrite in `suggested_fix` and the concept counts before and after in `issue`. A branch the current code handles and the rewrite drops must be shown unreachable in `evidence` (the type, a validating caller, a constraint); otherwise the rewrite keeps it.
4. Then check the items below.

Ranks run `delete`, then `simplify`, then `optimize`. Report the highest rank that works; never propose simplifying or optimizing code that can be deleted. Extracting a shared helper is `simplify` only when the total code across its call sites shrinks; otherwise it is no finding. Denser code with the same concepts (one-liners, chained ternaries, tricks) is not simpler. Never cut input validation at a trust boundary, error handling that prevents data loss, or a security check.

## Delete

1. **Speculative structure**: an interface with one implementation, a factory or strategy for two branches, a parameter or option no caller sets, config for a value that never changes, scaffolding for a later feature no task asks for.
2. **Defensive code out of place**: a try/catch, null check, or fallback, in a guard style the rest of the file doesn't use, guarding a value its callers already validate or its type already guarantees. Checks at a trust boundary stay.
3. **Redundant state**: state duplicating existing state, cached values that could be derived, observers or effects that could be direct calls.
4. **Reimplementation**: new code that an existing function in this codebase, the standard library, a native platform feature (CSS over JS, a DB constraint over app code, a framework built-in), or a dependency already in the manifest covers; a dependency the diff adds for what a few lines do. Search the repo's shared locations (utils, lib, shared, helpers, shared workspace packages) and the changed file's directory first, then the whole repo, with the Grep tool or quoted shell globs (`--include='*.ts'`); a search that errors or matches nothing because of the pattern proves nothing, so fix it and search again. In UI, the project's own components outrank native elements. Put the replacement's path and name in `suggested_fix`.
5. **Existence pre-checks**: checking that a file or resource exists before operating on it (TOCTOU). Operate directly and handle the error.
6. **Leftovers**: debug output (`console.log`, `print`, `debugger`, `Debug.WriteLine`) and suppressions added to get green (`any`, `as unknown as`, `@ts-ignore`, `# type: ignore`, `#pragma warning disable`, `!` null-forgiving). Remove the output; fix the type instead of suppressing it.

## Simplify

7. **Copy-paste with slight variation**: collapse the blocks into one path first (a loop, a table, a parameter the copies already differ by). Extract a helper only when collapsing doesn't fit and the total shrinks. Flag only when a fix to one block would need the same fix in the other; blocks that change for different reasons stay separate.
8. **Parameter sprawl**: parameters bolted onto a function instead of generalizing or restructuring what is there.
9. **Leaky abstractions**: internal details exposed that should stay encapsulated, or an existing abstraction boundary broken.
10. **Stringly-typed code**: raw strings where the codebase already has constants, string-union enums, or branded types.

## Optimize

11. **Unnecessary work**: redundant computation, repeated file reads, duplicate network or API calls, N+1 patterns.
12. **Missed concurrency**: independent operations run sequentially when they could run in parallel.
13. **Hot-path bloat**: new blocking work on startup or on per-request and per-render paths.
14. **Memory**: unbounded data structures, missing cleanup, event listener leaks.
15. **Overly broad operations**: reading whole files when a portion suffices, loading every item to filter for one.
16. **React**: when the diff touches React components, hooks, or stores, check it against `react-performance.md` in this directory; skip the rules marked (correctness) and the security rule, which other reviewers cover.

## Unranked

17. **Unsearchable code**: a new exported name that is a bare generic verb or noun (`validate`, `diff`, `handler`), a new synonym for a term the codebase already spells one way, an event name, flag, error code, or log key assembled by interpolation, an error message without a literal prefix that greps back to the throw site, a name the diff left stale after changing its behavior. Rename or write the literal in full; never rename a serialized or string-based contract name. Category `shape`, no `rank`.
18. **Placeholders**: `// ...`, `// rest of code`, `// implement here`, `// similar to above`, a bare `...` for omitted code, stub bodies, or a `TODO` the user or active skill did not ask for. Category `correctness`, no `rank`, severity `high`. Fix: write the missing code.

## Comments and docs

Review every comment the diff adds or changes, every changed documentation file (plans, specs, READMEs), and the READMEs and config templates that reference what the diff changed. Category `comments` for code comments, `docs` for documentation files, no `rank`. Skill files (anything under a skill's directory, including `SKILL.md`) and agent definitions are out of scope unless your prompt says the user asked to review them: their rationale is instruction for the model, not narrative.

A comment stays only for what code cannot say: a non-obvious invariant, a constraint, a deliberate gotcha, or the ceiling of a deliberate shortcut and when to lift it. Documentation states what to do; the reader executes from it.

19. **Comments that restate code**: what the next line does, data flow, usage, or anything names, types, and imports already show. Fix: delete.
20. **Multi-line comments**: any comment longer than one physical line, including one thought wrapped across lines and prose `/** */` blocks. Fix: cut to the single invariant on one line, or delete.
21. **Banners and headers**: section dividers, ASCII rules, module-header prose. Fix: delete.
22. **Narrative documentation**: rationale, background, alternatives considered, what a change replaced, what was tried before, and any `## Rationale`, `## Background`, or `## Alternatives` section. Fix: delete, or rewrite as the instruction the reader executes.
23. **Filler**: sections or boilerplate added to look complete, recaps, closing summaries. Fix: delete.
24. **Stale references outside the diff**: a README command, `.env.example` key, `appsettings*.json` section, or config template entry that the diff's code renamed, removed, or added without a matching change. Fix: update the line; for a file under `docs/`, report it instead of editing it.

Lint suppressions, type-checker directives, license headers, and shebangs are not prose comments; leave them.
