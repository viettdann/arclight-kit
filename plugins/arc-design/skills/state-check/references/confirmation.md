# State Check detailed instructions

Resolve all relative paths in this reference from the parent skill directory containing `SKILL.md`, not from `references/`.

## 4. Confirm

A trace is a hypothesis. For each P1 and P2, confirm it before reporting it as fact: a failing test with the project's component test setup (React Testing Library with `user-event`, Vue Test Utils) that clicks the control and asserts the promised state, or a reproduction in a dev server that is already running. When neither is possible, report the finding as `[unconfirmed]`. Without a fix request, a run leaves the repo as it found it: delete the confirming tests after recording their result (name and failure in the report); step 6 recreates them when the fix is asked for.

Optional runtime confirmation for a control suspected to do nothing, when a page that renders it is already running: `node ../design/scripts/screenshot.mjs <url> /tmp/state-check.png --click <css> --ax-diff` (repeat `--click` for a sequence; `--eval` or `--wait-for` to reach the state first; `--cookie` or `--header` for a page behind login). It clicks with the real pointer and prints how the accessibility tree changed; "no accessibility-tree change" confirms the control does nothing visible to assistive technology, and "the pointer lands on …" names an element covering it (a wiring defect, step 1). A change that only adds the wrong state still needs the trace. It runs outside the project: add no e2e tooling or test files for it.
