# Writing defaults

**Documentation is imperative, not narrative.** State what to do, not choice history or past attempts. No `## Rationale`, `## Background`, `## Alternatives`, or "why chosen" sections. Include only what the reader executes.

**A comment earns its place or it is removed.** Comment only what code can't say: a non-obvious invariant, a constraint, a deliberate gotcha, the ceiling of a deliberate shortcut and when to lift it. Every comment is one physical line; a comment that doesn't fit on one line says too much, so cut it to the single invariant instead of wrapping. Avoid prose blocks, banners, ASCII dividers, and module-header narration. Preserve required license headers, generated annotations, and tooling directives.

For comment examples, read `references/comment-examples.md` when needed.
