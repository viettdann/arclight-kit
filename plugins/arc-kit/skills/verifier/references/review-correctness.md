# Correctness, security, and tests review

Trace each changed code path with concrete inputs; style is out of scope. Category `correctness` for items 1-4 and 7, `security` for item 5, `tests` for item 6. For items 1-4, report only defects with an input or state that triggers them, and name that input or state in `issue`.

## Guards are run, not read

A guard the diff adds (a validator, authorization check, regex, lint rule, hook, or CI check) is verified by making it fire: create a directory with `mktemp -d "${TMPDIR:-/tmp}/verifier-guard.XXXXXX"`, copy in the input it guards and the config and paths it reads, break the copy the way the guard exists to catch, and run the guard on it. A guard that passes its own violation is a high finding, category `security` for an authentication, authorization, injection, or secrets guard and `correctness` otherwise; put the command in `issue`. Only when the guard still cannot run outside the repository, list it under `not_verified` with the reason. Never write inside the repository; `git status --short` must match at the start and the end.

## Checks

1. **Logic and edge cases**: empty, null, zero, negative, and maximum values; off-by-one and wrong boundary comparisons; inverted conditions; operations in the wrong order
2. **Fix in one caller only**: a bug fixed at the call site the task names while other callers of the same function or path keep the defect. Grep every caller; name the unfixed ones in `issue`.
3. **Error paths**: errors swallowed or logged and then ignored, a caught failure returned as success, a fallback default that hides missing data, a failure that leaves partial state behind
4. **Concurrency**: check-then-act races, mutable state shared across requests or threads, a missing `await`, fire-and-forget work whose failure nobody observes
5. **Security**:
   - **Injection**: untrusted input reaching SQL, shell commands, HTML, file paths, or outbound URLs without parameterization, encoding, or validation
   - **Access control**: a new endpoint or action without an authentication or authorization check, including access to another user's records
   - **Secrets**: secrets in code, logs, or error messages
   - **Dependencies**: a dependency the diff adds whose exact package name does not exist in the registry, or that the ecosystem audit (`npm audit`, `dotnet list package --vulnerable`, `pip-audit`) reports as high or critical; a version ceiling or pin the diff writes that excludes the registry's current release with no reason stated in the diff or plan (check with `npm view <pkg> version`, `dotnet package search <pkg> --exact-match`, or `pip index versions <pkg>`; bounds written from memory go stale)
   - **Frontend sinks**: `dangerouslySetInnerHTML`, `innerHTML`, `v-html`, or Markdown rendered with raw HTML (`rehype-raw`) on data that isn't sanitized; an `href` or `src` built from user data without a scheme check (`javascript:`); auth tokens kept in `localStorage`; a `message` event handler that doesn't check `event.origin`; a redirect to a `returnTo` or `redirect` parameter without an allowlist
6. **Tests**:
   - **Missing**: new or changed behavior with no proportionate test (documentation, metadata, and mechanical low-impact edits need none)
   - **Weak**: tests that assert implementation details (mock call counts, private state) instead of observable behavior, or that pass whatever the code does
   - **Weakened**: tests the diff deletes, skips (`.skip`, `xit`, `[Ignore]`, `Skip =`), or loosens without a planned behavior change; snapshot or approved files (`__snapshots__/`, `*.snap`, `*.verified.*`) the diff regenerated without a planned behavior change
   - **Test-only production code**: a method or property added to production code only for tests to call
   - **Wrong mocks**: a mock of the very side effect the test is meant to verify; a mock response missing fields the real API returns, so the code that reads them never runs under test
7. **React**: when the diff touches React components, hooks, or stores, also check the rules marked (correctness) in `react-performance.md`, in the same directory as this checklist; a rule there that says to report under security goes under item 5
