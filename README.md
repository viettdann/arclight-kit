# arclight-kit

Claude Code marketplace with three plugins:

- `arc-design`: UI design, redesign, restyle, rendering checks, interaction rules, and state-check audits.
- `arc-kit`: daily session defaults (`arc`), standalone planning and review skills, handoff, refactor, conventions, fresh-air, and the comment-lint and arc-compact hooks.
- `mgi-kit`: MGI .NET and TypeScript stack skills (API breaking change detection).

## Which skill

| Situation | Skill |
| --- | --- |
| Nothing exists yet: new page, screen, or project; tokens, themes, dark mode, `DESIGN.md` | `arc-design:design` |
| It exists and you want a new look (new style or direction), keeping content, URLs, and behavior | `arc-design:redesign` |
| It exists and looks generated; keep the layout, remove the AI tells | `arc-design:restyle` |
| A page runs; measure what breaks when it renders: overflow, clipped or overlapping text, contrast per theme, focus, names, targets, images, JS errors | `arc-design:ui-check` |
| Behavior and states: forms, tables, overlays, feedback, destructive actions, settings | `arc-design:ui-interaction` (used alongside the others) |
| A control does nothing or the wrong thing; a shared store action changed: trace each handler's state writes against what its label promises | `arc-design:state-check` |
| Session start in a project without your own CLAUDE.md: load the daily defaults (chat language, scope of a go-ahead, shared-worktree git, docs, comments, commits, reuse and minimal code, migrations, UI). Lowest priority: the project's CLAUDE.md and the running skill win; reloaded after compaction | `/arc-kit:arc` (user-invoked only) |
| Non-trivial feature or design decision before any code | `arc-kit:brainstorming` |
| A plan exists; stress-test it before executing | `arc-kit:plan-auditor` |
| A plan exists (file or chat); implement it step by step with sub-agents and verification; `tdd` turns on test-first | `arc-kit:executor` |
| Restructure existing code without changing behavior: extract, rename, split, reduce complexity, remove duplication | `arc-kit:refactor` |
| This session's work is done or about to be committed: completeness check, then review and fixes | `arc-kit:verifier` |
| Ending or pausing a session; resuming after `/clear` instead of `/compact` | `arc-kit:handoff` |
| Existing codebase: write its unwritten conventions into path-scoped `.claude/rules/` files so new code matches, or refresh them | `arc-kit:conventions` |
| Block a project's own skills, commands, and CLAUDE.md, or restore them | `arc-kit:fresh-air` |
| ASP.NET controller or DTO change: check it against its TypeScript/JavaScript consumers | `mgi-kit:api-contract` |

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

Optional runtimes: `node` for `design`'s contrast checker, Node 22+ and Chrome, Chromium, or Edge for the screenshot script (`restyle` and `redesign` check the rendered page with it, `design` uses it when asked), the same for `ui-check` (it needs a running page or a static file), `python3` for `restyle`'s tell scanner and `redesign`'s preserve check. Without them the skills still work and say what wasn't machine-checked. `arc-kit` needs `python3` for the comment-lint hook and `fresh-air`.

## Hooks

`arc-kit` registers `comment-lint` (`PostToolUse` on `Edit|Write`): it flags newly added comments that are wrapped across lines, longer than the width limit, banners or dividers, multi-line `/* */` blocks, or narrative Markdown headings (`Rationale`, `Background`, `Alternatives`), and exits 2 so Claude fixes them. It reports once per tool call even if the same script version is registered elsewhere (e.g. `~/.claude/settings.json`); check active hooks with `/hooks`.

| Option | Default | Effect |
| --- | --- | --- |
| `comment_lint_enabled` | `true` | Turn the hook off without disabling the plugin. |
| `comment_lint_width` | `150` | Max columns for a single-line comment (80–300). |

Set them in `/config` or when enabling the plugin. Tests: `python3 plugins/arc-kit/scripts/comment_lint_test.py`.

`arc-kit` also registers `arc-compact` (`SessionStart` on `compact`): when `/arc-kit:arc` was typed earlier in the session, it re-injects the `arc` rules after compaction; otherwise it prints nothing. It needs `sh`, `sed`, and `grep`.

## Changes

Each plugin keeps its own changelog: [`arc-design`](plugins/arc-design/CHANGELOG.md), [`arc-kit`](plugins/arc-kit/CHANGELOG.md), [`mgi-kit`](plugins/mgi-kit/CHANGELOG.md).
