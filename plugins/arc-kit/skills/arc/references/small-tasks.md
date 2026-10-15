# Small tasks

When the full skill (`brainstorming`, `executor`, `debug`) would be overhead, handle the task inline this way. A task that grows past it (several modules, a schema change, a multi-step plan) moves to the full skill.

**Spec an idea.** Ask at most three questions, only ones whose answer changes what gets built; take the default for the rest and state it. In chat, write the user's steps, the inputs and their validation, the success criterion, each screen's loading, empty, failure, and success states, and an acceptance checklist of `- [ ]` items a person can check by using the result. Nothing goes on disk unless asked.

**Build a scoped feature.** Follow the project's structure and styling and use the tools already installed; name a new dependency and why before adding it. A UI feature ships its loading, failure, and success states. Touch only what the feature needs. End with the changed files, any dependency added, and the steps to verify it by hand.

**Diagnose an error.** Trace the cause from the error and the code before editing. Report what was shown (command output, a log line, a reproduced run) apart from what is inferred, and label the inference. When a log or input is missing, ask for that exact one: which file, time window, or request. Apply the smallest fix that removes the cause, say in one line why it works, and give the steps that reproduce the bug before the fix and verify it after.
