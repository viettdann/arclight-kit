# Logic, contracts, and tests review

Trace each changed code path with concrete inputs; style and size are out of scope, and security goes to its own reviewer. Category `correctness` for items 1-7 and 11, `contract` for items 8-9, `tests` for item 10. For items 1-7, report only defects with an input or state that triggers them, and name that input or state in `issue`.

## Guards are run, not read

A guard the diff adds (a validator, regex, lint rule, hook, or CI check) is verified by making it fire: create a directory with `mktemp -d "${TMPDIR:-/tmp}/verifier-guard.XXXXXX"`, copy in the input it guards and the config and paths it reads, break the copy the way the guard exists to catch, and run the guard on it. A guard that passes its own violation is a high `correctness` finding; put the command in `issue`. Only when the guard still cannot run outside the repository, list it under `not_verified` with the reason. Never write inside the repository; `git status --short` must match at the start and the end. Authentication, authorization, injection, and secrets guards belong to the security reviewer.

## Checks

1. **Logic and edge cases**: empty, null, zero, negative, and maximum values; off-by-one and wrong boundary comparisons; inverted conditions; operations in the wrong order
2. **Fix in one caller only**: a bug fixed at the call site the task names while other callers of the same function or path keep the defect. Grep every caller; name the unfixed ones in `issue`.
3. **New enum or union value**: grep the sibling values and read every `switch`, allowlist array, filter, and if/else chain that consumes them, outside the diff included; a consumer that lets the new value fall through to a wrong default is the defect.
4. **Error paths**: errors swallowed or logged and then ignored, a caught failure returned as success, a fallback default that hides missing data, a failure that leaves partial state behind
5. **Conditional side effects**: one branch skips a side effect the others perform (save, audit entry, cache invalidation, notification); a log line claims an action the code skipped; an event or webhook fires only on the happy path
6. **Concurrency**: check-then-act races, mutable state shared across requests or threads, a missing `await`, fire-and-forget work whose failure nobody observes
7. **Data migrations**:
   - `NOT NULL` added to a column that holds NULLs, with no backfill or default first
   - An index created on a large table without `CONCURRENTLY` (Postgres) or the engine's online option (SQL Server `ONLINE = ON`); in EF Core, `IsCreatedConcurrently()` (Npgsql) or `IsCreatedOnline()` (SQL Server)
   - A down migration (`Down()` in EF Core) that does nothing or can't restore what `Up()` dropped
   - A backfill on a large table in one unbatched `UPDATE`
   - Old code running against the new schema during deploy: a column renamed or dropped while the previous release still reads or writes it, instead of add, migrate, then drop across releases
8. **Contract breaks**: a changed exported signature, HTTP route, DTO or serialized field name, string enum value, ORM mapping, event name, or config key whose consumers the diff does not update. Search the whole repo for consumers, string-based lookups included; the build stays green when a serialized name changes. Fix: update the consumers, or restore the old name when the change was not planned.
9. **API contract skill**: when the diff touches ASP.NET controllers or DTOs with TypeScript or JavaScript consumers, also call the Skill tool with `mgi-kit:api-contract` when it appears in your skill list; otherwise list this check under `not_verified`.
10. **Tests**:
   - **Missing**: a bug fix with no regression test; a new or changed branch or contract with no test when a plausible regression in it can be named; an authorization check with no test for the denied case
   - **Junk**: tests that assert a constant or string copied from the code, markup or style (a border, a class, a label), only that a function or command was called, framework or language behavior, or what the type checker already proves; tests added to match the project's existing tests rather than to catch a named regression. A characterization test pinned before a refactor is not junk
   - **Weak**: tests that assert implementation details (mock call counts, private state) instead of observable behavior, or that pass whatever the code does, including an expected value computed by the code under test or its helpers instead of a hand-derived literal
   - **Weakened**: tests the diff deletes, skips (`.skip`, `xit`, `[Ignore]`, `Skip =`), or loosens without a planned behavior change; snapshot or approved files (`__snapshots__/`, `*.snap`, `*.verified.*`) the diff regenerated without a planned behavior change
   - **Nondeterministic**: a test that depends on the clock, the timezone, the order of unordered results, or the real network; a fixed sleep or delay standing in for "the async work has finished" instead of waiting on that condition with a timeout
   - **Test-only production code**: a method or property added to production code only for tests to call
   - **Wrong mocks**: a mock of the very side effect the test is meant to verify; a mock response missing fields the real API returns, so the code that reads them never runs under test
11. **React**: when the diff touches React components, hooks, or stores, also check the rules marked (correctness) in `react-performance.md`, in the same directory as this checklist
