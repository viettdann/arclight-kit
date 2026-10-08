---
name: refactor
description: Restructure existing code without changing its behavior (extract, inline, rename, move, split large functions or modules, reduce complexity, remove duplication and dead code). Pins behavior with tests first, maps the contract and its consumers, and moves in small verified steps. Use when the user asks to refactor, restructure, split, extract, rename, or untangle code, in English or Vietnamese ("refactor", "tái cấu trúc", "tách hàm", "đổi tên", "dọn code", "giảm complexity"). Not for reviewing a finished diff (see verifier) or for rewrites meant to change behavior.
---

# Refactor

Change structure, never behavior. Behavior is everything a caller, user, or other system can observe: return values, thrown errors and their messages, output and wire formats, side effects and their order, sync versus async, null handling, log lines something parses, and every name another codebase depends on.

## 1. Scope

- State the goal in one line (what becomes easier to change) and the files in scope. Infer both from the request; ask only when the target is unclear.
- Keep feature work and bug fixes out. A bug found mid-refactor goes in the report, not in the diff; mixing the two makes the "behavior unchanged" claim unverifiable.
- If the scope spans several packages or more than a handful of files, show the step-2 contract map and the move sequence, and wait for approval before editing. For larger efforts, plan through `brainstorming` and run through `executor`; this skill's rules still apply to each step.

## 2. Map the contract surface

Before editing, list every surface in scope that something outside the scope depends on, then find its consumers across the whole repo with LSP find-references or grep (tests, scripts, other packages, the frontend):

- Exported functions, classes, and types: names, signatures, defaults, thrown error types
- HTTP routes, request and response DTOs, status codes
- Serialized names: JSON keys, `[JsonPropertyName]`, enum values serialized as strings, ORM table and column mappings, queue and event names, cache keys
- Config and env keys, CLI flags, file formats, public constants
- String-based lookups: DI registration by name, reflection, dynamic imports, route or template strings

The compiler does not see the serialized and string-based ones: renaming a serialized C# property or TS field changes the wire format while the build stays green. Treat these as frozen. If the goal needs one of them to change, stop and tell the user: that is a breaking change with its own consumer and migration work, not a refactor.

## 3. Pin behavior

- Run the tests that cover the scope and record the baseline. Report pre-existing failures; don't fix them. A slow or large suite goes through the `arc-kit:test-runner` agent, here and in step 5, with this baseline passed in.
- If coverage is thin, write characterization tests first (unit or integration, never e2e): call the code with representative and edge inputs and assert what it returns today, including output that looks wrong. A characterization test that asserts the "correct" value instead of the current one hides a behavior change. Pin only call paths the refactor will touch, and name that path for each test.
- If behavior can't be pinned (no harness, I/O that can't be faked), say so and limit the work to mechanical, tool-driven moves (LSP rename, extract) unless the user accepts the risk.

## 4. Move in small steps

- One transformation per step. After each: build or type-check, then run the pinned tests. On red, undo that step with Edit (not git) and take a smaller one.
- Prefer LSP rename over text replacement. With text replacement, update every consumer found in step 2 in the same step.
- Add abstraction only when it removes real duplication: no strategy, builder, or chain for two branches, no shared helper before three real call sites. Fewer layers is the usual win.
- An interface earns its place with two implementations that exist now (production and a test fake counts); with one, it is indirection. Inline it, unless something outside the scope implements or injects it by that name (step 2).
- Deletion test for a layer (a wrapper, service, helper module): imagine inlining it into its callers. If the complexity disappears, it was a pass-through; inline it. If the same logic would reappear in several callers, it earns its place; keep it.
- Delete dead code only after step 2's search, string-based lookups included, finds no consumer. If unsure, list it in the report instead.
- Match the surrounding style. Leave untouched lines alone so the diff stays reviewable.

## 5. Verify and report

- Run build, type-check, lint, the pinned tests, and the test suite of every touched package. Compare against the baseline.
- If the goal is a complexity target, measure it with the project's own analyzer (Sonar, ESLint `complexity` or `sonarjs/cognitive-complexity`, .NET code metrics) before and after, and put both numbers in the report.
- Grep for every old name to confirm no stale reference. Diff the frozen surfaces from step 2 to confirm they are unchanged.
- If the scope touched ASP.NET controllers or DTOs with TypeScript or JavaScript consumers, call the Skill tool with `mgi-kit:api-contract` when it is installed.

Report in this shape:

```markdown
**Goal**: one line
**Moves**: one line each (what moved where, what was renamed, extracted, deleted)
**Behavior**: unchanged; `<test command>`: <result vs baseline>
**Tests added**: characterization tests and their paths (kept in place)
**Not done**: bugs found, dead code left for confirmation, changes stopped at a contract boundary
```
