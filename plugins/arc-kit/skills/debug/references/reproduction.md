# Debug detailed instructions

Resolve all relative paths in this reference from the parent skill directory containing `SKILL.md`, not from `references/`.

## 2. Reproduce

- Get a command that fails now, trying in this order: an existing failing test; a new test at the lowest level that shows the bug (unit before integration, never e2e); a `curl` or script against the running app; a CLI call on a fixture input diffed against known-good output; a captured request, payload, or event replayed through the code path; a throwaway harness that calls the failing path with its dependencies stubbed; the same input run through the old and new version and diffed. When only a person can trigger it (a click, a device), copy `scripts/hitl-loop.sh`, edit its steps, and run it so the user's observations come back as `KEY=VALUE` lines.
- Tighten it before moving on: assert the reported symptom (the wrong value, the exact error), not "didn't crash"; pin time, seed randomness, and isolate files and network so every run gives the same verdict; cut setup until it runs in seconds.
- Intermittent: run the repro in a loop (20 runs or more) and record the failure rate. Raise the rate (more runs, parallel runs, stress, a sleep in the suspected window) until it fails often enough to test against. A fix is verified only when the same loop shows zero.
- Passes alone, fails in the suite: an earlier test leaves state behind (a file, a static or singleton, a database row, an environment variable, a faked clock). Run each candidate test followed by the failing one, or halve the list of tests that run before it, until one pair fails.
- Done when you have one command you have already run, whose output shows the user's symptom, and that you can rerun unattended with the same result. Don't read code to build a theory before it exists.
- Minimise: cut inputs, steps, data, and config one at a time, rerunning after each cut, until removing any remaining piece makes it pass. The minimal repro becomes the regression test.
- Can't reproduce: don't write a fix. Compare where it fails and where it doesn't (versions, config, data, timing), add a log line at the suspected boundary, and ask the user for the missing input: access to an environment that fails, a captured artifact (HAR, log dump, recording with timestamps), or permission for temporary instrumentation. If it still won't reproduce, report ranked hypotheses with the evidence for each and the observation that would decide between them; fix without a repro only on the user's go-ahead.
- Replace secrets with `<REDACTED>` in every command, output, and artifact you show, and keep credentials in environment variables rather than in the repro.
