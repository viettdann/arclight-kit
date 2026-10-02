# arclight-kit

Claude Code marketplace with three plugins:

- `arc-design`: UI design, redesign, restyle, rendering checks, and interaction rules.
- `arc-kit`: session working rules, plan-to-commit workflow, refactor, fresh-air, and the comment-lint hook.
- `mgi-kit`: MGI .NET and TypeScript stack skills (API breaking change detection).

## Which skill

| Situation | Skill |
| --- | --- |
| Nothing exists yet: new page, screen, or project; tokens, themes, dark mode, `DESIGN.md` | `arc-design:design` |
| It exists and you want a new look (new style or direction), keeping content, URLs, and behavior | `arc-design:redesign` |
| It exists and looks generated; keep the layout, remove the AI tells | `arc-design:restyle` |
| A page runs; measure what breaks when it renders: overflow, clipped or overlapping text, contrast per theme, focus, names, targets, images, JS errors | `arc-design:ui-check` |
| Behavior and states: forms, tables, overlays, feedback, destructive actions, settings | `arc-design:ui-interaction` (used alongside the others) |
| Start of any coding session: load the working rules (chat language, scope of a go-ahead, shared-worktree git, docs, comments, commits, migrations, UI) | `/arc-kit:arc` (user-invoked only) |
| Non-trivial feature or design decision before any code | `arc-kit:brainstorming` |
| A plan exists; stress-test it before executing | `arc-kit:plan-auditor` |
| A plan exists; implement it step by step with TDD, sub-agents, and verification | `arc-kit:executor` |
| Restructure existing code without changing behavior: extract, rename, split, reduce complexity, remove duplication | `arc-kit:refactor` |
| Work is done or about to be committed: completeness check, then review | `arc-kit:verifier` |
| Ending or pausing a session; resuming after `/clear` instead of `/compact` | `arc-kit:handoff` |
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

## Changes

- **arc-design 1.0.0**: First release.
  - `design`: new UI from a profile (tool or marketing) plus an optional style (`minimal`, `premium`, `brutalist`, `cinematic`, `playful`). Always loads tokens, typography, radius, and `materials.md` (solid and hairline, lightness layers, shadow, glass for layers floating over moving content, scrim, gradient and glow, texture, tint fill); cards, avatars, and dark mode on demand. Writes the project's `DESIGN.md`. Scripts: `contrast.mjs` (WCAG pairs, stacked backgrounds such as `"<tint> over <backdrop>"`) and `screenshot.mjs` (any width, light or dark, emulated media, `--wait-for`, `--eval`, keyboard `--focus`, real `--hover`, one element with `--selector`, exit 1 on horizontal overflow).
  - `redesign`: a new visual language for an existing product, keeping content, information architecture, URLs, and behavior; snapshots the source first and checks what it preserved with `preserve_check.py`.
  - `restyle`: removes AI tells from a generated-looking UI while keeping the layout; `scan_tells.py` finds them in code, and critique-only mode reports at most three findings by user impact.
  - `ui-check`: loads a running page at 375, 768, 1280, and 1920px and reports measured defects by severity: the element causing horizontal overflow, clipped and overlapping text, contrast per text element in each theme, focus with no visible change, controls without an accessible name, small targets, broken or distorted images, heading structure, JS errors, and failed requests. Fixes only when asked; `restyle` and `redesign` run it to verify.
  - `ui-interaction`: behavior and state rules for forms, tables, overlays, navigation, feedback, destructive actions, and settings, used alongside the other design skills.
- **arc-kit 1.0.0**: First release.
  - `/arc-kit:arc`: session working rules (chat language, scope of a go-ahead, shared-worktree git, docs, comments, commits, migrations, UI), including no placeholders in code and names and strings findable by grep.
  - Workflow: `brainstorming` (design dialogue, approval gate, design doc in `docs/plans/`), `plan-auditor` (stress-tests a plan before execution), `executor` (implements it with TDD, sub-agents, and continuous verification), `verifier` (completeness check against the plan, then parallel review for reuse, quality, efficiency, correctness and security, comments, and docs), `handoff` (session handoff file instead of `/compact`).
  - `refactor`: pins behavior with characterization tests, maps the contract surface and its consumers, and moves in small verified steps; wide scopes stop for approval first.
  - `fresh-air` blocks a project's own skills, commands, and `CLAUDE.md`, and restores them; the `comment-lint` hook flags wrapped, overlong, banner, and narrative comments.
- **mgi-kit 0.1.0**: First release.
  - `api-contract`, adapted from github/awesome-copilot (MIT): audits ASP.NET controllers, Minimal API endpoints, and DTOs against their TypeScript/JavaScript consumers in both directions; diff-scoped by default. `refactor` and `verifier` run it when it is installed.
