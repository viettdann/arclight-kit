# arclight-kit

Claude Code marketplace with three plugins:

- `arc-design`: UI design, redesign, restyle, rendering checks, interaction rules, and state-check audits.
- `arc-kit`: daily session defaults (`arc`), standalone planning and review skills, debug, research, writing, handoff, refactor, conventions, fresh-air, the `test-runner` agent, and the comment-lint, arc-compact, and destructive-guard hooks.
- `mgi-kit`: MGI .NET and TypeScript stack skills (API breaking change detection, .NET version upgrades).

## Which skill

| Situation | Skill |
| --- | --- |
| Nothing exists yet: new page, screen, or project; tokens, themes, dark mode, `DESIGN.md` | `arc-design:design` |
| It exists and you want a new look (new style or direction), keeping content, URLs, and behavior | `arc-design:redesign` |
| It exists and looks generated; keep the layout, remove the AI tells | `arc-design:restyle` |
| A page runs; measure what breaks when it renders: overflow, clipped or overlapping text, contrast per theme, focus, names, targets, images, JS errors | `arc-design:ui-check` |
| Behavior and states: forms, tables, overlays, feedback, destructive actions, settings, motion | `arc-design:ui-interaction` (used alongside the others) |
| A control does nothing or the wrong thing; a shared store action changed: trace each handler's state writes against what its label promises | `arc-design:state-check` |
| Session start in a project without your own CLAUDE.md: load the daily defaults (chat language, scope of a go-ahead, shared-worktree git, docs, comments, commits, reuse and minimal code, migrations, UI). Lowest priority: the project's CLAUDE.md and the running skill win; reloaded after compaction | `/arc-kit:arc` (user-invoked only) |
| Non-trivial feature or design decision before any code | `arc-kit:brainstorming` |
| A plan exists; stress-test it before executing | `arc-kit:plan-auditor` |
| A plan exists (file or chat); implement it step by step with sub-agents and verification; `tdd` turns on test-first | `arc-kit:executor` |
| Something errors, crashes, returns the wrong result, or regressed: reproduce, narrow with ranked hypotheses, fix the cause, keep a regression test | `arc-kit:debug` |
| Compare libraries, tools, or approaches, or check a current version, limit, price, CVE, or support date, with a source behind every figure | `arc-kit:research` |
| Write or check prose people read (README, docs, design docs, release notes, messages): remove autopilot patterns, keep the writer's voice | `arc-kit:writing` |
| Restructure existing code without changing behavior: extract, rename, split, reduce complexity, remove duplication | `arc-kit:refactor` |
| This session's work is done or about to be committed: completeness check, then review and fixes | `arc-kit:verifier` |
| Work has to continue somewhere this session can't follow (a later session after `/clear`, another repo or harness, a colleague, a forked side task); `resume` picks it up. Same task in this session with a full context: `/compact <what to keep>` instead | `/arc-kit:handoff` (user-invoked only) |
| Existing codebase: write its unwritten conventions into path-scoped `.claude/rules/` files so new code matches, or refresh them | `/arc-kit:conventions` (user-invoked only) |
| Block a project's own skills, commands, and CLAUDE.md, or restore them | `/arc-kit:fresh-air` (user-invoked only) |
| ASP.NET controller or DTO change: check it against its TypeScript/JavaScript consumers | `mgi-kit:api-contract` |
| Move a .NET solution to a newer target framework with its packages, SDK pin, Docker images, and CI | `mgi-kit:dotnet-upgrade` |

`design` combines a **profile** (tool or marketing: density, type size, depth) with an optional **style** (visual language):

| Style | For |
| --- | --- |
| `minimal` | Calm, document-like, Notion/Linear feel; tool or marketing |
| `premium` | Premium consumer, soft radii, diffused depth, slow motion; marketing |
| `brutalist` | Swiss print or terminal, visible grid, zero ornament; tool or marketing |
| `cinematic` | Immersive, scroll-paced storytelling, viewport-scale type, full-bleed imagery, dark tech; marketing |
| `playful` | Bubbly or neo-brutal, saturated multi-hue palette, chunky type, springs; marketing or consumer app |

No style named → the profile alone is the direction. Surface materials (solid and hairline, shadow, glass, scrim, gradient, texture) are shared by every style in `design/references/materials.md`; glass is a material for floating layers, not a style.

## Install

```bash
claude plugin marketplace add viettdann/arclight-kit
claude plugin install arc-design@arclight-kit
claude plugin install arc-kit@arclight-kit
claude plugin install mgi-kit@arclight-kit
```

Install any one alone; none depends on another. `arc-kit:refactor` and `arc-kit:verifier` run `mgi-kit:api-contract` when both are installed. Upgrading from `arclight`: `claude plugin uninstall arclight@arclight-kit` first.

Optional runtimes: `node` for `design`'s contrast checker, Node 22+ and Chrome, Chromium, or Edge for the screenshot script (`restyle` and `redesign` check the rendered page with it, `design` uses it when asked), the same for `ui-check` (it needs a running page or a static file), `python3` for `restyle`'s tell scanner and `redesign`'s preserve check. Without them the skills still work and say what wasn't machine-checked. `arc-kit` needs `python3` for the comment-lint and destructive-guard hooks and `fresh-air`.

## Agents

`arc-kit` ships `test-runner`: it runs a test command or the suite and returns only the counts and each failure with its location, message, likely cause, and whether a rerun passes, so long test output stays out of the main context. It reports and never fixes. `executor` (Phase 4) and `refactor` (baseline and verify) hand slow or full runs to it.

## Hooks

`arc-kit` registers `comment-lint` (`PostToolUse` on `Edit|Write`): it flags newly added comments that are wrapped across lines, longer than the width limit, banners or dividers, multi-line `/* */` blocks, or narrative Markdown headings (`Rationale`, `Background`, `Alternatives`), and exits 2 so Claude fixes them. It reports once per tool call even if the same script version is registered elsewhere (e.g. `~/.claude/settings.json`); check active hooks with `/hooks`.

| Option | Default | Effect |
| --- | --- | --- |
| `comment_lint_enabled` | `true` | Turn the hook off without disabling the plugin. |
| `comment_lint_width` | `150` | Max columns for a single-line comment (80–300). |
| `destructive_guard_enabled` | `false` | Turn on the destructive-command guard. |

Set them in `/config` or when enabling the plugin. Tests: `python3 plugins/arc-kit/scripts/comment_lint_test.py`.

`arc-kit` also registers `destructive-guard` (`PreToolUse` on `Bash`), off by default. It splits compound commands, including `$( )`, backticks, `bash -c` (and `-lc`), and wrappers such as `sudo`, `timeout`, and `xargs`, and treats heredoc bodies as data. It blocks recursive `rm` or `find -delete` of `/`, `~`, `$HOME`, or `..`, `${IFS}` tricks, and base64 piped into a shell. It asks first for other recursive `rm` and `find -delete`, `rsync --delete`, git discards (`reset --hard`, `checkout .`, `restore`, `clean -f`, `stash drop`, `branch -D`), SQL `DROP`/`TRUNCATE`/`DELETE` without `WHERE` sent to a SQL client, `docker system|image|container|network|builder prune`, `docker volume rm|prune`, `docker rm -f`, `docker compose down -v`, `kubectl delete`, `terraform destroy`, `chmod -R 777`, `dd of=/dev/`, and `mkfs`. `git push` is never checked. Deleting build artifacts by relative path and temp paths goes through without a prompt. Turn it on with `destructive_guard_enabled`; when off, the hook exits before starting Python. Tests: `python3 plugins/arc-kit/scripts/destructive_guard_test.py`.

`arc-kit` also registers `arc-compact` (`SessionStart` on `compact`): when `/arc-kit:arc` was typed earlier in the session, it re-injects the `arc` rules after compaction; otherwise it prints nothing. It needs `sh`, `sed`, and `grep`.

## Checks

`python3 scripts/skill_lint_test.py` checks every skill and agent: frontmatter, description and body budgets, referenced paths, qualified skill names, README and `plugin.json` listings, and that each `plugin.json` version matches its changelog. `python3 plugins/arc-design/skills/restyle/scripts/scan_tells_test.py` and `python3 plugins/arc-kit/skills/verifier/scripts/collect_diff_test.py` cover their scripts.

## Changes

Each plugin keeps its own changelog: [`arc-design`](plugins/arc-design/CHANGELOG.md), [`arc-kit`](plugins/arc-kit/CHANGELOG.md), [`mgi-kit`](plugins/mgi-kit/CHANGELOG.md).
