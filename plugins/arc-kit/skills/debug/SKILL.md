---
name: debug
description: "Find and fix the root cause of a bug: pin the symptom in one line, reproduce it with a command that fails now, narrow it with ranked hypotheses and the cheapest experiment that could disprove each (recent changes and git bisect first), fix it once in the shared path, and keep the repro as a regression test seen failing before the fix. Use when something errors, crashes, returns the wrong result, a test fails, or behavior regressed (\"debug\", \"fix this bug\", \"why does this fail\", \"sửa lỗi\", \"tại sao lỗi\", \"bị lỗi\", \"không chạy\", \"crash\", \"test fail\", \"trước chạy được giờ hỏng\"). Asked only why, it stops at the diagnosis. Not for a UI control that does nothing or resets state (see the arc-design state-check skill), rendering defects (see the arc-design ui-check skill), or build errors with an obvious message."
---

# Debug

Find the cause before changing code, then fix it once, with a test that failed before the fix. A diff that makes the symptom disappear without a confirmed cause is a guess.

Follow applicable AGENTS.md instructions. Use Vietnamese in chat and English in files unless the user requests otherwise. Resolve `scripts/` paths relative to this `SKILL.md`; run commands from the project root.

## 1. Pin the symptom

- Write it as one line: `Under X, it does Y; expected Z.` Take X from the report, stack trace, or logs. If Z is unclear, ask.
- Collect what exists: the full stack trace, the log lines, the request or input, versions, environment. Start from the first error in time, not the loudest; later errors are often its consequences.
- Production-only failure: work from the logs. Filter by correlation or trace id, read about two minutes around the first error, and list deploys, config changes, and flag flips in the hour before it.

## 2. Reproduce

- Get a command that fails now, trying in this order: an existing failing test; a new test at the lowest level that shows the bug (unit before integration, never e2e); a `curl` or script against the running app; a CLI call on a fixture input diffed against known-good output; a captured request, payload, or event replayed through the code path; a throwaway harness that calls the failing path with its dependencies stubbed; the same input run through the old and new version and diffed. When only a person can trigger it (a click, a device), copy `scripts/hitl-loop.sh`, edit its steps, and run it so the user's observations come back as `KEY=VALUE` lines.
- Tighten it before moving on: assert the reported symptom (the wrong value, the exact error), not "didn't crash"; pin time, seed randomness, and isolate files and network so every run gives the same verdict; cut setup until it runs in seconds.
- Intermittent: run the repro in a loop (20 runs or more) and record the failure rate. Raise the rate (more runs, parallel runs, stress, a sleep in the suspected window) until it fails often enough to test against. A fix is verified only when the same loop shows zero.
- Passes alone, fails in the suite: an earlier test leaves state behind (a file, a static or singleton, a database row, an environment variable, a faked clock). Run each candidate test followed by the failing one, or halve the list of tests that run before it, until one pair fails.
- Done when you have one command you have already run, whose output shows the user's symptom, and that you can rerun unattended with the same result. Don't read code to build a theory before it exists.
- Minimise: cut inputs, steps, data, and config one at a time, rerunning after each cut, until removing any remaining piece makes it pass. The minimal repro becomes the regression test.
- Can't reproduce: don't write a fix. Compare where it fails and where it doesn't (versions, config, data, timing), add a log line at the suspected boundary, and ask the user for the missing input: access to an environment that fails, a captured artifact (HAR, log dump, recording with timestamps), or permission for temporary instrumentation. If it still won't reproduce, report ranked hypotheses with the evidence for each and the observation that would decide between them; fix without a repro only on the user's go-ahead.
- Replace secrets with `<REDACTED>` in every command, output, and artifact you show, and keep credentials in environment variables rather than in the repro.

## 3. Narrow

- Recent change first. "It used to work": `git log --since=<date> -- <files in the stack trace>`. A known good commit: `git bisect run <repro>` in a separate worktree (`git worktree add ../<repo>-bisect <good-sha>`), never in the shared one, then `git worktree remove` it. Install dependencies and copy the untracked config the repro needs (`.env`, `appsettings.Development.json`) into it first, and make the repro exit 125 on a commit that doesn't build so bisect skips it instead of blaming it. Uncommitted changes are not in that worktree; test them where they are.
- Similar code that works (another endpoint, the same flow for another entity, the previous version): list every difference between it and the failing path, however small, and test the differences before dismissing any.
- A failure that crosses layers (UI → API → service → database, job → queue → worker): in one run, log what enters and leaves each boundary, then start from the first boundary where the value is wrong.
- List three to five hypotheses, ranked, each with its evidence and the prediction it makes: `If X is the cause, changing Y makes the failure disappear.` A hypothesis without a prediction gets sharpened or dropped. Show the ranked list to the user before testing (they may already have ruled one out) and continue without waiting for a reply.
- For the top one, run the cheapest experiment that tests its prediction: a breakpoint, a log line, an assertion, a grep, one changed input. Change one thing per experiment and record the result as confirmed or ruled out, with why.
- Slow, not wrong: measure a baseline first (a timing harness, the profiler, the query plan), then bisect or cut against that number; logs rarely find a performance regression.
- Searching an error externally: strip hosts, IPs, internal paths, SQL, tokens, and customer data first; search only the error class or message template and the library name.
- Log the value that actually reaches the failing line; don't infer it from reading code.
- Temporary log lines start with `DEBUG-<slug>` so one grep removes them all.
- Asked only why: report the diagnosis (section 5 without Fix and Test) and stop.

## 4. Fix

- Fix the cause, not the symptom. Not a fix: a try/catch that swallows, a null check or default for a value that should never be missing, a retry, sleep, or longer timeout for a race, a widened type, a skipped or loosened test. When the cause is outside the codebase (library bug, external API), a guard is acceptable with a one-line comment naming the cause and the upstream issue.
- Grep every caller of the function you change and put the fix in the shared path. Search for the same pattern in sibling code; fix the instances in scope and list the rest.
- The repro becomes the regression test. If it was a script and the project has a test harness, turn it into a test. Run it before applying the fix and see it fail for the bug's reason; a test that never failed proves nothing. Put it where it exercises the bug the way the call site does; when the only reachable level can't (the bug needs two callers or the full chain, and a unit test can't build that), don't write a shallow test that passes either way: report the missing seam as a finding.
- Three fixes that each failed or moved the symptom somewhere else: stop. Report the pattern (each fix exposed new coupling or shared state) as a likely design problem and ask before a fourth attempt.
- Stop and ask before a fix that touches more than 5 files, a schema change, a data fix in a shared or production environment, a config change on a shared environment, or a rollback.

## 5. Verify and report

- The repro passes, the tests of every touched package pass against the baseline, and `grep -rn "DEBUG-<slug>"` finds nothing.

```markdown
**Symptom**: Under X, it does Y; expected Z
**Cause**: file and symbol, one line on the mechanism
**Evidence**: the experiment that confirmed it
**Ruled out**: hypothesis: why
**Fix**: what changed, where
**Test**: path and name; failed before the fix, passes after (or the missing seam)
**Same pattern elsewhere**: fixed, or left with locations
```

State confidence only when no experiment confirmed the cause.
