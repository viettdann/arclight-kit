# arclight-kit for Codex

Three independent Codex plugins, containing 20 skills:

- **arc-design**: design new UI, redesign or refine existing UI, check rendering, implement interaction states, and trace what controls do to state.
- **arc-kit**: daily session defaults, planning, execution, debugging, research, writing, review, refactoring, conventions, handoffs, reversible project-skill disabling, and the comment-lint, arc-reload, and opt-in destructive-guard hooks.
- **mgi-kit**: audit ASP.NET API contracts against TypeScript and JavaScript consumers, and upgrade .NET solutions.

This branch targets Codex. See [the migration analysis](docs/codex-migration.md) for the platform changes and compatibility limits.

## Install

Use a Codex host with plugin marketplace support. From this checkout:

```bash
codex plugin marketplace add .
codex plugin marketplace list
codex
```

Open `/plugins`, select the `arclight-kit` marketplace, and install the plugins you want. Start a new session to load their skills. In the desktop app, open this project, restart the app, and select the repo marketplace in the plugin browser. Each plugin can be installed independently.

Once the `codex` branch has been pushed, register it remotely with:

```bash
codex plugin marketplace add viettdann/arclight-kit --ref codex
```

Check `codex plugin marketplace --help` if your installed CLI uses a different command set. Marketplace support depends on the host version; copying a plugin into the workspace does not by itself install or activate it. This repository does not modify your personal Codex configuration during validation.

Plugin hooks need review and trust in Codex before they run. Enable hooks in the host if disabled; do not treat installation as hook activation. See [OpenAI's plugin packaging guide](https://developers.openai.com/plugins/build/plugins) and [hook documentation](https://learn.chatgpt.com/docs/hooks).

## Choose a skill

Use `$` autocomplete to select an installed skill, or name the plugin and skill in your request. The catalog may display a plugin-qualified name such as `arc-kit:executor`; use the identifier exposed by your host when names collide.

| Task | Plugin | Skill |
| --- | --- | --- |
| New page, screen, tokens, themes, or `DESIGN.md` | arc-design | `$design` |
| New visual direction, preserving content and behavior | arc-design | `$redesign` |
| Refine a generic UI while preserving layout | arc-design | `$restyle` |
| Measure rendering and accessibility defects | arc-design | `$ui-check` |
| Forms, tables, navigation, overlays, and async states | arc-design | `$ui-interaction` |
| A control does nothing or the wrong thing; trace its state writes | arc-design | `$state-check` |
| Apply the daily defaults (chat language, scope, git, docs, comments, reuse and minimal code, UI); lowest priority, reloaded after compaction | arc-kit | `$arc` (explicit only) |
| Explore a non-trivial feature or architectural decision | arc-kit | `$brainstorming` |
| Audit a proposed implementation plan | arc-kit | `$plan-auditor` |
| Implement an existing plan; `tdd` turns on test-first | arc-kit | `$executor` |
| Reproduce a bug, confirm its cause, fix it once, keep a regression test | arc-kit | `$debug` |
| Compare libraries or approaches, or check a version, limit, price, CVE, or support date, with sources | arc-kit | `$research` |
| Write, check, or edit prose people read | arc-kit | `$writing` |
| Restructure code while preserving behavior | arc-kit | `$refactor` |
| Check completeness and review a change | arc-kit | `$verifier` |
| Carry work somewhere this session can't follow, or `resume` it | arc-kit | `$handoff` (explicit only) |
| Write an existing codebase's unwritten conventions into `AGENTS.md` | arc-kit | `$conventions` (explicit only) |
| Disable or restore a project's local skills | arc-kit | `$fresh-air` (explicit only) |
| Check backend/frontend contract drift | mgi-kit | `$api-contract` |
| Move a .NET solution to a newer target framework | mgi-kit | `$dotnet-upgrade` |

`arc` is optional, applies when explicitly selected, and yields to session and project instructions. Naming a skill in a request is enough; these are not Claude plugin slash commands. `refactor` and `verifier` can use `api-contract` when installed; otherwise they check relevant contracts directly. `executor`, `refactor`, and `verifier` run full or slow suites under the test runner brief (`plugins/arc-kit/skills/executor/references/test-runner.md`), delegated when the runtime allows it, inline otherwise; Codex plugins don't package custom agents.

`design` combines a **profile** (`tool`, `marketing`, or `read`) with an optional **style**:

| Style | Direction |
| --- | --- |
| `minimal` | Calm, document-like, warm monochrome |
| `premium` | Consumer surfaces, soft corners, restrained depth |
| `brutalist` | Swiss print or terminal, visible grid |
| `cinematic` | Immersive, scroll-paced, image-led |
| `playful` | Saturated palette, chunky type, spring motion |

Only load references needed by the task. Bundled script paths resolve from the installed skill's directory, while target project paths resolve from the project's working directory.

Keep each `SKILL.md` within 8,000 UTF-8 bytes, including frontmatter. Codex truncates larger skill prompts at this [runtime limit](https://github.com/openai/codex/blob/main/codex-rs/ext/skills/src/render.rs). Put detailed workflows and examples in `references/` and state when to read them in the entrypoint. Paths inside those references resolve from the skill directory unless stated otherwise. Skill lint enforces the entrypoint budget.

## Runtime requirements

- Python 3.11+ for `fresh-air` and repository validation; Python 3 for the other Python helpers.
- `git` and `sh` for the verifier's diff collector; `bash` for the debug skill's human-in-the-loop repro script.
- Node 22+ for browser helpers; Chrome, Chromium, or Edge available locally (including a supported Playwright browser cache). `CHROME=/absolute/path` selects a browser.
- A running page or static HTML file for rendering checks. Skill instructions allow starting the project's existing local dev command for an authorized check.
- Delegation is optional. Workflow skills use available Codex sub-agent tools only when allowed, inherit runtime model/concurrency settings, and work inline when delegation is unavailable.

Missing browser/runtime capabilities are reported as unchecked portions of a task. No MCP server or connector is required by these plugins.

## Comment lint

`arc-kit` registers `PostToolUse` for `apply_patch` and reads `tool_input.command`. It checks added comments in patch results for wrapping, excessive width, banners, multi-line block comments, and narrative Markdown headings. Findings return feedback to Codex; the edit has already happened.

| Environment variable | Default | Effect |
| --- | --- | --- |
| `ARC_COMMENT_LINT_ENABLED` | `true` | Set to `false`, `0`, `no`, or `off` to disable. |
| `ARC_COMMENT_LINT_WIDTH` | `150` | Width threshold, minimum 60 columns. |

Set these in the environment that launches Codex. They are script options, not Codex plugin settings. Shell-written changes do not trigger this hook. Check those files explicitly:

```bash
python3 plugins/arc-kit/scripts/comment-lint.py --files path/to/file.ts path/to/file.py
```

The standalone command checks all lines of the named files. The hook checks only added lines it can locate reliably in the final file; ambiguous patch context may leave lines unchecked. Files outside the hook working directory, generated files, unsupported/binary files, and inputs larger than 2 MB are skipped. This is a style aid, not an enforcement boundary.

## Destructive guard

Enable with `ARC_DESTRUCTIVE_GUARD_ENABLED=true` in the environment that launches Codex; it is off by default. The `PreToolUse` hook matches `Bash`, including unified exec. It blocks the upstream destructive-command patterns: recursive deletion, Git discards, broad SQL deletion, container and infrastructure teardown, raw device writes, and encoded shell payloads. Relative build artifacts and temporary paths follow the upstream allowlist. `git push` is not checked.

Codex does not support `permissionDecision: "ask"` yet, so both upstream ask and deny findings return `deny`. The reason tells the user to run an intended command outside Codex. See [the hook output contract](https://learn.chatgpt.com/docs/hooks). This is a guardrail; interactive stdin and specialized tool paths can bypass inspection.

## Arc reload

`arc-kit` also registers `SessionStart` on `compact`: when `$arc` was invoked earlier in the session (read from the session transcript, whose format Codex doesn't guarantee), `scripts/arc-compact.py` re-injects the `arc` defaults after compaction; otherwise it prints nothing. It needs Python 3 and the same hook trust as comment lint.

## Fresh air

`$fresh-air` disables discovered project `.agents/skills` using documented `[[skills.config]]` entries in your Codex user configuration. Its `off`, `status`, and `restore` commands operate on a named project; restore removes only entries owned by this helper. Review the skill's [usage and limits](plugins/arc-kit/skills/fresh-air/SKILL.md) before using it. Start a new Codex session after a configuration change.

Project `AGENTS.md` instructions, plugins, MCP servers, and hooks remain active. This tool is not a sandbox or an instruction-isolation mechanism.

## Validate

```bash
python3 scripts/validate_plugins.py
node --test scripts/cdp_auth_test.mjs
python3 -m unittest discover -s scripts -p '*_test.py'
python3 plugins/arc-kit/scripts/comment_lint_test.py
python3 plugins/arc-kit/scripts/arc_compact_test.py
python3 plugins/arc-kit/scripts/destructive_guard_test.py
python3 plugins/arc-design/skills/restyle/scripts/scan_tells_test.py
python3 plugins/arc-kit/skills/verifier/scripts/collect_diff_test.py
python3 -m unittest discover -s plugins/arc-kit/skills/fresh-air/tests
```

The validator checks this repo's package conventions, fallback-manifest consistency, skill metadata, bundled references, and hook wiring. It is not a replacement for a host installation test.

Each plugin keeps its own changelog: [arc-design](plugins/arc-design/CHANGELOG.md), [arc-kit](plugins/arc-kit/CHANGELOG.md), [mgi-kit](plugins/mgi-kit/CHANGELOG.md). The API contract skill retains its upstream [MIT notice](plugins/mgi-kit/skills/api-contract/LICENSE.txt).
