# Agent turns: Status, Steps, Approvals, Diffs, Context

Contents: turn status · steps · reasoning · questions and approvals · diffs · context · background tasks · composer while running · scroll · checks

## Turn status

- Each turn shows one status line in one of five states: running (naming the current step), waiting for you, done, failed, or stopped, told apart by text and shape, never color alone.
- Elapsed time appears after about 5s.
- The running indicator is static under `prefers-reduced-motion: reduce`.
- One `aria-live="polite"` region per thread announces status transitions only, never tokens.

## Steps

- Each tool call is one row, verb plus object ("Read src/app.ts", "Ran npm test"), with its state (running, done, failed, skipped) and its duration when over 1s; rows appear in run order and never reorder.
- When the turn ends the group collapses to a summary row ("Ran 6 steps · 1 failed") with failed steps left expanded.
- An expanded step shows input and output in monospace, long output truncated behind "Show all".

## Reasoning

- Collapsed by default, labeled with its duration ("Thought for 12s"), "Thinking…" while running.
- Styled quieter than the answer and never like it.
- Excluded from "Copy answer".

## Questions and approvals

- When the agent blocks on the user, turn status reads waiting and the card is the most prominent element in the thread.
- The card pins above the composer when scrolled out of view.
- It shows the exact command, file, or diff affected.
- Buttons name the action ("Run command", "Deny"), never Yes/No.
- Focus moves to the card only when the composer is not focused.
- Actions that send, delete, or run a command outside a sandbox have no Enter default.
- Irreversible actions follow `destructive.md`.
- Once answered, the card collapses to a record of the choice and accepts no second answer; a cancelled turn marks its open card expired.

## Diffs

- Unified in panes under about 1000px, split at or above, and the user's choice persists.
- Each file has a header with its path and +/− counts.
- Added and removed lines carry both a sign and a color.
- Long unchanged runs collapse behind an expand control.
- A proposed diff offers accept and reject per file, per hunk when the backend supports it.
- The applied state is shown separately from the generated one.

## Context

- The meter is a native `<meter>`, or `role="meter"` with `aria-valuenow`, `aria-valuemin`, `aria-valuemax` on a custom element (`components.md`, Picking the role), and never a color-only ring.
- It shows a percentage, and used/limit on hover and focus.
- At about 80% it warns with the action (compact, new session) next to it.

## Background tasks

- A task that outlives its turn has its own entry with a status.
- Completion or failure posts a notice in the thread or a toast linking to the result; failure notices persist until seen.
- Counts follow the badge rules in `feedback.md` (Badges).

## Composer while running

- Typing stays enabled, and the UI states whether a sent message queues or steers the running turn.
- Stop replaces Send.
- Each session keeps its own draft when switching sessions.
- Prompt box rules stay in `feedback.md` (Generated content).

## Scroll

- While the user is scrolled up, new steps never move the reading position.
- A "Jump to latest" button shows the count of new items.

## Checks

- [ ] Every turn shows one of running, waiting, done, failed, or stopped by text and shape, with elapsed time after ~5s, a static indicator under reduced motion, and a polite live region that announces transitions only.
- [ ] Each step is a verb-plus-object row with state and duration, in run order, collapsed to a summary at turn end with failures expanded.
- [ ] Reasoning is collapsed, labeled with its duration, quieter than the answer, and left out of "Copy answer".
- [ ] A blocking question sets status to waiting, pins above the composer, shows the exact action, names its buttons, has no Enter default for risky actions, and records its answer once.
- [ ] Diffs pick unified or split by width, show sign and color, collapse unchanged runs, and keep proposed and applied states apart.
- [ ] The context meter has a meter role with values, a percentage, used/limit on hover and focus, and a warning with its action near 80%.
- [ ] A background task outliving its turn has its own entry, and its failure notice persists until seen.
- [ ] While a turn runs, typing stays enabled, queue or steer is stated, Stop replaces Send, and each session keeps its draft.
- [ ] New steps never move a user who scrolled up, and "Jump to latest" shows the count of new items.
