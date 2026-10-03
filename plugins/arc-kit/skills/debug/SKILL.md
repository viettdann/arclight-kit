---
name: debug
description: "Find and fix the root cause of a bug: pin the symptom in one line, reproduce it with a command that fails now, narrow it with ranked hypotheses and the cheapest experiment that could disprove each (recent changes and git bisect first), fix it once in the shared path, and keep the repro as a regression test seen failing before the fix. Use when something errors, crashes, returns the wrong result, a test fails, or behavior regressed (\"debug\", \"fix this bug\", \"why does this fail\", \"sửa lỗi\", \"tại sao lỗi\", \"bị lỗi\", \"không chạy\", \"crash\", \"test fail\", \"trước chạy được giờ hỏng\"). Asked only why, it stops at the diagnosis. Not for a UI control that does nothing or resets state (see arc-design:state-check), rendering defects (see arc-design:ui-check), or build errors with an obvious message."
argument-hint: "[symptom, error, or failing test]"
---

# Debug

Find the cause before changing code, then fix it once, with a test that failed before the fix. A diff that makes the symptom disappear without a confirmed cause is a guess.

## 1. Pin the symptom

- Write it as one line: `Under X, it does Y; expected Z.` Take X from the report, stack trace, or logs. If Z is unclear, ask.
- Collect what exists: the full stack trace, the log lines, the request or input, versions, environment. Start from the first error in time, not the loudest; later errors are often its consequences.
- Production-only failure: work from the logs. Filter by correlation or trace id, read about two minutes around the first error, and list deploys, config changes, and flag flips in the hour before it.

## 2. Reproduce

- Get a command that fails now: an existing failing test, a new test at the lowest level that shows the bug (unit before integration, never e2e), or a script, `curl`, or REPL call.
- Intermittent: run the repro in a loop (20 runs or more) and record the failure rate. A fix is verified only when the same loop shows zero.
- Can't reproduce: don't write a fix. Compare where it fails and where it doesn't (versions, config, data, timing), add a log line at the suspected boundary, and ask the user for the missing input. If it still won't reproduce, report ranked hypotheses with the evidence for each and the observation that would decide between them; fix without a repro only on the user's go-ahead.

## 3. Narrow

- Recent change first. "It used to work": `git log --since=<date> -- <files in the stack trace>`. A known good commit: `git bisect run <repro>` in a separate worktree (`git worktree add ../<repo>-bisect <good-sha>`), never in the shared one, then `git worktree remove` it. Uncommitted changes are not in that worktree; test them where they are.
- List two or three hypotheses, ranked, each with its evidence. For the top one, run the cheapest experiment that could disprove it: a log line, an assertion, a breakpoint, a grep, one changed input. Change one thing per experiment and record the result as confirmed or ruled out, with why.
- Log the value that actually reaches the failing line; don't infer it from reading code.
- Temporary log lines start with `DEBUG-<slug>` so one grep removes them all.
- Asked only why: report the diagnosis (section 5 without Fix and Test) and stop.

## 4. Fix

- Fix the cause, not the symptom. Not a fix: a try/catch that swallows, a null check or default for a value that should never be missing, a retry, sleep, or longer timeout for a race, a widened type, a skipped or loosened test. When the cause is outside the codebase (library bug, external API), a guard is acceptable with a one-line comment naming the cause and the upstream issue.
- Grep every caller of the function you change and put the fix in the shared path. Search for the same pattern in sibling code; fix the instances in scope and list the rest.
- The repro becomes the regression test. If it was a script and the project has a test harness, turn it into a test. Run it before applying the fix and see it fail for the bug's reason; a test that never failed proves nothing.
- Stop and ask before a schema change, a data fix in a shared or production environment, a config change on a shared environment, or a rollback.

## 5. Verify and report

- The repro passes, the tests of every touched package pass against the baseline, and `grep -rn "DEBUG-<slug>"` finds nothing.

```markdown
**Symptom**: Under X, it does Y; expected Z
**Cause**: file and symbol, one line on the mechanism
**Evidence**: the experiment that confirmed it
**Ruled out**: hypothesis: why
**Fix**: what changed, where
**Test**: path and name; failed before the fix, passes after
**Same pattern elsewhere**: fixed, or left with locations
```

State confidence only when no experiment confirmed the cause.
