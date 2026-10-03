# Comments and docs review

Review every comment the diff adds or changes, every changed documentation file (plans, specs, READMEs), and the READMEs and config templates that reference what the diff changed. Category `comments` for code comments, `docs` for documentation files.

Skill files (anything under a skill's directory, including `SKILL.md` and `agents/openai.yaml`) are out of scope unless your assignment says the user asked to review them: their rationale is instruction for the model, not narrative.

A comment stays only for what code cannot say: a non-obvious invariant, a constraint, a deliberate gotcha, or the ceiling of a deliberate shortcut and when to lift it. Documentation states what to do; the reader executes from it.

1. **Comments that restate code**: what the next line does, data flow, usage, or anything names, types, and imports already show. Fix: delete.
2. **Multi-line comments**: any comment longer than one physical line, including one thought wrapped across lines and prose `/** */` blocks. Fix: cut to the single invariant on one line, or delete.
3. **Banners and headers**: section dividers, ASCII rules, module-header prose. Fix: delete.
4. **Narrative documentation**: rationale, background, alternatives considered, what a change replaced, what was tried before, and any `## Rationale`, `## Background`, or `## Alternatives` section. Fix: delete, or rewrite as the instruction the reader executes.
5. **Filler**: sections or boilerplate added to look complete, recaps, closing summaries. Fix: delete.
6. **Stale references outside the diff**: a README command, `.env.example` key, `appsettings*.json` section, or config template entry that the diff's code renamed, removed, or added without a matching change. Fix: update the line; update task-related files under `docs/` only within authorized editing scope, and leave them unstaged unless explicitly requested; otherwise report them.

Lint suppressions, type-checker directives, license headers, and shebangs are not prose comments; leave them.
