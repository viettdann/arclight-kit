# Test runner brief

A worker brief for running a test command or the project's suite and returning only the counts and the failures, so long test output stays out of the main context. Use it for a full or slow suite run, a baseline before a change, or a comparison against one (executor Phase 4, refactor baseline and verify, verifier checks). A fast one-file test run stays inline.

When the user or applicable instructions authorize delegation and the runtime provides it, pass this file's Rules, Cause, and Report sections to one worker on the inherited session model, with the inputs below. Otherwise run the suite inline under the same rules and keep only the report in the conversation.

The worker runs tests and reports what failed. It never fixes anything.

## Input

The caller passes some of:

- The command or filter to run. Without one, find it in this order: the project's `AGENTS.md`, `package.json` scripts, a `Makefile` or `justfile`, test projects in the `.sln` (`dotnet test <sln>`), `pyproject.toml`.
- A baseline: tests already failing before the change.
- A scope: packages, projects, or paths.

## Rules

- Never edit, create, or delete files, never install packages, never run git commands that change state, and never change test configuration to get a run through. If the run can't start (missing dependency, broken build, no database), report that as the result.
- Don't run e2e suites unless the given command includes them.
- A run that produces no output for several minutes is reported as hung, with the last lines it printed.
- For each failing test, run that test alone up to three more times. Any pass makes it flaky; three failures make it deterministic.

## Cause

Give each failure one cause and the one line of evidence behind it:

- `code`: the assertion shows the implementation returning the wrong value or throwing.
- `test`: the test asserts something the change intentionally altered, or its setup is wrong.
- `env`: missing service, port, file, variable, or dependency; the failure is outside the code under test.
- `flaky`: passed on a rerun.
- `fixture`: a missing or stale mock, fixture, snapshot, or seed.

## Report

Return only this, with no list of passing tests, no coverage, and no fix suggestions:

```
Command: <command>
Result: <total> total, <passed> passed, <failed> failed, <skipped> skipped (<duration>)

FAIL <test name> (<file>:<line>) [<cause>, deterministic|flaky]
  <assertion or error message, at most 5 lines>
  Evidence: <one line>
  Baseline: new | already failing
```

Without a baseline, omit the Baseline line. When everything passes, return the first two lines only.
