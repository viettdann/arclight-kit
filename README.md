# claude-ux-skills

Claude Code marketplace with one plugin, `arclight`.

## Which skill

| Situation | Skill |
| --- | --- |
| Nothing exists yet: new page, screen, or project; tokens, themes, dark mode, `DESIGN.md` | `arclight:design` |
| It exists and you want a new look (new style or direction), keeping content, URLs, and behavior | `arclight:redesign` |
| It exists and looks generated; keep the layout, remove the AI tells | `arclight:restyle` |
| Behavior and states: forms, tables, overlays, feedback, destructive actions, settings | `arclight:ui-interaction` (used alongside the others) |
| Start of any coding session: load the working rules (chat language, scope of a go-ahead, shared-worktree git, docs, comments, commits, migrations, UI) | `/arclight:arc` (user-invoked only) |

`design` combines a **profile** (tool or marketing: density, type size, depth) with an optional **style** (visual language):

| Style | For |
| --- | --- |
| `editorial-minimal` | Calm, document-like, Notion/Linear feel; tool or marketing |
| `soft-premium` | Premium consumer, soft radii, diffused depth, slow motion; marketing |
| `brutalist` | Swiss print or terminal, visible grid, zero ornament; tool or marketing |

No style named → the profile alone is the direction.

## Install

```bash
claude plugin marketplace add viettdann/claude-ux-skills
claude plugin install arclight@claude-ux-skills
```

Optional runtimes: `node` for `design`'s contrast checker, Node 22+ and Chrome, Chromium, or Edge for the screenshot script (`restyle` and `redesign` check the rendered page with it, `design` uses it when asked), `python3` for `restyle`'s tell scanner and `redesign`'s preserve check. Without them the skills still work and say what wasn't machine-checked.

## Changes

- **0.4.0**: Add `arc` skill (`/arclight:arc`, user-invoked only): the arclight projects' shared working rules plus three new ones: an answer is not a go-ahead, a go-ahead covers everything recommended and not dropped, an explicit command is the confirmation.
- **0.3.2**: Add `design/scripts/screenshot.mjs` (any width, several widths per call, `--full`, `--eval`, `--root`, exit 1 on horizontal overflow); `restyle` step 5 and `redesign` step 7 check the rendered page with it. `contrast.mjs` takes hex, `rgb()`, and `oklch()` as written. `restyle` drops the audit table; `redesign`'s audit becomes working notes; reports list only flagged behavior, changes to protected items, placeholders, and checks that couldn't run.
- **0.3.1**: Cross-skill paths use `${CLAUDE_PLUGIN_ROOT}/skills/<skill>/`. `overlays.md` split into `overlays.md`, `navigation.md`, and `gestures.md`. Fix contradictions: `aria-disabled` for typed confirm and empty filter chips, touch targets 44px coarse / 24px fine, accent off focus rings, weights 400/600, soft-premium full-bleed bands square. `restyle`: 3:1 input borders, type-scale value sizes, `code` group for behavior tells, contrast step, no em dashes. `design`: Tailwind v4 `text-text-muted` naming trap, easing names that don't shadow Tailwind's. Scripts: `scan_tells.py` and `preserve_check.py` exit 2 on a missing path, fewer false positives, meta-description parsing fixed, `contrast.mjs` accepts `rgb()` and clamps alpha.
- **0.3.0**: `design` adds `typography.md` and `radius.md` (always loaded) and `cards.md`, `avatars.md`, `dark-mode.md` (on demand); tool radius sm 4 / md 6 / lg 12; marketing radius per element. `ui-interaction` adds `settings.md`, inline edit, context menus, narrow tables, selection scope, badges, copy to clipboard, scroll restoration, sticky headers, resize handles, pull to refresh. `restyle` scanner adds surface, decoration, and code-tell rules.
- **0.2.1**: Skill paths use `${CLAUDE_SKILL_DIR}` instead of a `<skill-dir>` placeholder. `redesign` snapshots the source folder to a temp dir before editing instead of using `git stash`, lists classes that tests and analytics use during the audit, updates an existing `DESIGN.md` with the new direction, and gives full paths to the contrast script and the ui-interaction skill. `design` parses the style argument first, runs the marketing tell scan from its workflow, and reports contrast pairs that still fail. `restyle` decides hierarchy in a fixed order (state page, ordered peers, primary or equal), leaves a `TODO` instead of adding props, and writes the audit as a fixed-column table. `ui-interaction` splits verification into steps, defines when to skip the state note, and drops rules that repeat the always-loaded baseline.
- **0.2.0**: `ui-visual` renamed to `design`, with styles (`editorial-minimal`, `soft-premium`, `brutalist`) on top of the tool and marketing profiles. New `redesign` skill with `preserve_check.py`. Marketing profile extended (design read, layout, imagery, copy tells); scanner covers marketing and code tells.
