# Codex migration

## Scope

Convert this branch into a Codex plugin marketplace with three independently installable plugins and the existing 14 skills. Preserve the design references, browser helpers, source scanners, contract audit, and upstream license notice. Keep changes reviewable on the `codex` branch.

## Findings and implementation

| Original coupling | Codex implementation | Evidence in this branch |
| --- | --- | --- |
| `.claude-plugin/marketplace.json` with Claude installation commands | Repo marketplace with local source objects, installation policies, and categories | `.agents/plugins/marketplace.json`, `README.md` |
| Claude-only per-plugin manifests and `userConfig` options | Portable identity in root `plugin.json`; OpenAI settings in `extensions.com.openai`; matching `.codex-plugin/plugin.json` fallback for existing Codex hosts | Each `plugins/*/plugin.json` and `plugins/*/.codex-plugin/plugin.json` |
| `disable-model-invocation` and unsupported trigger metadata | Skill UI metadata and `policy.allow_implicit_invocation: false` for the two explicit-only skills | `skills/*/agents/openai.yaml`; `arc` and `fresh-air` policies |
| `CLAUDE_SKILL_DIR` and `CLAUDE_PLUGIN_ROOT` embedded in instructions | Paths relative to the loaded skill; resolve absolute script paths before executing from the project directory | `arc-design/skills/*/SKILL.md` |
| `AskUserQuestion`, named Claude models, fixed agent count, fork arguments | Available Codex tools, inherited model selection, runtime concurrency limits, inline fallback | `arc-kit/skills/executor/SKILL.md`, `verifier/SKILL.md` |
| Repeated approval gates even after implementation was requested | Retain authorization across discovery and execution; ask only about unresolved scope or material choices | `brainstorming/SKILL.md`, its examples, and `arc/SKILL.md` |
| Comment hook expects `Edit` / `Write` and `file_path` | Parse `apply_patch` from `tool_input.command`; resolve changed lines in each resulting file | `arc-kit/scripts/comment-lint.py`: `parse_patch`, `patch_added` |
| Comment options supplied through Claude plugin configuration | Explicit `ARC_COMMENT_LINT_ENABLED` and `ARC_COMMENT_LINT_WIDTH` environment variables | `comment-lint.py`: `option`; README option table |
| `fresh-air` edits Claude `settings.local.json`, skill overrides, and instruction exclusions | Reversible owned blocks of Codex `[[skills.config]]` entries; explicit operation on project skills | `arc-kit/skills/fresh-air/` |
| Handoff assumes `/clear`, Claude session variables, and `claude --resume` | Verified handoff file; `codex resume` only with a known session ID; compaction can continue normally | `arc-kit/skills/handoff/` |
| Claude plugin agent `test-runner` (fixed model) | Worker brief run delegated when the runtime allows it, inline otherwise; inherited model | `arc-kit/skills/executor/references/test-runner.md` |
| `arc-compact.sh` greps the Claude transcript for `/arc-kit:arc` | `SessionStart` on `compact` runs `arc-compact.py`, which reads user messages in the Codex transcript for `$arc`, `arc-kit:arc`, or an injected `<name>arc</name>` block | `arc-kit/scripts/arc-compact.py`, `arc_compact_test.py` |
| `conventions` writes path-scoped `.claude/rules/*.md` | Marked conventions block in the `AGENTS.md` at each layer's root, with an `Applies to` glob | `arc-kit/skills/conventions/SKILL.md` |
| `disable-model-invocation` on handoff and conventions | `policy.allow_implicit_invocation: false`, enforced by the validator | `skills/*/agents/openai.yaml` |

Paths in the last column are under `plugins/` unless otherwise stated. Historical changelog entries describe the old releases; active skill instructions and runtime configuration target Codex.

## Sync with the Claude line

The 2.2.0 releases (arc-design, arc-kit) and 1.2.0 (mgi-kit) integrate `main` through `f2bb39d` (Claude arc-kit 1.8.0, arc-design 1.5.0, mgi-kit 0.3.0). Merge commit `8acdccd` records both histories; the following adaptation commit ports runtime differences. The previous sync used a linear imported history through `8e91238`, with Codex adaptations on top, rather than a two-parent merge.

Future syncs fetch `origin` and merge `origin/main` into `codex`; use fast-forward when possible and an ordinary merge when histories diverge. Do not squash or cherry-pick the upstream batch. `git merge-base codex origin/main` identifies the shared upstream point, and `git log codex..origin/main` lists pending commits. Keep subsequent Codex adaptations separate when practical.

Authorization persists across discovery and execution. New workflow guidance retains evidence validation, fresh-context design review when delegation is allowed, and explicit reporting of decisions made without asking. Claude-only tools, approval resets, and platform paths are not carried over.

The new destructive guard uses `ARC_DESTRUCTIVE_GUARD_ENABLED`, disabled by default, and `${PLUGIN_ROOT}`. Codex recognizes shell calls as `Bash`, but does not support the upstream `ask` permission output: both ask and deny findings therefore block with `deny`. The reason directs intended execution outside Codex. This difference was checked against [the official hook contract](https://learn.chatgpt.com/docs/hooks) on 2026-10-05. Skill lint now checks root Codex manifests and discovery metadata, including the upstream 930-character description budget.

## Package behavior

The host reads the repo marketplace, resolves each plugin from the repository root, and loads skills from that plugin's `skills/` directory. Skill descriptions and UI metadata support discovery; the detailed instructions and references load only as needed. Optional sibling plugins are discovered through the active skill catalog, never a hard-coded cache location.

Current OpenAI packaging guidance prefers root `plugin.json` with an OpenAI extension. The compatibility manifest is included for Codex hosts that still consume `.codex-plugin/plugin.json`. The validator requires identical identity and OpenAI settings across both forms, preventing a newer host and an older host from receiving different hooks or descriptions.

The comment hook receives completed `apply_patch` calls, maps added lines to final file content, and returns feedback through stderr and exit status 2. A standalone file check covers edits made through other tools. The hook does not roll back edits or claim full enforcement.

`fresh-air` changes skill enablement in the selected Codex user configuration only when explicitly requested. Its restore operation removes its own entries and preserves unrelated configuration. It cannot erase instructions already loaded into a session; start a new session after changes. It does not disable project `AGENTS.md`, MCP servers, or plugin hooks.

## Codex workflow optimization

- Keep the original quality checks and domain references while removing hard-coded Claude tool and model assumptions.
- Make planning proportional to the task and reuse the authorization in the user's request. Discussion-only requests remain discussion-only.
- Use scoped file searches and load only relevant reference documents.
- Delegate independent work only when the active runtime permits it; specify file ownership and report back evidence. Run the same work inline when delegation is unavailable.
- Match verification to behavior and risk. Avoid mandatory TDD for documentation and minor reversible edits; retain regression checks for scripts that process patches or write user configuration.
- Treat handoff notes as verified supplemental context. Resolve stale notes against the current repository.
- Keep source and runtime configuration portable: no dependency on a particular user's Codex cache, agent model, or installed connector.

## Verification

The 2026-10-05 sync passed 145 tests across package and skill lint, comment lint, arc reload, destructive guard, diff collection, fresh-air, and the tell scanner. Package validation, Python compilation, JavaScript syntax checks, and `git diff --check` also passed. Browser behavior and live host installation were not exercised.

Run the commands in the README. The package validator checks the marketplace, both manifest forms, skill discovery metadata, explicit invocation policies, hook wiring, and bundled references. It validates this repository's conventions rather than implementing the entire external plugin schema.

Regression tests exercise manifest drift, path escapes, missing metadata and references, actual Codex patch payloads, and fresh-air disable/restore behavior in temporary configurations. Existing design helper scripts remain present and get Python/JavaScript syntax checks; browser rendering still requires a target page and a local browser.

Migration checks passed: 11 package regression tests, 39 comment-lint tests, and 18 fresh-air tests (68 total). The fresh-air suite includes marker text inside TOML multiline strings, which must be rejected without modifying the config. Python compilation, syntax checks for all four JavaScript helpers, a contrast-helper smoke check, and `git diff --check` also passed.

A live install is a separate host check: add this checkout as a marketplace, install a plugin, start a new session, select a skill, and review/trust its hook definition. The development environment used for this migration has no `codex` executable, so local structural validation and script tests do not establish that a specific desktop/CLI release has loaded the package. The remote branch must be pushed before the remote install command can work.

## References

Checked against the installed OpenAI plugin examples and these official references on 2026-10-03:

- [Package your plugin](https://developers.openai.com/plugins/build/plugins): portable manifests, OpenAI extensions, Codex fallback, marketplace paths and CLI registration.
- [Build skills](https://learn.chatgpt.com/docs/build-skills): skill directories, UI metadata, invocation policy, and skill-disable configuration.
- [Hooks](https://learn.chatgpt.com/docs/hooks): `apply_patch` payload, `PLUGIN_ROOT`, hook trust, and feedback semantics.
- [Developer commands](https://learn.chatgpt.com/docs/developer-commands): marketplace commands and session resume.
